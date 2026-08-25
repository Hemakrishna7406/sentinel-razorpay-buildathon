import asyncio
import os
import subprocess
import time
from sqlalchemy import create_engine, text
from benchmarks.load_test import load_test

DB_URL = os.environ.get("DATABASE_URL", "postgresql://sentinel:sentinelpassword@localhost:5432/sentinel_db")
engine = create_engine(DB_URL)

WORKERS = [1, 2, 4]
CONCURRENCIES = [100, 250, 500, 1000]
MAX_CC = 2
NTHREAD = "4"

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

async def scale_workers(count: int, max_tasks: int, nthread: str):
    print(f"\n[Scaling] Scaling sentinel-worker to {count} instances with MAX_CC={max_tasks}, XGB_NTHREAD={nthread}...")
    env = os.environ.copy()
    env["MAX_CONCURRENT_TASKS"] = str(max_tasks)
    env["XGB_NTHREAD"] = nthread
    env["INFERENCE_BACKEND"] = "cpu"
    subprocess.run(
        ["docker", "compose", "up", "-d", "--scale", f"sentinel-worker={count}", "--force-recreate", "sentinel-worker"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(8)

async def main():
    print("Starting Final CPU Horizontal Scaling Test...")
    print(f"Base Configuration: MAX_CONCURRENT_TASKS={MAX_CC}, XGB_NTHREAD={NTHREAD}")
    
    for w in WORKERS:
        await scale_workers(w, MAX_CC, NTHREAD)
        for cc in CONCURRENCIES:
            print(f"\n--- Testing {w} Workers @ {cc} Load CC ---")
            
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM audit_ledger"))
                conn.commit()
            
            await load_test(concurrency=cc, total_requests=cc * 5)
            
            time.sleep(2)
            invariants = verify_security_invariants()
            print("\nSECURITY INVARIANTS:")
            failed = False
            for k, v in invariants.items():
                print(f"  {k}: {v}")
                if v > 0:
                    failed = True
            
            if failed:
                print(f"[FAIL] SECURITY REGRESSION GATE FAILED AT {w} WORKERS, {cc} CC!")
                return
            else:
                print(f"[OK] SECURITY GATES PASSED")

    print("\nScaling Benchmark Complete.")
    await scale_workers(1, MAX_CC, NTHREAD)

if __name__ == "__main__":
    asyncio.run(main())
