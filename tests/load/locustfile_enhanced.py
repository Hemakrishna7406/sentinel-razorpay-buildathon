"""
Sentinel Enhanced Load Testing Suite
Using Locust for production-grade performance validation

PERFORMANCE TARGETS:
- Baseline (50 users): <30ms p99 latency, 200+ RPS
- Stress (200 users): <50ms p99 latency, 400+ RPS
- Spike (500 users): <100ms p99 latency, error rate <5%

Run with:
    # Baseline test
    locust -f tests/load/locustfile_enhanced.py --host http://localhost:8000 \
           --users 50 --spawn-rate 5 --run-time 300s --headless

    # Stress test
    locust -f tests/load/locustfile_enhanced.py --host http://localhost:8000 \
           --users 200 --spawn-rate 10 --run-time 600s --headless

    # Spike test
    locust -f tests/load/locustfile_enhanced.py --host http://localhost:8000 \
           --users 500 --spawn-rate 50 --run-time 300s --headless
"""

import uuid
import random
import time
import statistics
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser

# Enhanced metrics tracking
class PerformanceMetrics:
    def __init__(self):
        self.latencies = []
        self.decision_counts = {"ALLOW": 0, "ESCALATE": 0, "CONTAIN": 0}
        self.status_codes = {}
        self.timings_breakdown = {
            "api_idem_ms": [],
            "api_kafka_ms": [],
            "api_wait_ms": [],
            "worker_xgb_ms": [],
            "total_ms": []
        }
        self.errors = []
        self.start_time = None
        self.end_time = None

    def record_request(self, latency_ms, status_code, decision=None, timings=None):
        """Record a complete request with all metrics"""
        self.latencies.append(latency_ms)

        if status_code not in self.status_codes:
            self.status_codes[status_code] = 0
        self.status_codes[status_code] += 1

        if decision and decision in self.decision_counts:
            self.decision_counts[decision] += 1

        if timings:
            for key in self.timings_breakdown.keys():
                if key in timings:
                    self.timings_breakdown[key].append(timings[key])

    def record_error(self, error_msg):
        """Record an error"""
        self.errors.append(error_msg)

    def calculate_percentile(self, data, percentile):
        """Calculate percentile from sorted data"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def print_summary(self):
        """Print comprehensive performance summary"""
        print("\n" + "="*80)
        print("SENTINEL ENHANCED LOAD TEST REPORT")
        print("="*80)

        if not self.latencies:
            print("No requests recorded!")
            return

        # Overall metrics
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"  Total Requests: {len(self.latencies)}")
        print(f"  Test Duration: {(self.end_time - self.start_time):.2f}s")
        print(f"  Throughput: {len(self.latencies) / (self.end_time - self.start_time):.2f} RPS")

        # Latency percentiles
        print(f"\n⚡ LATENCY DISTRIBUTION")
        print(f"  Average: {statistics.mean(self.latencies):.2f}ms")
        print(f"  Median (p50): {self.calculate_percentile(self.latencies, 50):.2f}ms")
        print(f"  p95: {self.calculate_percentile(self.latencies, 95):.2f}ms")
        print(f"  p99: {self.calculate_percentile(self.latencies, 99):.2f}ms")
        print(f"  Max: {max(self.latencies):.2f}ms")
        print(f"  Min: {min(self.latencies):.2f}ms")

        # Target validation
        p99 = self.calculate_percentile(self.latencies, 99)
        rps = len(self.latencies) / (self.end_time - self.start_time)
        print(f"\n🎯 TARGET VALIDATION")
        print(f"  p99 < 30ms: {'✅ PASS' if p99 < 30 else '❌ FAIL'} (actual: {p99:.2f}ms)")
        print(f"  RPS > 200: {'✅ PASS' if rps > 200 else '❌ FAIL'} (actual: {rps:.2f})")

        # Timing breakdown
        if any(self.timings_breakdown.values()):
            print(f"\n⏱️  TIMING BREAKDOWN (averages)")
            for key, values in self.timings_breakdown.items():
                if values:
                    print(f"  {key}: {statistics.mean(values):.2f}ms")

        # Decision distribution
        total_decisions = sum(self.decision_counts.values())
        if total_decisions > 0:
            print(f"\n🔒 DECISION DISTRIBUTION")
            for decision, count in self.decision_counts.items():
                percentage = (count / total_decisions) * 100
                print(f"  {decision}: {count} ({percentage:.1f}%)")

        # Status codes
        print(f"\n📡 HTTP STATUS CODES")
        for code, count in sorted(self.status_codes.items()):
            percentage = (count / len(self.latencies)) * 100
            print(f"  {code}: {count} ({percentage:.1f}%)")

        # Error rate
        error_rate = (len(self.errors) / len(self.latencies)) * 100
        print(f"\n❌ ERROR RATE: {error_rate:.2f}% ({len(self.errors)}/{len(self.latencies)})")

        print("\n" + "="*80 + "\n")


# Global metrics instance
metrics = PerformanceMetrics()


class SentinelLoadUser(FastHttpUser):
    """
    Realistic load testing user simulating production traffic patterns
    """

    wait_time = between(0.1, 0.5)

    def on_start(self):
        """Called when a simulated user starts"""
        self.agent_id = f"agent-{random.randint(1, 50):03d}"
        self.session_id = uuid.uuid4().hex[:8]
        if not metrics.start_time:
            metrics.start_time = time.time()

    @task(70)
    def evaluate_normal_intent(self):
        """
        Normal transaction - should ALLOW (70% of traffic)
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{uuid.uuid4().hex}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_order",
            "amount": random.randint(10000, 100000),
            "currency": "INR",
            "recipient": f"customer-{random.randint(1, 1000):04d}@example.com",
            "context": {
                "session_id": self.session_id,
                "timestamp": int(time.time()),
            }
        }

        start = time.perf_counter()
        with self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            catch_response=True
        ) as response:
            latency_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                metrics.record_request(
                    latency_ms=latency_ms,
                    status_code=200,
                    decision=data.get("decision"),
                    timings=data.get("timings")
                )
                response.success()
            else:
                metrics.record_request(latency_ms, response.status_code)
                metrics.record_error(f"Status {response.status_code}")
                response.failure(f"Failed with status {response.status_code}")

    @task(20)
    def evaluate_high_amount(self):
        """
        High-value transaction - might ESCALATE (20% of traffic)
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{uuid.uuid4().hex}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_payout",
            "amount": random.randint(500000, 2000000),
            "currency": "INR",
            "recipient": f"vendor-{random.randint(1, 100):03d}",
            "context": {}
        }

        start = time.perf_counter()
        with self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            catch_response=True
        ) as response:
            latency_ms = (time.perf_counter() - start) * 1000

            if response.status_code in [200, 403]:
                if response.status_code == 200:
                    data = response.json()
                    metrics.record_request(
                        latency_ms=latency_ms,
                        status_code=200,
                        decision=data.get("decision"),
                        timings=data.get("timings")
                    )
                response.success()
            else:
                metrics.record_request(latency_ms, response.status_code)
                metrics.record_error(f"Status {response.status_code}")
                response.failure(f"Failed with status {response.status_code}")

    @task(5)
    def evaluate_burst_pattern(self):
        """
        Rapid-fire requests (velocity spike) - should CONTAIN (5% of traffic)
        """
        for i in range(3):
            intent_id = f"INT-{uuid.uuid4().hex[:12]}"
            idempotency_key = f"idem-{uuid.uuid4().hex}"

            payload = {
                "intent_id": intent_id,
                "agent_id": self.agent_id,
                "action_type": "create_order",
                "amount": 50000,
                "currency": "INR",
                "recipient": f"burst-{i}@example.com",
                "context": {}
            }

            start = time.perf_counter()
            response = self.client.post(
                "/evaluate",
                json=payload,
                headers={
                    "Idempotency-Key": idempotency_key,
                    "X-Sentinel-Mode": "govern"
                },
                name="/evaluate (burst)"
            )
            latency_ms = (time.perf_counter() - start) * 1000

            if response.status_code in [200, 403]:
                metrics.record_request(latency_ms, response.status_code)
            else:
                metrics.record_request(latency_ms, response.status_code)
                metrics.record_error(f"Burst failed: {response.status_code}")

            time.sleep(0.02)

    @task(3)
    def idempotent_retry(self):
        """
        Test idempotency - same intent retried (3% of traffic)
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{self.session_id}-{random.randint(1,100)}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_order",
            "amount": 75000,
            "currency": "INR",
            "recipient": "retry-test@example.com",
            "context": {}
        }

        # First request
        start = time.perf_counter()
        response1 = self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            name="/evaluate (idempotent)"
        )
        latency_ms = (time.perf_counter() - start) * 1000

        if response1.status_code == 200:
            metrics.record_request(latency_ms, 200)
        else:
            metrics.record_request(latency_ms, response1.status_code)

    @task(2)
    def health_check(self):
        """
        Health check endpoint (2% of traffic)
        """
        start = time.perf_counter()
        self.client.get("/health/live", name="/health/live")


