"""
Sentinel — Policy Engine

Combines raw ML probabilities, business rules, NL-compiled rules, and context
to produce ALLOW, ESCALATE, or CONTAIN. Only ALLOW can issue a capability.
"""

from typing import Any, Dict, Optional, Tuple

from security.capability_token import IntentContext, TokenManager
from security.nl_policy import NLPolicyCompiler

from ml.schema import BehavioralRiskResult, FusionResult, RiskAssessment, Decision


class PolicyEngine:
    def __init__(self, suspicious_threshold: float = 0.15):
        self.suspicious_threshold = suspicious_threshold
        self.token_manager = TokenManager()
        self.nl_compiler = NLPolicyCompiler()

    def evaluate(
        self, intent: IntentContext, context_features: Dict[str, Any], assessment: RiskAssessment
    ) -> Tuple[Decision, str, Optional[str]]:
        """
        Evaluate an intent and return (decision, reason, capability_token).
        Decision is ALLOW, ESCALATE, or CONTAIN. Non-ALLOW decisions never
        receive a capability token.
        """

        # Accepting a numeric score keeps the small synchronous simulator
        # backward-compatible; production callers pass a RiskAssessment.
        if isinstance(assessment, (int, float)):
            score = float(assessment)
            assessment = RiskAssessment(
                behavioral=BehavioralRiskResult(
                    risk_score=score,
                    confidence=1.0,
                    reason_codes=["LEGACY_SCORE"],
                    model_version="legacy",
                ),
                fusion=FusionResult(
                    final_risk=score,
                    disagreement=False,
                    decision=Decision.ESCALATE if score >= self.suspicious_threshold else Decision.ALLOW,
                    reason="Legacy score evaluation.",
                ),
            )

        # Rule 0: Model Availability
        if getattr(assessment.behavioral, "risk_status", None) == "MODEL_UNAVAILABLE":
            return Decision.ESCALATE, "Behavioral model is unavailable. Failing closed.", None

        # NL Policy Rules (user-defined, evaluated first)
        nl_context = {
            **context_features,
            "amount": intent.amount,
            "action_type": intent.action_type,
            "currency": intent.currency,
            "recipient": intent.recipient,
            "model_risk": assessment.behavioral.risk_score,
            "semantic_risk": assessment.semantic.risk_score if assessment.semantic else None,
            "fusion_risk": assessment.fusion.final_risk,
        }
        should_escalate, nl_reason = self.nl_compiler.evaluate(nl_context)
        if should_escalate:
            return Decision.ESCALATE, nl_reason, None

        # Rule 1: Insufficient history -> Conservative escalation
        if context_features.get("has_sufficient_history", 1) == 0:
            if intent.amount > 50000:
                return Decision.ESCALATE, "Insufficient history and amount exceeds new agent limit.", None

        # Rule 2: Absolute bounds
        if intent.amount > 10000000:
            return Decision.CONTAIN, "Amount exceeds absolute system limit.", None

        # Fusion Evaluation
        if assessment.fusion.decision in {Decision.ESCALATE, Decision.CONTAIN}:
            return assessment.fusion.decision, assessment.fusion.reason, None

        # Default ALLOW
        try:
            token = self.token_manager.issue_token(intent, Decision.ALLOW.value)
            return Decision.ALLOW, "Cleared all policy and fusion checks.", token
        except Exception as e:
            # Failsafe
            return Decision.ESCALATE, f"Failed to issue capability token: {str(e)}", None
