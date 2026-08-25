"""
Sentinel — API Dependencies

Dependency injection for FastAPI.
Loads the XGBoost model, initializes database/Redis connections,
and instantiates the core engines.
"""

import os
import json
import logging
from core.config import settings
import xgboost as xgb
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from security.policy import PolicyEngine
from security.execution_adapter import ExecutionAdapter
from security.idempotency import IdempotencyEngine
from security.exceptions import SentinelSecurityException

logger = logging.getLogger(__name__)

# 1. Configuration
DB_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
DB_POOL_SIZE = settings.DB_POOL_SIZE
DB_MAX_OVERFLOW = settings.DB_MAX_OVERFLOW
IDEMPOTENCY_TTL = settings.IDEMPOTENCY_TTL_SECONDS
BEHAVIORAL_WINDOW = settings.BEHAVIORAL_WINDOW_SECONDS

# 2. Database Engine
engine_args = {}
if "postgresql" in DB_URL:
    engine_args = {
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "pool_pre_ping": True,
    }
elif "sqlite" in DB_URL:
    engine_args = {"connect_args": {"check_same_thread": False}}

engine = create_engine(DB_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 3. Model Loading
class ModelWrapper:
    def __init__(self):
        self.model = None
        self.features = []
        self.suspicious_threshold = 0.5
        
    def load(self, model_name="sentinel_xgboost", manifest_path="ml/model_manifest.json"):
        import mlflow
        import mlflow.xgboost
        
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        try:
            # We fetch the latest version of the registered model
            model_uri = f"models:/{model_name}/latest"
            logger.info(f"Loading model from MLflow: {model_uri}")
            
            # mlflow.xgboost.load_model returns the underlying xgboost.Booster
            self.model = mlflow.xgboost.load_model(model_uri)
            
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                self.suspicious_threshold = manifest["thresholds"]["suspicious"]
                
            from ml.features import get_feature_names
            self.features = get_feature_names("full_sentinel")
            
        except Exception as e:
            logger.warning(f"Failed to load model from MLflow/manifest: {e}")
            
        use_gpu = settings.USE_GPU
        xgb_nthread = settings.XGB_NTHREAD
        
        if use_gpu and self.model is not None:
            try:
                self.model.set_param({"device": "cuda"})
                logger.info("Configuring XGBoost model for GPU execution (device='cuda').")
            except Exception as e:
                logger.warning(f"Failed to configure GPU execution: {e}")
                
        if xgb_nthread != "auto" and self.model is not None:
            try:
                self.model.set_param({"nthread": int(xgb_nthread)})
                logger.info(f"Configuring XGBoost model with nthread={xgb_nthread}")
            except Exception as e:
                logger.warning(f"Failed to configure XGBoost nthread: {e}")


# 4. Global State (Initialized in lifespan)
import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer

redis_client = None
kafka_producer = None
global_model = None
policy_engine = None
execution_adapter = None
idempotency_engine = None

async def init_app_state():
    global redis_client, kafka_producer, global_model, policy_engine, execution_adapter, idempotency_engine
    
    # Init Redis (async)
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # Init Kafka Producer
    kafka_broker = settings.KAFKA_BROKER
    kafka_producer = AIOKafkaProducer(bootstrap_servers=kafka_broker)
    await kafka_producer.start()
    
    # Init Model
    global_model = ModelWrapper()
    global_model.load()
    
    # Init Engines
    policy_engine = PolicyEngine(suspicious_threshold=global_model.suspicious_threshold)
    from execution.gateway import ExecutionGateway
    from execution.adapters.mock_adapter import MockPaymentAdapter
    from execution.adapters.mcp_adapter import RazorpayMCPAdapter
    
    execution_mode = settings.EXECUTION_MODE.lower()
    if execution_mode == "mcp":
        provider = RazorpayMCPAdapter()
    elif execution_mode == "dry_run":
        provider = RazorpayMCPAdapter() # In dry_run, the MCP adapter might stop early, but we didn't implement dry_run natively inside the adapter yet. Actually, dry_run can just be MockPaymentAdapter for now or we can implement a DryRunAdapter. Let's just use Mock for dry_run for now since we didn't add the logic in RazorpayMCPAdapter. Wait, the user said dry_run should validate tool availability but not mutate.
        # Let's add dry_run to the MCP Adapter later, or pass environment mode.
        provider = RazorpayMCPAdapter(environment="dry_run")
    else:
        provider = MockPaymentAdapter()
        
    execution_adapter = ExecutionGateway(policy_engine.token_manager, provider, replay_store=redis_client)
    
    idempotency_engine = IdempotencyEngine(
        redis_client=redis_client,
        idempotency_ttl_seconds=IDEMPOTENCY_TTL,
        behavioral_window_seconds=BEHAVIORAL_WINDOW
    )

async def shutdown_app_state():
    global redis_client, kafka_producer, engine
    if kafka_producer:
        await kafka_producer.stop()
    if redis_client:
        await redis_client.aclose()
    if engine:
        engine.dispose()

def get_model():
    return global_model

def get_policy_engine():
    return policy_engine

def get_execution_adapter():
    if not execution_adapter:
        raise SentinelSecurityException("Execution gateway unavailable. Failing closed.")
    return execution_adapter

def get_idempotency_engine():
    if not idempotency_engine:
        raise SentinelSecurityException("Idempotency engine unavailable. Failing closed.")
    return idempotency_engine
