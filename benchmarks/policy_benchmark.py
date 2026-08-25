import asyncio
import time

from benchmarks.metrics import MetricsCollector
from security.policy import PolicyEngine
from security.capability_token import IntentContext
from ml.schema import RiskAssessment, BehavioralRiskResult, FusionResult, Decision

async def benchmark_policy():
    print("Initializing Policy Engine...")
    engine = PolicyEngine(suspicious_threshold=0.5)
    
    intent = IntentContext(
        intent_id="pol_bench", agent_id="agent_1", action_type="refund",
        amount=100, currency="USD", recipient="user_1"
    )
    context = {"agent_id": "agent_1", "role": "financial_agent"}
    
    # Mock assessment
    behavioral = BehavioralRiskResult(
        risk_score=0.4, confidence=1.0, reason_codes=[], model_version="1.0"
    )
    fusion = FusionResult(
        final_risk=0.4, disagreement=False, decision=Decision.ALLOW, reason="Clear"
    )
    assessment = RiskAssessment(behavioral=behavioral, fusion=fusion)
    
    metrics = MetricsCollector()
    WARMUP = 100
    RUNS = 5000

    print("Warming up Policy Engine...")
    for _ in range(WARMUP):
        engine.evaluate(intent, context, assessment)
        
    print("Running Policy Engine Benchmark...")
    for i in range(RUNS):
        metrics.start()
        engine.evaluate(intent, context, assessment)
        metrics.stop()
        metrics.record((metrics.end_time - metrics.start_time) * 1000)
        
    metrics.print_summary("Policy Engine Evaluation")

if __name__ == "__main__":
    asyncio.run(benchmark_policy())
