"""
Sentinel — Idempotency & Duplicate Detection

Ensures exactly-once semantics for client requests and mitigates
accidental double-spends from faulty scripts (behavioral duplicates).
Uses Redis for atomic operations and distributed coordination.
"""

import time
import hashlib
import json
import logging
from typing import Optional

from redis import Redis
from security.exceptions import IdempotencyConflictException, BehavioralDuplicateException, SentinelSecurityException
from security.capability_token import IntentContext

logger = logging.getLogger(__name__)

class IdempotencyEngine:
    def __init__(self, redis_client: Redis, idempotency_ttl_seconds: int = 86400, behavioral_window_seconds: int = 5):
        self.redis_client = redis_client
        self.idempotency_ttl_seconds = idempotency_ttl_seconds
        self.behavioral_window_seconds = behavioral_window_seconds

    def _hash_intent(self, intent: IntentContext) -> str:
        """Create a deterministic hash of the critical intent fields."""
        payload = {
            "agent_id": getattr(intent, 'agent_id', ''),
            "action_type": intent.action_type,
            "amount": intent.amount,
            "currency": intent.currency,
            "recipient": intent.recipient
        }
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

    async def check_and_record(self, idempotency_key: str, intent: IntentContext, agent_id: str) -> Optional[str]:
        """
        Check idempotency and behavioral duplicate rules using atomic Redis operations.
        """
        intent_hash = self._hash_intent(intent)
        redis_idem_key = f"idem:{idempotency_key}"
        behavioral_key = f"agent:{agent_id}:behav:{intent_hash}"

        try:
            # 1. Atomic Idempotency Check & Reservation
            idem_value = json.dumps({
                "intent_hash": intent_hash,
                "state": "PROCESSING",
                "tx_id": None,
                "timestamp": time.time()
            })
            
            acquired = await self.redis_client.set(
                redis_idem_key, 
                idem_value, 
                nx=True, 
                ex=self.idempotency_ttl_seconds
            )
            
            if not acquired:
                existing_val_str = await self.redis_client.get(redis_idem_key)
                if not existing_val_str:
                    raise IdempotencyConflictException("Idempotency lock state is uncertain. Please retry.")
                    
                existing_val = json.loads(existing_val_str)
                
                if existing_val.get("intent_hash") != intent_hash:
                    raise IdempotencyConflictException("Idempotency key reused with different payload parameters.")
                
                state = existing_val.get("state")
                if state == "COMPLETED":
                    return existing_val.get("tx_id")
                elif state in {"PROCESSING", "PUBLISHING", "PUBLISHED", "EVALUATING", "PUBLISH_UNKNOWN"}:
                    raise IdempotencyConflictException(
                        f"A request with this idempotency key is already {state.lower()}."
                    )
                elif state == "FAILED":
                    # Retain the record for auditability while allowing an explicit retry.
                    existing_val["state"] = "PROCESSING"
                    existing_val["timestamp"] = time.time()
                    await self.redis_client.set(
                        redis_idem_key,
                        json.dumps(existing_val),
                        ex=self.idempotency_ttl_seconds,
                    )
                    return None
                else:
                    raise IdempotencyConflictException(f"Unknown idempotency state: {state}")

            # 2. Behavioral Duplicate Detection
            behav_acquired = await self.redis_client.set(
                behavioral_key,
                "1",
                nx=True,
                ex=self.behavioral_window_seconds
            )
            
            if not behav_acquired:
                # Rollback idempotency lock
                await self.redis_client.delete(redis_idem_key)
                raise BehavioralDuplicateException(
                    f"Behavioral duplicate detected. Exact same transaction attempted within {self.behavioral_window_seconds}s."
                )

            return None
            
        except (IdempotencyConflictException, BehavioralDuplicateException):
            raise
        except Exception as e:
            logger.error(f"Redis unavailable during idempotency check: {e}")
            raise SentinelSecurityException("Distributed state unavailable. Halting execution.")

    async def mark_completed(self, idempotency_key: str, intent_hash: str, tx_id: str):
        """Record the successful execution ID and transition to COMPLETED."""
        redis_idem_key = f"idem:{idempotency_key}"
        try:
            existing_val_str = await self.redis_client.get(redis_idem_key)
            if existing_val_str:
                existing_val = json.loads(existing_val_str)
                existing_val["state"] = "COMPLETED"
                existing_val["tx_id"] = tx_id
                
                await self.redis_client.set(redis_idem_key, json.dumps(existing_val), ex=self.idempotency_ttl_seconds)
        except Exception as e:
            logger.error(f"Failed to mark idempotency key as completed: {e}")

    async def mark_state(self, idempotency_key: str, state: str):
        """Persist lifecycle state; never delete a reservation after publication."""
        redis_idem_key = f"idem:{idempotency_key}"
        try:
            existing_val_str = await self.redis_client.get(redis_idem_key)
            if existing_val_str:
                existing_val = json.loads(existing_val_str)
                existing_val["state"] = state
                existing_val["timestamp"] = time.time()
                await self.redis_client.set(
                    redis_idem_key, json.dumps(existing_val), ex=self.idempotency_ttl_seconds
                )
        except Exception as e:
            logger.error(f"Failed to persist idempotency state {state}: {e}")

    async def mark_publishing(self, idempotency_key: str):
        await self.mark_state(idempotency_key, "PUBLISHING")

    async def mark_published(self, idempotency_key: str):
        await self.mark_state(idempotency_key, "PUBLISHED")

    async def mark_publish_unknown(self, idempotency_key: str):
        await self.mark_state(idempotency_key, "PUBLISH_UNKNOWN")

    async def mark_failed(self, idempotency_key: str):
        """Mark a pre-publication failure; record is retained for a safe retry."""
        await self.mark_state(idempotency_key, "FAILED")
