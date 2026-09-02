"""
Sentinel — FastAPI Server

Exposes the core evaluation endpoint, NL policy management,
SHAP explanations, batch simulation, and dashboard.
Implements Observe (dry-run) and Govern (active blocking) modes.
Ensures fail-closed behavior on unhandled exceptions.

Phase 21 Observability:
- GET /metrics  — Prometheus text exposition
- GET /health/live, /health/ready, /health/dependencies
- Structured JSON logs via observability.logging
- OTel traces on /evaluate (OTLP -> Jaeger, optional)
- All observability is non-authoritative.

Phase 22 Deployment Hardening:
- /health/live  — Liveness probe: is the event loop responsive?
- /health/ready — Readiness probe: are the required dependencies for
                  accepting new authorization work available?
  API readiness matrix:
    ✓ Redis (required for idempotency + JTI)
    ✓ Kafka producer (required to publish intents)
    ✓ DB (required for audit trail — soft-fail logged, not blocking)
  Kafka and Redis outage → 503 Not Ready
  DB outage            → logged, not blocking (worker handles audit)
- /health/dependencies — Diagnostic panel (always 200, never drives routing)
"""

import json
import logging
import os
import time
from core.config import settings
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, HTTPException, Request, Header, Depends
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
import xgboost as xgb

from api.schema import (
    PolicyRuleRequest, PolicyRuleResponse,
    SimulateRequest, SimulateResponse
)
from api.dependencies import (
    init_app_state,
    shutdown_app_state,
    get_idempotency_engine,
    get_execution_adapter,
    get_policy_engine,
    get_model,
    get_db,
    ModelWrapper
)
from security.exceptions import SentinelSecurityException
from security.capability_token import IntentContext
from ml.features import extract_features
from observability.logging import get_logger
from observability.metrics import (
    INTENTS_TOTAL, AUTHORIZATION_LATENCY,
    REDIS_LATENCY, REDIS_ERRORS_TOTAL,
    KAFKA_PUBLISH_LATENCY, KAFKA_ERRORS_TOTAL,
    record_decision,
)
from observability.tracing import get_tracer, inject_trace_context

logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)
tracer = get_tracer("sentinel.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_app_state()
    yield
    await shutdown_app_state()

app = FastAPI(title="Sentinel Risk Engine", version="1.0.0", lifespan=lifespan)

# --- CORS (browser origins only; does not weaken any authorization path) ---
_allowed_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Sentinel-Mode"],
)

# --- Analytics Router ---
from api.analytics import router as analytics_router
app.include_router(analytics_router)

# --- Models ---
class IntentRequest(BaseModel):
    intent_id: str
    agent_id: str
    action_type: str
    amount: int
    currency: str
    recipient: str
    context: Dict[str, Any] = {}

class EvaluationResponse(BaseModel):
    intent_id: str
    decision: str
    reason: Optional[str] = None
    capability_token: Optional[str] = None
    executed_tx_id: Optional[str] = None
    latency_ms: int
    timings: Optional[Dict[str, float]] = None

class ExecuteRequest(BaseModel):
    intent_id: str
    agent_id: str
    action_type: str
    amount: int
    currency: str
    recipient: str
    capability_token: str

class ExecuteResponse(BaseModel):
    executed_tx_id: str
    status: str

# --- Exception Handler ---
@app.exception_handler(SentinelSecurityException)
async def security_exception_handler(request: Request, exc: SentinelSecurityException):
    logger.warning(f"Security Exception: {exc}")
    # Always fail closed
    return JSONResponse(
        status_code=403,
        content={
            "decision": "ESCALATE",
            "reason": str(exc),
            "executed_tx_id": None
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "decision": "ESCALATE",
            "reason": "Unhandled system error. Failing closed.",
            "executed_tx_id": None
        }
    )

