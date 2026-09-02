# Sentinel Deployment Runbook

## Quick Start

### Prerequisites
- Kubernetes cluster (1.25+)
- kubectl configured
- Helm 3.x installed
- Docker images built and pushed

### Deploy to Staging

```bash
# 1. Set context
kubectl config use-context staging

# 2. Deploy with Helm
helm upgrade --install sentinel-staging ./helm/sentinel \
  --namespace staging \
  --create-namespace \
  --values helm/sentinel/values-staging.yaml \
  --wait

# 3. Verify
kubectl get pods -n staging
kubectl logs -f deployment/sentinel-api -n staging
curl https://staging.sentinel.example.com/health/ready
```

### Deploy to Production

```bash
# 1. Set context
kubectl config use-context production

# 2. Deploy with Helm
helm upgrade --install sentinel-prod ./helm/sentinel \
  --namespace production \
  --create-namespace \
  --values helm/sentinel/values-production.yaml \
  --wait --timeout=10m

# 3. Verify
kubectl rollout status deployment/sentinel-api -n production
kubectl get pods -n production
curl https://sentinel.example.com/health/ready
```

## Rollback Procedure

### Automated Rollback

```bash
# Rollback to previous release
helm rollback sentinel-prod -n production

# Rollback to specific revision
helm history sentinel-prod -n production
helm rollback sentinel-prod 3 -n production
```

### Manual Rollback

```bash
# 1. Identify last good image
kubectl describe deployment sentinel-api -n production

# 2. Update deployment
kubectl set image deployment/sentinel-api \
  api=ghcr.io/org/sentinel:sha-abc123 \
  -n production

# 3. Monitor rollout
kubectl rollout status deployment/sentinel-api -n production
```

## Scaling

### Manual Scaling

```bash
# Scale API pods
kubectl scale deployment sentinel-api --replicas=5 -n production

# Scale worker pods
kubectl scale deployment sentinel-worker --replicas=3 -n production
```

### Verify HPA

```bash
# Check HPA status
kubectl get hpa -n production

# Describe HPA
kubectl describe hpa sentinel-api-hpa -n production
```

## Monitoring Deployment

### Check Pod Status

```bash
# List all pods
kubectl get pods -n production

# Watch pod status
kubectl get pods -n production -w

# Check pod events
kubectl describe pod <pod-name> -n production
```

### Check Logs

```bash
# Tail logs
kubectl logs -f deployment/sentinel-api -n production

# Last 100 lines
kubectl logs --tail=100 deployment/sentinel-api -n production

# Logs from specific container
kubectl logs <pod-name> -c api -n production
```

### Health Checks

```bash
# Liveness check
kubectl exec -it <pod-name> -n production -- curl localhost:8000/health/live

# Readiness check
kubectl exec -it <pod-name> -n production -- curl localhost:8000/health/ready

# Dependencies check
kubectl exec -it <pod-name> -n production -- curl localhost:8000/health/dependencies
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl get events -n production --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs <pod-name> -n production --previous

# Describe pod
kubectl describe pod <pod-name> -n production
```

**Common causes:**
- Image pull errors (check ImagePullSecrets)
- Resource limits too low
- Missing secrets/configmaps
- Health check failing too quickly

### Service Not Reachable

```bash
# Check service
kubectl get svc -n production
kubectl describe svc sentinel-api -n production

# Check endpoints
kubectl get endpoints -n production

# Check ingress
kubectl get ingress -n production
kubectl describe ingress sentinel-ingress -n production
```

### Database Connection Issues

```bash
# Check secret
kubectl get secret sentinel-secrets -n production
kubectl get secret sentinel-secrets -n production -o yaml

# Test connection from pod
kubectl exec -it <pod-name> -n production -- \
  psql $DATABASE_URL -c "SELECT 1"
```

### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n production

# Check HPA status
kubectl get hpa -n production

# Increase resources
kubectl set resources deployment sentinel-api \
  --limits=cpu=4000m,memory=4Gi \
  --requests=cpu=1000m,memory=1Gi \
  -n production
```

## Emergency Procedures

### Complete Service Outage

1. **Check infrastructure**:
   ```bash
   kubectl get nodes
   kubectl top nodes
   ```

2. **Check all pods**:
   ```bash
   kubectl get pods --all-namespaces
   ```

3. **Scale up**:
   ```bash
   kubectl scale deployment sentinel-api --replicas=10 -n production
   ```

4. **Rollback if recent deployment**:
   ```bash
   helm rollback sentinel-prod -n production
   ```

### Database Down

1. **Check database pod**:
   ```bash
   kubectl get pods -l app=postgres -n production
   kubectl logs -f <postgres-pod> -n production
   ```

2. **Restart database**:
   ```bash
   kubectl delete pod <postgres-pod> -n production
   ```

3. **Restore from backup** (if corrupted):
   ```bash
   ./scripts/backup/restore-db.sh <backup-file>
   ```

### Redis Down

1. **Check Redis pod**:
   ```bash
   kubectl get pods -l app=redis -n production
   ```

2. **Restart Redis**:
   ```bash
   kubectl delete pod <redis-pod> -n production
   ```

**Note**: API should degrade gracefully (fail-closed) when Redis is unavailable.

## Post-Deployment Verification

### Automated Checks

```bash
# Run smoke tests
kubectl apply -f k8s/tests/smoke-test.yaml -n production
kubectl logs job/smoke-test -n production

# Check metrics
curl https://sentinel.example.com/metrics

# Verify security invariants
curl https://sentinel.example.com/api/security/invariants
```

### Manual Verification

1. Open dashboard: https://sentinel.example.com
2. Run demo scenario
3. Check Security Command Center (all invariants = 0)
4. Review Grafana dashboards
5. Check Prometheus alerts

## Maintenance Windows

### Planned Maintenance

1. **Notify users** (30 min before)
2. **Enable maintenance mode** (if applicable)
3. **Perform maintenance**
4. **Verify system health**
5. **Disable maintenance mode**
6. **Notify users** (completion)

### Database Maintenance

```bash
# 1. Scale down workers
kubectl scale deployment sentinel-worker --replicas=0 -n production

# 2. Perform maintenance
kubectl exec -it <postgres-pod> -n production -- \
  psql -U sentinel -d sentinel_db -c "VACUUM FULL ANALYZE"

# 3. Scale up workers
kubectl scale deployment sentinel-worker --replicas=2 -n production
```

## Contacts

- **On-Call Engineer**: PagerDuty escalation
- **Platform Team**: platform@example.com
- **Security Team**: security@example.com
- **Razorpay Support**: support@razorpay.com

## Additional Resources

- Architecture Docs: `docs/architecture.md`
- Runbooks: `docs/runbooks/`
- Dashboards: https://grafana.example.com
- Alerts: https://prometheus.example.com
