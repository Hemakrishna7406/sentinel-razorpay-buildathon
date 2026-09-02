# Sentinel RC1 - Security Remediation Guide

**Quick Fix Guide for HIGH Priority Findings**

This document provides step-by-step remediation instructions with code samples for the 2 HIGH severity findings that block production deployment.

---

## H-1: Implement Rate Limiting

**Severity:** HIGH  
**Estimated Fix Time:** 1 day (including testing)  
**Status:** REQUIRED BEFORE PRODUCTION  

### Step 1: Install Dependencies

Add to `requirements.txt`:

```txt
slowapi>=0.1.9
```

Install:

```bash
pip install slowapi
```

### Step 2: Update `api/main.py`

Add imports at the top:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

Update the `lifespan` function:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=settings.REDIS_URL,
        default_limits=["1000/hour"],  # Global default
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Existing startup
    await init_app_state()
    yield
    await shutdown_app_state()
```

Update the `app` initialization to reference limiter:

```python
app = FastAPI(title="Sentinel Risk Engine", version="1.0.0", lifespan=lifespan)

# Get limiter from app state
def get_limiter():
    return app.state.limiter

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)
```

### Step 3: Apply Rate Limits to Endpoints

Update the `/evaluate` endpoint:

```python
@app.post("/evaluate", response_model=EvaluationResponse)
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def evaluate_intent_sync(
    request: Request,
    intent: IntentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    mode: str = Header("govern", alias="X-Sentinel-Mode")
):
    # Existing implementation
    ...
```

Update other high-value endpoints:

```python
@app.post("/evaluate/async", status_code=202)
@limiter.limit("100/minute")
async def evaluate_intent_async(...):
    ...

@app.post("/execute", response_model=ExecuteResponse)
@limiter.limit("50/minute")  # More restrictive for execution
async def execute_intent(...):
    ...

@app.post("/policy/rules", response_model=PolicyRuleResponse)
@limiter.limit("10/minute")  # Very restrictive for policy changes
def add_policy_rule(...):
    ...
```

### Step 4: Add Configuration

Update `core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(True, description="Enable rate limiting")
    RATE_LIMIT_PER_MINUTE: int = Field(100, description="Max requests per minute per IP")
    RATE_LIMIT_PER_HOUR: int = Field(1000, description="Max requests per hour per IP")
```

### Step 5: Custom Rate Limit Error Handler (Optional)

Add custom error response:

```python
@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error response."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    
    return JSONResponse(
        status_code=429,
        headers={
            "Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"
        },
        content={
            "decision": "ESCALATE",
            "reason": "Rate limit exceeded. Too many requests from your IP address.",
            "retry_after_seconds": exc.retry_after if hasattr(exc, 'retry_after') else 60,
            "error_code": "RATE_LIMIT_EXCEEDED"
        }
    )
```

### Step 6: Testing

Create test file `tests/test_rate_limiting.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
import api.main

@pytest.mark.asyncio
async def test_rate_limit_enforced():
    """Test that rate limiting blocks excessive requests."""
    async with AsyncClient(
        transport=ASGITransport(app=api.main.app),
        base_url="http://test"
    ) as client:
        # Make requests until rate limited
        responses = []
        for i in range(110):  # Exceed 100/minute limit
            resp = await client.post(
                "/evaluate",
                json={
                    "intent_id": f"rate-test-{i}",
                    "agent_id": "test-agent",
                    "action_type": "payout",
                    "amount": 1000,
                    "currency": "INR",
                    "recipient": "test"
                },
                headers={"Idempotency-Key": f"key-{i}"}
            )
            responses.append(resp)
        
        # At least one should be rate limited
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0, "Expected some requests to be rate limited"
```

Run tests:

```bash
pytest tests/test_rate_limiting.py -v
```

### Step 7: Monitoring

Add Prometheus metrics (optional):

```python
from prometheus_client import Counter

RATE_LIMIT_EXCEEDED = Counter(
    'sentinel_rate_limit_exceeded_total',
    'Total rate limit rejections',
    ['endpoint']
)

# In rate limit handler:
RATE_LIMIT_EXCEEDED.labels(endpoint=request.url.path).inc()
```

### Step 8: Documentation

Update deployment docs with rate limiting configuration:

```yaml
# Production configuration
RATE_LIMIT_ENABLED: true
RATE_LIMIT_PER_MINUTE: 100
RATE_LIMIT_PER_HOUR: 1000

