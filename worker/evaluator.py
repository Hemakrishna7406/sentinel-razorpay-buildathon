"""
Sentinel — Evaluator Worker

Consumes `IntentSubmitted` events from Kafka (`intents.inbound`).
Computes ML features, runs XGBoost, evaluates policies.
If ALLOW, issues Capability Token.
Publishes `IntentEvaluated` to Kafka (`intents.evaluated`).
Replies via Redis Stream to unblock synchronous HTTP clients.

Production configuration (Phase 20 frozen):
    INFERENCE_BACKEND=cpu
    MAX_CONCURRENT_TASKS=2
    XGB_NTHREAD=4
    Kafka inbound partitions=4

Observability (Phase 21):
    Structured JSON logs via observability.logging
    Prometheus metrics via observability.metrics (scraped on METRICS_PORT)
    OTel traces via observability.tracing (OTLP -> Jaeger, optional)
    All observability is non-authoritative — failures never affect decisions.
"""

import asyncio
import json
import os
import time
import threading

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer, TopicPartition, OffsetAndMetadata
import redis.asyncio as redis
import pandas as pd
import xgboost as xgb

from api.dependencies import ModelWrapper
from security.policy import PolicyEngine
from security.capability_token import IntentContext
from observability.logging import get_logger
from observability.metrics import (
    DECISIONS_TOTAL, WORKER_ACTIVE_TASKS, WORKER_CAPACITY,
    WORKER_QUEUE_WAIT, WORKER_PROCESSING, ML_INFERENCE_LATENCY,
    ML_ERRORS_TOTAL, KAFKA_ERRORS_TOTAL, record_decision,
)
from observability.tracing import get_tracer, inject_trace_context, extract_trace_context

logger = get_logger(__name__)
tracer = get_tracer("sentinel.worker")

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:29092")
INBOUND_TOPIC = os.environ.get("KAFKA_INBOUND_TOPIC", "intents.inbound")
EVALUATED_TOPIC = os.environ.get("KAFKA_EVALUATED_TOPIC", "intents.evaluated")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
METRICS_PORT = int(os.environ.get("METRICS_PORT", "8001"))

INFERENCE_BACKEND = os.environ.get("INFERENCE_BACKEND", "cpu").lower()
GPU_BATCH_SIZE = int(os.environ.get("GPU_BATCH_SIZE", "16"))
GPU_BATCH_TIMEOUT_MS = int(os.environ.get("GPU_BATCH_TIMEOUT_MS", "5"))


def _start_metrics_server() -> None:
    """Start a lightweight HTTP server to expose /metrics for Prometheus scraping."""
    try:
        from prometheus_client import start_http_server
        start_http_server(METRICS_PORT)
        logger.info("Prometheus metrics server started", port=METRICS_PORT)
    except Exception as e:
        logger.warning("Metrics server failed to start — authorization unaffected", error=str(e))


class OffsetTracker:
    def __init__(self, consumer):
        self.consumer = consumer
        self.in_flight = {}
        self.max_seen = {}
        self.lock = asyncio.Lock()

    async def track_start(self, tp, offset):
        async with self.lock:
            if tp not in self.in_flight:
                self.in_flight[tp] = set()
                self.max_seen[tp] = -1
            self.in_flight[tp].add(offset)
            self.max_seen[tp] = max(self.max_seen[tp], offset)

    async def mark_done_and_commit(self, tp, offset):
        async with self.lock:
            if offset in self.in_flight.get(tp, set()):
                self.in_flight[tp].remove(offset)

            if not self.in_flight.get(tp):
                safe_offset = self.max_seen[tp]
            else:
                safe_offset = min(self.in_flight[tp]) - 1

            if safe_offset >= 0:
                await self.consumer.commit({
                    tp: OffsetAndMetadata(safe_offset + 1, "")
                })


