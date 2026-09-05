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
rate_limiter = None

async def init_app_state():
    global redis_client, kafka_producer, global_model, policy_engine, execution_adapter, idempotency_engine

    if settings.ENVIRONMENT == "production":
        if not settings.API_KEY:
            raise RuntimeError("API_KEY must be set in production environment.")
        if len(settings.API_KEY) < 32:
            raise RuntimeError("API_KEY must be at least 32 characters in production.")
        if settings.ENABLE_DEMO_ENDPOINTS:
            raise RuntimeError(
                "ENABLE_DEMO_ENDPOINTS must be False in production. "
                "Demo endpoints can inject arbitrary intents into the evaluation pipeline."
            )

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
    from execution.adapters.razorpay_direct import RazorpayDirectProvider

    execution_mode = settings.EXECUTION_MODE.lower()
    razorpay_provider_type = settings.RAZORPAY_PROVIDER.lower()
    razorpay_env = settings.RAZORPAY_ENVIRONMENT

    if execution_mode == "razorpay":
        # Production Razorpay integration
        if razorpay_provider_type == "direct":
            logger.info(f"Using RazorpayDirectProvider ({razorpay_env} mode)")
            provider = RazorpayDirectProvider(environment=razorpay_env)
        elif razorpay_provider_type == "mcp":
            logger.info(f"Using RazorpayMCPAdapter ({razorpay_env} mode)")
            provider = RazorpayMCPAdapter(environment=razorpay_env)
        else:
            logger.warning(f"Unknown RAZORPAY_PROVIDER: {razorpay_provider_type}, defaulting to MCP")
            provider = RazorpayMCPAdapter(environment=razorpay_env)
    elif execution_mode == "dry_run":
        logger.info("Using dry_run mode (MCP with no mutations)")
        provider = RazorpayMCPAdapter(environment="dry_run")
    else:
        logger.info("Using MockPaymentAdapter")
        provider = MockPaymentAdapter()

    execution_adapter = ExecutionGateway(policy_engine.token_manager, provider, replay_store=redis_client)
    
    idempotency_engine = IdempotencyEngine(
        redis_client=redis_client,
        idempotency_ttl_seconds=IDEMPOTENCY_TTL,
        behavioral_window_seconds=BEHAVIORAL_WINDOW
    )

    from security.rate_limiter import RedisRateLimiter
    global rate_limiter
    rate_limiter = RedisRateLimiter(redis_client=redis_client, max_requests=100, window_seconds=60)

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

def get_rate_limiter():
    if not rate_limiter:
        raise SentinelSecurityException("Rate limiter unavailable. Failing closed.")
    return rate_limiter