# For high-traffic deployments
RATE_LIMIT_PER_MINUTE: 500
RATE_LIMIT_PER_HOUR: 5000
```

### Validation Checklist

- [ ] slowapi installed and imported
- [ ] Rate limiter initialized with Redis storage
- [ ] Rate limits applied to all evaluation endpoints
- [ ] Custom error handler returns helpful message
- [ ] Retry-After header included in 429 responses
- [ ] Tests pass with rate limiting enabled
- [ ] Metrics capture rate limit events
- [ ] Documentation updated

---

## H-2: Add Security Headers

**Severity:** HIGH  
**Estimated Fix Time:** 2 hours  
**Status:** REQUIRED BEFORE PRODUCTION  

### Step 1: Create Security Headers Middleware

Add to `api/main.py` (before app initialization):

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all HTTP responses.
    
    Implements OWASP recommended security headers:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Restrict browser features
    - Strict-Transport-Security: Enforce HTTPS (when applicable)
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Prevent clickjacking - deny embedding in frames
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Content Security Policy
        # Adjust based on your frontend requirements
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # Allow inline scripts for React
            "style-src 'self' 'unsafe-inline'",   # Allow inline styles
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",  # Redundant with X-Frame-Options but good defense-in-depth
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Referrer policy - strict but allows cross-origin with origin only
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy - disable dangerous features
        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)
        
        # Strict-Transport-Security - only on HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # X-XSS-Protection - deprecated but harmless
        # Modern browsers use CSP instead
        response.headers["X-XSS-Protection"] = "0"
        
        return response
```

### Step 2: Register Middleware

Add middleware to app (after CORS, before routes):

```python
app = FastAPI(title="Sentinel Risk Engine", version="1.0.0", lifespan=lifespan)

# CORS middleware (existing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Idempotency-Key", "X-Sentinel-Mode"],
)

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)
```

### Step 3: Adjust CSP for Frontend

If your frontend needs specific CSP rules, create configuration:

Update `core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Security Headers
    CSP_SCRIPT_SRC: str = Field(
        "'self' 'unsafe-inline'",
        description="Content-Security-Policy script-src directive"
    )
    CSP_STYLE_SRC: str = Field(
        "'self' 'unsafe-inline'",
        description="Content-Security-Policy style-src directive"
    )
    HSTS_MAX_AGE: int = Field(
        31536000,
        description="Strict-Transport-Security max-age in seconds (1 year)"
    )
```

Update middleware to use settings:

```python
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # ... other headers ...
        
        # Dynamic CSP from settings
        csp_directives = [
            "default-src 'self'",
            f"script-src {settings.CSP_SCRIPT_SRC}",
            f"style-src {settings.CSP_STYLE_SRC}",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # ... rest of headers ...
```

### Step 4: Testing

Create test file `tests/test_security_headers.py`:

```python
import pytest
from fastapi.testclient import TestClient
import api.main

client = TestClient(api.main.app)

def test_x_frame_options_header():
    """Test clickjacking protection."""
    response = client.get("/")
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"

def test_x_content_type_options_header():
    """Test MIME-sniffing protection."""
    response = client.get("/health/live")
    assert "X-Content-Type-Options" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"

def test_content_security_policy_header():
    """Test CSP header present."""
    response = client.get("/")
    assert "Content-Security-Policy" in response.headers
    csp = response.headers["Content-Security-Policy"]
    assert "default-src" in csp
    assert "frame-ancestors 'none'" in csp

def test_referrer_policy_header():
    """Test referrer policy."""
    response = client.get("/audit")
    assert "Referrer-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"

def test_permissions_policy_header():
    """Test dangerous features disabled."""
    response = client.get("/")
    assert "Permissions-Policy" in response.headers
    policy = response.headers["Permissions-Policy"]
    assert "camera=()" in policy
    assert "microphone=()" in policy
    assert "geolocation=()" in policy

def test_security_headers_on_api_endpoints():
    """Test headers on JSON API responses."""
    response = client.get("/health/dependencies")
    assert response.headers.get("Content-Type") == "application/json"
    # Security headers should be present on API responses too
    assert "X-Content-Type-Options" in response.headers
    assert "X-Frame-Options" in response.headers
    assert "Content-Security-Policy" in response.headers

def test_hsts_header_on_https():
    """Test HSTS on HTTPS (may not be testable in local environment)."""
    # This test validates the logic; actual HTTPS testing requires proper setup
    response = client.get("/")
    # If test runs on HTTP, HSTS should be absent
    # If test runs on HTTPS, HSTS should be present
    # This is a placeholder - implement based on your test environment
    pass
```

