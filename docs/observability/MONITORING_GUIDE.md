# Monitoring and Observability Guide

## Stack Overview

**Sentinel Observability Stack:**

```
┌──────────────┐
│  Prometheus  │ ← Metrics collection
└──────┬───────┘
       │
       ↓
┌──────────────┐
│   Grafana    │ ← Visualization
└──────────────┘

┌──────────────┐
│ AlertManager │ ← Alert routing
└──────┬───────┘
       │
       ├─→ Slack
       ├─→ PagerDuty
       └─→ Email
```

## Installation

### 1. Install Prometheus Stack

```bash
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts

helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  -f monitoring/prometheus/values.yaml
```

**Components Installed:**
- Prometheus Server
- Alertmanager
- Grafana
- Node Exporter
- Kube State Metrics
- Prometheus Operator

### 2. Verify Installation

```bash
kubectl get pods -n monitoring

# Expected output:
# prometheus-prometheus-node-exporter-*     1/1     Running
# prometheus-kube-state-metrics-*           1/1     Running  
# prometheus-prometheus-server-*            1/1     Running
# prometheus-alertmanager-*                 1/1     Running
# prometheus-grafana-*                      1/1     Running
```

### 3. Access Grafana

```bash
# Port forward
kubectl port-forward -n monitoring \
  svc/prometheus-grafana 3000:80

# Open http://localhost:3000
# Default credentials: admin / prom-operator
```

## Metrics

### Application Metrics

**Sentinel exposes** `/metrics` **endpoint:**

```python
# core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

policy_evaluations_total = Counter(
    'policy_evaluations_total',
    'Total policy evaluations',
    ['decision', 'agent_id']
)

kafka_consumer_lag = Gauge(
    'kafka_consumer_lag',
    'Kafka consumer lag',
    ['topic', 'partition']
)

circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open)',
    ['name']
)
```

### Query Examples

**Request rate:**
```promql
rate(http_requests_total[5m])
```

**Error rate:**
```promql
rate(http_requests_total{status=~"5.."}[5m]) /
rate(http_requests_total[5m])
```

**P95 latency:**
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m]))
```

**Kafka lag:**
```promql
kafka_consumer_lag > 1000
```

## Dashboards

### Pre-built Dashboards

1. **Sentinel Overview** (`monitoring/grafana/dashboards/sentinel-overview.json`)
   - Request rate, error rate, latency
   - Kafka consumer lag
   - Circuit breaker status
   - Policy evaluation throughput

2. **Kubernetes Cluster** (bundled with kube-prometheus-stack)
   - Node resources
   - Pod status
   - Persistent volumes

3. **Application Performance** (custom)
   - API endpoint latency breakdown
   - Database query performance
   - Redis hit/miss ratio
   - Worker queue depth

### Import Custom Dashboard

```bash
# Via kubectl
kubectl create configmap sentinel-dashboard \
  --from-file=monitoring/grafana/dashboards/sentinel-overview.json \
  -n monitoring

# Or via Grafana UI
# Dashboards → Import → Upload JSON file
```

## Alerting

### Alert Rules

**Defined in** `k8s/production/monitoring.yaml`:

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| HighErrorRate | >5% 5xx errors for 5min | critical | Page oncall |
| HighLatency | P95 >2s for 5min | warning | Slack alert |
| KafkaConsumerLag | Lag >10K for 10min | warning | Investigate workers |
| PodCrashLooping | Restarts >0 for 15min | critical | Page oncall |
| HighMemoryUsage | >90% for 5min | warning | Scale up |

### Configure Alert Routing

**Edit** `monitoring/prometheus/values.yaml`:

```yaml
alertmanager:
  config:
    receivers:
      - name: 'slack'
        slack_configs:
          - api_url: '<SLACK_WEBHOOK_URL>'
            channel: '#sentinel-alerts'
      
      - name: 'pagerduty'
        pagerduty_configs:
          - service_key: '<PAGERDUTY_KEY>'
    
    route:
      routes:
        - match:
            severity: critical
          receiver: 'pagerduty'
        - match:
            severity: warning
          receiver: 'slack'
```

**Apply changes:**

```bash
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f monitoring/prometheus/values.yaml
```

### Test Alerts

```bash
# Trigger test alert
kubectl run -i --tty --rm debug \
  --image=curlimages/curl \
  --restart=Never \
  -- sh -c "while true; do curl http://sentinel-api.sentinel/health; done"