class StressTestUser(FastHttpUser):
    """
    High-intensity stress testing for peak load simulation
    """

    wait_time = between(0.01, 0.05)

    def on_start(self):
        self.agent_id = f"stress-{random.randint(1, 20):02d}"

    @task
    def rapid_fire(self):
        """
        Maximum throughput test
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{uuid.uuid4().hex}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_order",
            "amount": 10000,
            "currency": "INR",
            "recipient": "stress@example.com",
            "context": {}
        }

        start = time.perf_counter()
        response = self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            name="/evaluate (stress)"
        )
        latency_ms = (time.perf_counter() - start) * 1000
        metrics.record_request(latency_ms, response.status_code)


# Event handlers
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize metrics when test starts"""
    print("\n🚀 Starting Sentinel Enhanced Load Test")
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    metrics.start_time = time.time()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print comprehensive metrics when test completes"""
    metrics.end_time = time.time()
    metrics.print_summary()

    # Save metrics to file
    try:
        import json
        from datetime import datetime

        report_file = f"benchmarks/load-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": metrics.end_time - metrics.start_time,
            "total_requests": len(metrics.latencies),
            "throughput_rps": len(metrics.latencies) / (metrics.end_time - metrics.start_time),
            "latency_p50": metrics.calculate_percentile(metrics.latencies, 50),
            "latency_p95": metrics.calculate_percentile(metrics.latencies, 95),
            "latency_p99": metrics.calculate_percentile(metrics.latencies, 99),
            "latency_avg": statistics.mean(metrics.latencies) if metrics.latencies else 0,
            "decision_counts": metrics.decision_counts,
            "status_codes": metrics.status_codes,
            "error_count": len(metrics.errors),
            "error_rate_pct": (len(metrics.errors) / len(metrics.latencies) * 100) if metrics.latencies else 0,
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📝 Report saved to: {report_file}")
    except Exception as e:
        print(f"Failed to save report: {e}")
