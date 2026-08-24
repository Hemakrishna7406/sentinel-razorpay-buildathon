import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from execution.provider import PaymentExecutionProvider
from execution.schema import ExecutionReceipt
from security.capability_token import CapabilityPayload

class MockPaymentAdapter(PaymentExecutionProvider):
    def __init__(self, environment: str = "test"):
        self.environment = environment

    async def execute(self, capability: CapabilityPayload, args: Dict[str, Any]) -> ExecutionReceipt:
        start_time = time.time()
        tx_id = f"mock_{uuid.uuid4().hex[:12]}"
        
        latency = int((time.time() - start_time) * 1000) + 15
        
        return ExecutionReceipt(
            execution_id=tx_id,
            intent_id=capability.intent_id,
            decision_id=f"DEC-{uuid.uuid4().hex[:6]}",
            capability_jti=capability.jti,
            agent_id=capability.agent_id, # Wait, CapabilityPayload does not have agent_id in the current schema. I will add it.
            requested_action=capability.action_type,
            mcp_tool="mock_tool",
            requested_amount=capability.amount,
            executed_amount=capability.amount,
            currency=capability.currency,
            provider="mock-adapter",
            environment=self.environment,
            status="SUCCESS",
            latency_ms=latency,
            verification_status="VERIFIED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider_reference=tx_id
        )

    async def get_health(self) -> Dict[str, Any]:
        return {
            "provider": "mock-adapter",
            "transport": "local",
            "environment": self.environment,
            "status": "CONNECTED",
            "available_tools": 100,
            "allowed_actions": 5,
            "last_health_check": datetime.now(timezone.utc).isoformat()
        }
