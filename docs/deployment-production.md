# Sentinel Production Deployment Guide

## Overview

This guide covers deploying Sentinel to production environments. Sentinel is designed for fail-closed operation and requires careful infrastructure setup.

## Prerequisites

- Docker & Docker Compose (20.10+)
- Kubernetes cluster (optional, for k8s deployment)
- PostgreSQL 15+
- Redis 7+
- Kafka/Redpanda
- Razorpay API keys (test or live)

---

## Environment Configuration

### Required Environment Variables

```bash
# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
JSON_LOGS=true

# Database
DATABASE_URL=postgresql://sentinel:PASSWORD@postgres:5432/sentinel_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0

# Kafka/Redpanda
KAFKA_BROKER=redpanda:29092
KAFKA_INBOUND_TOPIC=intents.inbound
KAFKA_EVALUATED_TOPIC=intents.evaluated

# Security
CAPABILITY_SIGNING_KEY=<GENERATE_STRONG_SECRET>

# Razorpay Integration
EXECUTION_MODE=razorpay
RAZORPAY_PROVIDER=direct          # or 'mcp'
RAZORPAY_KEY_ID=rzp_live_XXX     # Use rzp_test_XXX for test mode
RAZORPAY_KEY_SECRET=<SECRET>
RAZORPAY_ENVIRONMENT=live         # or 'test'

# Worker Configuration
INFERENCE_BACKEND=cpu
MAX_CONCURRENT_TASKS=4
XGB_NTHREAD=8

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=sentinel-api
METRICS_PORT=8001

# CORS (for frontend)
CORS_ORIGINS=https://sentinel.yourdomain.com

# Idempotency & Security
IDEMPOTENCY_TTL_SECONDS=86400
BEHAVIORAL_WINDOW_SECONDS=5
```

### Generating Secrets

```bash
# Capability signing key (32+ bytes)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using openssl
openssl rand -base64 32
```

---

## Docker Compose Deployment

### 1. Prepare Configuration

```bash
# Clone repository
git clone https://github.com/yourusername/sentinel.git
cd sentinel

# Copy environment template
cp .env.example .env

# Edit .env with production values
nano .env
```

### 2. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Run Database Migrations

```bash
docker-compose exec sentinel-api alembic upgrade head
```

### 4. Verify Deployment

```bash
# Check health endpoints
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/dependencies

# Check metrics
curl http://localhost:8000/metrics
```

---

## Kubernetes Deployment

### Namespace Setup

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sentinel
```

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sentinel-config
  namespace: sentinel
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  KAFKA_INBOUND_TOPIC: "intents.inbound"
  KAFKA_EVALUATED_TOPIC: "intents.evaluated"
  # ... add other non-secret configs
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sentinel-secrets
  namespace: sentinel
type: Opaque
stringData:
  DATABASE_URL: "postgresql://sentinel:PASSWORD@postgres:5432/sentinel_db"
  REDIS_URL: "redis://redis:6379/0"
  CAPABILITY_SIGNING_KEY: "<YOUR_SECRET>"
  RAZORPAY_KEY_ID: "rzp_live_XXX"
  RAZORPAY_KEY_SECRET: "<SECRET>"
```

### API Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinel-api
  namespace: sentinel
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentinel-api
  template:
    metadata:
      labels:
        app: sentinel-api
    spec:
      containers:
      - name: api
        image: sentinel:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: sentinel-config
        - secretRef:
            name: sentinel-secrets
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

### Service & Ingress

```yaml
apiVersion: v1
kind: Service
metadata:
  name: sentinel-api
  namespace: sentinel
spec:
  selector:
    app: sentinel-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sentinel-ingress
  namespace: sentinel
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - sentinel.yourdomain.com
    secretName: sentinel-tls
  rules:
  - host: sentinel.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sentinel-api
            port:
              number: 80
```

---

## Infrastructure Dependencies

### PostgreSQL

```bash
# Using managed service (recommended)
# - AWS RDS
# - Google Cloud SQL
# - Azure Database for PostgreSQL

# Connection pooling recommended (pgbouncer)
# Enable SSL/TLS for connections
```

### Redis

```bash
# Using managed service (recommended)
# - AWS ElastiCache
# - Google Cloud Memorystore
# - Azure Cache for Redis

# Enable persistence (AOF + RDB)
# Configure maxmemory-policy: allkeys-lru
```

### Kafka/Redpanda

```bash
# Redpanda (Kafka-compatible, easier to operate)
# https://redpanda.com/

# Or AWS MSK, Confluent Cloud
# Configure retention: 7 days
# Enable replication factor: 3 (production)
```

---

## Security Hardening

### 1. Network Security

- Enable TLS for all external connections
- Use VPC/private networking for inter-service communication
- Firewall rules: Allow only necessary ports
- Use secrets manager (AWS Secrets Manager, Vault, etc.)

### 2. Authentication & Authorization

- Rotate Razorpay API keys regularly
- Use separate keys for test/live environments
- Implement API rate limiting (nginx, cloudflare)
- Enable audit logging for all admin actions

### 3. Database Security

- Use strong passwords (32+ characters)
- Enable SSL/TLS for database connections
- Regular backups (automated, encrypted)
- Test restore procedures quarterly

### 4. Monitoring & Alerts

```yaml
# Critical alerts
- Readiness probe failures
- Error rate > 1%
- p99 latency > 100ms
- Redis connection failures
- Kafka consumer lag > 1000
- Database connection pool exhaustion
```

---

## Observability Setup

### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sentinel-api'
    static_configs:
      - targets: ['sentinel-api:8000']
    metrics_path: '/metrics'

  - job_name: 'sentinel-worker'
    static_configs:
      - targets: ['sentinel-worker:8001']
```

### Grafana Dashboards

Import pre-built dashboard:
- `grafana/provisioning/dashboards/sentinel_overview.json`

Key metrics to monitor:
- Request rate (QPS)
- Authorization latency (p50, p95, p99)
- Decision distribution (ALLOW/ESCALATE/CONTAIN)
- Redis hit rate
- Kafka consumer lag
- Database query time

### Jaeger Tracing

```yaml
# Enable distributed tracing
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=sentinel-api

# Sampling strategy
OTEL_TRACES_SAMPLER=traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Secrets generated and stored securely
- [ ] Database migrations tested
- [ ] Razorpay API keys validated (test mode first)
- [ ] SSL certificates configured
- [ ] DNS records updated
- [ ] Backup strategy in place

### Deployment

- [ ] Deploy infrastructure (DB, Redis, Kafka)
- [ ] Run database migrations
- [ ] Deploy API service (blue-green recommended)
- [ ] Deploy worker service
- [ ] Deploy audit consumer
- [ ] Verify health checks pass
- [ ] Run smoke tests

### Post-Deployment

- [ ] Monitor error rates (< 0.1% expected)
- [ ] Verify Prometheus metrics
- [ ] Check Grafana dashboards
- [ ] Test fail-closed behavior (Redis down → ESCALATE)
- [ ] Verify audit chain integrity
- [ ] Load test (run `scripts/run_load_tests.sh`)

---

## Scaling Guidelines

### API Service

```yaml
# Horizontal scaling (recommended)
replicas: 3-10 (based on traffic)

# CPU-bound: ML inference
cpu_requests: 500m
cpu_limits: 1000m

# Memory: Model + request buffer
memory_requests: 512Mi
memory_limits: 1Gi
```

### Worker Service

```yaml
# Scale based on Kafka consumer lag
replicas: 2-5

# GPU optional (10x faster inference)
# If using GPU:
resources:
  limits:
    nvidia.com/gpu: 1
```

### Performance Targets

- **Latency**: p99 < 30ms (API path)
- **Throughput**: 300+ RPS per API pod (CPU)
- **Throughput**: 3000+ RPS per API pod (GPU)
- **Availability**: 99.9% (three nines)

---

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
pg_dump -h postgres -U sentinel sentinel_db | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip < backup_20260829.sql.gz | psql -h postgres -U sentinel sentinel_db
```

### Audit Chain Verification

```bash
# Verify cryptographic audit chain
curl http://localhost:8000/audit/verify

# Expected: {"status": "PASS", "records_checked": N, "invalid_record_ids": []}
```

### Disaster Recovery

1. **RPO (Recovery Point Objective)**: < 5 minutes
   - Kafka retention: 7 days
   - Database backups: Every 6 hours
   - Redis persistence: AOF + RDB

2. **RTO (Recovery Time Objective)**: < 30 minutes
   - Automated failover for managed services
   - Blue-green deployment for zero-downtime updates

---

## Rollback Procedure

```bash
# Docker Compose
docker-compose down
git checkout <previous-tag>
docker-compose up -d

# Kubernetes
kubectl rollout undo deployment/sentinel-api -n sentinel
kubectl rollout status deployment/sentinel-api -n sentinel
```

---

## Support & Monitoring

### Health Check URLs

- **Liveness**: `GET /health/live` (200 = alive)
- **Readiness**: `GET /health/ready` (200 = ready, 503 = not ready)
- **Dependencies**: `GET /health/dependencies` (diagnostic)

### Log Aggregation

- Enable structured JSON logging
- Ship to ELK, Datadog, or CloudWatch
- Alert on ERROR/CRITICAL logs

### Incident Response

1. Check `/health/dependencies` for degraded services
2. Review Grafana dashboards
3. Check Kafka consumer lag
4. Verify Redis connectivity
5. Review recent deployments/changes

---

## Production Razorpay Integration

### Test Mode (Recommended First)

```bash
RAZORPAY_ENVIRONMENT=test
RAZORPAY_KEY_ID=rzp_test_XXX
RAZORPAY_KEY_SECRET=<test_secret>
```

### Live Mode

```bash
RAZORPAY_ENVIRONMENT=live
RAZORPAY_KEY_ID=rzp_live_XXX
RAZORPAY_KEY_SECRET=<live_secret>
```

### Razorpay Webhooks (Optional)

Configure webhook for payment confirmations:

```python
# POST /webhooks/razorpay
# Verify signature, update audit log
```

---

## Cost Optimization

1. **Use managed services** (reduces operational overhead)
2. **Right-size resources** (start small, scale up)
3. **Enable autoscaling** (HPA in Kubernetes)
4. **Use spot instances** for non-critical workloads
5. **Compress logs** before shipping
6. **Cache static assets** (CDN for frontend)

---

## Compliance & Audit

- All decisions are cryptographically auditable
- Immutable audit trail in PostgreSQL
- Capability tokens include full context
- No financial action without valid token
- Fail-closed guarantee on all error paths

---

## Getting Help

- **Documentation**: `/docs` in repository
- **Issues**: GitHub Issues
- **Security**: security@yourdomain.com (private disclosure)

---

**Deployment Date**: YYYY-MM-DD  
**Version**: v1.0.0  
**Deployed By**: DevOps Team  
**Next Review**: YYYY-MM-DD
