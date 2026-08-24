# Sentinel — backend.md

FastAPI service implementing the modules in `architecture.md`. Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, Redis client, XGBoost + SHAP for inference.

---

## 1. API surface (from masterplan §24 — do not exceed this without a reason)

```
POST   /agents                        register an agent
GET    /agents/{agent_id}             agent details
GET    /agents/{agent_id}/profile     current behavioral profile

POST   /intents                       submit a financial intent (idempotent)
GET    /intents/{intent_id}           intent status

POST   /authorize                     internal: run the full decision pipeline for an intent
GET    /decisions/{decision_id}       decision detail incl. SHAP reasons (P1)

POST   /capabilities/verify           execution layer calls this before executing
POST   /simulate                      P1: dry-run a candidate policy against historical intents

GET    /audit                         paginated audit trail
GET    /audit/verify                  verify hash-chain integrity (ops/debug endpoint)
```

## 2. Pydantic models (core ones)

```python
class IntentIn(BaseModel):
    agent_id: str
    action: Literal["refund", "retry", "checkout", "payout"]
    amount: int  # paise, never float
    currency: Literal["INR"]
    recipient_id: str
    metadata: dict[str, Any] = {}

class Decision(BaseModel):
    decision_id: str
    intent_id: str
    risk_score: float
    risk_level: Literal["SAFE", "SUSPICIOUS", "HIGH-RISK"]
    action: Literal["ALLOW", "ESCALATE", "CONTAIN"]
    policy_version: str
    top_features: list[tuple[str, float]] | None = None  # SHAP, P1
    created_at: datetime

class CapabilityToken(BaseModel):
    intent_id: str
    agent_id: str
    action: str
    transaction_id: str
    amount: int
    currency: str
    recipient_id: str
    decision_id: str
    policy_version: str
    expires_at: datetime
    nonce: str
    signature: str  # HMAC over the above fields
```

Amounts are integers in paise throughout — never floats, anywhere in the pipeline. This is a small detail worth stating explicitly if a panel asks about money handling.

## 3. Capability token — issuance and verification

**Issuance** (`authorization/tokens.py`):
```python
def issue(intent: Intent, decision: Decision) -> CapabilityToken:
    token = CapabilityToken(
        intent_id=intent.id, agent_id=intent.agent_id, action=intent.action,
        transaction_id=generate_transaction_id(), amount=intent.amount,
        currency=intent.currency, recipient_id=intent.recipient_id,
        decision_id=decision.id, policy_version=decision.policy_version,
        expires_at=now() + timedelta(seconds=90), nonce=secrets.token_hex(16),
    )
    token.signature = hmac_sign(token.dict(exclude={"signature"}), SECRET_KEY)
    store_token(token)  # Redis, TTL = expires_at
    return token
```

**Verification** (`execution/verify.py`) — implements masterplan §16's invariants 1–6 directly as sequential checks, each with its own test:
```python
def verify(token: CapabilityToken, execution_request: ExecutionRequest) -> bool:
    if not token: return False                                    # invariant 1
    if token.expires_at < now(): return False                     # invariant 2
    if token.transaction_id != execution_request.transaction_id: return False  # invariant 3
    if token.agent_id != execution_request.agent_id: return False # invariant 4
    if token.amount != execution_request.amount: return False     # invariant 5
    if not hmac_verify(token, SECRET_KEY): return False            # invariant 6 (tamper)
    return True
```

Each `return False` above should be a separate test case in `tests/test_capabilities.py` — one test per invariant, named after the invariant, not bundled into one "test_token_validation."

## 4. Fail-closed middleware

```python
def fail_closed(fn):
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            log.error(f"fail-closed triggered in {fn.__name__}: {e}")
            return Decision(action="ESCALATE", risk_level="HIGH-RISK", ...)  # never ALLOW on error
    return wrapper

@fail_closed
async def run_authorization_pipeline(intent: IntentIn) -> Decision: ...
```

Wrap the entire `/authorize` path, and separately wrap capability issuance itself — if the risk model is up but the token signer is down, that must also resolve to ESCALATE, not to a 500 that an agent might misinterpret as "try again = approved."

## 5. Idempotency

```python
def idempotency_key(intent: IntentIn) -> str:
    bucket = int(time.time() // 60)  # 1-minute time bucket
    return hashlib.sha256(f"{intent.agent_id}:{intent.action}:{intent.amount}:{intent.recipient_id}:{bucket}".encode()).hexdigest()

async def ingest(intent: IntentIn):
    key = idempotency_key(intent)
    if not await redis.set(f"idem:{key}", "1", nx=True, ex=90):
        return await get_cached_decision(key)  # return prior decision, don't reprocess
    ...
```

## 6. Execution adapter interface

```python
class PaymentExecutionAdapter(ABC):
    @abstractmethod
    async def execute(self, token: CapabilityToken) -> ExecutionResult: ...

class MockPaymentAdapter(PaymentExecutionAdapter):
    async def execute(self, token): 
        return ExecutionResult(status="success", provider_ref=f"mock_{uuid4()}")

class RazorpayTestModeAdapter(PaymentExecutionAdapter):
    async def execute(self, token):
        # only wired if RAZORPAY_TEST_KEY is set; falls back to Mock otherwise
        ...
```

`get_adapter()` reads an env var and returns Mock by default — the whole system must run and demo correctly with zero external credentials configured.

## 7. Error responses

Every rejection (denied token, failed idempotency, fail-closed trigger) returns a structured reason, never a bare 4xx/5xx — this feeds directly into the audit log and the dashboard's decision-detail view:
```python
class DecisionRejection(BaseModel):
    reason_code: Literal["EXPIRED_TOKEN", "AMOUNT_MISMATCH", "DUPLICATE_INTENT",
                          "AUTHORIZATION_UNAVAILABLE", "POLICY_DENIED", "TAMPERED_TOKEN"]
    detail: str
```