class BatchInferenceQueue:
    """GPU batch inference queue — experimental, not the production path."""

    def __init__(self, model_wrapper, batch_size, timeout_ms):
        self.model_wrapper = model_wrapper
        self.batch_size = batch_size
        self.timeout_sec = timeout_ms / 1000.0
        self.queue = []
        self.lock = asyncio.Lock()
        self.event = asyncio.Event()
        self.task = asyncio.create_task(self._worker_loop())

    async def predict(self, features_dict):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        enqueue_time = time.perf_counter()
        async with self.lock:
            self.queue.append((features_dict, fut, enqueue_time))
            if len(self.queue) >= self.batch_size:
                self.event.set()
        return await fut

    async def _worker_loop(self):
        while True:
            try:
                await asyncio.wait_for(self.event.wait(), timeout=self.timeout_sec)
            except asyncio.TimeoutError:
                pass

            self.event.clear()

            async with self.lock:
                if not self.queue:
                    continue
                batch = self.queue[:self.batch_size]
                self.queue = self.queue[self.batch_size:]
                if len(self.queue) >= self.batch_size:
                    self.event.set()

            if not batch:
                continue

            try:
                features_list = [item[0] for item in batch]
                futs = [item[1] for item in batch]
                enqueue_times = [item[2] for item in batch]

                start_inf = time.perf_counter()

                def sync_predict():
                    df = pd.DataFrame(features_list)[self.model_wrapper.features]
                    dmatrix = xgb.DMatrix(df)
                    return self.model_wrapper.model.predict(dmatrix)

                preds = await asyncio.to_thread(sync_predict)
                end_inf = time.perf_counter()
                inf_ms = (end_inf - start_inf) * 1000

                for i, fut in enumerate(futs):
                    wait_ms = (start_inf - enqueue_times[i]) * 1000
                    fut.set_result((float(preds[i]), wait_ms, inf_ms))

            except Exception as e:
                logger.error("Batch inference failed", error=str(e))
                for _, fut, _ in batch:
                    try:
                        fut.set_exception(e)
                    except Exception:
                        pass


