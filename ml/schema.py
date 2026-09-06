from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class Decision(str, Enum):
    ALLOW = "ALLOW"
    ESCALATE = "ESCALATE"
    CONTAIN = "CONTAIN"


class BehavioralRiskResult(BaseModel):
    risk_score: Optional[float] = None
    risk_status: Optional[str] = None
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
    final_risk: Optional[float] = None
    disagreement: bool
    decision: Decision
    reason: str


class RiskAssessment(BaseModel):
    behavioral: BehavioralRiskResult
    semantic: Optional[SemanticRiskResult] = None
    fusion: FusionResult
