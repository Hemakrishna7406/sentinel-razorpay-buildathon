"""
Sentinel Load Testing Suite
Using Locust for production-grade load testing

Run with:
    locust -f tests/load/locustfile.py --host http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 60s --headless
"""

import uuid
import random
import time
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser

# Metrics tracking
request_latencies = []
decision_counts = {"ALLOW": 0, "ESCALATE": 0, "CONTAIN": 0}


class SentinelUser(FastHttpUser):
    """
    Simulates an AI agent making authorization requests to Sentinel.
    """

    wait_time = between(0.1, 0.5)  # Simulate agent think time

    def on_start(self):
        """Called when a simulated user starts"""
        self.agent_id = f"agent-{random.randint(1, 20):03d}"
        self.session_id = uuid.uuid4().hex[:8]

    @task(10)
    def evaluate_normal_intent(self):
        """
        Normal transaction - should ALLOW
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{uuid.uuid4().hex}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_order",
            "amount": random.randint(10000, 100000),  # ₹100 to ₹1000
            "currency": "INR",
            "recipient": f"customer-{random.randint(1, 1000):04d}@example.com",
            "context": {
                "session_id": self.session_id,
                "timestamp": int(time.time()),
            }
        }

        with self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                decision = data.get("decision")
                latency_ms = data.get("latency_ms", 0)

                # Track metrics
                request_latencies.append(latency_ms)
                if decision in decision_counts:
                    decision_counts[decision] += 1

                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(3)
    def evaluate_high_amount(self):
        """
        High-value transaction - might ESCALATE
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{uuid.uuid4().hex}"

        payload = {
            "intent_id": intent_id,
            "agent_id": self.agent_id,
            "action_type": "create_payout",
            "amount": random.randint(500000, 2000000),  # ₹5000 to ₹20,000
            "currency": "INR",
            "recipient": f"vendor-{random.randint(1, 100):03d}",
            "context": {}
        }

        with self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            catch_response=True
        ) as response:
            if response.status_code in [200, 403]:
                if response.status_code == 200:
                    data = response.json()
                    decision = data.get("decision")
                    if decision in decision_counts:
                        decision_counts[decision] += 1
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")

    @task(1)
    def evaluate_burst_pattern(self):
        """
        Rapid-fire requests (velocity spike) - should CONTAIN
        """
        for i in range(5):
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

            self.client.post(
                "/evaluate",
                json=payload,
                headers={
                    "Idempotency-Key": idempotency_key,
                    "X-Sentinel-Mode": "govern"
                },
                name="/evaluate (burst)"
            )

            time.sleep(0.05)  # 50ms between burst requests

    @task(2)
    def idempotent_retry(self):
        """
        Test idempotency - same intent retried
        """
        intent_id = f"INT-{uuid.uuid4().hex[:12]}"
        idempotency_key = f"idem-{self.session_id}-retry"

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
        response1 = self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            name="/evaluate (idempotent-first)"
        )

        # Retry same request
        time.sleep(0.1)
        response2 = self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            name="/evaluate (idempotent-retry)"
        )

        # Both should succeed (second should return cached result)
        if response1.status_code == 200 and response2.status_code == 200:
            pass  # Success
        else:
            print(f"Idempotency test failed: {response1.status_code}, {response2.status_code}")

    @task(1)
    def health_check(self):
        """
        Check system health
        """
        self.client.get("/health/live", name="/health/live")

    @task(1)
    def get_audit_log(self):
        """
        Fetch audit log
        """
        self.client.get("/audit?limit=10", name="/audit")


class StressTestUser(FastHttpUser):
    """
    Aggressive stress testing - pushes system limits
    """

    wait_time = between(0.01, 0.1)  # Minimal wait time

    def on_start(self):
        self.agent_id = f"stress-{random.randint(1, 10):02d}"

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

        self.client.post(
            "/evaluate",
            json=payload,
            headers={
                "Idempotency-Key": idempotency_key,
                "X-Sentinel-Mode": "govern"
            },
            name="/evaluate (stress)"
        )


# Event handlers for custom metrics
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """
    Called when the load test stops - print summary
    """
    print("\n" + "="*60)
    print("SENTINEL LOAD TEST SUMMARY")
    print("="*60)

    if request_latencies:
        sorted_latencies = sorted(request_latencies)
        p50 = sorted_latencies[len(sorted_latencies) // 2]
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
        p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
        avg = sum(sorted_latencies) / len(sorted_latencies)

        print(f"\nLatency Metrics:")
        print(f"  Average: {avg:.2f}ms")
        print(f"  p50:     {p50:.2f}ms")
        print(f"  p95:     {p95:.2f}ms")
        print(f"  p99:     {p99:.2f}ms")

    print(f"\nDecision Distribution:")
    total_decisions = sum(decision_counts.values())
    if total_decisions > 0:
        for decision, count in decision_counts.items():
            percentage = (count / total_decisions) * 100
            print(f"  {decision}: {count} ({percentage:.1f}%)")

    print("\n" + "="*60)
    print(f"Total Requests Tracked: {len(request_latencies)}")
    print("="*60 + "\n")
