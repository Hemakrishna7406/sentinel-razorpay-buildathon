"""
Sentinel — Scaling Benchmark Script

A load testing script to measure the throughput (TPS) and latency
of the Event-Driven Architecture (`POST /evaluate/async`).

Usage:
1. Ensure the infrastructure is running:
   docker-compose up -d --build
2. Scale the workers:
   docker-compose up -d --scale sentinel-worker=3
3. Run the benchmark:
   python scripts/benchmark.py --workers 3 --requests 5000 --concurrency 100
"""

import asyncio
import time
import argparse
import uuid
import json
import statistics
import aiohttp

async def send_request(session, url, payload, headers):
    start = time.perf_counter()
    try:
        async with session.post(url, json=payload, headers=headers) as response:
            status = response.status
            await response.read()
    except Exception as e:
        status = 0
    end = time.perf_counter()
    return status, (end - start) * 1000  # Latency in ms

async def run_benchmark(num_requests: int, concurrency: int, target_url: str):
    print(f"Starting benchmark: {num_requests} requests with concurrency {concurrency}...")
    
    payloads = []
    for _ in range(num_requests):
        intent_id = f"bench_{uuid.uuid4().hex[:8]}"
        payload = {
            "intent_id": intent_id,
            "agent_id": f"agent_{uuid.uuid4().hex[:4]}",
            "action_type": "payout",
            "amount": 1000,
            "currency": "INR",
            "recipient": "bench_recipient"
        }
        headers = {"Idempotency-Key": f"idem_{intent_id}"}
        payloads.append((payload, headers))
        
    start_time = time.perf_counter()
    
    latencies = []
    status_counts = {}
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bound_request(p, h):
            async with semaphore:
                return await send_request(session, target_url, p, h)
                
        tasks = [bound_request(p, h) for p, h in payloads]
        results = await asyncio.gather(*tasks)
        
        for status, latency in results:
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == 202:
                latencies.append(latency)
                
    total_time = time.perf_counter() - start_time
    
    # Calculate metrics
    tps = num_requests / total_time if total_time > 0 else 0
    
    if latencies:
        p50 = statistics.median(latencies)
        p95 = statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies)
        p99 = statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        avg = statistics.mean(latencies)
    else:
        p50 = p95 = p99 = avg = 0.0

    print("\n" + "="*40)
    print("BENCHMARK RESULTS")
    print("="*40)
    print(f"Total Requests  : {num_requests}")
    print(f"Concurrency     : {concurrency}")
    print(f"Total Time      : {total_time:.2f} seconds")
    print(f"Throughput      : {tps:.2f} TPS")
    print("-" * 40)
    print("LATENCY (Async API Accept):")
    print(f"  Average : {avg:.2f} ms")
    print(f"  p50     : {p50:.2f} ms")
    print(f"  p95     : {p95:.2f} ms")
    print(f"  p99     : {p99:.2f} ms")
    print("-" * 40)
    print("STATUS CODES:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status} : {count}")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentinel Scaling Benchmark")
    parser.add_argument("--requests", type=int, default=1000, help="Total number of requests")
    parser.add_argument("--concurrency", type=int, default=50, help="Number of concurrent requests")
    parser.add_argument("--url", type=str, default="http://localhost:8000/evaluate/async", help="Target API URL")
    
    args = parser.parse_args()
    
    # Needs aiohttp: pip install aiohttp
    asyncio.run(run_benchmark(args.requests, args.concurrency, args.url))
