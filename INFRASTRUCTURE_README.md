# Sentinel Production Infrastructure

**Complete AWS + Kubernetes infrastructure for production-grade deployment of Sentinel.**

---

## 📁 Repository Structure

```
sentinel-razorpay-buildathon/
├── terraform/                      # AWS Infrastructure as Code
│   ├── main.tf                    # Root module
│   ├── variables.tf               # Input variables
│   ├── outputs.tf                 # Terraform outputs
│   └── modules/
│       ├── vpc/                   # VPC with 3 AZs, public/private/database subnets
│       ├── eks/                   # EKS cluster, node groups, IRSA
│       ├── rds/                   # PostgreSQL Multi-AZ with automated backups
│       ├── elasticache/           # Redis cluster with automatic failover
│       ├── msk/                   # Kafka cluster with 3 brokers
│       └── ecr/                   # Container registries
│
├── .github/workflows/             # CI/CD Pipelines
│   ├── ci.yml                    # Lint, test, security scan, build
│   ├── cd.yml                    # Deploy to EKS production
│   └── terraform.yml             # Infrastructure changes
│
├── k8s/                          # Kubernetes Manifests
│   ├── base/                     # Base deployments (api, worker, audit)
│   └── production/
│       ├── kustomization.yaml    # Kustomize overlay
│       ├── network-policy.yaml   # Zero-trust network segmentation
│       ├── monitoring.yaml       # Prometheus ServiceMonitors + alerts
│       └── patches/              # Production-specific patches
│
├── helm/sentinel/                # Helm Chart
│   ├── Chart.yaml
│   ├── values.yaml               # Default values
│   └── templates/                # K8s resource templates
│
├── docker/                       # Multi-stage Dockerfiles
│   ├── Dockerfile.api            # FastAPI application
│   ├── Dockerfile.worker         # Kafka consumer workers
│   └── Dockerfile.audit          # Audit trail verifier
│
├── monitoring/                   # Observability Stack
│   ├── prometheus/
│   │   └── values.yaml          # Prometheus + AlertManager config
│   └── grafana/
│       └── dashboards/          # Pre-built Sentinel dashboards
│
├── security/                     # Security Hardening
│   ├── secrets-management.yaml   # AWS Secrets Manager integration
│   ├── pod-security-policy.yaml  # Restricted PSP
│   └── SECURITY_CHECKLIST.md     # Pre/post-deployment checklist
│
├── scripts/                      # Deployment Scripts
│   ├── deploy.sh                # One-command production deploy
│   ├── rollback.sh              # Emergency rollback
│   └── security-validator.sh    # Pre-deployment security scan
│
└── docs/deployment/              # Deployment Guides
    ├── TERRAFORM_GUIDE.md       # Infrastructure setup walkthrough
    ├── CI_CD_GUIDE.md           # Pipeline configuration
    └── MONITORING_GUIDE.md      # Observability setup
```

---

## 🚀 Quick Start (0 to Production in 45 minutes)

### Prerequisites

- **AWS Account** with admin access
- **Tools installed**: `terraform`, `kubectl`, `helm`, `aws-cli`, `docker`
- **GitHub repo** with Actions enabled

### Phase 1: Deploy AWS Infrastructure (25-35 min)

```bash
# 1. Create Terraform state backend
cd terraform
aws s3api create-bucket --bucket sentinel-terraform-state --region us-east-1
aws dynamodb create-table --table-name sentinel-terraform-locks \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST

# 2. Initialize and apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan
# ☕ Wait 25-35 minutes for EKS, RDS, MSK, ElastiCache

# 3. Save outputs
terraform output > ../infrastructure-outputs.txt
```

### Phase 2: Configure Kubernetes (5 min)

```bash
# 1. Update kubeconfig
aws eks update-kubeconfig --name sentinel-production --region us-east-1

# 2. Install core add-ons
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
    -n kube-system --set clusterName=sentinel-production

# 3. Install monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
    -n monitoring --create-namespace -f monitoring/prometheus/values.yaml
```

