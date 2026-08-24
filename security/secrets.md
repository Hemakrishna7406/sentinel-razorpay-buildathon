# Secrets Management

Sentinel adheres to strict secret isolation to prevent lateral movement or credential exposure in the event of a frontend or agent compromise.

## Secret Isolation Principle

No cryptographic material or Razorpay API keys are ever transmitted to, or accessible by, the React frontend or the autonomous agent.

### Environment-Based Secrets
Sentinel relies exclusively on environment variables for sensitive configuration:
- `RAZORPAY_KEY_ID`: Razorpay Test Mode Key ID.
- `RAZORPAY_KEY_SECRET`: Razorpay Test Mode Key Secret.
- `CAPABILITY_SIGNING_KEY`: A >=32 byte secret used to HMAC-SHA256 sign capability tokens.
- `REDIS_URL`: Connection string for the Redis state store.

## Startup Validation
Sentinel's `TokenManager` enforces a fail-closed startup validation check:
- If `CAPABILITY_SIGNING_KEY` is missing or empty, the application refuses to start.
- If the key is too weak (< 32 characters), the application refuses to start.
- If a known development key is used in a production environment, the application refuses to start.

## Frontend Leak Prevention
A mandatory CI test (`test_frontend_secrets.py`) statically analyzes the frontend bundle to ensure no backend keys were accidentally injected via build pipelines.
