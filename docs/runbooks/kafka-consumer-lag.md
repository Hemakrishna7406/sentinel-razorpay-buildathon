# Kafka Consumer Lag Runbook

## Overview
Kafka consumer lag occurs when workers cannot process intents fast enough, causing authorization latency spikes. This runbook guides you through diagnosing lag and scaling workers appropriately.

---

## Symptoms

### Observable Indicators
- Prometheus metrics show:
  - `kafka_consumer_lag_messages{topic="intents.inbound"}` > 1000
  - `sentinel_evaluation_latency_seconds` p99 > 2 seconds
- Grafana dashboard shows backlog growth
- Users report slow authorization responses
- Worker CPU/memory utilization at capacity

### Thresholds

| Lag (messages) | Severity | Action Required |
|----------------|----------|-----------------|
| < 100 | Normal | None |
| 100-1000 | Warning | Monitor |
| 1000-5000 | Degraded | Scale up workers |
| > 5000 | Critical | Immediate scaling + investigation |

---

## Impact Assessment

| Lag Range | Expected Latency | User Impact |
|-----------|------------------|-------------|
| < 100 | < 500ms | None |
| 100-1000 | 500ms - 2s | Minor delay |
| 1000-5000 | 2s - 10s | Significant delay |
| > 5000 | > 10s | Timeouts, user complaints |

---

## Diagnosis Procedure

### 1. Check Current Lag

```bash
# View consumer lag via Kafka CLI
kubectl exec -it sentinel-kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group sentinel-evaluator-group

# Expected output columns: TOPIC, PARTITION, CURRENT-OFFSET, LOG-END-OFFSET, LAG

# Check via Prometheus
curl -s http://prometheus:9090/api/v1/query \
  --data-urlencode 'query=kafka_consumer_lag_messages{topic="intents.inbound"}' \
  | jq '.data.result[0].value[1]'
```

### 2. Identify Bottleneck

```bash
# Check worker CPU/memory utilization
kubectl top pods -l component=worker

# View worker active tasks
curl -s http://sentinel-worker:8001/metrics | grep sentinel_worker_active_tasks

# Check XGBoost inference latency
curl -s http://sentinel-worker:8001/metrics | grep sentinel_ml_inference_latency

# Inspect recent worker logs for errors
kubectl logs -l component=worker --tail=100 | grep -i error
```

### 3. Assess Partition Distribution

```bash
# Check partition assignment
kubectl logs -l component=worker --tail=200 | grep -i "partition"

# Verify workers are consuming from all partitions
# With 4 partitions and 5 workers, expect uneven distribution (4 active, 1 idle)
```

---

## Response Procedure

### Scenario A: Worker Capacity (Most Common)

**Trigger**: Lag > 1000, worker CPU > 75%, no errors

```bash
# Scale up workers (from 5 to 10)
kubectl scale deployment sentinel-worker --replicas=10

# Monitor lag reduction
watch -n 5 'kubectl exec -it sentinel-kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group sentinel-evaluator-group | grep intents.inbound'

# Verify workers are processing
kubectl logs -l component=worker --tail=20 -f | grep "Intent evaluated"
```

### Scenario B: Slow ML Inference

**Trigger**: Lag > 1000, `sentinel_ml_inference_latency` p99 > 200ms

```bash
# Check if GPU is enabled (if available)
kubectl get pods -l component=worker -o yaml | grep -i "INFERENCE_BACKEND"

# Option 1: Enable GPU inference (if hardware available)
kubectl set env deployment/sentinel-worker INFERENCE_BACKEND=gpu

# Option 2: Increase XGBoost threads
kubectl set env deployment/sentinel-worker XGB_NTHREAD=8

# Option 3: Reduce concurrent tasks per worker (increase parallelism via more workers)
kubectl set env deployment/sentinel-worker MAX_CONCURRENT_TASKS=16
kubectl scale deployment sentinel-worker --replicas=15
```

### Scenario C: Kafka Partition Bottleneck

**Trigger**: Lag > 1000, only 4 workers active (with > 4 workers deployed)

