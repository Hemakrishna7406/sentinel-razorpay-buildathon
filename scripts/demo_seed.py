import asyncio
import httpx
import time
import random
import argparse

API_URL = "http://127.0.0.1:8000"

SCENARIOS = [
    "normal",
    "abuse-burst",
    "privilege-violation",
    "suspicious",
    "malicious",
    "replay",
    "redis_failure"
]

async def trigger_scenario(client, scenario):
    try:
        print(f"Triggering scenario: {scenario}")
        response = await client.post(f"{API_URL}/demo/scenarios/{scenario}")
        if response.status_code == 200:
            print(f"✅ Successfully triggered {scenario}")
        else:
            print(f"❌ Failed to trigger {scenario}. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error triggering {scenario}: {e}")

async def run_seed_loop(interval=5):
    print(f"Starting Demo Seed Script (Interval: {interval}s)")
    print(f"Targeting: {API_URL}/demo/scenarios/...")
    
    async with httpx.AsyncClient() as client:
        while True:
            # Weight normal traffic higher to make it look realistic
            weights = [50, 10, 10, 10, 10, 5, 5]
            scenario = random.choices(SCENARIOS, weights=weights, k=1)[0]
            
            await trigger_scenario(client, scenario)
            
            # Wait before next event
            await asyncio.sleep(interval + random.uniform(-1, 2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Sentinel Demo Dashboard")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between scenarios")
    parser.add_argument("--once", action="store_true", help="Run all scenarios once and exit")
    
    args = parser.parse_args()
    
    if args.once:
        async def run_all():
            async with httpx.AsyncClient() as client:
                for scenario in SCENARIOS:
                    await trigger_scenario(client, scenario)
                    await asyncio.sleep(6) # Give time for the SSE events to finish
        asyncio.run(run_all())
    else:
        try:
            asyncio.run(run_seed_loop(args.interval))
        except KeyboardInterrupt:
            print("\nShutting down demo seed script.")
