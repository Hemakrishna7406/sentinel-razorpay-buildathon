# Razorpay Integration Architecture

## Executive Summary

Sentinel implements a **clean separation** between authorization (Sentinel's control plane) and execution (payment rails like Razorpay). This architectural pattern enables Sentinel to work with any payment provider while maintaining strong security guarantees.

---

## Architecture: Execution Boundary Separation

```
┌────────────────────────┐
│   Autonomous AI Agent  │
│   (Claude, GPT-4, etc) │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│      SENTINEL          │
│  Authorization Plane   │
├────────────────────────┤
│  1. Behavioral Risk    │
│  2. Semantic Risk      │
│  3. Policy Evaluation  │
│  4. Idempotency Check  │
└───────────┬────────────┘
            │
      Authorization
       Decision
            │
            ▼
┌────────────────────────┐
│  Capability Token      │
│  (Signed JWT, 5s TTL)  │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Execution Adapter     │
│  Interface (Abstract)  │
└───────────┬────────────┘
            │
    ┌───────┴────────┐
    │                │
    ▼                ▼
┌─────────┐    ┌─────────┐
│Razorpay │    │  Other  │
│ Direct  │    │  Rails  │
│  SDK    │    │(MCP,etc)│
└─────────┘    └─────────┘
```

---

## Why This Matters

### 1. **Provider-Agnostic Security**
Sentinel's authorization logic is **completely independent** of the payment provider. You can swap Razorpay for Stripe, internal ledgers, or any financial system without changing security policies.

### 2. **Fail-Closed Guarantee**
Authorization happens **before** the execution context. If Sentinel fails, no capability token is issued, and no payment executes.

### 3. **Cryptographic Auditability**
Every execution is tied to a signed capability token. The audit chain proves which authorization decision led to which financial transaction.

### 4. **Minimal Blast Radius**
Payment provider outages don't affect Sentinel's authorization decisions. Sentinel can continue issuing ESCALATE/CONTAIN decisions even when Razorpay is unavailable.

---

## Razorpay Direct Adapter

### Implementation

**File**: `execution/adapters/razorpay_direct.py`  
**Provider**: Official Razorpay Python SDK  
**Modes**: Test and Live (configurable via environment)

### Supported Operations

| Action | Razorpay API | Status |
|--------|--------------|--------|
| `create_order` | Orders API | ✅ Implemented |
| `create_payout` | Payouts API | ✅ Implemented |
| `refund` | Refunds API | ✅ Implemented |
| `fetch_payment` | Payments API | ✅ Implemented |

### Security Invariants

Before calling Razorpay, the execution adapter verifies:

1. **Token Signature**: Capability token is cryptographically signed
2. **Token Expiry**: Token is within 5-second TTL
3. **Token Binding**: Action, amount, recipient match token claims
4. **Single-Use**: JTI (JWT ID) has not been used before
5. **Intent Match**: Intent ID matches authorization

If **any** invariant fails → **BLOCK** (no Razorpay API call)

---

## Configuration

### Environment Variables

```bash
# Razorpay Credentials
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...

# Environment Mode
RAZORPAY_ENVIRONMENT=test  # or "live"

# Provider Selection
RAZORPAY_PROVIDER=direct   # or "mcp"
```

### Initialization

```python
from execution.adapters.razorpay_direct import RazorpayDirectProvider

provider = RazorpayDirectProvider(environment="test")

# Health check
health = await provider.get_health()
# {"provider": "razorpay-direct", "status": "HEALTHY", ...}
```

---

## Authorization → Execution Flow

### Example: Agent Requests Payout

**1. Agent Intent**  
```json
{
  "agent_id": "checkout-agent-01",
  "action": "create_payout",
  "amount": 250000,  // ₹2,500 in paise
  "recipient": "fa_abc123"
}
```

**2. Sentinel Evaluates**
- Behavioral risk: 0.08 (low)
- Policy: ALLOW
- Issues capability token (5s TTL, single-use)

**3. Execution Adapter Validates**
- Token signature ✅
- Token expiry ✅  
- Action match ✅
- Amount match ✅
- JTI unused ✅

**4. Razorpay API Called**
```python
payout = client.payout.create({
  "amount": 250000,
  "fund_account_id": "fa_abc123",
  "reference_id": capability_jti,
  ...
})
```

**5. Receipt Logged**
```json
{
  "execution_id": "exec_xyz",
  "capability_jti": "cap_abc",
  "provider_reference": "payout_razorpay_id",
  "status": "SUCCESS"
}
```

---

## Error Handling

### Razorpay SDK Errors

| Error Type | Sentinel Response | User Impact |
|------------|-------------------|-------------|
| `BadRequestError` | status="FAILED" | User sees error, can retry |
| `GatewayError` | status="UNKNOWN" | Uncertain state, investigate |
| `ServerError` | status="UNKNOWN" | Uncertain state, investigate |
| Network timeout | status="UNKNOWN" | Uncertain state, investigate |

**Idempotency protects against retries** - if the same intent is retried with the same idempotency key, Sentinel returns the original execution result.

---

## Integration Status

### ✅ What's Implemented

- Razorpay Python SDK integration
- 4 core operations (Order, Payout, Refund, Fetch)
- Test and Live mode support
- Health check endpoint
- Comprehensive error handling
- Capability token verification
- JTI replay protection

### ⚠️ What's Missing (Future Work)

- Webhook verification for payment status updates
- Bulk payout operations
- Razorpay MCP server integration
- Payment link creation
- Subscription management
- Automated reconciliation pipeline

---

## Testing

### Unit Tests

```bash
pytest tests/execution/test_razorpay_adapter.py
```

### Integration Tests

```bash
# Requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env
pytest tests/execution/test_razorpay_integration.py -v
```

### Health Check

```bash
curl http://localhost:8000/execution/provider
```

Expected response:
```json
{
  "provider": "razorpay-direct",
  "status": "HEALTHY",
  "environment": "test",
  "api_latency_ms": 234,
  "supported_actions": ["create_order", "create_payout", "refund", "fetch_payment"]
}
```

---

## Security Considerations

### 1. **Key Management**
- **Never commit** Razorpay keys to git
- Use environment variables or secret managers
- Rotate keys quarterly
- Use separate test/live keys

### 2. **Capability Token TTL**
- Default: **5 seconds** (enough for execution, not for abuse)
- Single-use JTI prevents replay attacks
- Token embeds exact amount/recipient (no substitution possible)

### 3. **Audit Trail**
- Every Razorpay API call is logged with:
  - Capability JTI
  - Intent ID
  - Decision ID
  - Provider reference (Razorpay order/payout ID)
- Merkle hash chain prevents tampering

### 4. **Fail-Closed Execution**
- Missing token → BLOCK
- Invalid token → BLOCK
- Expired token → BLOCK
- Wrong amount → BLOCK
- Used JTI → BLOCK

**NO uncertainty produces execution**.

---

## Deployment Checklist

### Before Production

- [ ] Set `RAZORPAY_ENVIRONMENT=live`
- [ ] Configure production `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`
- [ ] Test health check endpoint
- [ ] Configure webhook endpoints (if using)
- [ ] Set up Razorpay Dashboard monitoring
- [ ] Configure rate limits
- [ ] Test idempotency with live keys (small amounts)
- [ ] Set up alerting for failed executions
- [ ] Document incident response procedures

---

## Comparison: Direct SDK vs MCP

| Feature | Razorpay Direct SDK | Razorpay MCP Server |
|---------|---------------------|---------------------|
| Latency | ~200-500ms | ~300-700ms (extra hop) |
| Setup | Simple (pip install) | Requires MCP server |
| Isolation | In-process | Separate process |
| Best for | Production workloads | Agent development |

**Sentinel supports both**. Choose based on your deployment constraints.

---

## Frequently Asked Questions

### Q: Does Sentinel lock me into Razorpay?

**A:** No. The execution adapter interface is abstract. You can implement adapters for any payment rail (Stripe, internal ledgers, bank APIs, etc.) without changing Sentinel's authorization logic.

### Q: What happens if Razorpay is down?

**A:** Sentinel continues to authorize (ALLOW/ESCALATE/CONTAIN) based on behavioral risk and policy. Executions fail with status="UNKNOWN", but no unsafe ALLOWs are issued.

### Q: How does idempotency work across retries?

**A:** Each intent has an idempotency key. If the same key is used twice:
- First call: Normal evaluation → Issues token → Executes → Logs execution ID
- Second call: Returns original execution ID immediately (no re-execution)

### Q: Can an agent bypass Sentinel and call Razorpay directly?

**A:** Only if the agent has direct access to `RAZORPAY_KEY_SECRET`. In production, the secret should only be accessible to Sentinel's execution worker, not the AI agent.

---

## Additional Resources

- **Razorpay API Docs**: https://razorpay.com/docs/api/
- **Sentinel Architecture**: `docs/architecture.md`
- **Capability Tokens**: `security/capability-token.md`
- **Idempotency Engine**: `security/idempotency.md`

---

**Status**: ✅ Production-ready  
**Last Updated**: August 29, 2026  
**Maintainer**: Sentinel Team