```bash
# Current: 4 partitions, can only utilize 4 workers concurrently
# Solution: Increase partitions (requires rebalancing)

# Step 1: Increase partitions to 8
kubectl exec -it sentinel-kafka-0 -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --alter \
  --topic intents.inbound \
  --partitions 8

# Step 2: Wait for rebalancing (1-2 minutes)
kubectl logs -l component=worker --tail=50 | grep -i "rebalance"

# Step 3: Scale workers to match new partition count
kubectl scale deployment sentinel-worker --replicas=8

# Verify lag reduction
watch -n 5 'kubectl exec -it sentinel-kafka-0 -- kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group sentinel-evaluator-group'
```

### Scenario D: Kafka Broker Saturation

**Trigger**: Lag > 1000, Kafka CPU/disk I/O at capacity

```bash
# Check Kafka broker metrics
kubectl exec -it sentinel-kafka-0 -- kafka-run-class.sh kafka.tools.JmxTool \
  --object-name kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec \
  --jmx-url service:jmx:rmi:///jndi/rmi://localhost:9999/jmxrmi

# Solution: Scale Kafka cluster
helm upgrade sentinel ./helm/sentinel \
  --set kafka.replicaCount=5 \
  --set kafka.resources.limits.cpu=4000m
```

---

## Scaling Decision Matrix

| Condition | Action | Expected Result |
|-----------|--------|-----------------|
| Lag < 1000, Worker CPU < 70% | None | System healthy |
| Lag 1000-5000, Worker CPU > 70% | Scale workers to +50% | Lag clears in 5-10 min |
| Lag > 5000, Worker CPU > 80% | Scale workers to +100% | Lag clears in 10-20 min |
| Lag > 5000, Worker CPU < 50% | Investigate bottleneck (ML, DB, Redis) | Case-by-case |
| Lag persistent, 4 workers idle | Increase Kafka partitions | Utilize all workers |

---

## Prevention

### Proactive Measures

1. **Horizontal Pod Autoscaler (HPA)**:
   ```yaml
   # Already configured in helm/sentinel/templates/hpa.yaml
   maxReplicas: 20
   targetCPUUtilizationPercentage: 75
   ```

2. **Kafka Partition Planning**:
   - Rule of thumb: Partitions ≥ Max expected workers
   - Current: 4 partitions → supports up to 4 concurrent workers
   - Recommendation: 8-12 partitions for future scaling

3. **Monitoring Alerts**:
   ```yaml
   # prometheus/alerts.yaml
   - alert: KafkaConsumerLagHigh
     expr: kafka_consumer_lag_messages{topic="intents.inbound"} > 1000
     for: 5m
     labels:
       severity: warning
     annotations:
       summary: "Kafka consumer lag > 1000 messages"

   - alert: KafkaConsumerLagCritical
     expr: kafka_consumer_lag_messages{topic="intents.inbound"} > 5000
     for: 2m
     labels:
       severity: critical
     annotations:
       summary: "Kafka consumer lag > 5000 messages"
   ```

---

## Rollback

If scaling causes instability:

```bash
# Roll back to previous replica count
kubectl scale deployment sentinel-worker --replicas=5

# Verify stability
kubectl rollout status deployment/sentinel-worker

# Check logs for errors
kubectl logs -l component=worker --tail=100
```

---

## Post-Incident

### Verification Checklist
- [ ] Kafka consumer lag < 100 messages
- [ ] Worker CPU utilization 60-70%
- [ ] Evaluation latency p99 < 500ms
- [ ] No worker error logs
- [ ] HPA is scaling automatically

### Root Cause Analysis
- Was traffic spike expected (marketing campaign, product launch)?
- Were workers under-provisioned?
- Was there a performance regression (slow ML model, DB query)?
- Were Kafka partitions insufficient?

### Action Items
- [ ] Adjust HPA thresholds if needed
- [ ] Increase Kafka partitions if worker scaling limited
- [ ] Optimize ML inference if bottleneck identified
- [ ] Review capacity planning for next traffic spike

---

## Related Runbooks
- [High Latency](high-latency.md) - Latency diagnosis flowchart
- [Redis Outage](redis-outage.md) - Redis failover procedure
- [Deployment Rollback](deployment-rollback.md) - Rollback procedures
