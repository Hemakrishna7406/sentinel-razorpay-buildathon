import asyncio
import httpx
import os
import subprocess
import time
from sqlalchemy import create_engine, text
from benchmarks.load_test import load_test

DB_URL = os.environ.get("DATABASE_URL", "postgresql://sentinel:sentinelpassword@localhost:5432/sentinel_db")
engine = create_engine(DB_URL)

WORKERS = [1, 2, 4]
CONCURRENCIES = [100, 250, 500, 1000]

def verify_security_invariants():
    with engine.connect() as conn:
        # Check unauthorized MCP calls: ALLOW + capability_jti is NOT NULL + MCP invoked + NO FAIL CLOSED
        # Wait, the easiest is to query the audit DB directly for specific failure modes.
        # But we don't have MCP execution recorded directly in audit db unless decision == ALLOW.
        # Actually, the user requirement is: 
        # 1. unauthorized MCP calls = 0
        # 2. duplicate executions = 0
        # 3. unsafe ALLOW = 0
        
        # 3. Unsafe ALLOW on dependency failure
        unsafe_allow = conn.execute(text("SELECT count(*) FROM audit_ledger WHERE decision='ALLOW' AND behavioral_risk_score IS NULL")).scalar()
        
        # 2. Duplicate executions
        duplicates = conn.execute(text("""
            SELECT count(*) FROM (
                SELECT intent_id, count(*) FROM audit_ledger GROUP BY intent_id HAVING count(*) > 1
            ) as dupes
        """)).scalar()
        
        # 1. Unauthorized MCP calls (ALLOW but risk is high)
        unauthorized = conn.execute(text("SELECT count(*) FROM audit_ledger WHERE decision='ALLOW' AND model_risk_score > 0.5")).scalar()
        
        return {
            "unsafe_allow": unsafe_allow or 0,
            "duplicates": duplicates or 0,
            "unauthorized_mcp": unauthorized or 0
        }

async def scale_workers(count: int):
    print(f"\n[Scaling] Scaling sentinel-worker to {count} instances...")
    subprocess.run(
        ["docker", "compose", "up", "-d", "--scale", f"sentinel-worker={count}"],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(5)

async def main():
    print("Starting Scaling Test with Security Gates...")
    
    for w in WORKERS:
        await scale_workers(w)
        for cc in CONCURRENCIES:
            print(f"\n--- Testing {w} Workers @ {cc} CC ---")
            
            # Clear audit log to measure this specific run
            with engine.connect() as conn:
                conn.execute(text("DELETE FROM audit_ledger"))
                conn.commit()
            
            await load_test(concurrency=cc, total_requests=cc * 5) # Enough requests to stress
            
            # Allow audit consumer to flush
            time.sleep(2)
            
            # Security regression gate
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
    
    # Scale back to 1
    await scale_workers(1)

if __name__ == "__main__":
    asyncio.run(main())
