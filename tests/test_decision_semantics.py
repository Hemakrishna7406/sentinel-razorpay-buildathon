"""Regression tests for the three terminal governance decisions."""

from ml.fusion.risk_fusion import RiskFusionEngine
from ml.schema import BehavioralRiskResult, RiskAssessment
from security.capability_token import IntentContext
from security.policy import PolicyEngine


def assessment(score: float) -> RiskAssessment:
    behavioral = BehavioralRiskResult(
        risk_score=score,
        confidence=1.0,
        reason_codes=["TEST"],
        model_version="test",
    )
    return RiskAssessment(
        behavioral=behavioral,
        fusion=RiskFusionEngine().fuse(behavioral, None),
    )


def intent(amount: int = 1_000) -> IntentContext:
    return IntentContext("intent-1", "agent-1", "payout", amount, "INR", "recipient-1")


def test_allow_issues_an_exact_action_capability():
    decision, _, token = PolicyEngine().evaluate(intent(), {"has_sufficient_history": 1}, assessment(0.1))
    assert decision == "ALLOW"
    assert token is not None


def test_escalate_issues_no_capability():
    decision, _, token = PolicyEngine().evaluate(intent(), {"has_sufficient_history": 1}, assessment(0.6))
    assert decision == "ESCALATE"
    assert token is None


def test_contain_issues_no_capability():
    decision, _, token = PolicyEngine().evaluate(intent(amount=10_000_001), {}, assessment(0.1))
    assert decision == "CONTAIN"
    assert token is None


def test_high_fused_risk_contains():
    decision, _, token = PolicyEngine().evaluate(intent(), {"has_sufficient_history": 1}, assessment(0.9))
    assert decision == "CONTAIN"
    assert token is None
