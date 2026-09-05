# Sentinel Helm Chart

Production-ready Helm chart for deploying Sentinel ML-powered authorization gateway on Kubernetes.

## Overview

This Helm chart deploys a complete Sentinel stack with:
- **API Service**: REST API for authorization requests (3-10 replicas with HPA)
- **Worker Service**: ML evaluation workers (5-20 replicas with HPA)
- **Audit Service**: Audit trail consumer (2 replicas)
- **Redis**: Idempotency and rate limiting (with Sentinel failover)
- **Kafka**: Event streaming (3 brokers with 4 partitions)
- **PostgreSQL**: Persistent storage (with read replicas)
- **MLflow**: Model registry and tracking
- **Observability**: Prometheus, Jaeger, Grafana integration

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PersistentVolume provisioner support
- 16 CPU cores and 32GB RAM minimum for production

## Installation

### 1. Add Helm Dependencies (Optional)

If using external charts for Redis, Kafka, PostgreSQL:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm dependency update ./helm/sentinel
```

### 2. Create Secrets

**IMPORTANT**: Never commit secrets to version control. Use external secret management.

```bash
# Create secrets using kubectl
kubectl create namespace sentinel

kubectl create secret generic sentinel-secrets \
  --from-literal=database-url='postgresql://sentinel:PASSWORD@postgres:5432/sentinel' \
  --from-literal=redis-url='redis://:PASSWORD@redis-master:6379/0' \
  --from-literal=capability-signing-key='GENERATE_STRONG_KEY_MIN_32_CHARS' \
  --from-literal=api-key='GENERATE_STRONG_KEY_MIN_32_CHARS' \
  --from-literal=admin-api-key='GENERATE_STRONG_KEY_MIN_32_CHARS' \
  --from-literal=redis-password='REDIS_PASSWORD' \
  --from-literal=postgres-admin-password='POSTGRES_ADMIN_PASSWORD' \
  --from-literal=postgres-password='POSTGRES_USER_PASSWORD' \
  -n sentinel
```

**Recommended**: Use [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) or [external-secrets](https://external-secrets.io/) in production.

### 3. Install the Chart

```bash
# Install with default values
helm install sentinel ./helm/sentinel -n sentinel --create-namespace

# Install with custom values
helm install sentinel ./helm/sentinel -n sentinel \
  --set api.replicaCount=5 \
  --set worker.replicaCount=10 \
  --set global.environment=production
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -n sentinel

# Check services
kubectl get svc -n sentinel

# Check health endpoints
kubectl port-forward svc/sentinel-api 8000:80 -n sentinel
curl http://localhost:8000/health/ready
```

## Configuration

### values.yaml Structure

Key configuration sections:

```yaml
global:
  environment: production          # Environment name
  imageRegistry: docker.io        # Container registry

api:
  replicaCount: 3                 # Initial replica count
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70

worker:
  replicaCount: 5
  maxConcurrentTasks: 32          # Tasks per worker
  inferenceBackend: cpu           # cpu or gpu
  xgbNThread: "4"                 # XGBoost threads
```

### Common Customizations

#### Scale for High Traffic

```bash
helm upgrade sentinel ./helm/sentinel \
  --set api.autoscaling.maxReplicas=20 \
  --set worker.autoscaling.maxReplicas=40 \
  --set kafka.topics[0].partitions=8
```

#### Enable GPU Inference

```bash
helm upgrade sentinel ./helm/sentinel \
  --set worker.inferenceBackend=gpu \
  --set worker.resources.limits.nvidia.com/gpu=1
```

#### Increase Database Pool

```bash
helm upgrade sentinel ./helm/sentinel \
  --set configMap.data.DB_POOL_SIZE=200 \
  --set configMap.data.DB_MAX_OVERFLOW=100