### Phase 3: Deploy Application (5 min)

```bash
# 1. Run security validation
./scripts/security-validator.sh

# 2. Deploy Sentinel
./scripts/deploy.sh production

# 3. Verify
kubectl get pods -n sentinel
kubectl logs -f deployment/sentinel-api -n sentinel
```

**Total Time**: ~45 minutes to full production deployment

---

## 🏗️ Architecture

### AWS Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                         VPC (10.0.0.0/16)                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Public      │  │  Public      │  │  Public      │      │
│  │  Subnet AZ-1 │  │  Subnet AZ-2 │  │  Subnet AZ-3 │      │
│  │  NAT Gateway │  │  NAT Gateway │  │  NAT Gateway │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │  Private     │  │  Private     │  │  Private     │      │
│  │  Subnet AZ-1 │  │  Subnet AZ-2 │  │  Subnet AZ-3 │      │
│  │  EKS Nodes   │  │  EKS Nodes   │  │  EKS Nodes   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐      │
│  │  Database    │  │  Database    │  │  Database    │      │
│  │  Subnet AZ-1 │  │  Subnet AZ-2 │  │  Subnet AZ-3 │      │
│  │ RDS/Redis    │  │ RDS/Redis    │  │  MSK Kafka   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Kubernetes Workloads

```
┌─────────────────────────────────────────────────────────────┐
│                     EKS Cluster                              │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Namespace: sentinel                                 │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ sentinel-api │  │sentinel-worker│ │sentinel- │  │   │
│  │  │              │  │               │  │audit     │  │   │
│  │  │ Replicas: 3-10│ │ Replicas: 5-20│ │Replicas:2│  │   │
│  │  │ HPA enabled  │  │ HPA enabled   │  │          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  │                                                       │   │
│  │  Network Policies: deny-all default, explicit allow  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Namespace: monitoring                               │   │
│  │                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ Prometheus   │  │ AlertManager │  │ Grafana  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 💰 Cost Breakdown

**Monthly AWS costs** (us-east-1, production):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| **EKS Control Plane** | 1 cluster | $73 |
| **EC2 Instances** | 3× t3.xlarge (on-demand) | ~$450 |
| **RDS PostgreSQL** | db.r6g.xlarge Multi-AZ | ~$550 |
| **ElastiCache Redis** | 3× cache.r6g.large | ~$450 |
| **MSK Kafka** | 3× kafka.m5.large | ~$540 |
| **NAT Gateway** | 3× (one per AZ) | ~$100 |
| **Application Load Balancer** | 1× ALB | ~$25 |
| **Data Transfer** | ~1TB egress | ~$90 |
| **CloudWatch Logs** | ~50GB/month | ~$25 |
| **Secrets Manager** | 5 secrets | ~$2 |
| **ECR Storage** | ~20GB images | ~$2 |
| **S3** | Terraform state | <$1 |
| **TOTAL** | | **~$2,308/month** |

**Cost Optimization Options:**

1. **Use Spot Instances** for worker nodes: Save ~60% on EC2 ($450 → $180)
2. **Reserved Instances** (1-year): Save ~30% on RDS/ElastiCache (~$300/month)
3. **Smaller MSK instances** (kafka.t3.small): $540 → $75
4. **Single NAT Gateway**: $100 → $33 (reduces HA)

**Optimized Monthly Cost**: ~$1,100-1,400

---

## 🔒 Security Features

### Infrastructure-Level

- ✅ **VPC Isolation**: Private subnets for workloads, no direct internet access
- ✅ **Encryption at Rest**: KMS keys for RDS, ElastiCache, MSK, EBS volumes
- ✅ **Encryption in Transit**: TLS 1.3 for all inter-service communication
- ✅ **Secrets Management**: AWS Secrets Manager + IRSA (no secrets in code)
- ✅ **IAM Least Privilege**: Separate roles for API, workers, audit
- ✅ **VPC Flow Logs**: Audit trail for network traffic
- ✅ **GuardDuty**: Threat detection enabled
- ✅ **AWS Config**: Compliance monitoring

### Application-Level

- ✅ **API Authentication**: HMAC-SHA256 API keys (timing-safe comparison)
- ✅ **Rate Limiting**: Redis token bucket, 100 req/60s default
- ✅ **Input Validation**: Pydantic schemas on all endpoints
- ✅ **Circuit Breakers**: Fail-closed on Redis/Kafka/DB/MLflow failure
- ✅ **Audit Logging**: Tamper-proof cryptographic audit chain
- ✅ **Capability Tokens**: 5-second TTL, JTI replay protection

### Kubernetes-Level

- ✅ **Pod Security Policy**: Non-root user, read-only root FS, dropped capabilities
- ✅ **Network Policies**: Zero-trust segmentation (deny-all default)
- ✅ **RBAC**: Minimal service account permissions
- ✅ **Image Scanning**: Trivy scans on ECR push
- ✅ **Resource Limits**: CPU/memory limits prevent noisy neighbor issues

---

## 📊 Monitoring & Observability

### Metrics (Prometheus)

**Application metrics** exposed at `/metrics`:

- `http_requests_total` - Request rate by endpoint/status
- `http_request_duration_seconds` - Latency histogram
- `policy_evaluations_total` - Policy decisions (allow/block/restrict)
- `kafka_consumer_lag` - Worker backlog
- `circuit_breaker_state` - External dependency health

**Query examples:**

```promql
# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Kafka lag alert
kafka_consumer_lag > 10000
```

### Dashboards (Grafana)

**Pre-built dashboards** in `monitoring/grafana/dashboards/`:

1. **Sentinel Overview** - Request rate, error rate, latency, Kafka lag
2. **Kubernetes Cluster** - Node resources, pod status, PVs
3. **Application Performance** - API endpoint breakdown, DB queries

**Access Grafana:**

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open http://localhost:3000
# Credentials: admin / prom-operator
```

