import asyncio
import time
import httpx
import sys

async def run_waterfall():
    print("Sending single request to trace waterfall...")
    intent = {
        "intent_id": "waterfall_test",
        "agent_id": "agent_test",
        "action_type": "refund",
        "amount": 100,
        "currency": "USD",
        "recipient": "user_test",
        "context": {"scenario": "normal"}
    }
    
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "http://127.0.0.1:8000/evaluate",
                json=intent,
                headers={"Idempotency-Key": "waterfall_idem", "X-Sentinel-Mode": "govern"}
            )
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("Waterfall Timings (ms):")
                timings = data.get("timings", {})
                for k, v in timings.items():
                    print(f"  {k}: {v:.2f} ms")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_waterfall())
