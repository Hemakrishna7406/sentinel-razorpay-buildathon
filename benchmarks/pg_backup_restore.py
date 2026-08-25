"""
Sentinel — Phase 22.7 Gate D: PostgreSQL Backup / Restore Verification

Performs a real backup/restore cycle entirely inside the Docker container:
1. pg_dump to /tmp/sentinel_backup.sql
2. DELETE all rows from audit_ledger
3. Restore via psql
4. Run verify_audit_chain.py via docker exec (inside the container's python env)
5. Verify count and chain integrity
"""

import subprocess
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONTAINER = "sentinel-razorpay-buildathon-postgres-1"
DB_NAME = "sentinel_db"
DB_USER = "sentinel"
BACKUP_PATH = "/tmp/sentinel_backup.sql"


def docker_psql(cmd, capture=False):
    full = ["docker", "exec", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-c", cmd]
    result = subprocess.run(full, capture_output=capture, text=True)
    return result


def run(cmd, check=True, capture=False):
    result = subprocess.run(cmd, capture_output=capture, text=True)
    if check and result.returncode != 0:
        out = result.stdout + result.stderr
        print(f"WARNING/ERROR running: {' '.join(cmd)}\n{out}")
    return result


def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def count_records():
    result = docker_psql("SELECT COUNT(*) FROM audit_ledger;", capture=True)
    for line in result.stdout.strip().splitlines():
        line = line.strip()
        if line.isdigit():
            return int(line)
    return -1


if __name__ == "__main__":
    t0 = time.perf_counter()

    step("1. Creating pg_dump backup inside container")
    run(["docker", "exec", CONTAINER, "pg_dump", "-U", DB_USER, "-d", DB_NAME, "-f", BACKUP_PATH])
    result = subprocess.run(["docker", "exec", CONTAINER, "wc", "-c", BACKUP_PATH], capture_output=True, text=True)
    print(f"Backup created: {BACKUP_PATH}")
    print(f"Backup size: {result.stdout.strip()}")

    step("2. Counting records before destroy")
    before_count = count_records()
    print(f"Records in audit_ledger: {before_count}")
    assert before_count > 0, "Expected at least some records in audit_ledger"

    step("3. Destroying audit_ledger data (simulating disk loss)")
    docker_psql("DELETE FROM audit_ledger;")
    after_destroy = count_records()
    print(f"Records after DELETE: {after_destroy}")
    assert after_destroy == 0, "Table was not empty after DELETE"

    step("4. Restoring from backup")
    run(["docker", "exec", CONTAINER, "psql", "-U", DB_USER, "-d", DB_NAME, "-f", BACKUP_PATH])
    after_restore = count_records()
    print(f"Records after restore: {after_restore}")
    assert after_restore == before_count, f"Record count mismatch: expected {before_count}, got {after_restore}"

    step("5. Verifying audit chain integrity (cryptographic hash chain)")
    # Run the Python verifier in a context that can reach the DB inside the container
    verify_result = subprocess.run(
        ["docker", "exec", CONTAINER, "sh", "-c",
         f"psql -U {DB_USER} -d {DB_NAME} -t -c "
         f"'SELECT record_hash, previous_hash FROM audit_ledger ORDER BY id' | head -5"],
        capture_output=True, text=True
    )
    print("Sample hashes from restored records:")
    print(verify_result.stdout)

    # Use our local verifier which talks to the DB via the exposed port
    # The pg container password is sentinelpassword per the env vars
    env_with_pg = os.environ.copy()
    env_with_pg["DATABASE_URL"] = "postgresql://sentinel:sentinelpassword@localhost:5432/sentinel_db"
    
    verify_local = subprocess.run(
        ["uv", "run", "python", "verify_audit_chain.py"],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env_with_pg
    )
    print(verify_local.stdout)
    if verify_local.returncode == 0:
        print("Audit chain integrity: VERIFIED [OK]")
    else:
        print("Audit chain verification FAILED:")
        print(verify_local.stderr)
        sys.exit(1)

    step("6. Summary")
    elapsed = time.perf_counter() - t0
    print(f"Records preserved:      {after_restore}/{before_count}")
    print(f"Audit chain integrity:  VERIFIED [OK]")
    print(f"RPO (lost records):     0")
    print(f"Total drill duration:   {elapsed:.2f}s")
