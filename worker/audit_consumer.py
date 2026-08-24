"""
Sentinel — Audit Consumer

Consumes `IntentEvaluated` events from Kafka (`intents.evaluated`).
Performs idempotent writes to PostgreSQL.
Commits Kafka offset ONLY after successful DB commit (At-least-once).
"""

import asyncio
import json
import logging
import os

from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from db.models import AuditRecord
from security.audit_chain import audit_record_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:29092")
EVALUATED_TOPIC = os.environ.get("KAFKA_EVALUATED_TOPIC", "intents.evaluated")
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///./sentinel.db")

async def main():
    logger.info("Starting Audit Consumer...")
    
    engine = create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    consumer = AIOKafkaConsumer(
        EVALUATED_TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id="sentinel-audit-group",
        auto_offset_reset="earliest",
        enable_auto_commit=False
    )
    
    await consumer.start()
    logger.info("Audit Consumer ready, listening for evaluated intents.")
    
    try:
        async for msg in consumer:
            try:
                event = json.loads(msg.value.decode('utf-8'))
                
                with SessionLocal() as db:
                    if "sqlite" in DB_URL:
                        existing = db.query(AuditRecord).filter_by(intent_id=event["intent_id"]).first()
                        if existing:
                            logger.info(f"Audit record {event['intent_id']} already exists. Skipping.")
                            await consumer.commit()
                            continue
                            
                    last_record = db.query(AuditRecord).order_by(AuditRecord.id.desc()).first()
                    prev_hash = last_record.record_hash if last_record else None
                    
                    jti = None
                    token = event.get("capability_token")
                    if token and isinstance(token, str):
                        try:
                            # Token format: '{"jti": "...", ...}.signature'
                            payload_str = token.split(".")[0]
                            jti = json.loads(payload_str).get("jti")
                        except Exception:
                            pass

                    record_dict = {
                        "previous_hash": prev_hash,
                        "intent_id": event["intent_id"],
                        "agent_id": event["agent_id"],
                        "action_type": event["action_type"],
                        "amount": event["amount"],
                        "currency": event["currency"],
                        "recipient": event["recipient"],
                        "model_risk_score": event.get("model_risk_score"),
                        "behavioral_risk_score": event.get("behavioral_risk_score"),
                        "semantic_risk_score": event.get("semantic_risk_score"),
                        "fusion_disagreement": str(event.get("fusion_disagreement")).lower(),
                        "decision": event["decision"],
                        "decision_reason": event["decision_reason"],
                        "capability_jti": jti,
                        "executed_tx_id": None
                    }
                    record_dict["record_hash"] = audit_record_hash(record_dict)
                    
                    if "postgresql" in DB_URL:
                        stmt = insert(AuditRecord).values(**record_dict)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['intent_id'])
                        db.execute(stmt)
                    else:
                        record = AuditRecord(**record_dict)
                        db.add(record)
                        
                    db.commit()
                    
                # At-least-once: Commit offset after successful DB insert
                await consumer.commit()
                logger.info(f"Audited decision for {event['intent_id']}")
                
            except Exception as e:
                logger.error(f"Error auditing message {msg.offset}: {e}")
                # We sleep briefly to prevent rapid retry loops during DB downtime
                await asyncio.sleep(5)
                
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())
