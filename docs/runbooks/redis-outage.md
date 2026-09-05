# Redis Outage Runbook

## Overview
Redis is critical for Sentinel's idempotency, rate limiting, and real-time reply coordination. A Redis outage causes authorization requests to fail-closed (ESCALATE) to maintain security invariants.

---

## Symptoms

### Observable Indicators
- `/health/ready` endpoint returns `503 Service Unavailable`
- Prometheus metrics show:
  - `sentinel_redis_errors_total` spiking
  - `sentinel_redis_breaker_state` = `open`
- Logs show `CircuitBreakerError: redis`
- All evaluation requests return `decision: ESCALATE` with reason `REDIS_UNAVAILABLE`

### User Impact
- **CRITICAL**: All authorization requests fail-closed (ESCALATE)
- No new capability tokens are issued
- Agent requests are blocked pending manual review
- Idempotency protection is degraded

---

## Impact Assessment

| Severity | Impact | Response Time |
|----------|--------|---------------|
| **P0 - Critical** | Complete authorization denial | < 5 minutes |

### Blast Radius
- **API Service**: All evaluation endpoints blocked
- **Worker Service**: Cannot write results to Redis streams
- **Audit Trail**: Intact (uses Kafka + PostgreSQL)
- **Data Loss**: None (fail-closed prevents unauthorized operations)

---

## Response Procedure

### 1. Immediate Triage (< 2 minutes)

```bash
# Check Redis cluster health
kubectl exec -it sentinel-redis-master-0 -- redis-cli ping
# Expected: PONG

# Check circuit breaker state
curl http://sentinel-api/health/circuit-breakers
# Expected: redis.state = "open"

# View recent Redis errors
kubectl logs -l component=api --tail=50 | grep -i redis

# Check Redis Sentinel status (if enabled)
kubectl exec -it sentinel-redis-master-0 -- redis-cli -p 26379 SENTINEL masters
```

### 2. Verify Failover Capability (if using Redis Sentinel/Cluster)

```bash
# Check Redis Sentinel quorum
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli -p 26379 SENTINEL ckquorum mymaster
# Expected: OK 2 usable Sentinels. Quorum and failover authorization can be reached

# Force failover if master is unresponsive
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli -p 26379 SENTINEL failover mymaster

# Verify new master
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster
```

### 3. Check Idempotency Key Preservation

```bash
# Verify idempotency keys are intact after failover
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli --scan --pattern "idem:*" | head -10

# Check TTLs are preserved
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli TTL "idem:sample-key-here"
```

### 4. Restart Affected Services (if needed)

```bash
# Restart API pods to reset circuit breakers
kubectl rollout restart deployment/sentinel-api

# Monitor rollout
kubectl rollout status deployment/sentinel-api

# Verify health
curl http://sentinel-api/health/ready
# Expected: 200 OK

# Check circuit breaker recovery
curl http://sentinel-api/health/circuit-breakers | jq '.redis.state'
# Expected: "closed"
```

### 5. Resume Traffic

```bash
# Gradually scale up workers
kubectl scale deployment sentinel-worker --replicas=5

# Monitor evaluation latency
watch -n 2 'curl -s http://sentinel-api/metrics | grep sentinel_evaluation_latency'

# Check for normal decision distribution
curl -s http://sentinel-api/metrics | grep sentinel_decisions_total
```

---

## Prevention

### Proactive Measures
1. **Enable Redis Sentinel** for automatic failover (minimum 3 sentinels)
2. **Cross-AZ Replication**: Deploy Redis replicas across availability zones
3. **Health Monitoring**: Alert on `redis_master_link_down_since_seconds > 10`
4. **Circuit Breaker Tuning**: Adjust `fail_max` and `timeout_duration` if needed

### Configuration Recommendations

```yaml
# helm/sentinel/values.yaml
redis:
  enabled: true
  sentinel:
    enabled: true
    quorum: 2
  replica:
    replicaCount: 2
  master:
    persistence:
      enabled: true
      size: 8Gi
```

### Monitoring Alerts

```yaml
# prometheus/alerts.yaml
- alert: RedisCircuitBreakerOpen
  expr: sentinel_redis_breaker_state == 1
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Redis circuit breaker is OPEN"
    description: "All authorization requests are failing closed"

- alert: RedisMasterDown
  expr: redis_master_link_down_since_seconds > 30
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Redis master-replica link down"
```

---

## Rollback

If Redis cannot be recovered:

1. **Temporary Failover to Observe Mode** (emergency only):
   ```bash
   # NOT RECOMMENDED: Only for critical business continuity
   kubectl set env deployment/sentinel-api EVALUATION_MODE=observe
   # This shadows decisions but does NOT enforce them
   ```

2. **Scale Down to Controlled Capacity**:
   ```bash
   kubectl scale deployment sentinel-api --replicas=1
   kubectl scale deployment sentinel-worker --replicas=1
   ```

---

## Post-Incident

### Verification Checklist
- [ ] Redis cluster is healthy (all replicas in sync)
- [ ] Circuit breakers are CLOSED (redis.state = "closed")
- [ ] Idempotency keys are preserved
- [ ] `/health/ready` returns 200 OK
- [ ] Authorization requests return normal decision distribution (ALLOW/DENY)
- [ ] Prometheus metrics show no Redis errors

### Root Cause Analysis
- Document incident timeline
- Identify Redis failure trigger (network, OOM, disk failure)
- Review Redis persistence settings (AOF/RDB)
- Verify backup/restore procedures

### Action Items
- [ ] Enable Redis Sentinel if not already configured
- [ ] Implement cross-region Redis replication
- [ ] Add automated failover testing to CI/CD
- [ ] Review Redis memory limits and eviction policies

---

## Escalation Path

| Time Since Incident | Action |
|---------------------|--------|
| T+5 min | Page on-call SRE |
| T+15 min | Escalate to Infrastructure Team Lead |
| T+30 min | Engage Redis expert / DBA |
| T+1 hour | Executive notification (if user-facing impact) |

---

## Related Runbooks
- [Kafka Consumer Lag](kafka-consumer-lag.md) - Worker scaling
- [High Latency](high-latency.md) - Latency diagnosis
- [Deployment Rollback](deployment-rollback.md) - Rollback procedures
