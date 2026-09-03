import logging
from typing import Optional

from ml.schema import BehavioralRiskResult, SemanticRiskResult, FusionResult, Decision

logger = logging.getLogger(__name__)

class RiskFusionEngine:
    def __init__(
        self,
        disagreement_threshold: float = 0.6,
        base_escalation_threshold: float = 0.15,
        containment_threshold: float = 0.85,
    ):
        self.disagreement_threshold = disagreement_threshold
        self.base_escalation_threshold = base_escalation_threshold
        self.containment_threshold = containment_threshold

    def fuse(self, behavioral: BehavioralRiskResult, semantic: Optional[SemanticRiskResult]) -> FusionResult:
        if behavioral.risk_score is None or getattr(behavioral, "risk_status", None) == "MODEL_UNAVAILABLE":
            return FusionResult(
                final_risk=None,
                disagreement=False,
                decision=Decision.ESCALATE,
                reason="Behavioral model unavailable (risk score is NULL). Uncertainty implies risk."
            )
        
        if not semantic:
            # Degraded operation: Semantic provider unavailable
            if behavioral.risk_score >= self.containment_threshold:
                decision = Decision.CONTAIN
            else:
                decision = Decision.ESCALATE
            return FusionResult(
                final_risk=behavioral.risk_score,
                disagreement=False,
                decision=decision,
                reason="Semantic provider unavailable. Failing closed to ESCALATE."
            )
            
        # We have both signals
        disagreement = abs(behavioral.risk_score - semantic.risk_score) > self.disagreement_threshold
        
        # Calculate final risk using a strict Fail-Closed Maximum
        # Do NOT average signals, as that masks highly anomalous semantic signals with low behavioral ones.
        final_risk = max(behavioral.risk_score, semantic.risk_score)
            
        if disagreement:
            return FusionResult(
                final_risk=final_risk,
                disagreement=True,
                decision=Decision.ESCALATE,
                reason=f"MODEL DISAGREEMENT: Behavioral ({behavioral.risk_score:.2f}) vs Semantic ({semantic.risk_score:.2f}). Escalate due to uncertainty."
            )
            
        # Low confidence semantic with high risk -> uncertainty signal
        if semantic.risk_score > self.base_escalation_threshold and semantic.confidence < 0.5:
            return FusionResult(
                final_risk=final_risk,
                disagreement=False,
                decision=Decision.ESCALATE,
                reason="High semantic risk but low confidence. Treating uncertainty as risk."
            )

        if final_risk >= self.containment_threshold:
            return FusionResult(
                final_risk=final_risk,
                disagreement=False,
                decision=Decision.CONTAIN,
                reason=f"Fused risk score {final_risk:.2f} exceeds containment threshold {self.containment_threshold}.",
            )

        if final_risk >= self.base_escalation_threshold:
            return FusionResult(
                final_risk=final_risk,
                disagreement=False,
                decision=Decision.ESCALATE,
                reason=f"Fused risk score {final_risk:.2f} exceeds threshold {self.base_escalation_threshold}."
            )
            
        return FusionResult(
            final_risk=final_risk,
            disagreement=False,
            decision=Decision.ALLOW,
            reason="Models agree. Risk is below escalation threshold."
        )
