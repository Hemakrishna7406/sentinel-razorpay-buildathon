# Security Invariant Break Runbook

## Overview
Sentinel's security model is built on cryptographic guarantees and audit chain integrity. This runbook responds to audit chain breaks, capability token forgery attempts, or fail-open conditions that violate security invariants.

**CRITICAL**: Any security invariant break is a P0 incident requiring immediate response.

---

## Security Invariants

Sentinel enforces these non-negotiable guarantees:

1. **Fail-Closed**: Any uncertainty → ESCALATE (never fail-open)
2. **Audit Completeness**: Every decision is logged to audit trail (Kafka + DB)
3. **Capability Token Integrity**: Tokens are cryptographically signed and verified
4. **Idempotency**: Duplicate requests produce identical decisions
5. **Rate Limiting**: Agent request rates are bounded

**Invariant Break** = Any violation of the above, detected via monitoring or audit.

---

## Symptoms

### Critical Indicators
- **Audit Chain Gap**: Missing audit records in database
- **Capability Token Forgery**: Token verification failures
- **Fail-Open Detection**: ALLOW decision without valid token
- **Idempotency Violation**: Same intent produces different decisions
- **Rate Limit Bypass**: Agent exceeds rate limit without rejection

### Monitoring Alerts

```yaml
# prometheus/alerts.yaml
- alert: AuditChainGap
  expr: rate(sentinel_audit_records_total[5m]) < rate(sentinel_decisions_total[5m])
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "Audit records lag behind decisions — potential data loss"

- alert: CapabilityTokenVerificationFailure
  expr: rate(sentinel_token_verification_errors_total[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Capability token verification failures detected"

- alert: FailOpenDetected
  expr: sentinel_decisions_total{decision="ALLOW",reason="FAIL_OPEN"} > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "FAIL-OPEN condition detected — security invariant violated"
```

---

## Response Procedure

### Phase 1: Immediate Containment (< 5 minutes)

```bash
# 1. STOP accepting new requests
kubectl scale deployment sentinel-api --replicas=0

# 2. Isolate affected workers
kubectl label pods -l component=worker quarantine=true

# 3. Preserve forensic evidence
kubectl exec -it sentinel-kafka-0 -- kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic intents.evaluated \
  --from-beginning > /tmp/audit-trail-$(date +%s).json

# 4. Capture database snapshot
kubectl exec -it sentinel-postgres-0 -- \
  pg_dump -U sentinel -Fc sentinel > /tmp/sentinel-db-$(date +%s).dump

# 5. Capture Redis state
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli --rdb /tmp/sentinel-redis-$(date +%s).rdb

# 6. Notify incident response team
# Send PagerDuty alert with severity: CRITICAL
```

---

## Scenario-Specific Responses

### Scenario A: Audit Chain Gap

**Symptom**: Decisions logged but audit records missing

```bash
# 1. Check audit consumer health
kubectl logs -l component=audit --tail=100

# 2. Check Kafka topic retention
kubectl exec -it sentinel-kafka-0 -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic intents.evaluated

# 3. Check database writes
kubectl exec -it sentinel-postgres-0 -- psql -U sentinel -c \
  "SELECT COUNT(*) FROM audit_log WHERE timestamp > NOW() - INTERVAL '1 hour';"

# 4. Identify missing records
# Compare Kafka offsets vs DB records
kubectl exec -it sentinel-kafka-0 -- kafka-run-class.sh kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic intents.evaluated

# 5. Replay missing records (if Kafka retention allows)
kubectl rollout restart deployment sentinel-audit
kubectl logs -l component=audit -f | grep "Audit record written"

# 6. Verify gap closure
# Check that audit_log count matches evaluated events count
```

**Root Cause Analysis**:
- Was audit consumer down?
- Database connection pool exhausted?
- Kafka partition reassignment?

---

### Scenario B: Capability Token Forgery Attempt

**Symptom**: Token signature verification failures

```bash
# 1. Identify affected tokens
kubectl logs -l component=api --tail=500 | grep "Token verification failed"

# 2. Extract token metadata
# Parse logs to identify:
# - agent_id
# - intent_id
# - timestamp
# - IP address

# 3. Block affected agent
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli SADD "blocked_agents" "<agent_id>"

# 4. Rotate signing key (emergency only)
# Generate new key
openssl rand -base64 64 > /tmp/new_signing_key.txt

# Update secret
kubectl create secret generic sentinel-secrets \
  --from-file=capability-signing-key=/tmp/new_signing_key.txt \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart API to load new key
kubectl rollout restart deployment sentinel-api

# 5. Invalidate all outstanding tokens (revoke via Redis)
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli FLUSHDB  # CAUTION: Nuclear option, clears all idempotency keys

# 6. Audit all recent ALLOW decisions with old key
# Review audit logs for unauthorized operations
```

**Root Cause Analysis**:
- Was signing key leaked?
- Weak key generation?
- Insider threat?

---

### Scenario C: Fail-Open Condition

