import asyncio
import os
import subprocess
import time
from sqlalchemy import create_engine, text
from benchmarks.load_test import load_test

DB_URL = os.environ.get("DATABASE_URL", "postgresql://sentinel:sentinelpassword@localhost:5432/sentinel_db")
engine = create_engine(DB_URL)

BATCH_SIZES = [1, 16, 32, 64]
TIMEOUTS_MS = [0, 2, 5, 10, 20]

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

async def configure_gpu_worker(batch_size: int, timeout: int):
    print(f"\n[Config] Restarting sentinel-worker with GPU batch={batch_size}, timeout={timeout}ms...")
    env = os.environ.copy()
    env["INFERENCE_BACKEND"] = "gpu"
    env["USE_GPU"] = "true"
    env["GPU_BATCH_SIZE"] = str(batch_size)
    env["GPU_BATCH_TIMEOUT_MS"] = str(timeout)
    # Give the worker a high MAX_CONCURRENT_TASKS so it can actually fill the batch queue
    env["MAX_CONCURRENT_TASKS"] = "100" 
    
    subprocess.run(
        ["docker", "compose", "up", "-d", "--scale", "sentinel-worker=1", "--force-recreate", "sentinel-worker"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(8)

async def main():
    print("Starting GPU Batching Evaluation (RTX 4060)...")
    load_cc = 250
    reqs = 1000
    
    for b in BATCH_SIZES:
        for t in TIMEOUTS_MS:
            # Skip if batch size is 1 but timeout > 0 (timeout doesn't matter for batch=1)
            if b == 1 and t > 0:
                continue
                
            await configure_gpu_worker(b, t)
            print(f"\n--- Testing GPU Batch={b}, Timeout={t}ms @ {load_cc} CC ---")
            
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM audit_ledger"))
                conn.commit()
            
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

    print("\nGPU Batching Benchmark Complete.")
    
    # Restore to CPU Baseline
    env = os.environ.copy()
    env["INFERENCE_BACKEND"] = "cpu"
    env["MAX_CONCURRENT_TASKS"] = "5"
    subprocess.run(
        ["docker", "compose", "up", "-d", "--scale", "sentinel-worker=1", "--force-recreate", "sentinel-worker"],
        env=env,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

if __name__ == "__main__":
    asyncio.run(main())