async def main():
    logger.info("Starting Evaluator Worker",
                inference_backend=INFERENCE_BACKEND,
                max_concurrent_tasks=os.environ.get("MAX_CONCURRENT_TASKS", "2"),
                xgb_nthread=os.environ.get("XGB_NTHREAD", "4"))

    # Start metrics scrape server in a background thread (non-blocking)
    threading.Thread(target=_start_metrics_server, daemon=True).start()

    model_wrapper = ModelWrapper()
    model_wrapper.load()
    policy_engine = PolicyEngine(suspicious_threshold=model_wrapper.suspicious_threshold)

    gpu_queue = None
    if INFERENCE_BACKEND == "gpu":
        gpu_queue = BatchInferenceQueue(model_wrapper, GPU_BATCH_SIZE, GPU_BATCH_TIMEOUT_MS)
        logger.info("GPU Batch Queue initialized",
                    batch_size=GPU_BATCH_SIZE, timeout_ms=GPU_BATCH_TIMEOUT_MS)

    from ml.providers.semantic_engine import SimulatedSemanticClient
    from ml.fusion.risk_fusion import RiskFusionEngine
    from ml.features import extract_features
    from ml.schema import BehavioralRiskResult, RiskAssessment, Decision

    semantic_client = SimulatedSemanticClient()
    risk_fusion = RiskFusionEngine(
        disagreement_threshold=0.6,
        base_escalation_threshold=model_wrapper.suspicious_threshold
    )

    consumer = AIOKafkaConsumer(
        INBOUND_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id="sentinel-evaluator-group",
        auto_offset_reset="earliest",
        enable_auto_commit=False
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)

    await consumer.start()
    await producer.start()

    MAX_CONCURRENT_TASKS = int(os.environ.get("MAX_CONCURRENT_TASKS", "2"))
    try:
        WORKER_CAPACITY.set(MAX_CONCURRENT_TASKS)
    except Exception:
        pass

    logger.info("Evaluator Worker ready",
                max_concurrent_tasks=MAX_CONCURRENT_TASKS,
                inference_backend=INFERENCE_BACKEND,
                kafka_topic=INBOUND_TOPIC)

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
    tracker = OffsetTracker(consumer)
    tasks = set()

    async def process_message(msg):
        receive_time = time.perf_counter()
        tp = TopicPartition(msg.topic, msg.partition)
        offset = msg.offset
        await tracker.track_start(tp, offset)

        try:
            WORKER_ACTIVE_TASKS.inc()
        except Exception:
            pass

        intent_id = "unknown"
        agent_id = "unknown"
        decision_value = "ESCALATE"
        reason = "DEPENDENCY_FAILURE"

        try:
            # Record queue wait time
            try:
                WORKER_QUEUE_WAIT.observe(time.perf_counter() - receive_time)
            except Exception:
                pass

            t_start = time.perf_counter()
            start_time = time.time()
            event = json.loads(msg.value.decode('utf-8'))
            t_parse = time.perf_counter()

            # Extract trace context from Kafka payload (non-authoritative)
            otel_ctx = extract_trace_context(event)

            intent_data = event["intent"]
            context_data = event.get("context", {})
            agent_id = event["agent_id"]
            mode = event.get("mode", "govern")
            intent_id = intent_data["intent_id"]

            bound_log = logger.bind(intent_id=intent_id, agent_id=agent_id)

            intent = IntentContext(
                intent_id=intent_id,
                agent_id=agent_id,
                action_type=intent_data["action_type"],
                amount=intent_data["amount"],
                currency=intent_data["currency"],
                recipient=intent_data["recipient"]
            )

            # ── Feature Extraction ──────────────────────────────────────────
            with tracer.start_as_current_span("sentinel.feature.extraction",
                                              context=otel_ctx) as span:
                def extract():
                    return extract_features(context_data)
                features = await asyncio.to_thread(extract)
                t_features = time.perf_counter()

            # ── XGBoost Inference ───────────────────────────────────────────
            model_risk = None
            model_available = model_wrapper.model is not None
            queue_wait_ms = 0.0
            inf_ms = 0.0

            with tracer.start_as_current_span("sentinel.xgboost.inference") as span:
                if model_available:
                    if INFERENCE_BACKEND == "gpu" and gpu_queue:
                        try:
                            model_risk, queue_wait_ms, inf_ms = await gpu_queue.predict(features)
                        except Exception as e:
                            logger.error("GPU batch failed — falling back", error=str(e))
                            model_available = False
                            try:
                                ML_ERRORS_TOTAL.inc()
                            except Exception:
                                pass
                    else:
                        def sync_predict():
                            df = pd.DataFrame([features])[model_wrapper.features]
                            dmatrix = xgb.DMatrix(df)
                            return float(model_wrapper.model.predict(dmatrix)[0])
                        try:
                            inf_start = time.perf_counter()
                            model_risk = await asyncio.to_thread(sync_predict)
                            inf_ms = (time.perf_counter() - inf_start) * 1000
                            try:
                                ML_INFERENCE_LATENCY.labels(backend="cpu").observe(inf_ms / 1000.0)
                            except Exception:
                                pass
                        except Exception as e:
                            logger.error("XGBoost inference failed", intent_id=intent_id, error=str(e))
                            model_available = False
                            try:
                                ML_ERRORS_TOTAL.inc()
                            except Exception:
                                pass

            t_ml = time.perf_counter()

            # ── Policy Evaluation ───────────────────────────────────────────
            with tracer.start_as_current_span("sentinel.policy.evaluate") as span:
                def sync_policy():
                    behavioral = BehavioralRiskResult(
                        risk_score=model_risk,
                        risk_status="MODEL_AVAILABLE" if model_available else "MODEL_UNAVAILABLE",
                        confidence=0.92 if model_available else 0.0,
                        reason_codes=(
                            ["VELOCITY_DRIFT"] if model_available and model_risk > 0.5
                            else ["NORMAL"] if model_available
                            else ["MODEL_UNAVAILABLE"]
                        ),
                        model_version="xgb-v3"
                    )

                    if model_available:
                        try:
                            semantic_result = semantic_client.evaluate(intent, context_data)
                        except Exception as e:
                            bound_log.warning("Semantic provider unavailable", error=str(e))
                            semantic_result = None
                    else:
                        semantic_result = None

                    fusion_result = risk_fusion.fuse(behavioral, semantic_result)
                    assessment = RiskAssessment(
                        behavioral=behavioral,
                        semantic=semantic_result,
                        fusion=fusion_result
                    )

                    decision, reason_text, token = policy_engine.evaluate(intent, context_data, assessment)
                    return behavioral, semantic_result, fusion_result, assessment, decision, reason_text, token

                (behavioral, semantic_result, fusion_result, assessment,
                 decision, reason, token) = await asyncio.to_thread(sync_policy)

            t_policy = time.perf_counter()

            processing_s = time.perf_counter() - t_start
            try:
                WORKER_PROCESSING.observe(processing_s)
            except Exception:
                pass

            if mode.lower() == "observe":
                shadow_decision = decision.value
                decision = Decision.ALLOW
                reason = f"[OBSERVE MODE] Shadow decision was {shadow_decision}: {reason}"
                token = None

            decision_value = decision.value

            # Record decision metric (non-authoritative, never raises)
            try:
                record_decision(decision_value, reason)
            except Exception:
                pass

            # ── Risk score metric ───────────────────────────────────────────
            if assessment.fusion.final_risk is not None:
                try:
                    from observability.metrics import RISK_SCORE
                    RISK_SCORE.observe(assessment.fusion.final_risk)
                except Exception:
                    pass

            result = {
                "intent_id": intent.intent_id,
                "agent_id": agent_id,
                "action_type": intent.action_type,
                "amount": intent.amount,
                "currency": intent.currency,
                "recipient": intent.recipient,
                "model_risk_score": assessment.fusion.final_risk,
                "behavioral_risk_score": behavioral.risk_score,
                "semantic_risk_score": semantic_result.risk_score if semantic_result else None,
                "fusion_disagreement": fusion_result.disagreement,
                "decision": decision_value,
                "decision_reason": reason,
                "capability_token": token,
                "timestamp": time.time(),
                "latency_ms": int((time.time() - start_time) * 1000),
                "timings": {
                    "queue_ms": (t_parse - t_start) * 1000,
                    "features_ms": (t_features - t_parse) * 1000,
                    "batch_wait_ms": queue_wait_ms,
                    "gpu_inference_ms": inf_ms,
                    "policy_ms": (t_policy - t_ml) * 1000
                }
            }

            bound_log.info("Intent evaluated",
                           decision=decision_value,
                           model_risk=assessment.fusion.final_risk,
                           latency_ms=result["latency_ms"])

            await producer.send_and_wait(
                EVALUATED_TOPIC,
                key=agent_id.encode('utf-8'),
                value=json.dumps(result).encode('utf-8')
            )

            reply_key = f"reply:{intent.intent_id}"
            await redis_client.xadd(reply_key, {"data": json.dumps(result)}, maxlen=10)
            await redis_client.expire(reply_key, 30)

        except Exception as e:
            logger.error("Error processing message",
                         intent_id=intent_id,
                         agent_id=agent_id,
                         offset=offset,
                         error=str(e))
            try:
                KAFKA_ERRORS_TOTAL.labels(operation="process").inc()
            except Exception:
                pass
        finally:
            try:
                WORKER_ACTIVE_TASKS.dec()
            except Exception:
                pass
            await tracker.mark_done_and_commit(tp, offset)

    try:
        async for msg in consumer:
            await semaphore.acquire()
            task = asyncio.create_task(process_message(msg))
            tasks.add(task)

            def on_done(t):
                tasks.discard(t)
                semaphore.release()

            task.add_done_callback(on_done)
    finally:
        await consumer.stop()
        await producer.stop()
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
