import pytest
import asyncio
import os

os.environ.setdefault("CAPABILITY_SIGNING_KEY", "test-secret-key-must-be-at-least-32-bytes-long")
os.environ["MLFLOW_TRACKING_URI"] = "file:///tmp/mlruns"
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"

class MockRedis:
    def __init__(self):
        self.store = {}
        self.lock = asyncio.Lock()
    async def get(self, key):
        return self.store.get(key)
    async def set(self, key, value, ex=None, nx=False):
        async with self.lock:
            if nx and key in self.store:
                return None
            self.store[key] = value
            return True
    async def xread(self, *args, **kwargs):
        import json
        return [[b"stream", [[b"msg_id", {b"data": json.dumps({
            "intent_id": "test",
            "decision": "ALLOW",
            "capability_token": "mock_token",
            "latency_ms": 10
        }).encode("utf-8")}]]]]
    async def aclose(self):
        pass

class MockKafkaProducer:
    def __init__(self, *args, **kwargs):
        pass
    async def start(self):
        pass
    async def stop(self):
        pass
    async def send_and_wait(self, *args, **kwargs):
        pass

@pytest.fixture(autouse=True, scope="session")
def patch_infrastructure():
    import redis.asyncio as aioredis
    from aiokafka import AIOKafkaProducer
    
    # Mock redis and kafka to prevent tests from failing when infrastructure is not running
    aioredis.from_url = lambda *args, **kwargs: MockRedis()
    
    # We have to patch the class itself or the import in dependencies
    import api.dependencies
    api.dependencies.AIOKafkaProducer = MockKafkaProducer