```

## Production Checklist

- [ ] Secrets managed via external secret operator (not Helm)
- [ ] Resource requests/limits tuned for workload
- [ ] HPA enabled with appropriate thresholds
- [ ] Redis Sentinel enabled for HA
- [ ] Kafka replication factor = 3
- [ ] PostgreSQL read replicas enabled
- [ ] Persistent volumes configured with backups
- [ ] Network policies enabled
- [ ] Prometheus scraping configured
- [ ] Alerting rules deployed
- [ ] Runbooks reviewed and accessible

## Monitoring

### Prometheus Metrics

Metrics are exposed on:
- API: `http://sentinel-api:8000/metrics`
- Worker: `http://sentinel-worker:8001/metrics`
- Audit: `http://sentinel-audit:8002/metrics`

Key metrics:
- `sentinel_decisions_total` - Decision count by type
- `sentinel_evaluation_latency_seconds` - Evaluation latency histogram
- `sentinel_redis_breaker_state` - Circuit breaker status
- `sentinel_worker_active_tasks` - Worker utilization

### Grafana Dashboards

Import pre-built dashboards from `observability/grafana/dashboards/`:
- Sentinel Overview
- Worker Performance
- Kafka Consumer Lag
- Circuit Breaker Status

## Troubleshooting

### Pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs -l component=api -n sentinel --tail=100

# Common causes:
# - Secrets not created
# - Database connection failed
# - Redis/Kafka not ready

# Solution: Verify secrets and wait for dependencies
kubectl get secret sentinel-secrets -n sentinel
kubectl get pods -l app.kubernetes.io/name=redis -n sentinel
```

### High Latency

See [High Latency Runbook](../../docs/runbooks/high-latency.md)

```bash
# Quick diagnosis
kubectl top pods -n sentinel
curl http://sentinel-api:8000/metrics | grep latency
```

### Redis Circuit Breaker Open

See [Redis Outage Runbook](../../docs/runbooks/redis-outage.md)

```bash
# Check circuit breaker status
curl http://sentinel-api:8000/health/circuit-breakers

# Check Redis health
kubectl exec -it redis-master-0 -n sentinel -- redis-cli ping
```

## Upgrading

```bash
# Upgrade to new chart version
helm upgrade sentinel ./helm/sentinel -n sentinel

# Rollback if issues occur
helm rollback sentinel -n sentinel
```

See [Deployment Rollback Runbook](../../docs/runbooks/deployment-rollback.md) for detailed procedures.

## Uninstallation

```bash
# Uninstall chart
helm uninstall sentinel -n sentinel

# Optional: Delete PVCs (data loss!)
kubectl delete pvc -l app=sentinel -n sentinel

# Delete namespace
kubectl delete namespace sentinel
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Sentinel API (3-10 replicas, HPA)              │
│  • Authorization requests                                    │
│  • Health checks                                             │
│  • Circuit breaker protection                                │
└─────────┬───────────────────────────────┬───────────────────┘
          │                               │
          ▼                               ▼
┌──────────────────────┐      ┌─────────────────────────────┐
│    Redis Cluster     │      │      Kafka Cluster          │
│  • Idempotency       │      │  • Event streaming          │
│  • Rate limiting     │      │  • intents.inbound          │
│  • Redis Sentinel HA │      │  • intents.evaluated        │
└──────────────────────┘      └──────────┬──────────────────┘
                                         │
                                         ▼
                            ┌────────────────────────────────┐
                            │ Worker (5-20 replicas, HPA)    │
                            │ • ML evaluation                │
                            │ • Feature extraction           │
                            │ • Policy decisions             │
                            └────────┬───────────────────────┘
                                     │
                                     ▼
                        ┌────────────────────────────────────┐
                        │     PostgreSQL (with replicas)     │
                        │  • Audit trail                     │
                        │  • Persistent storage              │
                        └────────────────────────────────────┘
```

## Support

For issues and questions:
- GitHub Issues: [sentinel-razorpay-buildathon/issues](https://github.com/sentinel/issues)
- Runbooks: `docs/runbooks/`
- Team: sentinel@razorpay.com

## License

Proprietary - Razorpay Buildathon 2026
