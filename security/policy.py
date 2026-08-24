"""
Sentinel — Policy Engine

Combines raw ML probabilities, business rules, NL-compiled rules, and context 
to produce a final decision (ALLOW or ESCALATE) and issues a Capability Token if allowed.
"""

from typing import Any, Dict, Optional, Tuple

from security.capability_token import IntentContext, TokenManager
from security.nl_policy import NLPolicyCompiler


from ml.schema import RiskAssessment

class PolicyEngine:
    def __init__(self, suspicious_threshold: float = 0.5):
        self.suspicious_threshold = suspicious_threshold
        self.token_manager = TokenManager()
        self.nl_compiler = NLPolicyCompiler()
        
    def evaluate(self, intent: IntentContext, context_features: Dict[str, Any], assessment: RiskAssessment) -> Tuple[str, str, Optional[str]]:
        """
        Evaluate an intent and return (decision, reason, capability_token).
        decision is either "ALLOW" or "ESCALATE".
        """
        
        # NL Policy Rules (user-defined, evaluated first)
        nl_context = {
            **context_features,
            "amount": intent.amount,
            "action_type": intent.action_type,
            "currency": intent.currency,
            "recipient": intent.recipient,
            "model_risk": assessment.behavioral.risk_score,
            "semantic_risk": assessment.semantic.risk_score if assessment.semantic else 0.0,
            "fusion_risk": assessment.fusion.final_risk
        }
        should_escalate, nl_reason = self.nl_compiler.evaluate(nl_context)
        if should_escalate:
            return "ESCALATE", nl_reason, None
        
        # Rule 1: Insufficient history -> Conservative escalation
        if context_features.get("has_sufficient_history", 1) == 0:
            if intent.amount > 50000:
                return "ESCALATE", "Insufficient history and amount exceeds new agent limit.", None
                
        # Rule 2: Absolute bounds
        if intent.amount > 10000000:
            return "ESCALATE", "Amount exceeds absolute system limit.", None
            
        # Fusion Evaluation
        if assessment.fusion.decision == "ESCALATE":
            return "ESCALATE", assessment.fusion.reason, None
            
        # Default ALLOW
        try:
            token = self.token_manager.issue_token(intent, "ALLOW")
            return "ALLOW", "Cleared all policy and fusion checks.", token
        except Exception as e:
            # Failsafe
            return "ESCALATE", f"Failed to issue capability token: {str(e)}", None

