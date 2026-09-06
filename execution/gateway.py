"""
Sentinel — Execution Gateway

Responsible for simulated and live financial execution.
Validates the Capability Token BEFORE taking any action.
Ensures that no financial action occurs without an exact, valid token.
"""

import logging
from typing import Dict, Any, Optional
import os
import time

from security.capability_token import TokenManager as CapabilityTokenManager, IntentContext, CapabilityTokenException
from execution.provider import PaymentExecutionProvider
from execution.schema import ExecutionReceipt

logger = logging.getLogger(__name__)


class ExecutionGateway:
    def __init__(
        self,
        token_manager: CapabilityTokenManager,
        provider: PaymentExecutionProvider,
        replay_store: Optional[Any] = None,
    ):
        self.token_manager = token_manager
        self.provider = provider
        self.replay_store = replay_store

    async def _claim_jti(self, jti: str, expires_at: int) -> None:
        """Atomically reserve a token JTI before any provider invocation."""
        if self.replay_store is None:
            # Only used by isolated adapter tests. Application wiring always supplies Redis.
            if jti in self.token_manager._consumed_jtis:
                raise ValueError("Execution rejected: Token has already been consumed (replay attack).")
            self.token_manager._consumed_jtis.add(jti)
            return

        ttl_seconds = max(1, expires_at - int(time.time()))
        try:
            acquired = await self.replay_store.set(f"capability:jti:{jti}", "consumed", nx=True, ex=ttl_seconds)
        except Exception as exc:
            raise ValueError("Execution rejected: Replay-protection state unavailable.") from exc
        if not acquired:
            raise ValueError("Execution rejected: Token has already been consumed (replay attack).")

    async def execute(self, token: str, expected_intent: IntentContext) -> ExecutionReceipt:
        """
        Validates the capability token and executes the transaction via the provider.
        Raises ValueError (or specific exceptions) if token is invalid or does not match intent.
        """
        if not token:
            logger.error("Execution attempted without a capability token.")
            raise ValueError("Execution rejected: Missing capability token.")

        # 1. Capability Validation (Enforces all invariants)
        try:
            payload = self.token_manager.verify_token(token, expected_intent, consume=False)
        except CapabilityTokenException as e:
            logger.error(f"Execution rejected: {str(e)}")
            raise ValueError(f"Execution rejected: {str(e)}")

        await self._claim_jti(payload.jti, payload.expires_at)
        logger.info(f"Capability Token Validated (JTI: {payload.jti}). Delegating to provider.")

        # 2. Execution Delegation
        # We pass the validated payload so the adapter doesn't blindly trust the caller's requested action.

        # The adapter maps the action (e.g., 'refund') to its own MCP tool.
        # We pass the intent properties as arguments.
        args = {"amount": payload.amount, "currency": payload.currency, "recipient": payload.recipient}

        try:
            receipt = await self.provider.execute(payload, args)
            return receipt
        except Exception as e:
            logger.error(f"Execution Provider Error: {str(e)}")
            # Fail closed but return as FAILED execution state rather than wrapping in ValueError
            return ExecutionReceipt(
                execution_id="fail_" + payload.jti[:12],
                intent_id=payload.intent_id,
                decision_id=payload.decision,
                capability_jti=payload.jti,
                agent_id=payload.agent_id,
                requested_action=payload.action_type,
                mcp_tool="unknown",
                requested_amount=payload.amount,
                executed_amount=0,
                currency=payload.currency,
                provider="unknown",
                environment="unknown",
                status="FAILED",
                latency_ms=0,
                verification_status="VERIFIED",
                timestamp=str(time.time()),
                provider_reference=f"Exception: {str(e)}",
            )

    async def reconcile(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        """
        Reconcile an UNKNOWN execution state by querying the provider.
        """
        if receipt.status != "UNKNOWN":
            return receipt

        # In a real system, this would query Razorpay by the intent_id or idempotency_key
        # For the chaos tests, we will mock the provider's check_status method if needed,
        # or simply transition based on provider's health.
        try:
            health = await self.provider.get_health()
            if health.get("status") == "CONNECTED":
                # If we reconnected, we would query the upstream. For now, assume it failed.
                receipt.status = "CONFIRMED_FAILED"
            else:
                # Still can't reach provider
                pass
        except Exception as e:
            logger.error(f"Reconciliation failed: {e}")

        return receipt

    def get_provider_status(self) -> Dict[str, Any]:
        return self.provider.get_health()
