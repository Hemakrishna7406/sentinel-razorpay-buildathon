import logging
from typing import Optional

from ml.schema import BehavioralRiskResult, SemanticRiskResult, FusionResult

logger = logging.getLogger(__name__)

class RiskFusionEngine:
    def __init__(self, disagreement_threshold: float = 0.6, base_escalation_threshold: float = 0.5):
        self.disagreement_threshold = disagreement_threshold
        self.base_escalation_threshold = base_escalation_threshold

    def fuse(self, behavioral: BehavioralRiskResult, semantic: Optional[SemanticRiskResult]) -> FusionResult:
        
        if not semantic:
            # Degraded operation: Semantic provider unavailable
            decision = "ESCALATE" if behavioral.risk_score >= self.base_escalation_threshold else "ALLOW"
            return FusionResult(
                final_risk=behavioral.risk_score,
                disagreement=False,
                decision=decision,
                reason="Semantic provider unavailable. Fallback to behavioral risk."
            )
            
        # We have both signals
        disagreement = abs(behavioral.risk_score - semantic.risk_score) > self.disagreement_threshold
        
        # Calculate a simple confidence-weighted fusion score
        total_confidence = behavioral.confidence + semantic.confidence
        if total_confidence > 0:
            final_risk = (
                (behavioral.risk_score * behavioral.confidence) + 
                (semantic.risk_score * semantic.confidence)
            ) / total_confidence
        else:
            final_risk = max(behavioral.risk_score, semantic.risk_score)
            
        if disagreement:
            return FusionResult(
                final_risk=final_risk,
                disagreement=True,
                decision="ESCALATE",
                reason=f"MODEL DISAGREEMENT: Behavioral ({behavioral.risk_score:.2f}) vs Semantic ({semantic.risk_score:.2f}). Escalate due to uncertainty."
            )
            
        # Low confidence semantic with high risk -> uncertainty signal
        if semantic.risk_score > self.base_escalation_threshold and semantic.confidence < 0.5:
            return FusionResult(
                final_risk=final_risk,
                disagreement=False,
                decision="ESCALATE",
                reason="High semantic risk but low confidence. Treating uncertainty as risk."
            )

        if final_risk >= self.base_escalation_threshold:
            return FusionResult(
                final_risk=final_risk,
                disagreement=False,
                decision="ESCALATE",
                reason=f"Fused risk score {final_risk:.2f} exceeds threshold {self.base_escalation_threshold}."
            )
            
        return FusionResult(
            final_risk=final_risk,
            disagreement=False,
            decision="ALLOW",
            reason="Models agree. Risk is below escalation threshold."
        )