Run tests:

```bash
pytest tests/test_security_headers.py -v
```

### Step 5: Validate with Security Scanners

Use online tools to validate headers:

```bash
# After deploying to staging
curl -I https://your-staging-url.com

# Check with securityheaders.com
# Visit: https://securityheaders.com/?q=your-staging-url.com
```

### Step 6: CSP Reporting (Optional)

Add CSP violation reporting:

```python
# In SecurityHeadersMiddleware
csp_directives.append("report-uri /api/csp-violations")

# Add endpoint to receive reports
@app.post("/api/csp-violations")
async def csp_violation_report(request: Request):
    """Receive CSP violation reports from browsers."""
    body = await request.json()
    logger.warning("CSP Violation", extra={
        "csp_report": body,
        "user_agent": request.headers.get("User-Agent")
    })
    return {"status": "received"}
```

### Validation Checklist

- [ ] SecurityHeadersMiddleware class created
- [ ] Middleware registered in app
- [ ] All required headers implemented:
  - [ ] X-Frame-Options
  - [ ] X-Content-Type-Options
  - [ ] Content-Security-Policy
  - [ ] Referrer-Policy
  - [ ] Permissions-Policy
  - [ ] HSTS (on HTTPS)
- [ ] CSP directives adjusted for frontend
- [ ] Tests pass
- [ ] Headers validated with online scanner
- [ ] Dashboard loads correctly (no CSP violations)

---

## Verification

After implementing both fixes, run:

```bash
# 1. Run security validation script
python scripts/security_check.py --environment production

# 2. Run security tests
pytest tests/test_security_headers.py tests/test_rate_limiting.py -v

# 3. Run full test suite (ensure nothing broke)
pytest tests/ -v

# 4. Manual verification
curl -I http://localhost:8000/
# Should see: X-Frame-Options, X-Content-Type-Options, CSP, etc.

# 5. Test rate limiting
for i in {1..110}; do curl -X POST http://localhost:8000/evaluate -H "Content-Type: application/json" -d '{"intent_id":"test-'$i'","agent_id":"test","action_type":"payout","amount":1000,"currency":"INR","recipient":"test"}' -H "Idempotency-Key: key-'$i'"; done
# Should see some 429 responses
```

---

## Timeline

| Task | Time | Priority |
|------|------|----------|
| H-1: Install slowapi | 10 min | HIGH |
| H-1: Implement rate limiter | 2 hours | HIGH |
| H-1: Write tests | 2 hours | HIGH |
| H-1: Testing & validation | 2 hours | HIGH |
| **H-1 Total** | **6-8 hours** | **HIGH** |
| | | |
| H-2: Create middleware | 30 min | HIGH |
| H-2: Configure CSP | 1 hour | HIGH |
| H-2: Write tests | 1 hour | HIGH |
| H-2: Validation | 30 min | HIGH |
| **H-2 Total** | **3 hours** | **HIGH** |
| | | |
| **TOTAL** | **9-11 hours** | **1-2 days** |

---

## Rollback Plan

If issues arise after deployment:

### Disable Rate Limiting

```python
# In core/config.py
RATE_LIMIT_ENABLED: bool = Field(False, description="Temporarily disable")

# In api/main.py
if settings.RATE_LIMIT_ENABLED:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### Relax Security Headers

```python
# Temporarily relax CSP if frontend breaks
csp_directives = [
    "default-src *",  # Allow all sources (NOT RECOMMENDED - DEBUG ONLY)
    "script-src * 'unsafe-inline' 'unsafe-eval'",
    "style-src * 'unsafe-inline'",
]
```

**Note:** Only use in emergency. Investigate and fix properly ASAP.

---

## Support

For questions or issues during implementation:

1. Review full penetration test report: `security/PENETRATION-TEST-REPORT.md`
2. Check test examples: `tests/test_security_enhancements.py`
3. Run security validation: `python scripts/security_check.py`
4. Contact security team for clarification

---

**Document Version:** 1.0  
**Last Updated:** 2026-08-29  
**Status:** Ready for Implementation
