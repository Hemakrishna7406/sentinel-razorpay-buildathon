import pytest
from ml.schema import BehavioralRiskResult, SemanticRiskResult, Decision
from ml.fusion.risk_fusion import RiskFusionEngine

def test_fusion_invariant_1_both_low():
    """TEST 1: behavioral = low, semantic = low -> Expected: ALLOW"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision == Decision.ALLOW

def test_fusion_invariant_2_behavioral_high_semantic_low():
    """TEST 2: behavioral = high, semantic = low -> Expected: ESCALATE or CONTAIN"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.75, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    # The max logic (0.75 > 0.15) should ESCALATE, plus disagreement logic (0.75 - 0.05 > 0.6) forces ESCALATE.
    assert result.decision == Decision.ESCALATE

def test_fusion_invariant_3_behavioral_low_semantic_high():
    """TEST 3: behavioral = low, semantic = high -> Expected: ESCALATE or CONTAIN"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.75, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision == Decision.ESCALATE

def test_fusion_invariant_4_behavioral_critical_semantic_low():
    """TEST 4: behavioral = critical, semantic = low -> MUST NOT become ALLOW"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.95, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision != Decision.ALLOW

def test_fusion_invariant_5_behavioral_low_semantic_critical():
    """TEST 5: behavioral = low, semantic = critical -> MUST NOT become ALLOW"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.95, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision != Decision.ALLOW

def test_fusion_invariant_6_both_critical():
    """TEST 6: both critical -> Expected: CONTAIN"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    behavioral = BehavioralRiskResult(risk_score=0.95, confidence=0.9, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.90, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision == Decision.CONTAIN

def test_fusion_invariant_7_missing_risk():
    """TEST 7: missing/invalid risk -> safe fail-closed behavior"""
    engine = RiskFusionEngine(disagreement_threshold=0.6, base_escalation_threshold=0.15, containment_threshold=0.85)
    # Behavioral missing entirely
    behavioral = BehavioralRiskResult(risk_score=None, confidence=0.0, reason_codes=[], model_version="v1")
    semantic = SemanticRiskResult(risk_score=0.05, confidence=0.9, reason_codes=[], provider="sim", model_version="sim", latency_ms=10)
    
    result = engine.fuse(behavioral, semantic)
    assert result.decision == Decision.ESCALATE
    
    # Semantic missing entirely (degraded operation)
    behavioral2 = BehavioralRiskResult(risk_score=0.20, confidence=0.9, reason_codes=[], model_version="v1")
    result2 = engine.fuse(behavioral2, None)
    assert result2.decision == Decision.ESCALATE