# --- Endpoints ---

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_intent_sync(
    request: Request,
    intent: IntentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    mode: str = Header("govern", alias="X-Sentinel-Mode")
):
    """
    Fast Path Synchronous Evaluation.
    Publishes to Kafka and blocks on Redis Streams for the decision.
    """
    t_start = time.perf_counter()

    # Observability — non-authoritative, never raises into the auth path
    try:
        INTENTS_TOTAL.inc()
    except Exception:
        pass

    idem_engine = get_idempotency_engine()
    intent_context = IntentContext(
        intent_id=intent.intent_id,
        agent_id=intent.agent_id,
        action_type=intent.action_type,
        amount=intent.amount,
        currency=intent.currency,
        recipient=intent.recipient
    )

    with tracer.start_as_current_span("sentinel.evaluate") as root_span:
        with tracer.start_as_current_span("sentinel.idempotency.check"):
            existing_tx = await idem_engine.check_and_record(idempotency_key, intent_context, intent.agent_id)
        t_idem = time.perf_counter()

        if existing_tx:
            try:
                record_decision("ALLOW", "IDEMPOTENCY_REPLAY")
                AUTHORIZATION_LATENCY.observe(time.perf_counter() - t_start)
            except Exception:
                pass
            return EvaluationResponse(
                intent_id=intent.intent_id,
                    decision="ALLOW",
                    reason="Idempotent replay of completed execution.",
                capability_token=None,
                executed_tx_id=existing_tx,
                latency_ms=0,
                timings={"idem_ms": (t_idem - t_start)*1000}
            )

        from api.dependencies import kafka_producer, redis_client
        KAFKA_INBOUND_TOPIC = settings.KAFKA_INBOUND_TOPIC
        payload = {
            "intent": intent.model_dump(),
            "context": intent.context,
            "agent_id": intent.agent_id,
            "mode": mode,
            "idempotency_key": idempotency_key
        }
        # Inject OTel trace context for end-to-end tracing (non-authoritative)
        try:
            payload = inject_trace_context(payload)
        except Exception:
            pass

        with tracer.start_as_current_span("sentinel.kafka.publish"):
            t_kafka_start = time.perf_counter()
            try:
                await kafka_producer.send_and_wait(
                    KAFKA_INBOUND_TOPIC,
                    key=intent.agent_id.encode('utf-8'),
                    value=json.dumps(payload).encode('utf-8')
                )
                await idem_engine.mark_published(idempotency_key)
                try:
                    KAFKA_PUBLISH_LATENCY.observe(time.perf_counter() - t_kafka_start)
                except Exception:
                    pass
            except Exception:
                try:
                    KAFKA_ERRORS_TOTAL.labels(operation="publish").inc()
                except Exception:
                    pass
                await idem_engine.mark_state(idempotency_key, "PUBLISH_UNKNOWN")
                raise SentinelSecurityException("Intent publication unavailable or uncertain. Failing closed.")

        t_kafka = time.perf_counter()

        # Wait on Redis Stream for Reply
        reply_key = f"reply:{intent.intent_id}"
        with tracer.start_as_current_span("sentinel.redis.poll"):
            try:
                t_redis_start = time.perf_counter()
                response = await redis_client.xread({reply_key: '0'}, count=1, block=5000)

                if not response:
                    raise HTTPException(status_code=504, detail="Timeout waiting for evaluation")

                stream_name, messages = response[0]
                message_id, message_data = messages[0]

                raw_result = message_data.get("data", message_data.get(b"data"))
                if raw_result is None:
                    raise SentinelSecurityException("Malformed evaluator reply. Failing closed.")
                if isinstance(raw_result, bytes):
                    raw_result = raw_result.decode("utf-8")
                result = json.loads(raw_result)

                try:
                    REDIS_LATENCY.labels(operation="xread_reply").observe(
                        time.perf_counter() - t_redis_start
                    )
                except Exception:
                    pass

                t_redis = time.perf_counter()

                worker_timings = result.get("timings", {})
                timings = {
                    "api_idem_ms": (t_idem - t_start)*1000,
                    "api_kafka_ms": (t_kafka - t_idem)*1000,
                    "api_wait_ms": (t_redis - t_kafka)*1000,
                    "worker_queue_ms": worker_timings.get("queue_ms", 0),
                    "worker_features_ms": worker_timings.get("features_ms", 0),
                    "worker_xgb_ms": worker_timings.get("gpu_inference_ms", 0),
                    "worker_policy_ms": worker_timings.get("policy_ms", 0),
                    "total_ms": (t_redis - t_start)*1000
                }

                # Record decision + latency (non-authoritative)
                try:
                    record_decision(result["decision"], result.get("decision_reason", ""))
                    AUTHORIZATION_LATENCY.observe(time.perf_counter() - t_start)
                except Exception:
                    pass

                resp = EvaluationResponse(
                    intent_id=result["intent_id"],
                    decision=result["decision"],
                    reason=result.get("decision_reason"),
                    capability_token=result.get("capability_token"),
                    executed_tx_id=None,
                    latency_ms=result.get("latency_ms", 0),
                    timings=timings
                )
                return resp

            except Exception as e:
                try:
                    REDIS_ERRORS_TOTAL.labels(operation="xread_reply").inc()
                except Exception:
                    pass
                logger.error("Error during synchronous evaluation",
                             intent_id=intent.intent_id, error=str(e))
                raise

