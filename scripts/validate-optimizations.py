#!/usr/bin/env python3
"""
Sentinel Performance Optimization Validator
Verifies all optimization files are in place and ready for testing
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"  # No Color


def print_header(text):
    print(f"\n{YELLOW}{'='*80}{NC}")
    print(f"{YELLOW}{text}{NC}")
    print(f"{YELLOW}{'='*80}{NC}\n")


def check_file(filepath, description):
    """Check if a file exists and print status"""
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        print(f"{GREEN}✓{NC} {description}")
        print(f"  Path: {filepath}")
        print(f"  Size: {size:,} bytes")
        return True
    else:
        print(f"{RED}✗{NC} {description}")
        print(f"  Path: {filepath} (NOT FOUND)")
        return False


def main():
    print_header("SENTINEL PERFORMANCE OPTIMIZATION VALIDATOR")

    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    all_ok = True

    # Check code optimizations
    print(f"\n{YELLOW}📁 CODE OPTIMIZATIONS{NC}")
    print("-" * 80)

    files = {
        "api/dependencies_optimized.py": "Optimized API Dependencies (Redis pooling, Kafka tuning)",
        "security/idempotency_optimized.py": "Optimized Idempotency Engine (Redis pipelining)",
    }

    for filepath, desc in files.items():
        if not check_file(filepath, desc):
            all_ok = False

    # Check database optimizations
    print(f"\n{YELLOW}🗄️  DATABASE OPTIMIZATIONS{NC}")
    print("-" * 80)

    files = {
        "alembic/versions/performance_indexes.sql": "Database Performance Indexes (6 strategic indexes)",
    }

    for filepath, desc in files.items():
        if not check_file(filepath, desc):
            all_ok = False

    # Check load testing
    print(f"\n{YELLOW}🔬 LOAD TESTING{NC}")
    print("-" * 80)

    files = {
        "tests/load/locustfile_enhanced.py": "Enhanced Locust Load Tests (comprehensive metrics)",
        "benchmarks/run_all_benchmarks.py": "Component Benchmark Suite (Redis, XGBoost, etc.)",
    }

    for filepath, desc in files.items():
        if not check_file(filepath, desc):
            all_ok = False

    # Check automation scripts
    print(f"\n{YELLOW}⚙️  AUTOMATION SCRIPTS{NC}")
    print("-" * 80)

    files = {
        "scripts/run-performance-tests.sh": "Linux/Mac Performance Test Runner",
        "scripts/run-performance-tests.bat": "Windows Performance Test Runner",
    }

    for filepath, desc in files.items():
        if not check_file(filepath, desc):
            all_ok = False

    # Check documentation
    print(f"\n{YELLOW}📚 DOCUMENTATION{NC}")
    print("-" * 80)

    files = {
        "benchmarks/PERFORMANCE-OPTIMIZATION-REPORT.md": "Detailed Technical Report (500+ lines)",
        "PERFORMANCE-README.md": "Performance Testing Guide (400+ lines)",
        "TASK-BACKEND-PERFORMANCE-COMPLETE.md": "Task Completion Summary",
    }

    for filepath, desc in files.items():
        if not check_file(filepath, desc):
            all_ok = False

    # Prerequisites check
    print(f"\n{YELLOW}🔧 PREREQUISITES CHECK{NC}")
    print("-" * 80)

    try:
        import locust

        print(f"{GREEN}✓{NC} Locust installed (version {locust.__version__})")
    except ImportError:
        print(f"{RED}✗{NC} Locust not installed (run: pip install locust)")
        all_ok = False

    try:
        import redis

        print(f"{GREEN}✓{NC} Redis client installed")
    except ImportError:
        print(f"{YELLOW}⚠{NC} Redis client not installed (optional for benchmarks)")

    try:
        import xgboost

        print(f"{GREEN}✓{NC} XGBoost installed (version {xgboost.__version__})")
    except ImportError:
        print(f"{YELLOW}⚠{NC} XGBoost not installed (required for benchmarks)")

    # Docker check
    import subprocess

    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"{GREEN}✓{NC} Docker available ({version})")
        else:
            print(f"{RED}✗{NC} Docker not available")
            all_ok = False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{RED}✗{NC} Docker not available")
        all_ok = False

    # Summary
    print_header("VALIDATION SUMMARY")

    if all_ok:
        print(f"{GREEN}✅ ALL CHECKS PASSED{NC}")
        print("\nAll optimization files are in place and prerequisites are met.")
        print("\nNext steps:")
        print("  1. Start Docker services: docker-compose up -d postgres redis redpanda")
        print(
            "  2. Apply database indexes: docker exec -i sentinel-postgres psql -U sentinel -d sentinel < alembic/versions/performance_indexes.sql"
        )
        print("  3. Run performance tests: scripts/run-performance-tests.sh (or .bat on Windows)")
        print("\nOr use the automated script:")
        print("  chmod +x scripts/run-performance-tests.sh && ./scripts/run-performance-tests.sh")
        return 0
    else:
        print(f"{RED}❌ SOME CHECKS FAILED{NC}")
        print("\nSome required files or prerequisites are missing.")
        print("Please review the output above and ensure all files are created.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
