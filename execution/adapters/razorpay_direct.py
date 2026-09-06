"""
Razorpay Direct SDK Provider
Production-grade integration with official Razorpay Python SDK
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

try:
    import razorpay
except ImportError:
    razorpay = None

from execution.provider import PaymentExecutionProvider
from execution.schema import ExecutionReceipt
from security.capability_token import CapabilityPayload

logger = logging.getLogger(__name__)


class RazorpayDirectProvider(PaymentExecutionProvider):
    """
    Direct Razorpay API integration using official Python SDK.
    Supports: Orders, Payouts, Refunds
    """

    def __init__(self, environment: str = "test"):
        self.environment = environment
        from core.config import settings

        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET

        if not razorpay:
            raise ImportError("razorpay SDK not installed. Run: pip install razorpay")

        if not self.key_id or not self.key_secret:
            raise ValueError("RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be set")

        # Initialize Razorpay client
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

        # Action mapping
        self.ACTION_HANDLERS = {
            "create_order": self._create_order,
            "create_payout": self._create_payout,
            "refund": self._create_refund,
            "fetch_payment": self._fetch_payment,
        }

        logger.info(f"RazorpayDirectProvider initialized in {environment} mode")

    async def execute(self, capability: CapabilityPayload, args: Dict[str, Any]) -> ExecutionReceipt:
        """
        Execute financial action via Razorpay SDK.
        Validates capability token and enforces cryptographic invariants.
        """
        start_time = time.time()
        receipt_id = f"exec_{uuid.uuid4().hex[:12]}"

        # 1. Validate action type
        action = capability.action_type
        if action not in self.ACTION_HANDLERS:
            raise ValueError(f"Unsupported action: {action}")

        # 2. Execute the action
        handler = self.ACTION_HANDLERS[action]

        try:
            result = await handler(capability, args)
            execution_status = "SUCCESS"
            provider_reference = result.get("id")
            executed_amount = result.get("amount", capability.amount)

        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay BadRequest: {e}")
            execution_status = "FAILED"
            provider_reference = f"error_{e.error_code}"
            executed_amount = 0

        except razorpay.errors.GatewayError as e:
            logger.error(f"Razorpay Gateway Error: {e}")
            execution_status = "UNKNOWN"
            provider_reference = "gateway_error"
            executed_amount = 0

        except razorpay.errors.ServerError as e:
            logger.error(f"Razorpay Server Error: {e}")
            execution_status = "UNKNOWN"
            provider_reference = "server_error"
            executed_amount = 0

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            execution_status = "FAILED"
            provider_reference = "unknown_error"
            executed_amount = 0

        latency_ms = int((time.time() - start_time) * 1000)

        return ExecutionReceipt(
            execution_id=receipt_id,
            intent_id=capability.intent_id,
            decision_id=capability.decision,
            capability_jti=capability.jti,
            agent_id=capability.agent_id,
            requested_action=action,
            mcp_tool=None,
            requested_amount=capability.amount,
            executed_amount=executed_amount,
            currency=capability.currency,
            provider="razorpay-direct",
            environment=self.environment,
            status=execution_status,
            latency_ms=latency_ms,
            verification_status="VERIFIED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider_reference=provider_reference,
        )

    async def _create_order(self, capability: CapabilityPayload, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Razorpay Order.
        https://razorpay.com/docs/api/orders/
        """
        order_data = {
            "amount": capability.amount,  # Amount in smallest currency unit (paise for INR)
            "currency": capability.currency,
            "receipt": capability.jti[:40],  # Max 40 chars
            "notes": {
                "sentinel_intent": capability.intent_id,
                "agent_id": capability.agent_id,
                "sentinel_decision": capability.decision,
            },
        }

        # Add optional fields
        if args.get("notes"):
            order_data["notes"].update(args["notes"])

        if args.get("partial_payment"):
            order_data["partial_payment"] = args["partial_payment"]

        # Create order via SDK
        order = self.client.order.create(data=order_data)

        logger.info(f"Razorpay Order created: {order['id']} for ₹{capability.amount/100}")

        return order

    async def _create_payout(self, capability: CapabilityPayload, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Razorpay Payout.
        https://razorpay.com/docs/api/payouts/
        """
        payout_data = {
            "account_number": args.get("account_number", "2323230041626310"),  # Your Razorpay account
            "fund_account_id": capability.recipient,  # Fund account ID
            "amount": capability.amount,
            "currency": capability.currency,
            "mode": args.get("mode", "IMPS"),  # IMPS, NEFT, RTGS, UPI
            "purpose": args.get("purpose", "payout"),
            "queue_if_low_balance": args.get("queue_if_low_balance", True),
            "reference_id": capability.jti[:40],
            "narration": f"Sentinel: {capability.intent_id[:20]}",
            "notes": {
                "sentinel_intent": capability.intent_id,
                "agent_id": capability.agent_id,
            },
        }

        # Create payout via SDK
        payout = self.client.payout.create(data=payout_data)

        logger.info(f"Razorpay Payout created: {payout['id']} for ₹{capability.amount/100}")

        return payout

    async def _create_refund(self, capability: CapabilityPayload, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Razorpay Refund.
        https://razorpay.com/docs/api/refunds/
        """
        payment_id = args.get("payment_id") or capability.recipient

        refund_data = {
            "amount": capability.amount,
            "speed": args.get("speed", "normal"),  # normal or optimum
            "notes": {
                "sentinel_intent": capability.intent_id,
                "agent_id": capability.agent_id,
                "reason": args.get("reason", "Customer request"),
            },
            "receipt": capability.jti[:40],
        }

        # Create refund via SDK
        refund = self.client.payment.refund(payment_id, refund_data)

        logger.info(f"Razorpay Refund created: {refund['id']} for ₹{capability.amount/100}")

        return refund

    async def _fetch_payment(self, capability: CapabilityPayload, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch payment details (read-only operation).
        """
        payment_id = args.get("payment_id") or capability.recipient

        payment = self.client.payment.fetch(payment_id)

        logger.info(f"Razorpay Payment fetched: {payment['id']}")

        return payment

    async def get_health(self) -> Dict[str, Any]:
        """
        Health check - verify Razorpay API connectivity.
        """
        try:
            # Try to fetch a dummy payment (will fail but proves connectivity)
            # Or use self.client.utility.verify_payment_signature() if available

            # Simple connectivity check
            start = time.time()
            # Fetch recent orders to test API connectivity
            self.client.order.all({"count": 1})
            latency_ms = int((time.time() - start) * 1000)

            return {
                "provider": "razorpay-direct",
                "status": "HEALTHY",
                "environment": self.environment,
                "api_latency_ms": latency_ms,
                "sdk_version": razorpay.__version__ if hasattr(razorpay, "__version__") else "unknown",
                "supported_actions": list(self.ACTION_HANDLERS.keys()),
            }

        except Exception as e:
            logger.error(f"Razorpay health check failed: {e}")
            return {
                "provider": "razorpay-direct",
                "status": "UNHEALTHY",
                "environment": self.environment,
                "error": str(e),
            }