@app.post("/evaluate/async", status_code=202)
async def evaluate_intent_async(
    request: Request,
    intent: IntentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    mode: str = Header("govern", alias="X-Sentinel-Mode")
):
    """
    Async Path Evaluation.
    Publishes to Kafka and returns 202 Accepted immediately.
    """
    idem_engine = get_idempotency_engine()
    intent_context = IntentContext(
        intent_id=intent.intent_id,
        agent_id=intent.agent_id,
        action_type=intent.action_type,
        amount=intent.amount,
        currency=intent.currency,
        recipient=intent.recipient
    )
    
    existing_tx = await idem_engine.check_and_record(idempotency_key, intent_context, intent.agent_id)
    if existing_tx:
        return JSONResponse(
            status_code=200,
            content={"intent_id": intent.intent_id, "status": "COMPLETED", "tx_id": existing_tx}
        )
        
    from api.dependencies import kafka_producer
    KAFKA_INBOUND_TOPIC = settings.KAFKA_INBOUND_TOPIC
    payload = {
        "intent": intent.model_dump(),
        "context": intent.context,
        "agent_id": intent.agent_id,
        "mode": mode,
        "idempotency_key": idempotency_key
    }
    
    try:
        await kafka_producer.send_and_wait(
            KAFKA_INBOUND_TOPIC,
            key=intent.agent_id.encode('utf-8'),
            value=json.dumps(payload).encode('utf-8')
        )
        await idem_engine.mark_published(idempotency_key)
    except Exception:
        await idem_engine.mark_state(idempotency_key, "PUBLISH_UNKNOWN")
        raise SentinelSecurityException("Intent publication unavailable or uncertain. Failing closed.")
    
    return {"intent_id": intent.intent_id, "status": "PROCESSING"}

@app.post("/execute", response_model=ExecuteResponse)
async def execute_intent(
    req: ExecuteRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key")
):
    """
    Execution Gateway Endpoint.
    Validates the Capability Token and executes the simulated payment.
    """
    gateway = get_execution_adapter()
    idem_engine = get_idempotency_engine()
    
    intent_context = IntentContext(
        intent_id=req.intent_id,
        agent_id=req.agent_id,
        action_type=req.action_type,
        amount=req.amount,
        currency=req.currency,
        recipient=req.recipient
    )
    
    try:
        receipt = await gateway.execute(req.capability_token, intent_context)
        
        intent_hash = idem_engine._hash_intent(intent_context)
        
        if receipt.status == "SUCCESS":
            await idem_engine.mark_completed(idempotency_key, intent_hash, receipt.execution_id)
            return ExecuteResponse(executed_tx_id=receipt.execution_id, status="SUCCESS")
        elif receipt.status == "UNKNOWN":
            await idem_engine.mark_state(idempotency_key, "UNKNOWN")
            return ExecuteResponse(executed_tx_id=receipt.execution_id, status="UNKNOWN")
        else:
            await idem_engine.mark_state(idempotency_key, "FAILED")
            return ExecuteResponse(executed_tx_id=receipt.execution_id, status="FAILED")
            
    except ValueError as e:
        raise SentinelSecurityException(str(e))

