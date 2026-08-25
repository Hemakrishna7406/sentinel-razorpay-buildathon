import asyncio
import time
from unittest.mock import AsyncMock

from benchmarks.metrics import MetricsCollector
from security.idempotency import IdempotencyEngine
from security.capability_token import IntentContext

# Note: Tier A Microbenchmark uses a mocked Redis to measure python overhead.
# To measure actual Redis latency, we will use a separate test against real Redis.
async def benchmark_redis_mocked():
    print("Initializing Mocked Idempotency Engine...")
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    
    engine = IdempotencyEngine(mock_redis)
    intent = IntentContext(
        intent_id="idem_bench", agent_id="agent_1", action_type="refund",
        amount=100, currency="USD", recipient="user_1"
    )
    
    metrics = MetricsCollector()
    WARMUP = 100
    RUNS = 2000

    for _ in range(WARMUP):
        await engine.check_and_record(f"key_{_}", intent, "agent_1")
        
    print("Running Mocked Redis Idempotency Benchmark...")
    for i in range(RUNS):
        metrics.start()
        await engine.check_and_record(f"key_run_{i}", intent, "agent_1")
        metrics.stop()
        metrics.record((metrics.end_time - metrics.start_time) * 1000)
        
    metrics.print_summary("Idempotency Engine (Mocked I/O)")

if __name__ == "__main__":
    asyncio.run(benchmark_redis_mocked())
