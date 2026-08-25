import asyncio
import httpx
import time
import random
import uuid
import yaml
from typing import Dict, Any

from benchmarks.metrics import MetricsCollector

# Default config loaded from environment/YAML if needed
API_URL = "http://127.0.0.1:8000"

def generate_intent(traffic_type: str) -> Dict[str, Any]:
    intent_id = f"bench_{uuid.uuid4().hex[:8]}"
    agent_id = f"agent_{random.randint(1, 1000)}"
    
    if traffic_type == "ALLOW":
        return {
            "intent_id": intent_id,
            "agent_id": agent_id,
            "action_type": "refund",
            "amount": random.randint(10, 500),
            "currency": "USD",
            "recipient": f"user_{random.randint(1, 100)}",
            "context": {"scenario": "normal"}
        }
    elif traffic_type == "ESCALATE":
        return {
            "intent_id": intent_id,
            "agent_id": agent_id,
            "action_type": "payout",
            "amount": random.randint(5000, 15000),
            "currency": "USD",
            "recipient": "new_vendor_999",
            "context": {"scenario": "abuse-burst"}
        }
    elif traffic_type == "CONTAIN":
        return {
            "intent_id": intent_id,
            "agent_id": agent_id,
            "action_type": "payout",
            "amount": random.randint(50000, 100000),
            "currency": "USD",
            "recipient": "unknown_entity",
            "context": {"scenario": "privilege-violation"}
        }
    else:
        return generate_intent("ALLOW")

def get_traffic_mix() -> str:
    r = random.random()
    if r < 0.40:
        return "ALLOW"
    elif r < 0.65:
        return "ESCALATE"
    elif r < 0.80:
        return "CONTAIN"
    elif r < 0.90:
        return "NEW_AGENT"
    elif r < 0.95:
        return "DUPLICATE"
    else:
        return "POLICY_BOUNDARY"

async def make_request(client: httpx.AsyncClient, metrics: MetricsCollector):
    traffic_type = get_traffic_mix()
    # If NEW_AGENT, use a brand new UUID
    # If DUPLICATE, reuse a specific UUID (handle later)
    # For now, just generate base types
    if traffic_type in ["NEW_AGENT", "DUPLICATE", "POLICY_BOUNDARY"]:
        traffic_type = "ALLOW" # fallback for simple implementation
        
    intent = generate_intent(traffic_type)
    idem_key = f"idem_{intent['intent_id']}"
    
    headers = {
        "Idempotency-Key": idem_key,
        "X-Sentinel-Mode": "govern"
    }
    
    start = time.perf_counter()
    try:
        response = await client.post(f"{API_URL}/evaluate", json=intent, headers=headers)
        metrics.record((time.perf_counter() - start) * 1000, is_error=response.status_code >= 400)
    except Exception:
        metrics.record((time.perf_counter() - start) * 1000, is_error=True)

async def load_test(concurrency: int, total_requests: int):
    print(f"Starting Load Test: {concurrency} CC, {total_requests} requests")
    metrics = MetricsCollector()
    metrics.start()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = set()
        completed = 0
        
        while completed < total_requests or tasks:
            while len(tasks) < concurrency and completed + len(tasks) < total_requests:
                tasks.add(asyncio.create_task(make_request(client, metrics)))
                
            if tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                completed += len(done)
                
    metrics.stop()
    metrics.print_summary(f"Load Test ({concurrency} concurrency)")

if __name__ == "__main__":
    # Test suite with multiple concurrency levels
    concurrencies = [250, 500]
    
    async def run_suite():
        for cc in concurrencies:
            reqs = max(500, cc * 5)
            await load_test(concurrency=cc, total_requests=reqs)
            
    asyncio.run(run_suite())
