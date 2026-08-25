import asyncio
import httpx
import time
import uuid

from benchmarks.metrics import MetricsCollector
from benchmarks.load_test import generate_intent, API_URL

async def measure_authorization_latency():
    print("Starting Authorization Latency Benchmark (Sequential)")
    metrics_cold = MetricsCollector()
    metrics_warm = MetricsCollector()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Cold start measurement (first 10 requests)
        print("Measuring Cold Start...")
        metrics_cold.start()
        for i in range(10):
            intent = generate_intent("ALLOW")
            idem_key = f"idem_cold_{uuid.uuid4().hex}"
            
            start = time.perf_counter()
            try:
                res = await client.post(
                    f"{API_URL}/evaluate", 
                    json=intent, 
                    headers={"Idempotency-Key": idem_key, "X-Sentinel-Mode": "govern"}
                )
                metrics_cold.record((time.perf_counter() - start) * 1000, is_error=res.status_code >= 400)
            except Exception:
                metrics_cold.record((time.perf_counter() - start) * 1000, is_error=True)
        metrics_cold.stop()
                
        # Warm measurement (next 500 requests)
        print("Measuring Warm State...")
        metrics_warm.start()
        for i in range(500):
            intent = generate_intent("ALLOW")
            idem_key = f"idem_warm_{uuid.uuid4().hex}"
            
            start = time.perf_counter()
            try:
                res = await client.post(
                    f"{API_URL}/evaluate", 
                    json=intent, 
                    headers={"Idempotency-Key": idem_key, "X-Sentinel-Mode": "govern"}
                )
                metrics_warm.record((time.perf_counter() - start) * 1000, is_error=res.status_code >= 400)
            except Exception:
                metrics_warm.record((time.perf_counter() - start) * 1000, is_error=True)
        metrics_warm.stop()
        
    metrics_cold.print_summary("Cold Start Latency (First 10 reqs)")
    metrics_warm.print_summary("Warm State Latency (Next 500 reqs)")

if __name__ == "__main__":
    asyncio.run(measure_authorization_latency())
