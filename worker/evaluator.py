"""
Sentinel — Evaluator Worker

Consumes `IntentSubmitted` events from Kafka (`intents.inbound`).
Computes ML features, runs XGBoost, evaluates policies.
If ALLOW, issues Capability Token.
Publishes `IntentEvaluated` to Kafka (`intents.evaluated`).
Replies via Redis Stream to unblock synchronous HTTP clients.
"""

import asyncio
import json
import logging
import os
import time

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import redis.asyncio as redis
import pandas as pd
import xgboost as xgb

from api.dependencies import ModelWrapper
from security.policy import PolicyEngine
from security.capability_token import IntentContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:29092")
INBOUND_TOPIC = os.environ.get("KAFKA_INBOUND_TOPIC", "intents.inbound")
EVALUATED_TOPIC = os.environ.get("KAFKA_EVALUATED_TOPIC", "intents.evaluated")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

async def main():
    logger.info("Starting Evaluator Worker...")
    
    # Initialize ML & Policy
    model_wrapper = ModelWrapper()
    model_wrapper.load()
    policy_engine = PolicyEngine(suspicious_threshold=model_wrapper.suspicious_threshold)
    
    from ml.providers.semantic_engine import SimulatedSemanticClient
    from ml.fusion.risk_fusion import RiskFusionEngine
    
    semantic_client = SimulatedSemanticClient()
    risk_fusion = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=model_wrapper.suspicious_threshold)
    
    # Initialize Kafka Consumer & Producer
    consumer = AIOKafkaConsumer(
        INBOUND_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id="sentinel-evaluator-group",
        auto_offset_reset="earliest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)
    
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    await consumer.start()
    await producer.start()
    
    logger.info("Evaluator Worker ready, listening for intents.")
    
    try:
        async for msg in consumer:
            start_time = time.time()
            try:
                event = json.loads(msg.value.decode('utf-8'))
                
                # 1. Parse Event
                intent_data = event["intent"]
                context_data = event.get("context", {})
                agent_id = event["agent_id"]
                mode = event.get("mode", "govern")
                
                intent = IntentContext(
                    intent_id=intent_data["intent_id"],
                    agent_id=agent_id,
                    action_type=intent_data["action_type"],
                    amount=intent_data["amount"],
                    currency=intent_data["currency"],
                    recipient=intent_data["recipient"]
                )
                
                # 2. Extract Features
                from ml.features import extract_features
                features = extract_features(context_data)
                
                # 3. Behavioral ML Inference
                model_risk = None
                model_available = model_wrapper.model is not None
                if model_available:
                    df_feats = pd.DataFrame([features])[model_wrapper.features]
                    dmatrix = xgb.DMatrix(df_feats)
                    model_risk = float(model_wrapper.model.predict(dmatrix)[0])
                
                from ml.schema import BehavioralRiskResult, RiskAssessment
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

                # 3.1 Semantic Provider Inference
                if model_available:
                    try:
                        semantic_result = semantic_client.evaluate(intent, context_data)
                    except Exception as e:
                        logger.warning(f"Semantic Provider unavailable: {e}")
                        semantic_result = None
                else:
                    semantic_result = None

                # 3.2 Risk Fusion
                fusion_result = risk_fusion.fuse(behavioral, semantic_result)

                assessment = RiskAssessment(
                    behavioral=behavioral,
                    semantic=semantic_result,
                    fusion=fusion_result
                )

                from ml.schema import Decision
                # 4. Policy Evaluation
                decision, reason, token = policy_engine.evaluate(intent, context_data, assessment)
                
                if mode.lower() == "observe":
                    shadow_decision = decision.value
                    decision = Decision.ALLOW
                    reason = f"[OBSERVE MODE] Shadow decision was {shadow_decision}: {reason}"
                    token = None
                
                # 5. Build Result Payload
                result = {
                    "intent_id": intent.intent_id,
                    "agent_id": agent_id,
                    "action_type": intent.action_type,
                    "amount": intent.amount,
                    "currency": intent.currency,
                    "recipient": intent.recipient,
                    "model_risk_score": assessment.fusion.final_risk,  # Backwards compatibility
                    "behavioral_risk_score": behavioral.risk_score,
                    "semantic_risk_score": semantic_result.risk_score if semantic_result else None,
                    "fusion_disagreement": fusion_result.disagreement,
                    "decision": decision.value,
                    "decision_reason": reason,
                    "capability_token": token,
                    "timestamp": time.time(),
                    "latency_ms": int((time.time() - start_time) * 1000)
                }
                
                # 6. Publish to Kafka (`intents.evaluated`)
                await producer.send_and_wait(
                    EVALUATED_TOPIC,
                    key=agent_id.encode('utf-8'),
                    value=json.dumps(result).encode('utf-8')
                )
                
                # 7. Reply via Redis Stream for synchronous API unblocking
                reply_key = f"reply:{intent.intent_id}"
                await redis_client.xadd(reply_key, {"data": json.dumps(result)}, maxlen=10)
                await redis_client.expire(reply_key, 30)
                
                logger.info(f"Evaluated {intent.intent_id} -> {decision} in {result['latency_ms']}ms")
                
            except Exception as e:
                logger.error(f"Error processing message {msg.offset}: {e}", exc_info=True)
                
    finally:
        await consumer.stop()
        await producer.stop()
        await redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
