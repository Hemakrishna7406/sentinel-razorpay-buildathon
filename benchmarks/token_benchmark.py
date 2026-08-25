import asyncio

from benchmarks.metrics import MetricsCollector
from security.capability_token import TokenManager, IntentContext

async def benchmark_token():
    print("Initializing Capability Token Manager...")
    manager = TokenManager()
    
    intent = IntentContext(
        intent_id="tok_bench", agent_id="agent_1", action_type="refund",
        amount=100, currency="USD", recipient="user_1"
    )
    
    metrics_issue = MetricsCollector()
    metrics_verify = MetricsCollector()
    WARMUP = 100
    RUNS = 5000

    print("Warming up Token Manager...")
    for _ in range(WARMUP):
        token = manager.issue_token(intent, "ALLOW")
        manager.verify_token(token, intent)
        
    print("Running Token Manager Benchmark...")
    for i in range(RUNS):
        metrics_issue.start()
        token = manager.issue_token(intent, "ALLOW")
        metrics_issue.stop()
        metrics_issue.record((metrics_issue.end_time - metrics_issue.start_time) * 1000)
        
        metrics_verify.start()
        manager.verify_token(token, intent)
        metrics_verify.stop()
        metrics_verify.record((metrics_verify.end_time - metrics_verify.start_time) * 1000)
        
    metrics_issue.print_summary("Token Issuance")
    metrics_verify.print_summary("Token Verification")

if __name__ == "__main__":
    asyncio.run(benchmark_token())