### Alerts (AlertManager)

**Critical alerts** → **PagerDuty**  
**Warning alerts** → **Slack**

| Alert | Threshold | Action |
|-------|-----------|--------|
| HighErrorRate | >5% for 5min | Page oncall |
| HighLatency | P95 >2s for 5min | Slack alert |
| KafkaConsumerLag | >10K for 10min | Scale workers |
| PodCrashLooping | Restarts for 15min | Page oncall |

---

## 🔄 CI/CD Pipeline

### CI Pipeline (`.github/workflows/ci.yml`)

**Triggers**: Push/PR to `main` or `develop`

**Stages:**

1. **Lint & Test**
   - `black --check .` (code formatting)
   - `ruff check .` (linting)
   - `mypy api/ core/` (type checking)
   - `pytest tests/ --cov` (unit + integration tests)

2. **Security Scan**
   - Trivy vulnerability scanner
   - Bandit security linter

3. **Build & Push**
   - Build Docker images (api, worker, audit)
   - Push to ECR with tags: `<git-sha>`, `latest`

### CD Pipeline (`.github/workflows/cd.yml`)

**Triggers**: Push to `main` (auto-deploy)

**Stages:**

1. **Deploy to EKS**
   - `helm upgrade --install sentinel`
   - Rolling update (max surge: 1, max unavailable: 0)

2. **Verify**
   - `kubectl rollout status`
   - Health check: `curl /health/live`

3. **Notify**
   - Slack notification with deployment status

**Rollback on failure**: Automatic via Helm

**Manual rollback:**

```bash
./scripts/rollback.sh [revision-number]
```

---

## 📘 Documentation

