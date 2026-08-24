from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class IntentRequest(BaseModel):
    intent_id: str = Field(..., description="Unique ID for this request")
    action_type: str = Field(..., description="Type of action (e.g., payout, refund, checkout, retry)")
    amount: int = Field(..., description="Amount in paise (must be integer)")
    currency: str = Field(..., description="Currency code (e.g., INR)")
    recipient: str = Field(..., description="Recipient identifier")
    agent_id: str = Field(..., description="Agent initiating the request")
    
    # Optional context fields (usually provided by backend context builders)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class FeatureContribution(BaseModel):
    feature: str
    value: Optional[float] = None
    shap_value: float
    direction: str

class EvaluationResponse(BaseModel):
    intent_id: str
    decision: str = Field(..., description="ALLOW or ESCALATE")
    reason: str
    model_risk_score: Optional[float] = None
    capability_token: Optional[str] = None
    executed_tx_id: Optional[str] = None
    explanation: Optional[List[FeatureContribution]] = None

class PolicyRuleRequest(BaseModel):
    text: str = Field(..., description="NL rule, e.g. 'ESCALATE IF amount > 5000000'")
    rule_id: Optional[str] = None

class PolicyRuleResponse(BaseModel):
    rule_id: str
    text: str
    status: str = "active"

class SimulateRequest(BaseModel):
    """Batch simulation: run N synthetic intents through the pipeline."""
    num_samples: int = Field(100, ge=1, le=10000)
    seed: int = Field(42)
    mode: str = Field("govern", description="observe or govern")

class SimulateResponse(BaseModel):
    total: int
    allowed: int
    escalated: int
    avg_risk_score: float
    escalation_rate: float
    decisions: List[Dict[str, Any]]

class SentinelExecutionEvent(BaseModel):
    event_id: str
    timestamp: str
    intent_id: str
    agent_id: str
    stage: str # INTENT, BEHAVIOR, POLICY, CAPABILITY, MCP, RAZORPAY, VERIFICATION, AUDIT
    behavioral_risk: Optional[float] = None
    semantic_risk: Optional[float] = None
    policy_decision: Optional[str] = None
    capability_issued: Optional[bool] = None
    mcp_tool: Optional[str] = None
    mcp_invocation: Optional[bool] = None
    execution_status: Optional[str] = None
    provider_reference: Optional[str] = None
    latency_ms: Optional[int] = None
    reason_codes: Optional[List[str]] = None
