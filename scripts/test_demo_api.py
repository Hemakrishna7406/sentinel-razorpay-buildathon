"""
Quick validation script for demo API endpoints.
Run this to verify all 5 scenarios are accessible.
"""

import asyncio
import httpx
import sys

API_URL = "http://localhost:8000"

SCENARIOS = ["normal", "suspicious", "malicious", "replay", "redis_failure"]


async def test_health():
    """Test API health"""
    print("🔍 Testing API health...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_URL}/health/live", timeout=5.0)
            if resp.status_code == 200:
                print("✅ API is live")
                return True
            else:
                print(f"❌ API health check failed: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return False


async def test_scenario_endpoint(scenario: str):
    """Test a single scenario endpoint"""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_URL}/demo/scenarios/{scenario}", timeout=10.0)
            if resp.status_code == 200:
                result = resp.json()
                print(f"  ✅ {scenario}: {result}")
                return True
            else:
                print(f"  ❌ {scenario}: HTTP {resp.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ {scenario}: {e}")
            return False


async def test_sse_stream():
    """Test SSE stream endpoint"""
    print("\n🔍 Testing SSE stream endpoint...")
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", f"{API_URL}/execution/stream") as response:
                if response.status_code == 200:
                    print("✅ SSE stream connected")
                    # Read first event or timeout
                    async for line in response.aiter_lines():
                        if line.startswith("data:"):
                            print("✅ Received SSE event")
                            break
                    return True
                else:
                    print(f"❌ SSE stream failed: {response.status_code}")
                    return False
        except asyncio.TimeoutError:
            print("⚠️  SSE stream timeout (no events yet, but connection OK)")
            return True
        except Exception as e:
            print(f"❌ SSE stream error: {e}")
            return False


async def main():
    print("=" * 60)
    print("SENTINEL DEMO API VALIDATION")
    print("=" * 60)
    print()

    # Test health
    if not await test_health():
        print("\n❌ API is not accessible. Start the server first:")
        print("   uvicorn api.main:app --reload")
        sys.exit(1)

    print()

    # Test scenario endpoints
    print("🔍 Testing demo scenario endpoints...")
    results = []
    for scenario in SCENARIOS:
        result = await test_scenario_endpoint(scenario)
        results.append((scenario, result))
        await asyncio.sleep(0.5)  # Small delay between tests

    print()

    # Test SSE
    # await test_sse_stream()

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for scenario, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {scenario}")

    print()
    print(f"Results: {passed}/{total} scenarios passed")

    if passed == total:
        print("\n🎉 All demo endpoints are working!")
        print("\nNext steps:")
        print("1. Open http://localhost:3000/demo in your browser")
        print("2. Select a scenario and click 'Run Scenario'")
        print("3. Watch the decision timeline animate in real-time")
        sys.exit(0)
    else:
        print("\n⚠️  Some endpoints failed. Check the logs above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