| Guide | Description |
|-------|-------------|
| [TERRAFORM_GUIDE.md](docs/deployment/TERRAFORM_GUIDE.md) | Infrastructure setup, cost estimates, troubleshooting |
| [CI_CD_GUIDE.md](docs/deployment/CI_CD_GUIDE.md) | Pipeline configuration, secrets setup, best practices |
| [MONITORING_GUIDE.md](docs/observability/MONITORING_GUIDE.md) | Metrics, dashboards, alerts, logging |
| [SECURITY_CHECKLIST.md](security/SECURITY_CHECKLIST.md) | Pre/post-deployment security validation |
| [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) | Complete production deployment guide |

---

## 🛠️ Deployment Scripts

```bash
# Deploy to production
./scripts/deploy.sh production

# Rollback to previous version
./scripts/rollback.sh

# Run security validation
./scripts/security-validator.sh
```

---

## 🔥 Troubleshooting

### EKS Nodes Not Joining Cluster

```bash
# Check node IAM role
aws iam get-role --role-name sentinel-production-eks-node-role

# Check security groups
aws eks describe-cluster --name sentinel-production --query cluster.resourcesVpcConfig.securityGroupIds
```

### RDS Connection Timeout

```bash
# Verify security group allows EKS nodes
aws ec2 describe-security-groups --filters Name=tag:Name,Values=sentinel-production-rds-sg
```

### Helm Deployment Timeout

```bash
# Check pod status
kubectl get pods -n sentinel
kubectl describe pod <pod-name> -n sentinel
kubectl logs <pod-name> -n sentinel
```

### High Kafka Consumer Lag

```bash
# Scale up workers
kubectl scale deployment sentinel-worker -n sentinel --replicas=10

# Check worker logs
kubectl logs -f deployment/sentinel-worker -n sentinel
```

---

## 🚨 Emergency Procedures

### Incident Response

1. **Check dashboards**: Grafana → Sentinel Overview
2. **Check alerts**: AlertManager console
3. **Check logs**: CloudWatch Logs or `kubectl logs`
4. **Rollback if needed**: `./scripts/rollback.sh`

### Disaster Recovery

**RDS Backup Restoration:**

```bash
aws rds restore-db-instance-from-db-snapshot \
    --db-instance-identifier sentinel-production-restored \
    --db-snapshot-identifier <snapshot-id>
```

**Redis Snapshot Restoration:**

```bash
aws elasticache create-replication-group \
    --replication-group-id sentinel-production-restored \
    --snapshot-name <snapshot-name>
```

---

## 📈 Scaling

### Horizontal Pod Autoscaler (HPA)

**Already configured** for API and workers:

```yaml
# API: 3-10 replicas (target CPU: 70%)
# Worker: 5-20 replicas (target CPU: 70%)
```

**Manual scaling:**

```bash
kubectl scale deployment sentinel-api -n sentinel --replicas=5
```

### Cluster Autoscaler

**Installed** with Helm:

```bash
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
    --namespace kube-system \
    --set autoDiscovery.clusterName=sentinel-production
```

Auto-scales EKS node group (2-10 nodes).

---

## 🎯 Capacity Planning

**Current Capacity:**

- **API**: 3-10 pods × 4 workers = 12-40 concurrent requests
- **Workers**: 5-20 pods × Kafka consumers = handle 10K+ TPS
- **Database**: db.r6g.xlarge = ~5000 IOPS, 150 connections
- **Redis**: 3-node cluster = ~50K ops/sec
- **Kafka**: 3 brokers = ~100MB/sec throughput

**Load Testing:**

```bash
# Run k6 load test
k6 run --vus 100 --duration 5m tests/load/api-load-test.js
```

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow.

---

## 📄 License

MIT License - see [LICENSE](LICENSE)

---

## 🙋 Support

- **Issues**: https://github.com/Hemakrishna7406/sentinel-razorpay-buildathon/issues
- **Security**: security@example.com
- **PagerDuty**: https://company.pagerduty.com

---

**Sentinel** - Production-grade financial agent governance at scale.  
Built for the **Razorpay AI Buildathon 2026** 🚀