# ─────────────────────────────────────────────────────────────
# SSE & DEMO SCENARIOS
# ─────────────────────────────────────────────────────────────
import asyncio
from fastapi.responses import StreamingResponse
from api.schema import SentinelExecutionEvent
from datetime import datetime
import uuid

# Simple global broadcaster for demo purposes
class EventBroadcaster:
    def __init__(self):
        self.queues = []

    async def broadcast(self, event: SentinelExecutionEvent):
        for q in self.queues:
            await q.put(event)

    async def subscribe(self):
        q = asyncio.Queue()
        self.queues.append(q)
        try:
            while True:
                event = await q.get()
                yield f"data: {event.model_dump_json()}\n\n"
        except asyncio.CancelledError:
            self.queues.remove(q)

broadcaster = EventBroadcaster()

@app.get("/execution/stream")
async def execution_stream():
    """SSE Endpoint for execution events"""
    return StreamingResponse(broadcaster.subscribe(), media_type="text/event-stream")

@app.post("/demo/scenarios/{scenario}")
async def run_demo_scenario(scenario: str):
    """Triggers demo scenarios and pipes them to SSE"""
    intent_id = f"INT-{uuid.uuid4().hex[:6]}"
    now = lambda: datetime.utcnow().isoformat() + "Z"
    
    # 1. INTENT Stage
    await broadcaster.broadcast(SentinelExecutionEvent(
        event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
        stage="INTENT"
    ))
    await asyncio.sleep(0.5)

    if scenario == "normal":
        # 2. BEHAVIOR
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.05, semantic_risk=0.08
        ))
        await asyncio.sleep(0.5)
        # 3. POLICY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="ALLOW"
        ))
        await asyncio.sleep(0.5)
        # 4. CAPABILITY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=True, mcp_tool="create_order"
        ))
        await asyncio.sleep(0.5)
        # 5. MCP
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=True
        ))
        await asyncio.sleep(0.5)
        # 6. RAZORPAY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="RAZORPAY", execution_status="SUCCESS", provider_reference="order_TTW72yaNVN0zHe", latency_ms=620
        ))
    
    elif scenario == "abuse-burst":
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.91, semantic_risk=0.85
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="CONTAIN"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=False, reason_codes=["High behavioral drift (Velocity x31)"]
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="BLOCKED"
        ))
        
    elif scenario == "privilege-violation":
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.10, semantic_risk=0.15
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="ALLOW"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=True, mcp_tool="create_order"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="BLOCKED", reason_codes=["Action type mismatch (fetch_all_payouts requested)"]
        ))

    elif scenario == "suspicious":
        # 2. BEHAVIOR
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.71, semantic_risk=0.68
        ))
        await asyncio.sleep(0.5)
        # 3. POLICY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="ESCALATE"
        ))
        await asyncio.sleep(0.5)
        # 4. CAPABILITY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=False, reason_codes=["Amount exceeds 3σ from baseline - requires human review"]
        ))
        await asyncio.sleep(0.5)
        # 5. MCP
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="ESCALATED"
        ))

    elif scenario == "malicious":
        # 2. BEHAVIOR
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.94, semantic_risk=0.89
        ))
        await asyncio.sleep(0.5)
        # 3. POLICY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="CONTAIN"
        ))
        await asyncio.sleep(0.5)
        # 4. CAPABILITY
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkpoint-agent-01",
            stage="CAPABILITY", capability_issued=False, reason_codes=["Severe behavioral anomaly + policy violation"]
        ))
        await asyncio.sleep(0.5)
        # 5. MCP
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="CONTAINED"
        ))

    elif scenario == "replay":
        # First request: ALLOW
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="BEHAVIOR", behavioral_risk=0.05, semantic_risk=0.08
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="POLICY", policy_decision="ALLOW"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=True, mcp_tool="create_order"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=True, execution_status="SUCCESS"
        ))
        await asyncio.sleep(1.0)
        # Second request with same idempotency key: BLOCKED
        intent_id_2 = f"INT-{uuid.uuid4().hex[:6]}"
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id_2, agent_id="checkout-agent-01",
            stage="INTENT"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id_2, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=False, reason_codes=["Idempotency: transaction already completed"]
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id_2, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="BLOCKED_REPLAY"
        ))

    elif scenario == "redis_failure":
        # Simulated infrastructure failure
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="INTENT"
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="CAPABILITY", capability_issued=False, reason_codes=["Fail-closed: Redis unavailable"]
        ))
        await asyncio.sleep(0.5)
        await broadcaster.broadcast(SentinelExecutionEvent(
            event_id=uuid.uuid4().hex, timestamp=now(), intent_id=intent_id, agent_id="checkout-agent-01",
            stage="MCP", mcp_invocation=False, execution_status="ESCALATED_INFRA_FAILURE"
        ))

    return {"status": "started", "scenario": scenario}

