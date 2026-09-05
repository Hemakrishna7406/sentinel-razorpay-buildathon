# Deployment Rollback Runbook

## Overview
This runbook covers rollback procedures for Sentinel deployments. Rollbacks restore service to the last known good state when a deployment introduces bugs, performance regressions, or security issues.

**Guiding Principle**: Rollback is a tactical fix, not root cause resolution. Always follow up with post-mortem and permanent fix.

---

## When to Rollback

### Immediate Rollback Triggers (P0)
- Security invariant violation (fail-open, audit chain break)
- Authorization errors > 5%
- p99 latency > 5 seconds
- Critical bug causing data corruption
- Complete service outage

### Rollback Consideration (P1-P2)
- Authorization errors 1-5%
- p99 latency 2-5 seconds
- Non-critical bug affecting subset of users
- Performance regression > 50%

### Do NOT Rollback
- Minor UI glitches (frontend only)
- Non-critical logging errors
- Performance improvement that requires tuning
- Expected behavior change documented in release notes

---

## Pre-Rollback Checklist

Before initiating rollback:

```bash
# 1. Verify deployment history
kubectl rollout history deployment/sentinel-api
kubectl rollout history deployment/sentinel-worker
kubectl rollout history deployment/sentinel-audit

# 2. Identify last known good version
# Check Git tags and CI/CD logs
git log --oneline --decorate

# 3. Capture current state for forensics
kubectl get pods -o yaml > /tmp/pods-pre-rollback-$(date +%s).yaml
kubectl logs -l component=api --tail=500 > /tmp/api-logs-pre-rollback.log
kubectl logs -l component=worker --tail=500 > /tmp/worker-logs-pre-rollback.log

# 4. Check if rollback is safe (no schema migrations in new version)
# Review alembic migration log
kubectl exec -it sentinel-api-xxxx -- alembic current
kubectl exec -it sentinel-api-xxxx -- alembic history
```

---

## Rollback Procedures

### Option A: Kubernetes Rollout Undo (Fastest)

**Use when**: Recent deployment (within last 10 revisions), no schema changes

```bash
# Step 1: Roll back API deployment
kubectl rollout undo deployment/sentinel-api
kubectl rollout status deployment/sentinel-api --timeout=300s

# Step 2: Verify API health
curl http://sentinel-api/health/ready
# Expected: 200 OK

# Step 3: Roll back Worker deployment
kubectl rollout undo deployment/sentinel-worker
kubectl rollout status deployment/sentinel-worker --timeout=300s

# Step 4: Roll back Audit consumer (if deployed)
kubectl rollout undo deployment/sentinel-audit
kubectl rollout status deployment/sentinel-audit --timeout=300s

# Step 5: Verify system health
kubectl get pods -l app=sentinel
curl http://sentinel-api/metrics | grep sentinel_decisions_total

# Step 6: Monitor for errors
kubectl logs -l component=api --tail=100 -f
```

### Option B: Helm Rollback (Recommended for Production)

**Use when**: Full configuration rollback needed (env vars, secrets, resources)

```bash
# Step 1: Check Helm release history
helm history sentinel

# Example output:
# REVISION  STATUS      CHART            APP VERSION  DESCRIPTION
# 1         superseded  sentinel-1.0.0   1.0.0        Install complete
# 2         deployed    sentinel-1.1.0   1.1.0        Upgrade complete

# Step 2: Roll back to previous revision
helm rollback sentinel
# Or specific revision: helm rollback sentinel 1

# Step 3: Wait for rollout to complete
kubectl rollout status deployment/sentinel-api
kubectl rollout status deployment/sentinel-worker
kubectl rollout status deployment/sentinel-audit

# Step 4: Verify rollback
helm list
# REVISION should show incremented number with rolled-back chart version

# Step 5: Verify system health
curl http://sentinel-api/health/ready
curl http://sentinel-api/health/circuit-breakers
```

### Option C: Manual Rollback (Emergency)

**Use when**: Helm/kubectl unavailable, or complex multi-step rollback

