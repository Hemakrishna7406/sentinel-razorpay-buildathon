"""
Sentinel — DR Metrics Benchmark (Gate C)
Measures actual values for RTO and Graceful Drain Latency using Docker containers.
"""

import asyncio
import time
import subprocess
import json
import uuid
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def measure_rto():
    print("--- Measuring Worker Recovery RTO ---")
    rto_measurements = []
    
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from core.config import settings
    
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BROKER)
    await producer.start()
    
    consumer = AIOKafkaConsumer(
        settings.KAFKA_EVALUATED_TOPIC,
        bootstrap_servers=settings.KAFKA_BROKER,
        group_id=f"benchmark-rto-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="latest"
    )
    await consumer.start()
    
    # Ensure worker is stopped first
    subprocess.run(["docker", "stop", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)
    
    for i in range(5):
        intent_id = f"rto-bench-{uuid.uuid4().hex[:8]}"
        payload = {
            "intent": {
                "intent_id": intent_id,
                "action_type": "transfer",
                "amount": 1000,
                "currency": "USD",
                "recipient": "user_1"
            },
            "agent_id": "rto-agent",
            "context": {}
        }
        
        # Publish test message
        await producer.send_and_wait(settings.KAFKA_INBOUND_TOPIC, json.dumps(payload).encode('utf-8'))
        
        t0 = time.perf_counter()
        
        # Start worker container
        subprocess.run(["docker", "start", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)
        
        # Wait for the evaluated message
        try:
            async for msg in consumer:
                event = json.loads(msg.value.decode('utf-8'))
                if event.get("intent_id") == intent_id:
                    t5 = time.perf_counter()
                    break
        except Exception:
            pass
            
        rto = t5 - t0
        rto_measurements.append(rto)
        print(f"Run {i+1}: {rto:.2f}s")
        
        # Stop worker for next run
        subprocess.run(["docker", "stop", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)
        
    await producer.stop()
    await consumer.stop()
    
    rto_measurements.sort()
    print(f"RTO p50: {rto_measurements[2]:.2f}s")
    print(f"RTO max: {rto_measurements[-1]:.2f}s")


async def measure_drain():
    print("\n--- Measuring Graceful Drain Latency ---")
    drain_measurements = []
    
    from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
    from core.config import settings
    
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BROKER)
    await producer.start()

    for i in range(3):
        # Ensure worker is running
        subprocess.run(["docker", "start", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)
        await asyncio.sleep(2) # Let it warm up
        
        intent_id = f"drain-bench-{uuid.uuid4().hex[:8]}"
        payload = {
            "intent": {
                "intent_id": intent_id,
                "action_type": "transfer",
                "amount": 1000,
                "currency": "USD",
                "recipient": "user_1"
            },
            "agent_id": "drain-agent",
            "context": {}
        }
        
        # We publish the message and immediately issue a docker stop
        await producer.send_and_wait(settings.KAFKA_INBOUND_TOPIC, json.dumps(payload).encode('utf-8'))
        
        t0 = time.perf_counter()
        
        # docker stop sends SIGTERM, waits gracefully up to 30s
        subprocess.run(["docker", "stop", "--time", "30", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)
        
        t1 = time.perf_counter()
        
        drain_measurements.append(t1 - t0)
        print(f"Run {i+1} Drain Time: {t1 - t0:.3f}s")
        
    await producer.stop()
    
    drain_measurements.sort()
    print(f"Drain max: {drain_measurements[-1]:.3f}s")
    
    # Restart the worker at the end for normal operation
    subprocess.run(["docker", "start", "sentinel-razorpay-buildathon-sentinel-worker-1"], capture_output=True)


if __name__ == "__main__":
    asyncio.run(measure_rto())
    asyncio.run(measure_drain())