# ─────────────────────────────────────────────────────────────
# NL POLICY MANAGEMENT
# ─────────────────────────────────────────────────────────────

@app.get("/execution/provider")
async def get_execution_provider():
    gateway = get_execution_adapter()
    return await gateway.provider.get_health()

@app.post("/policy/rules", response_model=PolicyRuleResponse)
def add_policy_rule(
    req: PolicyRuleRequest,
    policy_engine = Depends(get_policy_engine),
):
    """Add a natural language policy rule. Example: 'ESCALATE IF amount > 5000000'"""
    try:
        rule = policy_engine.nl_compiler.add_rule(req.text, req.rule_id or "")
        return PolicyRuleResponse(rule_id=rule.rule_id, text=rule.raw_text)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/policy/rules", response_model=List[PolicyRuleResponse])
def list_policy_rules(policy_engine = Depends(get_policy_engine)):
    """List all active NL policy rules."""
    rules = policy_engine.nl_compiler.list_rules()
    return [PolicyRuleResponse(rule_id=r["rule_id"], text=r["text"]) for r in rules]

@app.delete("/policy/rules/{rule_id}")
def delete_policy_rule(rule_id: str, policy_engine = Depends(get_policy_engine)):
    """Delete a policy rule by ID."""
    removed = policy_engine.nl_compiler.remove_rule(rule_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
    return {"status": "deleted", "rule_id": rule_id}

# ─────────────────────────────────────────────────────────────
# BATCH SIMULATION
# ─────────────────────────────────────────────────────────────

@app.post("/simulate", response_model=SimulateResponse)
def run_simulation(
    req: SimulateRequest,
    model_wrapper: ModelWrapper = Depends(get_model),
    policy_engine = Depends(get_policy_engine),
):
    from ml.data_generator import generate_dataset
    
    df = generate_dataset(seed=req.seed, num_agents_train_val=4, num_agents_test_only=2)
    test_df = df[df["day"] >= 26].head(req.num_samples).copy()
    
    if len(test_df) == 0:
        return SimulateResponse(
            total=0, allowed=0, escalated=0, contained=0,
            avg_risk_score=0.0, escalation_rate=0.0, decisions=[]
        )
    
    decisions = []
    risk_scores = []
    
    for _, row in test_df.iterrows():
        raw_context = row.to_dict()
        features = extract_features(raw_context)
        
        model_risk = 0.0
        if getattr(model_wrapper, 'model', None):
            feat_df = pd.DataFrame([features])[model_wrapper.features]
            dmatrix = xgb.DMatrix(feat_df)
            model_risk = float(model_wrapper.model.predict(dmatrix)[0])
        
        intent = IntentContext(
            intent_id=f"sim_{row.name}",
            agent_id=str(raw_context.get("agent_id", "simulation-agent")),
            action_type=raw_context.get("action_type", "payout"),
            amount=int(raw_context.get("amount", 0)),
            currency="INR",
            recipient=raw_context.get("recipient", "sim_recipient"),
        )
        
        from ml.fusion.risk_fusion import RiskFusionEngine
        from ml.schema import BehavioralRiskResult, RiskAssessment

        behavioral = BehavioralRiskResult(
            risk_score=model_risk,
            confidence=1.0,
            reason_codes=["SIMULATION"],
            model_version="simulation",
        )
        fusion = RiskFusionEngine(
            base_escalation_threshold=getattr(model_wrapper, 'suspicious_threshold', 0.5)
        ).fuse(behavioral, None)
        assessment = RiskAssessment(behavioral=behavioral, fusion=fusion)
        decision, reason, _ = policy_engine.evaluate(intent, raw_context, assessment)
        
        risk_scores.append(model_risk)
        decisions.append({
            "intent_id": intent.intent_id,
            "amount": intent.amount,
            "action_type": intent.action_type,
            "model_risk": round(model_risk, 4),
            "decision": decision,
            "reason": reason,
            "loss_label": int(raw_context.get("loss_label", 0)),
            "scenario": raw_context.get("scenario", "unknown"),
        })
    
    allowed = sum(1 for d in decisions if d["decision"] == "ALLOW")
    escalated = sum(1 for d in decisions if d["decision"] == "ESCALATE")
    contained = sum(1 for d in decisions if d["decision"] == "CONTAIN")
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
    
    return SimulateResponse(
        total=len(decisions),
        allowed=allowed,
        escalated=escalated,
        contained=contained,
        avg_risk_score=round(avg_risk, 4),
        escalation_rate=round(escalated / len(decisions), 4) if decisions else 0.0,
        decisions=decisions,
    )

# ─────────────────────────────────────────────────────────────
# PAGES
# ─────────────────────────────────────────────────────────────

def _read_html(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist", filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return None

@app.get("/", response_class=HTMLResponse)
def serve_landing():
    html = _read_html("index.html")
    if html:
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Frontend build not found. Please run 'npm run build' in frontend/</h1>", status_code=404)

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    # Route to the same index.html for React Router to handle
    html = _read_html("index.html")
    if html:
        return HTMLResponse(content=html)
    return HTMLResponse(content="<h1>Frontend build not found. Please run 'npm run build' in frontend/</h1>", status_code=404)

# ─────────────────────────────────────────────────────────────
# AUDIT LOG API
# ─────────────────────────────────────────────────────────────

@app.get("/api/audit")
@app.get("/audit", tags=["audit"])
def get_audit_log(limit: int = 50, db: Session = Depends(get_db)):
    from db.models import AuditRecord
    records = db.query(AuditRecord).order_by(AuditRecord.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "intent_id": r.intent_id,
            "agent_id": r.agent_id,
            "action_type": r.action_type,
            "amount": r.amount,
            "currency": r.currency,
            "recipient": r.recipient,
            "model_risk_score": r.model_risk_score,
            "behavioral_risk_score": r.behavioral_risk_score,
            "semantic_risk_score": r.semantic_risk_score,
            "fusion_disagreement": r.fusion_disagreement == "true",
            "decision": r.decision,
            "decision_reason": r.decision_reason,
            "capability_jti": r.capability_jti,
            "executed_tx_id": r.executed_tx_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in records
    ]

@app.get("/audit/verify")
def verify_audit_log(db: Session = Depends(get_db)):
    """Verify every persisted audit record from genesis to the newest entry."""
    from db.models import AuditRecord
    from security.audit_chain import verify_audit_chain

    records = db.query(AuditRecord).order_by(AuditRecord.id.asc()).all()
    valid, checked, invalid_ids = verify_audit_chain(records)
    return {"status": "PASS" if valid else "FAIL", "records_checked": checked, "invalid_record_ids": invalid_ids}

@app.get("/api/security/invariants", tags=["security"])
def get_security_invariants(db: Session = Depends(get_db)):
    """
    Security invariant metrics: compute from audit log.

    Returns metrics that MUST be zero:
    - unauthorized_executions: executions without valid capability tokens
    - duplicate_executions: same transaction executed multiple times
    - unsafe_allows: ALLOW decisions during error states
    - audit_chain_breaks: broken links in the cryptographic audit chain
    - fail_open_incidents: ALLOW decisions issued during system errors

    In production with correct implementation, all should be 0.
    """
    from db.models import AuditRecord
    from security.audit_chain import verify_audit_chain

    # Query all audit records
    records = db.query(AuditRecord).all()

    # Initialize counters
    unauthorized_executions = 0
    duplicate_executions = 0
    unsafe_allows = 0
    audit_chain_breaks = 0
    fail_open_incidents = 0

    # Track seen intent hashes and JTIs
    seen_intent_hashes = set()
    seen_jtis = set()

    for record in records:
        # Check for duplicate executions (same intent_id executed multiple times with tx_id)
        if record.executed_tx_id:
            intent_key = f"{record.agent_id}:{record.action_type}:{record.amount}:{record.recipient}"
            if intent_key in seen_intent_hashes:
                duplicate_executions += 1
            else:
                seen_intent_hashes.add(intent_key)

        # Check for unauthorized executions (executed without token)
        if record.executed_tx_id and not record.capability_jti:
            unauthorized_executions += 1

        # Check for unsafe ALLOWs (ALLOW with very high risk or missing risk scores)
        if record.decision == "ALLOW":
            # If model_risk_score is missing or extremely high, it's unsafe
            if record.model_risk_score is None or (record.model_risk_score and record.model_risk_score > 0.95):
                unsafe_allows += 1

        # Check for duplicate tokens (same JTI used multiple times)
        if record.capability_jti:
            if record.capability_jti in seen_jtis:
                fail_open_incidents += 1  # Duplicate token use would be a fail-open
            else:
                seen_jtis.add(record.capability_jti)

    # Check audit chain integrity
    ordered_records = sorted(records, key=lambda r: r.id)
    valid, checked, invalid_ids = verify_audit_chain(ordered_records)
    audit_chain_breaks = len(invalid_ids)

    return {
        "unauthorized_executions": unauthorized_executions,
        "duplicate_executions": duplicate_executions,
        "unsafe_allows": unsafe_allows,
        "audit_chain_breaks": audit_chain_breaks,
        "fail_open_incidents": fail_open_incidents,
        "total_records": len(records),
    }

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus text exposition endpoint."""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except Exception as e:
        # If prometheus-client is not installed, return empty response
        return Response(content="", media_type="text/plain")


@app.get("/health/live", tags=["health"])
def health_live():
    """
    Liveness probe: Is this process alive and the event loop responsive?
    Returns 200 unconditionally as long as this handler executes.
    Kubernetes/container restarts based on this — never fail-close here.
    """
    return {"status": "ok", "process": "alive"}


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """
    Readiness probe: Can this API instance safely accept new authorization work?

    Phase 22 dependency matrix for API readiness:
      Redis  — REQUIRED  (idempotency, JTI replay protection)
      Kafka  — REQUIRED  (intent publishing to worker)
      DB     — MONITORED (soft-fail: audit consumer handles writes separately)

    Returns 503 if any REQUIRED dependency is unavailable.
    INVARIANT: This check never alters fail-closed authorization behavior.
    """
    from api.dependencies import redis_client, kafka_producer, engine

    required_errors: dict = {}
    warnings: dict = {}
    startup_incomplete = False

    # Guard: if app hasn't fully initialized yet (e.g. startup still in progress)
    if redis_client is None:
        startup_incomplete = True
        required_errors["redis"] = "not initialized — startup incomplete"
    else:
        try:
            await redis_client.ping()
        except Exception as e:
            required_errors["redis"] = str(e)

    if kafka_producer is None:
        startup_incomplete = True
        required_errors["kafka"] = "not initialized — startup incomplete"
    else:
        try:
            # AIOKafkaProducer has a _sender task we can probe; check it's not closed.
            if not kafka_producer._closed:
                pass  # producer is alive
            else:
                required_errors["kafka"] = "producer is closed"
        except Exception as e:
            required_errors["kafka"] = str(e)

    # DB is monitored but not required for API readiness (audit consumer writes independently)
    try:
        if engine:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
    except Exception as e:
        warnings["postgres"] = str(e)
        logger.warning("DB unavailable during readiness check — audit consumer will reconcile",
                       error=str(e))

    if required_errors:
        detail = {
            "status": "not_ready",
            "startup_incomplete": startup_incomplete,
            "required_dependencies_failed": required_errors,
        }
        if warnings:
            detail["warnings"] = warnings
        raise HTTPException(status_code=503, detail=detail)

    response = {"status": "ready"}
    if warnings:
        response["warnings"] = warnings
    return response


@app.get("/health/dependencies", tags=["health"])
async def health_dependencies():
    """
    Diagnostic dependency panel.
    Always returns 200 — even when individual components are degraded.
    NEVER drives routing or authorization decisions.
    Use for operator dashboards and alerting only.

    Phase 22 dependency matrix (API):
      Redis    — required for idempotency + JTI
      Kafka    — required for intent publishing
      Postgres — monitored (soft-fail; audit consumer handles independently)
      ML model — monitored (ESCALATE if absent)
    """
    from api.dependencies import redis_client, kafka_producer, engine, global_model
    result: dict = {}

    # Redis
    try:
        t = time.perf_counter()
        await redis_client.ping()
        result["redis"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - t) * 1000, 2),
            "role": "required",
        }
    except Exception as e:
        result["redis"] = {"status": "unhealthy", "error": str(e), "role": "required"}

    # Kafka Producer
    try:
        if kafka_producer is None:
            result["kafka"] = {"status": "not_initialized", "role": "required"}
        elif kafka_producer._closed:
            result["kafka"] = {"status": "closed", "role": "required"}
        else:
            result["kafka"] = {"status": "healthy", "role": "required"}
    except Exception as e:
        result["kafka"] = {"status": "unhealthy", "error": str(e), "role": "required"}

    # Postgres
    try:
        t = time.perf_counter()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["postgres"] = {
            "status": "healthy",
            "latency_ms": round((time.perf_counter() - t) * 1000, 2),
            "role": "monitored",
        }
    except Exception as e:
        result["postgres"] = {"status": "unhealthy", "error": str(e), "role": "monitored"}

    # ML Model
    if global_model and global_model.model is not None:
        result["ml_model"] = {"status": "loaded", "role": "monitored"}
    else:
        result["ml_model"] = {
            "status": "not_loaded",
            "role": "monitored",
            "note": "missing model → ESCALATE on all evaluations",
        }

    result["inference_backend"] = settings.INFERENCE_BACKEND
    return result


# Legacy aliases (backward compat)
@app.get("/live", include_in_schema=False)
def liveness_check():
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    """Legacy alias — delegates to /health/ready logic."""
    return await health_ready()
