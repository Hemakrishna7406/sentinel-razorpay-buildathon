import os
import sys

# Ensure the root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from security.policy import PolicyEngine
from ml.schema import BehavioralRiskResult, RiskAssessment, SemanticRiskResult, Decision
from ml.fusion.risk_fusion import RiskFusionEngine
from security.capability_token import IntentContext
import uuid


def print_result(name, passed, detail):
    status = "PASS" if passed else "FAIL"
    print(f"{status} | {name}\n      {detail}\n")


def test_evasion_resistance():
    print("Testing Evasion Resistance (High Behavioral Risk, Low Semantic)...")

    # 1. Setup Intent
    intent = IntentContext(
        intent_id=f"int_{uuid.uuid4().hex[:8]}",
        agent_id="test_agent",
        action_type="payout",
        amount=1000,
        currency="INR",
        recipient="bank_test",
    )
    context_data = {"has_sufficient_history": 1}

    # 2. Simulate ML Output
    # An attacker tries to mimic normal semantics (semantic risk = 0.05)
    # but the behavior model detects velocity drift (behavioral risk = 0.95)
    behavioral = BehavioralRiskResult(
        risk_score=0.95, confidence=0.9, reason_codes=["VELOCITY_DRIFT"], model_version="xgb-v3"
    )
    semantic = SemanticRiskResult(
        risk_score=0.05,
        confidence=0.9,
        reason_codes=["NORMAL_CONTEXT"],
        provider="sim",
        model_version="sim",
        latency_ms=10,
    )

    # 3. Risk Fusion (Should take max() and return ESCALATE because 0.95 > 0.15)
    fusion_engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15)
    fusion_result = fusion_engine.fuse(behavioral, semantic)

    assessment = RiskAssessment(behavioral=behavioral, semantic=semantic, fusion=fusion_result)

    # 4. Policy Engine Evaluation
    policy = PolicyEngine(suspicious_threshold=0.15)
    decision, reason, token = policy.evaluate(intent, context_data, assessment)

    passed = decision == Decision.ESCALATE and token is None
    print_result(
        "Evasion Resistance (Fusion Max Enforced)",
        passed,
        f"Decision: {decision.value}, Final Risk: {fusion_result.final_risk}, Reason: {reason}",
    )


def test_absolute_bounds():
    print("Testing Absolute Bounds Rule (Amount > 10,000,000)...")

    intent = IntentContext(
        intent_id=f"int_{uuid.uuid4().hex[:8]}",
        agent_id="test_agent_bounds",
        action_type="payout",
        amount=99999999,
        currency="INR",
        recipient="bank_test",
    )
    context_data = {"has_sufficient_history": 1}

    # Even if ML says perfectly safe (risk = 0.01)
    behavioral = BehavioralRiskResult(risk_score=0.01, confidence=0.9, reason_codes=[], model_version="xgb-v3")
    semantic = SemanticRiskResult(
        risk_score=0.01, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10
    )

    fusion_engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15)
    fusion_result = fusion_engine.fuse(behavioral, semantic)
    assessment = RiskAssessment(behavioral=behavioral, semantic=semantic, fusion=fusion_result)

    policy = PolicyEngine(suspicious_threshold=0.15)
    decision, reason, token = policy.evaluate(intent, context_data, assessment)

    passed = decision == Decision.CONTAIN and token is None
    print_result("Absolute Bounds Enforcement", passed, f"Decision: {decision.value}, Reason: {reason}")


def run_all():
    print("--- Sentinel Core Governance Proofs ---")
    test_evasion_resistance()
    test_absolute_bounds()
    print("--- Proof Execution Complete ---")


if __name__ == "__main__":
    run_all()
