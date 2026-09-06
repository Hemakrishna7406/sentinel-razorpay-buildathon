import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environment
    ENVIRONMENT: str = Field("development", description="Current environment (development, production)")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    JSON_LOGS: bool = Field(True, description="Whether to output JSON structured logs")

    # Kafka
    KAFKA_BROKER: str = Field("localhost:29092", description="Kafka broker address")
    KAFKA_INBOUND_TOPIC: str = Field("intents.inbound", description="Topic for incoming intents")
    KAFKA_EVALUATED_TOPIC: str = Field("intents.evaluated", description="Topic for evaluated intents")

    # Security & Authentication
    API_KEY: str = Field("", description="API key for agent endpoints. Required in production.")
    ADMIN_API_KEY: str = Field("", description="Admin API key for policy management. Required in production.")
    ENABLE_DEMO_ENDPOINTS: bool = Field(
        False, description="Enable demo scenario injection. MUST be False in production."
    )

    # Database
    DATABASE_URL: str = Field("sqlite:///./sentinel.db", description="SQLAlchemy DB URL")
    DB_POOL_SIZE: int = Field(20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(10, description="Database connection max overflow")

    # Redis
    REDIS_URL: str = Field("redis://localhost:6379/0", description="Redis connection URL")

    # Auth & Execution
    CAPABILITY_SIGNING_KEY: str = Field(
        "sentinel-local-dev-secret-do-not-use-in-prod", description="Key for signing capability tokens"
    )
    EXECUTION_MODE: str = Field("mock", description="Execution adapter mode (mock, razorpay)")
    RAZORPAY_PROVIDER: str = Field("mcp", description="Razorpay provider type (mcp, direct)")
    RAZORPAY_KEY_ID: Optional[str] = Field(None, description="Razorpay Key ID")
    RAZORPAY_KEY_SECRET: Optional[str] = Field(None, description="Razorpay Key Secret")
    RAZORPAY_ENVIRONMENT: str = Field("test", description="Razorpay environment (test, live)")

    # Worker & ML configuration
    INFERENCE_BACKEND: str = Field("cpu", description="ML Inference backend (cpu, gpu)")
    USE_GPU: bool = Field(False, description="Flag for using GPU")
    MAX_CONCURRENT_TASKS: int = Field(2, description="Max concurrent tasks per worker")
    XGB_NTHREAD: str = Field("4", description="Threads for XGBoost inference ('auto' or integer)")
    GPU_BATCH_SIZE: int = Field(16, description="Batch size if GPU is used")
    GPU_BATCH_TIMEOUT_MS: int = Field(5, description="Timeout for GPU batching in ms")

    # MLflow
    MLFLOW_TRACKING_URI: str = Field("http://localhost:5000", description="MLFlow tracking URI")

    # Observability
    METRICS_PORT: int = Field(8001, description="Port for prometheus metrics scrape on worker")
    AUDIT_METRICS_PORT: int = Field(8002, description="Port for prometheus metrics scrape on audit consumer")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field("", description="OpenTelemetry exporter endpoint")
    OTEL_SERVICE_NAME: str = Field("sentinel", description="OTel service name")

    # CORS (comma-separated origins allowed to call the API directly, e.g. Vite dev server)
    CORS_ORIGINS: str = Field(
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
        description="Comma-separated list of allowed browser origins",
    )

    # Security Tuning
    IDEMPOTENCY_TTL_SECONDS: int = Field(86400, description="Idempotency TTL")
    BEHAVIORAL_WINDOW_SECONDS: int = Field(5, description="Behavioral tracking window")


settings = Settings()
