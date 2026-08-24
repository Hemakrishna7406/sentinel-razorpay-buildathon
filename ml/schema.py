from typing import List, Optional
from pydantic import BaseModel

class BehavioralRiskResult(BaseModel):
    risk_score: float
    confidence: float
    reason_codes: List[str]
    model_version: str

class SemanticRiskResult(BaseModel):
    risk_score: float
    confidence: float
    reason_codes: List[str]
    provider: str
    model_version: str
    latency_ms: int

class FusionResult(BaseModel):
    final_risk: float
    disagreement: bool
    decision: str  # ALLOW, ESCALATE, CONTAIN
    reason: str

class RiskAssessment(BaseModel):
    behavioral: BehavioralRiskResult
    semantic: Optional[SemanticRiskResult] = None
    fusion: FusionResult