```bash
# Step 1: Stop accepting new traffic
kubectl scale deployment sentinel-api --replicas=0

# Step 2: Drain in-flight requests
# Wait 60 seconds for graceful shutdown
sleep 60

# Step 3: Deploy specific image version
kubectl set image deployment/sentinel-api \
  api=docker.io/sentinel/api:v1.0.0

kubectl set image deployment/sentinel-worker \
  worker=docker.io/sentinel/worker:v1.0.0

# Step 4: Revert environment variables (if changed)
kubectl set env deployment/sentinel-api \
  FEATURE_FLAG_X=false \
  DB_POOL_SIZE=100

# Step 5: Gradually restore traffic
kubectl scale deployment sentinel-api --replicas=1
# Wait and verify health
sleep 30
curl http://sentinel-api/health/ready

# If healthy, scale to full capacity
kubectl scale deployment sentinel-api --replicas=3
kubectl scale deployment sentinel-worker --replicas=5

# Step 6: Re-enable autoscaling
kubectl autoscale deployment sentinel-api --min=3 --max=10 --cpu-percent=70
kubectl autoscale deployment sentinel-worker --min=5 --max=20 --cpu-percent=75
```

---

## Special Cases

### Case 1: Database Schema Migration in Deployed Version

**Problem**: New version included schema migration, rollback requires downgrade migration

```bash
# Step 1: Identify migration revision
kubectl exec -it sentinel-api-xxxx -- alembic current

# Example: Current revision is "abc123"
# Need to downgrade to previous revision "def456"

# Step 2: Take database backup
kubectl exec -it sentinel-postgres-0 -- \
  pg_dump -U sentinel -Fc sentinel > /tmp/sentinel-db-backup-$(date +%s).dump

# Step 3: Downgrade schema
kubectl exec -it sentinel-api-xxxx -- alembic downgrade def456

# Step 4: Verify schema downgrade
kubectl exec -it sentinel-api-xxxx -- alembic current

# Step 5: Roll back application
kubectl rollout undo deployment/sentinel-api

# Step 6: Verify system health
curl http://sentinel-api/health/ready
```

**Prevention**: Never deploy schema migrations with application code. Use separate migration jobs.

### Case 2: Configuration Drift (env vars, secrets changed)

**Problem**: Environment variables or secrets modified outside Helm

```bash
# Step 1: Export current ConfigMap/Secrets for comparison
kubectl get configmap sentinel-config -o yaml > /tmp/configmap-current.yaml
kubectl get secret sentinel-secrets -o yaml > /tmp/secrets-current.yaml

# Step 2: Restore from Git (assuming IaC tracked)
kubectl apply -f k8s/base/configmap.yaml
kubectl apply -f k8s/base/secrets.yaml

# Step 3: Restart deployments to pick up changes
kubectl rollout restart deployment/sentinel-api
kubectl rollout restart deployment/sentinel-worker

# Step 4: Verify health
curl http://sentinel-api/health/ready
```

### Case 3: Kafka Topic Misconfiguration

**Problem**: New deployment changed Kafka topic configuration (partitions, retention)

```bash
# Step 1: Identify topic changes
kubectl exec -it sentinel-kafka-0 -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --topic intents.inbound

# Step 2: Restore original partition count (if increased)
# WARNING: Cannot decrease partitions, only increase
# If partitions increased, consumers must be restarted

# Step 3: Restore retention policy
kubectl exec -it sentinel-kafka-0 -- kafka-configs.sh \
  --bootstrap-server localhost:9092 \
  --entity-type topics \
  --entity-name intents.inbound \
  --alter \
  --add-config retention.ms=604800000  # 7 days

# Step 4: Restart consumers
kubectl rollout restart deployment/sentinel-worker
kubectl rollout restart deployment/sentinel-audit
```

### Case 4: ML Model Rollback

**Problem**: New ML model version causes poor decisions or performance regression

