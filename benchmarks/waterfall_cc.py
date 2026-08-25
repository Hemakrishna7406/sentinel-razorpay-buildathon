import asyncio
import time
import httpx

async def load_test_waterfall():
    print("Sending 250 concurrent requests...")
    
    async def make_req(client, i):
        intent = {
            "intent_id": f"bench_{i}",
            "agent_id": f"agent_{i}",
            "action_type": "refund",
            "amount": 100,
            "currency": "USD",
            "recipient": "user_test",
            "context": {"scenario": "normal"}
        }
        try:
            res = await client.post(
                "http://127.0.0.1:8000/evaluate",
                json=intent,
                headers={"Idempotency-Key": f"waterfall_{i}", "X-Sentinel-Mode": "govern"}
            )
            if res.status_code == 200:
                data = res.json()
                timings = data.get("timings", {})
                return timings
        except:
            pass
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [make_req(client, i) for i in range(250)]
        results = await asyncio.gather(*tasks)
    
    valid = [r for r in results if r]
    if not valid:
        print("No valid results")
        return
        
    avg_queue = sum(r.get("worker_queue_ms", 0) for r in valid) / len(valid)
    max_queue = max(r.get("worker_queue_ms", 0) for r in valid)
    avg_features = sum(r.get("worker_features_ms", 0) for r in valid) / len(valid)
    avg_api_wait = sum(r.get("api_wait_ms", 0) for r in valid) / len(valid)
    max_api_wait = max(r.get("api_wait_ms", 0) for r in valid)
    
    print(f"Total valid: {len(valid)}")
    print(f"Avg Worker Queue MS: {avg_queue:.2f}")
    print(f"Max Worker Queue MS: {max_queue:.2f}")
    print(f"Avg Worker Features MS: {avg_features:.2f}")
    print(f"Avg API Wait MS: {avg_api_wait:.2f}")
    print(f"Max API Wait MS: {max_api_wait:.2f}")

if __name__ == "__main__":
    asyncio.run(load_test_waterfall())