**Symptom**: ALLOW decision without valid capability token

```bash
# 1. Identify fail-open decisions
kubectl logs -l component=worker --tail=1000 | grep "decision.*ALLOW" | grep -v "token"

# 2. Check for code deployment anomalies
kubectl rollout history deployment sentinel-worker

# 3. Roll back to last known good version
kubectl rollout undo deployment sentinel-worker

# 4. Verify fail-closed behavior restored
# Submit test intent with forced dependency failure
curl -X POST http://sentinel-api/v1/intents \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "agent_id": "test-agent",
    "action_type": "refund",
    "amount": 100000,
    "currency": "INR",
    "recipient": "test@example.com"
  }'

# Expected: decision = ESCALATE if Redis/Kafka unavailable

# 5. Audit all recent ALLOW decisions
# Manual review required
```

**Root Cause Analysis**:
- Code regression (missed error handling)?
- Configuration error (EVALUATION_MODE=observe set incorrectly)?
- Dependency circuit breaker bypassed?

---

### Scenario D: Idempotency Violation

**Symptom**: Same intent produces different decisions

```bash
# 1. Identify duplicate intents with different decisions
kubectl exec -it sentinel-postgres-0 -- psql -U sentinel -c \
  "SELECT intent_id, COUNT(DISTINCT decision) as decision_count
   FROM audit_log
   GROUP BY intent_id
   HAVING COUNT(DISTINCT decision) > 1;"

# 2. Check Redis idempotency key expiration
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli SCAN 0 MATCH "idem:*" COUNT 100

# 3. Verify idempotency TTL configuration
kubectl get configmap sentinel-config -o yaml | grep IDEMPOTENCY_TTL

# 4. Check for clock skew
kubectl exec -it sentinel-api-xxxx -- date
kubectl exec -it sentinel-worker-xxxx -- date

# 5. Investigate behavioral context changes
# Same intent, different context (velocity, reputation) may produce different decisions
# Verify this is expected behavior, not an invariant violation
```

**Root Cause Analysis**:
- Redis key expiration too short?
- Clock skew between services?
- Context data not captured in idempotency key?

---

### Scenario E: Rate Limit Bypass

**Symptom**: Agent exceeds rate limit without rejection

```bash
# 1. Check rate limiter circuit breaker
curl http://sentinel-api:8000/health/circuit-breakers | jq '.redis.state'

# 2. Verify rate limit enforcement
kubectl logs -l component=api --tail=200 | grep -i "rate limit"

# 3. Check Redis key expiration
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli TTL "rate_limit:<agent_id>"

# 4. Manually block agent
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli SET "rate_limit:<agent_id>" 9999 EX 3600

# 5. Verify rejection
curl -X POST http://sentinel-api/v1/intents \
  -H "Authorization: Bearer $API_KEY" \
  -d '{"agent_id":"<agent_id>",...}'

# Expected: 429 Too Many Requests
```

---

## Recovery Procedure

```bash
# 1. Verify invariants restored
# Run invariant test suite
cd tests
python test_security_invariants.py

# 2. Gradually restore service
kubectl scale deployment sentinel-worker --replicas=2
kubectl scale deployment sentinel-api --replicas=1

# 3. Monitor for anomalies
watch -n 5 'curl -s http://sentinel-api:8000/metrics | grep sentinel_decisions_total'

# 4. Perform controlled smoke test
# Submit known-good intents, verify decisions match expected

# 5. Scale to full capacity
kubectl scale deployment sentinel-worker --replicas=5
kubectl scale deployment sentinel-api --replicas=3

# 6. Re-enable autoscaling
kubectl autoscale deployment sentinel-api --min=3 --max=10 --cpu-percent=70
kubectl autoscale deployment sentinel-worker --min=5 --max=20 --cpu-percent=75
```

---

## Post-Incident

### Forensic Analysis
- [ ] Review all audit logs for timeline of invariant break
- [ ] Identify root cause (code, config, infrastructure)
- [ ] Enumerate impacted intents (if any unauthorized operations occurred)
- [ ] Determine data integrity (all decisions audited correctly?)

### Security Review
- [ ] Rotate capability signing key
- [ ] Review access control (who can deploy, who can access secrets)
- [ ] Audit recent code changes for security regressions
- [ ] Penetration test capability token validation logic

### Action Items
- [ ] Add automated invariant testing to CI/CD
- [ ] Implement additional monitoring for invariant breaks
- [ ] Update incident response runbook with lessons learned
- [ ] Conduct security training for engineering team

---

## Escalation

**Immediate notification required**:
- CISO / Security Team Lead
- Engineering Director
- Legal / Compliance (if customer data impacted)
- CEO (if public-facing impact or regulatory reporting required)

---

## Related Runbooks
- [Deployment Rollback](deployment-rollback.md) - Emergency rollback procedures
- [Redis Outage](redis-outage.md) - Idempotency engine failure
- [High Latency](high-latency.md) - Performance degradation
