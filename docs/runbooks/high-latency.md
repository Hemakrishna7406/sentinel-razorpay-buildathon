# High Latency Runbook

## Overview
This runbook provides a systematic approach to diagnosing and resolving high authorization latency in Sentinel. Target SLA: p99 latency < 500ms for evaluation requests.

---

## Symptoms

### Observable Indicators
- Prometheus metrics show:
  - `sentinel_evaluation_latency_seconds` p99 > 500ms
  - `sentinel_worker_queue_wait_seconds` p99 > 100ms
- Grafana dashboard shows latency spikes
- Users report slow authorization responses
- Timeouts in agent logs

### Severity Levels

| p99 Latency | Severity | User Impact |
|-------------|----------|-------------|
| < 500ms | Normal | None |
| 500ms - 2s | Degraded | Noticeable delay |
| 2s - 10s | Severe | User complaints |
| > 10s | Critical | Timeouts, failures |

---

## Diagnosis Flowchart

```
High Latency Detected
         |
         v
[Check Worker Queue Wait Time]
         |
    > 100ms? ----YES----> [Worker Capacity Issue] → Scale workers
         |                                          → See Kafka Consumer Lag runbook
         NO
         |
         v
[Check ML Inference Latency]
         |
    > 200ms? ----YES----> [ML Model Issue] → Optimize XGBoost
         |                                   → Enable GPU
         |                                   → Reduce model complexity
         NO
         |
         v
[Check Redis Latency]
         |
    > 50ms? -----YES----> [Redis Issue] → Check network
         |                                → Check Redis memory
         |                                → See Redis Outage runbook
         NO
         |
         v
[Check Database Latency]
         |
    > 100ms? ----YES----> [DB Issue] → Check slow queries
         |                             → Scale DB connections
         |                             → Add indexes
         NO
         |
         v
[Check Kafka Latency]
         |
    > 50ms? -----YES----> [Kafka Issue] → Check broker health
         |                                → Check network
         |                                → Scale Kafka cluster
         NO
         |
         v
[Check Network/External Services]
         |
         v
[Escalate to Infrastructure Team]
```

---

## Detailed Diagnosis Steps

### 1. Identify Latency Component

```bash
# Get latency breakdown from worker metrics
curl -s http://sentinel-worker:8001/metrics | grep sentinel_worker_processing

# Check timing breakdown in recent evaluations
kubectl logs -l component=worker --tail=50 | grep "timings" | jq '.timings'

# Example output:
# {
#   "queue_ms": 45,
#   "features_ms": 12,
#   "batch_wait_ms": 0,
#   "gpu_inference_ms": 0,
#   "policy_ms": 8
# }
```

### 2. Worker Queue Wait (queue_ms > 100)

**Root Cause**: Too many requests, not enough workers

```bash
# Check current worker utilization
kubectl top pods -l component=worker

# Check active tasks vs capacity
curl -s http://sentinel-worker:8001/metrics | grep -E "(active_tasks|capacity)"

# Expected output:
# sentinel_worker_active_tasks{} 28
# sentinel_worker_capacity{} 32

# If active_tasks near capacity, scale up
kubectl scale deployment sentinel-worker --replicas=10

# Monitor improvement
watch -n 2 'curl -s http://sentinel-worker:8001/metrics | grep queue_wait'
```

See also: [Kafka Consumer Lag Runbook](kafka-consumer-lag.md)

### 3. ML Inference (gpu_inference_ms > 200 or features_ms > 50)

**Root Cause**: Slow XGBoost model inference

```bash
# Check current inference backend
kubectl get pods -l component=worker -o yaml | grep INFERENCE_BACKEND

# Check XGBoost thread configuration
kubectl get pods -l component=worker -o yaml | grep XGB_NTHREAD

# Option A: Increase XGBoost threads (if CPU available)
kubectl set env deployment/sentinel-worker XGB_NTHREAD=8

# Option B: Enable GPU inference (if hardware available)
kubectl set env deployment/sentinel-worker INFERENCE_BACKEND=gpu \
  GPU_BATCH_SIZE=32 \
  GPU_BATCH_TIMEOUT_MS=10

# Option C: Optimize model (requires ML team)
# - Reduce tree depth
# - Reduce number of estimators
# - Quantize model weights
```

### 4. Redis Latency (Redis operations > 50ms)

**Root Cause**: Redis slow, network congestion, or memory pressure

```bash
# Check Redis latency
kubectl exec -it sentinel-redis-master-0 -- redis-cli --latency

# Check Redis memory usage
kubectl exec -it sentinel-redis-master-0 -- redis-cli INFO memory

# Check for slow commands
kubectl exec -it sentinel-redis-master-0 -- redis-cli SLOWLOG GET 10

# Common fixes:
# 1. Increase Redis memory limits
helm upgrade sentinel ./helm/sentinel \
  --set redis.master.resources.limits.memory=2Gi

# 2. Enable Redis persistence optimization
kubectl exec -it sentinel-redis-master-0 -- \
  redis-cli CONFIG SET save ""

# 3. Check network latency between API/Worker and Redis
kubectl exec -it sentinel-api-xxxx -- ping sentinel-redis-master
```

