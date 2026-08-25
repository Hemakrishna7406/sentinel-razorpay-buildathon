import asyncio
import httpx
import os
import subprocess
import time
from benchmarks.load_test import load_test

CONCURRENCIES = [1, 5, 10, 25, 50, 100, 200]

async def restart_worker_with_cc(max_tasks: int):
    print(f"\n[{max_tasks}] Restarting worker with MAX_CONCURRENT_TASKS={max_tasks}...")
    env = os.environ.copy()
    env["MAX_CONCURRENT_TASKS"] = str(max_tasks)
    
    # Restart the worker
    subprocess.run(
        ["docker", "compose", "up", "-d", "--force-recreate", "sentinel-worker"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    # Give it a moment to boot
    time.sleep(3)

async def main():
    print("Starting Concurrency Limits Benchmark...")
    print("Testing CC limits on a single worker to find the saturation knee.")
    
    # Keep load test fixed to a moderately high concurrency that stresses the system
    # but allows the worker CC to be the bottleneck.
    CLIENT_CC = 250
    TOTAL_REQS = 1000
    
    for max_tasks in CONCURRENCIES:
        await restart_worker_with_cc(max_tasks)
        print(f"\n--- Testing MAX_CONCURRENT_TASKS={max_tasks} (Load: {CLIENT_CC} CC, {TOTAL_REQS} reqs) ---")
        
        # We invoke load_test function which prints its own output
        await load_test(concurrency=CLIENT_CC, total_requests=TOTAL_REQS)
        
    print("\nConcurrency Benchmark Complete.")

if __name__ == "__main__":
    asyncio.run(main())
