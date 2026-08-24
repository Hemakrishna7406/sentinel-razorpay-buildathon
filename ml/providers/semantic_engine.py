import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any

from ml.schema import SemanticRiskResult
from security.capability_token import IntentContext

class SemanticRiskProvider(ABC):
    @abstractmethod
    def evaluate(self, intent: IntentContext, context: Dict[str, Any]) -> SemanticRiskResult:
        pass

class SimulatedSemanticClient(SemanticRiskProvider):
    """
    Simulates a foundation model evaluating a transaction sequence.
    Generates deterministic contextual signals rather than random noise.
    """
    def evaluate(self, intent: IntentContext, context: Dict[str, Any]) -> SemanticRiskResult:
        start_time = time.time()
        
        # Simulate some latency
        time.sleep(0.02)
        
        risk_score = 0.1
        confidence = 0.90
        reason_codes = []
        
        # Deterministic rules to simulate semantic pattern recognition
        scenario = context.get("scenario", "")
        
        if "unseen" in scenario or "novel" in scenario:
            risk_score += 0.4
            reason_codes.append("RECIPIENT_NOVELTY")
            confidence = 0.85
            
        if "escalation" in scenario or "rapid" in scenario:
            risk_score += 0.3
            reason_codes.append("SEQUENCE_ESCALATION")
            
        if intent.amount > 50000:
            risk_score += 0.1
            reason_codes.append("HIGH_VALUE_CONTEXT")
            
        # Introduce occasional low confidence to test disagreement handling
        if "ambiguous" in scenario:
            confidence = 0.40
            reason_codes.append("AMBIGUOUS_INTENT_PATTERN")

        risk_score = min(max(risk_score, 0.0), 1.0)
        
        latency_ms = int((time.time() - start_time) * 1000)

        return SemanticRiskResult(
            risk_score=risk_score,
            confidence=confidence,
            reason_codes=reason_codes or ["NORMAL_CONTEXT"],
            provider="simulated-semantic",
            model_version="sim-v1",
            latency_ms=latency_ms
        )

class VulcanClient(SemanticRiskProvider):
    """
    Simulated semantic risk provider.
    """
    def evaluate(self, intent: IntentContext, context: Dict[str, Any]) -> SemanticRiskResult:
        raise NotImplementedError("Genuine Vulcan API access not configured.")
