from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionReceipt:
    execution_id: str
    intent_id: str
    decision_id: str
    capability_jti: str
    agent_id: str
    requested_action: str
    mcp_tool: Optional[str]
    requested_amount: int
    executed_amount: int
    currency: str
    provider: str
    environment: str
    status: str
    latency_ms: int
    verification_status: str
    timestamp: str
    provider_reference: Optional[str]