# Generate errors
curl -X POST http://sentinel-api.sentinel/evaluate \
  -H "Content-Type: application/json" \
  -d '{"invalid": "payload"}'
```

## Logs

### Centralized Logging with FluentBit

**Install:**

```bash
helm repo add fluent https://fluent.github.io/helm-charts

helm install fluent-bit fluent/fluent-bit \
  -n logging \
  --create-namespace \
  --set backend.type=cloudwatch \
  --set backend.cloudwatch.region=us-east-1 \
  --set backend.cloudwatch.log_group_name=/aws/eks/sentinel-production
```

### Query Logs

**CloudWatch Insights:**

```sql
fields @timestamp, @message
| filter kubernetes.namespace_name = "sentinel"
| filter kubernetes.pod_name like /sentinel-api/
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**kubectl logs:**

```bash
# Tail logs
kubectl logs -f deployment/sentinel-api -n sentinel

# Last 100 lines
kubectl logs --tail=100 deployment/sentinel-api -n sentinel

# Logs from specific time
kubectl logs --since=1h deployment/sentinel-api -n sentinel
```

## Tracing (Optional)

### Install Jaeger

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts

helm install jaeger jaegertracing/jaeger \
  -n tracing \
  --create-namespace \
  --set collector.service.type=ClusterIP
```

### Instrument Application

**Add to** `requirements.txt`:
```
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-instrumentation-fastapi==0.41b0
opentelemetry-exporter-jaeger==1.20.0
```

**Update** `api/main.py`:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent.tracing",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

FastAPIInstrumentor.instrument_app(app)
```

## Troubleshooting

### Prometheus Not Scraping Targets

**Check ServiceMonitor:**

```bash
kubectl get servicemonitor -n sentinel

# Verify labels match
kubectl get svc sentinel-api -n sentinel --show-labels
```

### Grafana Dashboard Not Loading Data

**Verify Prometheus datasource:**

```bash
# Port forward Prometheus
kubectl port-forward -n monitoring svc/prometheus-server 9090:9090

# Test query: http://localhost:9090/graph
rate(http_requests_total[5m])
```

### High Cardinality Warning

**Problem**: Too many unique label combinations

**Fix**: Limit label values

```python
# BAD: unbounded labels
Counter('requests', 'Requests', ['user_id', 'session_id'])

# GOOD: bounded labels
Counter('requests', 'Requests', ['endpoint', 'status'])
```

## Performance Tuning

### Prometheus Retention

**Increase retention:**

```yaml
# monitoring/prometheus/values.yaml
prometheus:
  prometheusSpec:
    retention: 60d  # Default 30d
```

### Reduce Scrape Frequency

**For non-critical metrics:**

```yaml
# k8s/production/monitoring.yaml
spec:
  endpoints:
    - port: metrics
      interval: 60s  # Default 30s
```

### Query Optimization

**Use recording rules for expensive queries:**

```yaml
# monitoring/prometheus/rules.yaml
groups:
  - name: sentinel.rules
    interval: 60s
    rules:
      - record: job:http_requests:rate5m
        expr: rate(http_requests_total[5m])
```

## Capacity Planning

### Prometheus Storage

**Estimate:** `~1-2 bytes per sample`

```
Time series: 10,000
Samples/sec: 1 (30s interval)
Retention: 30 days

Storage = 10,000 × 1 byte × 86,400 sec/day × 30 days
        ≈ 25 GB
```

**Add headroom:** Provision **50-100 GB**

### Grafana Concurrent Users

- **<10 users**: 1 replica, 512MB RAM
- **10-50 users**: 2 replicas, 1GB RAM
- **50-100 users**: 3 replicas, 2GB RAM

## SLI/SLO Monitoring

**Define SLOs:**

| Metric | Target | Measurement Window |
|--------|--------|-------------------|
| Availability | 99.9% | 30 days |
| Latency (P95) | <500ms | 7 days |
| Error Rate | <0.1% | 7 days |

**Create SLO dashboard** with error budget tracking.

**Query for error budget:**

```promql
1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d])) /
  sum(rate(http_requests_total[30d]))
) >= 0.999
```
