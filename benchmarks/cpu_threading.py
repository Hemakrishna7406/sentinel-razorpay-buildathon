import asyncio
import os
import subprocess
import time
from sqlalchemy import create_engine, text
from benchmarks.load_test import load_test
import psutil

DB_URL = os.environ.get("DATABASE_URL", "postgresql://sentinel:sentinelpassword@localhost:5432/sentinel_db")
engine = create_engine(DB_URL)

MAX_CC_LIST = [1, 2, 5, 10]
NTHREAD_LIST = ["1", "2", "4", "auto"]

def verify_security_invariants():
    with engine.connect() as conn:
        unsafe_allow = conn.execute(text("SELECT count(*) FROM audit_ledger WHERE decision='ALLOW' AND behavioral_risk_score IS NULL")).scalar()
        duplicates = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT intent_id, count(*) FROM audit_ledger GROUP BY intent_id HAVING count(*) > 1
            ) as dupes
        """)).scalar()
        unauthorized = conn.execute(text("SELECT count(*) FROM audit_ledger WHERE decision='ALLOW' AND model_risk_score > 0.5")).scalar()
        return {
            "unsafe_allow": unsafe_allow or 0,
            "duplicates": duplicates or 0,
            "unauthorized_mcp": unauthorized or 0
        }

def measure_cpu():
    return psutil.cpu_percent(interval=1)

async def configure_worker(max_tasks: int, nthread: str):
    print(f"\n[Config] Restarting sentinel-worker with MAX_CONCURRENT_TASKS={max_tasks}, XGB_NTHREAD={nthread}...")
    env = os.environ.copy()
    env["MAX_CONCURRENT_TASKS"] = str(max_tasks)
    env["XGB_NTHREAD"] = nthread
    subprocess.run(
        ["docker", "compose", "up", "-d", "--scale", "sentinel-worker=1", "--force-recreate", "sentinel-worker"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(8)

async def main():
    print("Starting CPU Threading Matrix Test...")
    
    # We will test at a fixed concurrency of 100 to quickly find the optimal operating point.
    load_cc = 100
    reqs = 500
    
    for max_tasks in MAX_CC_LIST:
        for nthread in NTHREAD_LIST:
            await configure_worker(max_tasks, nthread)
            print(f"\n--- Testing MAX_CC={max_tasks}, nthread={nthread} @ {load_cc} CC ---")
            
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM audit_ledger"))
                conn.commit()
            
            # Start CPU measurement in background or just measure overall system CPU
            # For simplicity, we just measure the load_test time, psutil during the test is hard to isolate 
            # to just the container in Python without docker stats.
            
            await load_test(concurrency=load_cc, total_requests=reqs)
            
            time.sleep(2)
            invariants = verify_security_invariants()
            print("SECURITY INVARIANTS:")
            failed = False
            for k, v in invariants.items():
                print(f"  {k}: {v}")
                if v > 0:
                    failed = True
            
            if failed:
                print(f"[FAIL] SECURITY REGRESSION GATE FAILED!")
                return
            else:
                print(f"[OK] SECURITY GATES PASSED")

    print("\nThreading Matrix Benchmark Complete.")
    await configure_worker(5, "auto")

if __name__ == "__main__":
    asyncio.run(main())