### 5. Database Latency (DB queries > 100ms)

**Root Cause**: Slow queries, connection pool exhaustion, or DB saturation

```bash
# Check database connection pool utilization
curl -s http://sentinel-api:8000/health/details | jq '.database.pool'

# Check slow queries (PostgreSQL)
kubectl exec -it sentinel-postgres-0 -- psql -U sentinel -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Common fixes:
# 1. Increase connection pool size (already done in Phase 23)
kubectl set env deployment/sentinel-api DB_POOL_SIZE=100 DB_MAX_OVERFLOW=50

# 2. Add missing indexes
# Identify via: EXPLAIN ANALYZE <slow_query>

# 3. Scale database read replicas
helm upgrade sentinel ./helm/sentinel \
  --set postgresql.readReplicas.replicaCount=3
```

### 6. Kafka Latency (Kafka publish > 50ms)

**Root Cause**: Kafka broker saturation, network issues, or ack timeout

```bash
# Check Kafka broker metrics
kubectl exec -it sentinel-kafka-0 -- kafka-run-class.sh kafka.tools.JmxTool \
  --object-name kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce

# Check Kafka replication lag
kubectl exec -it sentinel-kafka-0 -- kafka-run-class.sh kafka.tools.JmxTool \
  --object-name kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions

# Common fixes:
# 1. Reduce acknowledgment requirement (careful: reduces durability)
kubectl set env deployment/sentinel-api KAFKA_ACKS=1  # Default is "all"

# 2. Increase Kafka broker resources
helm upgrade sentinel ./helm/sentinel \
  --set kafka.resources.limits.cpu=4000m \
  --set kafka.resources.limits.memory=8Gi

# 3. Scale Kafka cluster
helm upgrade sentinel ./helm/sentinel --set kafka.replicaCount=5
```

---

## Quick Fixes by Symptom

| Symptom | Quick Fix | Expected Improvement |
|---------|-----------|----------------------|
| Worker queue wait > 100ms | `kubectl scale deployment sentinel-worker --replicas=10` | -50% queue wait |
| ML inference > 200ms | `kubectl set env deployment/sentinel-worker XGB_NTHREAD=8` | -30% inference time |
| Redis latency > 50ms | Check Redis memory, increase limits | -40% Redis latency |
| DB queries > 100ms | Verify pool size = 100, add indexes | -60% DB latency |
| Kafka publish > 50ms | Scale Kafka brokers | -50% Kafka latency |

---

## Prevention

### Proactive Measures

1. **Capacity Planning**:
   - Workers: 1 worker per 100 RPS
   - Redis: 2GB memory per 1M keys
   - Database: 100 connections per 1000 RPS
   - Kafka: 1 partition per 500 RPS

2. **Load Testing**:
   ```bash
   # Run load test before production
   cd benchmarks
   python load_test.py --target-rps 1000 --duration 300
   ```

3. **Monitoring Alerts**:
   ```yaml
   # prometheus/alerts.yaml
   - alert: HighEvaluationLatency
     expr: histogram_quantile(0.99, sentinel_evaluation_latency_seconds) > 0.5
     for: 5m
     labels:
       severity: warning
     annotations:
       summary: "p99 evaluation latency > 500ms"

   - alert: CriticalEvaluationLatency
     expr: histogram_quantile(0.99, sentinel_evaluation_latency_seconds) > 2.0
     for: 2m
     labels:
       severity: critical
     annotations:
       summary: "p99 evaluation latency > 2s"
   ```

4. **Autoscaling**:
   - Ensure HPA is enabled for API and Worker
   - Set appropriate CPU/memory thresholds (70-75%)

---

## Rollback

If changes cause instability:

```bash
# Revert environment variables
kubectl rollout undo deployment/sentinel-worker

# Revert scaling
kubectl scale deployment sentinel-worker --replicas=5
kubectl scale deployment sentinel-api --replicas=3

# Revert Helm changes
helm rollback sentinel
```

---

## Post-Incident

### Verification Checklist
- [ ] p99 latency < 500ms
- [ ] Worker queue wait < 50ms
- [ ] ML inference < 150ms
- [ ] Redis latency < 20ms
- [ ] Database queries < 50ms
- [ ] No error logs
- [ ] Grafana dashboard shows normal latency distribution

### Root Cause Analysis
- Was latency spike correlated with traffic increase?
- Was there a code deployment that introduced regression?
- Were infrastructure resources under-provisioned?
- Was there a dependency outage (Redis, Kafka, DB)?

### Action Items
- [ ] Update capacity planning if traffic baseline increased
- [ ] Add missing indexes if slow queries identified
- [ ] Optimize ML model if inference is bottleneck
- [ ] Review HPA thresholds for faster scaling

---

## Related Runbooks
- [Kafka Consumer Lag](kafka-consumer-lag.md) - Worker scaling procedures
- [Redis Outage](redis-outage.md) - Redis troubleshooting
- [Deployment Rollback](deployment-rollback.md) - Rollback procedures