```bash
# Step 1: Identify current model version
kubectl exec -it sentinel-worker-xxxx -- \
  python -c "import mlflow; print(mlflow.get_model_version('sentinel_xgboost', 'latest'))"

# Step 2: Roll back to previous model version in MLflow
# Option A: Promote previous version to "Production" stage
mlflow models update-model-version \
  --name sentinel_xgboost \
  --version 42 \
  --stage Production

# Option B: Set environment variable to use specific version
kubectl set env deployment/sentinel-worker \
  MLFLOW_MODEL_VERSION=42

# Step 3: Restart workers to reload model
kubectl rollout restart deployment/sentinel-worker

# Step 4: Verify model version loaded
kubectl logs -l component=worker --tail=50 | grep "Loading model"

# Step 5: Monitor decision quality
# Check metrics: sentinel_decisions_total, sentinel_risk_score
curl -s http://sentinel-worker:8001/metrics | grep -E "(decisions|risk_score)"
```

---

## Verification After Rollback

```bash
# 1. Health checks
curl http://sentinel-api/health/ready
curl http://sentinel-api/health/live
curl http://sentinel-api/health/circuit-breakers

# 2. Functional smoke test
curl -X POST http://sentinel-api/v1/intents \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "smoke-test-agent",
    "action_type": "refund",
    "amount": 1000,
    "currency": "INR",
    "recipient": "test@example.com",
    "context": {"velocity_1h": 1}
  }'

# Expected: decision in [ALLOW, DENY, ESCALATE] with valid capability_token

# 3. Performance verification
# p99 latency should return to baseline
curl -s http://sentinel-api/metrics | grep sentinel_evaluation_latency_seconds

# 4. Error rate check
# Should be < 0.1%
curl -s http://sentinel-api/metrics | grep sentinel_errors_total

# 5. Audit trail verification
# All decisions should be logged
kubectl exec -it sentinel-postgres-0 -- psql -U sentinel -c \
  "SELECT COUNT(*) FROM audit_log WHERE timestamp > NOW() - INTERVAL '5 minutes';"
```

---

## Prevention

### Pre-Deployment Checklist
- [ ] Load test in staging environment (1000 RPS for 10 minutes)
- [ ] Run security test suite (ensure fail-closed behavior)
- [ ] Verify no database schema changes (or separate migration job)
- [ ] Document rollback plan in deployment ticket
- [ ] Tag release in Git for easy rollback reference

### Deployment Best Practices
- **Blue-Green Deployment**: Run new version alongside old, switch traffic gradually
- **Canary Deployment**: Deploy to 10% of pods, monitor, then full rollout
- **Feature Flags**: Enable new features gradually via config, not deployment

### Monitoring During Deployment
```bash
# Watch key metrics during deployment
watch -n 2 'curl -s http://sentinel-api/metrics | grep -E "(decisions|latency|errors)"'

# Monitor error logs
kubectl logs -l component=api --tail=100 -f | grep -i error

# Check decision distribution
curl -s http://sentinel-api/metrics | grep sentinel_decisions_total
```

---

## Post-Rollback

### Immediate Actions
- [ ] Announce rollback to team (Slack, incident channel)
- [ ] Update deployment status page (if public-facing)
- [ ] Schedule post-mortem meeting (within 24 hours)

### Post-Mortem Questions
1. What triggered the rollback?
2. How was the issue detected? (monitoring, user report, manual testing)
3. What was the root cause?
4. How long was service degraded?
5. How many users were impacted?
6. What prevented this from being caught in staging?
7. What can be automated to prevent similar issues?

### Follow-Up Action Items
- [ ] Fix root cause in development
- [ ] Add test coverage for failure mode
- [ ] Update deployment checklist
- [ ] Improve monitoring/alerting if issue wasn't auto-detected
- [ ] Re-deploy fix with proper validation

---

## Escalation

| Time Since Incident | Action |
|---------------------|--------|
| T+0 | On-call engineer initiates rollback |
| T+10 min | Notify team lead of rollback in progress |
| T+30 min | If rollback unsuccessful, escalate to engineering director |
| T+1 hour | If still unresolved, engage incident commander + all hands |

---

## Related Runbooks
- [High Latency](high-latency.md) - Performance regression diagnosis
- [Security Invariant](security-invariant.md) - Security issue response
- [Redis Outage](redis-outage.md) - Redis dependency failure
- [Kafka Consumer Lag](kafka-consumer-lag.md) - Worker scaling issues
