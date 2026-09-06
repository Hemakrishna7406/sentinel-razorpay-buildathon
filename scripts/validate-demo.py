#!/usr/bin/env python3
"""
Sentinel Demo Validation Script

Validates all 5 demo scenarios execute correctly by hitting the backend API.
This ensures the demo will work flawlessly during the judge presentation.

Demo Scenarios:
1. Normal Agent - Legitimate transfer (ALLOW)
2. Suspicious Agent - Anomalous behavior (ESCALATE)
3. Malicious Agent - Clear attack (CONTAIN)
4. Replay Attack - Duplicate JTI (REJECT)
5. Redis Failure - Graceful degradation (FAIL_CLOSED)
"""

import asyncio
import sys
from typing import Dict, Any

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Run: pip install httpx")
    sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10.0

# Expected outcomes for each scenario
EXPECTED_OUTCOMES = {
    "normal": {"decision": "ALLOW", "risk_score_max": 0.15},
    "suspicious": {"decision": "ESCALATE", "risk_score_min": 0.65},
    "malicious": {"decision": "CONTAIN", "risk_score_min": 0.85},
    "replay": {"decision": "ALLOW"},  # First request, second would be BLOCKED
    "redis_failure": {"decision": "ESCALATE"},  # Fail-closed behavior
}


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


async def check_backend_health(client: httpx.AsyncClient) -> bool:
    """Check if backend is running and healthy"""
    try:
        response = await client.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print(f"{Colors.GREEN}✅ Backend is healthy{Colors.NC}")
            return True
        else:
            print(f"{Colors.RED}❌ Backend returned status {response.status_code}{Colors.NC}")
            return False
    except httpx.ConnectError:
        print(f"{Colors.RED}❌ Cannot connect to backend at {BASE_URL}{Colors.NC}")
        print(f"{Colors.YELLOW}   Make sure the backend is running (uvicorn api.main:app){Colors.NC}")
        return False
    except Exception as e:
        print(f"{Colors.RED}❌ Health check failed: {e}{Colors.NC}")
        return False


async def test_scenario(client: httpx.AsyncClient, scenario_name: str, expected: Dict[str, Any]) -> bool:
    """
    Test a single demo scenario

    Args:
        client: HTTP client
        scenario_name: Name of the scenario to test
        expected: Expected outcome (decision, risk_score, etc.)

    Returns:
        True if scenario passes, False otherwise
    """
    try:
        print(f"\n{Colors.BLUE}Testing: {scenario_name}{Colors.NC}")

        # Call the demo scenario endpoint
        response = await client.post(f"{BASE_URL}/demo/scenarios/{scenario_name}", timeout=TIMEOUT)

        if response.status_code != 200:
            print(f"  {Colors.RED}❌ API returned status {response.status_code}{Colors.NC}")
            print(f"     Response: {response.text}")
            return False

        data = response.json()

        # Validate decision
        if "decision" in expected:
            actual_decision = data.get("decision", "UNKNOWN")
            if actual_decision == expected["decision"]:
                print(f"  {Colors.GREEN}✅ Decision: {actual_decision}{Colors.NC}")
            else:
                print(f"  {Colors.RED}❌ Expected decision {expected['decision']}, got {actual_decision}{Colors.NC}")
                return False

        # Validate risk score (if applicable)
        risk_score = data.get("risk_score")
        if risk_score is not None:
            print(f"  {Colors.GREEN}✅ Risk Score: {risk_score:.3f}{Colors.NC}")

            if "risk_score_max" in expected and risk_score > expected["risk_score_max"]:
                print(f"  {Colors.RED}❌ Risk score too high: {risk_score} > {expected['risk_score_max']}{Colors.NC}")
                return False

            if "risk_score_min" in expected and risk_score < expected["risk_score_min"]:
                print(f"  {Colors.RED}❌ Risk score too low: {risk_score} < {expected['risk_score_min']}{Colors.NC}")
                return False

        # Validate response time
        response_time = data.get("latency_ms", 0)
        if response_time > 0:
            print(f"  {Colors.GREEN}✅ Latency: {response_time}ms{Colors.NC}")

            if response_time > 1000:
                print(f"  {Colors.YELLOW}⚠️  Warning: Latency over 1 second{Colors.NC}")

        print(f"{Colors.GREEN}✅ {scenario_name} scenario passed{Colors.NC}")
        return True

    except httpx.TimeoutException:
        print(f"  {Colors.RED}❌ Request timed out after {TIMEOUT}s{Colors.NC}")
        return False
    except Exception as e:
        print(f"  {Colors.RED}❌ Error: {e}{Colors.NC}")
        return False


async def main():
    """Main validation flow"""
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║          SENTINEL DEMO VALIDATION                          ║")
    print("╠════════════════════════════════════════════════════════════╣")
    print("║  Validating all demo scenarios for judge presentation     ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    async with httpx.AsyncClient() as client:
        # Check backend health first
        if not await check_backend_health(client):
            print(f"\n{Colors.RED}❌ Demo validation failed - backend not available{Colors.NC}\n")
            sys.exit(1)

        # Test each scenario
        results = []
        for scenario_name, expected in EXPECTED_OUTCOMES.items():
            result = await test_scenario(client, scenario_name, expected)
            results.append((scenario_name, result))
            await asyncio.sleep(0.5)  # Brief pause between tests

    # Print summary
    print("\n╔════════════════════════════════════════════════════════════╗")
    print("║                    VALIDATION SUMMARY                      ║")
    print("╠════════════════════════════════════════════════════════════╣")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for scenario_name, result in results:
        status = f"{Colors.GREEN}PASS ✅{Colors.NC}" if result else f"{Colors.RED}FAIL ❌{Colors.NC}"
        print(f"║  {scenario_name:<25} {status}              ║")

    print("║                                                            ║")

    if passed == total:
        print(f"║  {Colors.GREEN}Status: 🚀 DEMO READY 🚀{Colors.NC}                              ║")
        print("║                                                            ║")
        print(f"║  {Colors.GREEN}All {total} scenarios validated. Ready for judges!{Colors.NC}        ║")
        exit_code = 0
    else:
        print(f"║  {Colors.RED}Status: ⚠️  VALIDATION FAILED ⚠️{Colors.NC}                       ║")
        print("║                                                            ║")
        print(f"║  {Colors.RED}{passed}/{total} scenarios passed. Fix failures before demo.{Colors.NC}    ║")
        exit_code = 1

    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Validation interrupted{Colors.NC}\n")
        sys.exit(1)
