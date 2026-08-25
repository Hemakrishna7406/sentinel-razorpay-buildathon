"""
Sentinel — Audit Consumer

Consumes `IntentEvaluated` events from Kafka (`intents.evaluated`).
Performs idempotent writes to PostgreSQL.
Commits Kafka offset ONLY after successful DB commit (At-least-once).

Phase 21 Observability:
- Structured JSON logs via observability.logging
- Prometheus metrics (postgres latency/errors) scraped on METRICS_PORT
- All observability is non-authoritative — failures never affect audit writes.
"""

import asyncio
import json
import time
import threading

from core.config import settings
from aiokafka import AIOKafkaConsumer
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert

from db.models import AuditRecord
from security.audit_chain import audit_record_hash
from observability.logging import get_logger
from observability.metrics import POSTGRES_LATENCY, POSTGRES_ERRORS_TOTAL

logger = get_logger(__name__)

KAFKA_BROKER = settings.KAFKA_BROKER
EVALUATED_TOPIC = settings.KAFKA_EVALUATED_TOPIC
DB_URL = settings.DATABASE_URL
METRICS_PORT = settings.AUDIT_METRICS_PORT


def _start_metrics_server() -> None:
    try:
        from prometheus_client import start_http_server
        start_http_server(METRICS_PORT)
        logger.info("Audit consumer metrics server started", port=METRICS_PORT)
    except Exception as e:
        logger.warning("Metrics server failed to start — audit unaffected", error=str(e))


async def main():
    logger.info("Starting Audit Consumer")

    threading.Thread(target=_start_metrics_server, daemon=True).start()

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
    logger.info("Audit Consumer ready", kafka_topic=EVALUATED_TOPIC)

    try:
        async for msg in consumer:
            intent_id = "unknown"
            try:
                event = json.loads(msg.value.decode('utf-8'))
                intent_id = event.get("intent_id", "unknown")
                bound_log = logger.bind(intent_id=intent_id)

                t_db_start = time.perf_counter()
                with SessionLocal() as db:
                    if "sqlite" in DB_URL:
                        existing = db.query(AuditRecord).filter_by(intent_id=event["intent_id"]).first()
                        if existing:
                            bound_log.info("Audit record already exists — skipping (idempotent)")
                            await consumer.commit()
                            continue

                    last_record = db.query(AuditRecord).order_by(AuditRecord.id.desc()).first()
                    prev_hash = last_record.record_hash if last_record else None

                    jti = None
                    token = event.get("capability_token")
                    if token and isinstance(token, str):
                        try:
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

                db_latency = time.perf_counter() - t_db_start
                try:
                    POSTGRES_LATENCY.labels(operation="audit_insert").observe(db_latency)
                except Exception:
                    pass

                # At-least-once: commit offset only after successful DB write
                await consumer.commit()
                bound_log.info("Audit record written",
                               decision=event["decision"],
                               db_latency_ms=round(db_latency * 1000, 2))

            except Exception as e:
                logger.error("Error auditing message",
                             intent_id=intent_id,
                             offset=msg.offset,
                             error=str(e))
                try:
                    POSTGRES_ERRORS_TOTAL.labels(operation="audit_insert").inc()
                except Exception:
                    pass
                # Brief pause to prevent rapid retry loops during DB downtime
                await asyncio.sleep(5)

    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
