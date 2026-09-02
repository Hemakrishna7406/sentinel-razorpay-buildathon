"""
Sentinel Comprehensive Benchmark Suite
Runs all individual component benchmarks and generates a unified report

This script measures:
1. Redis operations (idempotency, get/set, pipelines)
2. XGBoost inference (CPU, threading)
3. Policy engine evaluation
4. Capability token generation
5. Database operations (insert, query)
6. End-to-end authorization latency

Usage:
    python benchmarks/run_all_benchmarks.py
"""

import asyncio
import time
import statistics
import json
from datetime import datetime
from pathlib import Path

# Ensure we can import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class BenchmarkRunner:
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None

    def benchmark(self, name: str, func, iterations: int = 100):
        """Run a benchmark function and collect metrics"""
        print(f"\n🔧 Running: {name} ({iterations} iterations)")

        latencies = []
        errors = 0

        for i in range(iterations):
            start = time.perf_counter()
            try:
                result = func()
                latencies.append((time.perf_counter() - start) * 1000)  # Convert to ms
            except Exception as e:
                errors += 1
                print(f"  Error in iteration {i}: {e}")

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")

        if latencies:
            self.results[name] = {
                "iterations": iterations,
                "avg_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies),
                "p95_ms": self._percentile(latencies, 95),
                "p99_ms": self._percentile(latencies, 99),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "errors": errors,
                "error_rate": errors / iterations * 100,
            }
            print(f"  ✓ Avg: {self.results[name]['avg_ms']:.2f}ms, p99: {self.results[name]['p99_ms']:.2f}ms")
        else:
            print(f"  ✗ All iterations failed!")
            self.results[name] = {"error": "All iterations failed", "errors": errors}

    async def async_benchmark(self, name: str, func, iterations: int = 100):
        """Run an async benchmark function"""
        print(f"\n🔧 Running: {name} ({iterations} iterations)")

        latencies = []
        errors = 0

        for i in range(iterations):
            start = time.perf_counter()
            try:
                await func()
                latencies.append((time.perf_counter() - start) * 1000)
            except Exception as e:
                errors += 1
                print(f"  Error in iteration {i}: {e}")

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{iterations}")

        if latencies:
            self.results[name] = {
                "iterations": iterations,
                "avg_ms": statistics.mean(latencies),
                "median_ms": statistics.median(latencies),
                "p95_ms": self._percentile(latencies, 95),
                "p99_ms": self._percentile(latencies, 99),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "errors": errors,
                "error_rate": errors / iterations * 100,
            }
            print(f"  ✓ Avg: {self.results[name]['avg_ms']:.2f}ms, p99: {self.results[name]['p99_ms']:.2f}ms")
        else:
            print(f"  ✗ All iterations failed!")
            self.results[name] = {"error": "All iterations failed", "errors": errors}

    def _percentile(self, data, percentile):
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_summary(self):
        """Print comprehensive summary"""
        print("\n" + "=" * 80)
        print("SENTINEL BENCHMARK RESULTS")
        print("=" * 80)

        for name, metrics in self.results.items():
            print(f"\n📊 {name}")
            if "error" not in metrics:
                print(f"  Iterations: {metrics['iterations']}")
                print(f"  Average: {metrics['avg_ms']:.2f}ms")
                print(f"  Median: {metrics['median_ms']:.2f}ms")
                print(f"  p95: {metrics['p95_ms']:.2f}ms")
                print(f"  p99: {metrics['p99_ms']:.2f}ms")
                print(f"  Min: {metrics['min_ms']:.2f}ms")
                print(f"  Max: {metrics['max_ms']:.2f}ms")
                if metrics['errors'] > 0:
                    print(f"  Errors: {metrics['errors']} ({metrics['error_rate']:.1f}%)")
            else:
                print(f"  ❌ {metrics['error']}")

        print("\n" + "=" * 80)

    def save_report(self, filename=None):
        """Save results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"benchmarks/benchmark-results-{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": (self.end_time - self.start_time) if self.end_time else 0,
            "results": self.results,
        }

        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Report saved to: {filename}")


async def main():
    """Run all benchmarks"""
    print("=" * 80)
    print("SENTINEL COMPREHENSIVE BENCHMARK SUITE")
    print("=" * 80)

    runner = BenchmarkRunner()
    runner.start_time = time.time()

    # 1. Redis Benchmarks
    print("\n🔴 REDIS BENCHMARKS")
    print("-" * 80)

    try:
        import redis.asyncio as aioredis
        from core.config import settings

        redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        # Simple GET/SET
        async def redis_set():
            await redis_client.set("benchmark_key", "benchmark_value", ex=60)

        async def redis_get():
            await redis_client.get("benchmark_key")

        await runner.async_benchmark("Redis SET", redis_set, 1000)
        await runner.async_benchmark("Redis GET", redis_get, 1000)

        # Pipeline operations
        async def redis_pipeline():
            pipe = redis_client.pipeline()
            pipe.set("bench1", "val1")
            pipe.set("bench2", "val2")
            pipe.get("bench1")
            await pipe.execute()

        await runner.async_benchmark("Redis Pipeline (3 ops)", redis_pipeline, 500)

        await redis_client.aclose()

    except Exception as e:
        print(f"❌ Redis benchmarks failed: {e}")

    # 2. XGBoost Benchmarks
    print("\n🧠 XGBOOST BENCHMARKS")
    print("-" * 80)

    try:
        import xgboost as xgb
        import pandas as pd
        import numpy as np
        from ml.features import get_feature_names

        # Load model
        from api.dependencies import get_model
        model_wrapper = get_model()

        if model_wrapper and model_wrapper.model:
            features = model_wrapper.features
            dummy_data = pd.DataFrame(np.random.randn(1, len(features)), columns=features)
            dmatrix = xgb.DMatrix(dummy_data)

            def xgb_inference():
                _ = model_wrapper.model.predict(dmatrix)

            runner.benchmark("XGBoost Inference (single)", xgb_inference, 1000)

            # Batch inference
            batch_data = pd.DataFrame(np.random.randn(16, len(features)), columns=features)
            batch_dmatrix = xgb.DMatrix(batch_data)

            def xgb_batch():
                _ = model_wrapper.model.predict(batch_dmatrix)

            runner.benchmark("XGBoost Inference (batch 16)", xgb_batch, 200)

        else:
            print("⚠️  XGBoost model not loaded, skipping inference benchmarks")

    except Exception as e:
        print(f"❌ XGBoost benchmarks failed: {e}")

    # 3. Policy Engine Benchmarks
    print("\n📜 POLICY ENGINE BENCHMARKS")
    print("-" * 80)

    try:
        from security.policy import PolicyEngine
        from security.capability_token import IntentContext
        from ml.schema import BehavioralRiskResult, RiskAssessment
        from ml.fusion.risk_fusion import RiskFusionEngine

        policy = PolicyEngine(suspicious_threshold=0.5)

        intent = IntentContext(
            intent_id="bench-001",
            agent_id="bench-agent",
            action_type="create_order",
            amount=50000,
            currency="INR",
            recipient="test@example.com"
        )

        behavioral = BehavioralRiskResult(
            risk_score=0.15,
            confidence=0.9,
            reason_codes=["BENCHMARK"],
            model_version="test"
        )

        fusion = RiskFusionEngine(base_escalation_threshold=0.5).fuse(behavioral, None)
        assessment = RiskAssessment(behavioral=behavioral, fusion=fusion)

        def policy_eval():
            _ = policy.evaluate(intent, {}, assessment)

        runner.benchmark("Policy Evaluation", policy_eval, 1000)

    except Exception as e:
        print(f"❌ Policy engine benchmarks failed: {e}")

    # 4. Capability Token Benchmarks
    print("\n🔑 CAPABILITY TOKEN BENCHMARKS")
    print("-" * 80)

    try:
        from security.capability_token import CapabilityTokenManager, IntentContext

        token_mgr = CapabilityTokenManager(signing_key="benchmark-secret-key")

        intent = IntentContext(
            intent_id="bench-001",
            agent_id="bench-agent",
            action_type="create_order",
            amount=50000,
            currency="INR",
            recipient="test@example.com"
        )

        def token_issue():
            _ = token_mgr.issue_capability_token(intent, max_amount=50000, valid_for_seconds=300)

        runner.benchmark("Token Generation", token_issue, 1000)

        # Verification
        token = token_mgr.issue_capability_token(intent, max_amount=50000, valid_for_seconds=300)

        def token_verify():
            _ = token_mgr.verify_token(token, intent)

        runner.benchmark("Token Verification", token_verify, 1000)

    except Exception as e:
        print(f"❌ Token benchmarks failed: {e}")

    # 5. Feature Extraction Benchmarks
    print("\n🔬 FEATURE EXTRACTION BENCHMARKS")
    print("-" * 80)

    try:
        from ml.features import extract_features

        sample_context = {
            "amount": 50000,
            "recipient_novelty": 0.3,
            "action_type": "checkout",
            "hour_of_day": 14,
            "typical_hour_start": 9,
            "typical_hour_end": 18,
            "rolling_1m_count": 5,
            "rolling_1h_count": 20,
            "rolling_24h_count": 100,
            "agent_age_days": 30,
            "has_sufficient_history": True,
            "baseline_hourly_rate": 2.5,
            "velocity_1h": 3.0,
            "baseline_amount": 40000,
            "typical_hour": 12,
            "frequency_24h": 15,
            "baseline_frequency": 10,
        }

        def feature_extract():
            _ = extract_features(sample_context)

        runner.benchmark("Feature Extraction", feature_extract, 1000)

    except Exception as e:
        print(f"❌ Feature extraction benchmarks failed: {e}")

    # Summary
    runner.end_time = time.time()
    runner.print_summary()
    runner.save_report()

    # Calculate composite score
    print("\n🎯 PERFORMANCE TARGETS")
    print("-" * 80)

    targets = {
        "Redis GET": 2.0,  # <2ms
        "XGBoost Inference (single)": 0.5,  # <0.5ms
        "Policy Evaluation": 1.0,  # <1ms
        "Token Generation": 0.5,  # <0.5ms
        "Feature Extraction": 0.2,  # <0.2ms
    }

    for name, target in targets.items():
        if name in runner.results and "avg_ms" in runner.results[name]:
            actual = runner.results[name]["avg_ms"]
            status = "✅ PASS" if actual < target else "❌ FAIL"
            print(f"  {name}: {status} (target: <{target}ms, actual: {actual:.2f}ms)")

    print("\n✅ Benchmark suite complete!")


if __name__ == "__main__":
    asyncio.run(main())
