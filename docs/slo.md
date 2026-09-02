# Sentinel Service Level Objectives (SLOs)

## Overview

Sentinel's SLOs define the expected reliability and performance of the authorization control plane. These SLOs directly impact our ability to protect financial transactions safely.

---

## SLO Definitions

### 1. Availability SLO

**Target**: 99.9% uptime (three nines)

**Measurement**:
```
availability = successful_requests / total_requests
```

**Error Budget**:
- **Monthly**: 43 minutes of downtime
- **Weekly**: 10 minutes of downtime
- **Daily**: 1.4 minutes of downtime

**Measurement Window**: 30 days rolling

**What Counts as Downtime**:
- HTTP 5xx responses
- Request timeouts (>10s)
- Service completely unavailable

**What Doesn't Count**:
- Planned maintenance (with notification)
- Client errors (4xx)
- Upstream failures (Razorpay, external APIs)

---

### 2. Latency SLO

**Target**: 95% of authorization requests complete in <30ms

**Measurement**:
```
latency_slo = count(requests < 30ms) / total_requests
```

**Error Budget**:
- 5% of requests can exceed 30ms
- If 10,000 requests/hour, 500 can be slow

**Measurement Window**: 7 days rolling

**Measurement Point**: End-to-end authorization decision time
- From: API receives `/evaluate` request
- To: API returns authorization decision

**Excludes**:
- Network latency (client ↔ server)
- Execution time (after capability token issued)

---

### 3. Correctness SLO

**Target**: Zero security violations

**Metrics**:
- Unauthorized executions: **0**
- Duplicate executions: **0**
- Unsafe ALLOWs: **0**
- Audit chain breaks: **0**
- Fail-open incidents: **0**

**Measurement Window**: All time (no error budget)

**Why Zero?**
Sentinel's security guarantees are binary. A single violation represents a critical failure that could allow financial fraud.

**Detection**:
- Continuous monitoring via Security Command Center
- Automated alerts on any non-zero invariant
- Daily audit chain verification

---

### 4. Data Durability SLO

**Target**: Zero audit log data loss (RPO = 0)

**Measurement**:
- All authorization decisions written to audit log
- Audit chain cryptographically verifiable
- No gaps in sequence

**Measurement Window**: All time

**Guarantees**:
- Every decision logged before capability token issued
- Audit trail survives system failures
- Merkle hash chain detects tampering

---

## SLO Tracking

### Dashboards

**Grafana Dashboard: SLO Overview**
- Real-time SLO compliance
- Error budget remaining
- Burn rate (how fast budget is consumed)
- Trend analysis

**URL**: `https://grafana.example.com/d/sentinel-slo`

### Prometheus Queries

**Availability (30-day)**:
```promql
1 - (
  sum(rate(sentinel_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(sentinel_requests_total[30d]))
)
```

**Latency SLO (7-day)**:
```promql
sum(rate(sentinel_authorization_latency_bucket{le="0.03"}[7d]))
/
sum(rate(sentinel_authorization_latency_count[7d]))
```

**Security Invariants**:
```promql
sum(sentinel_security_invariant_violations) by (invariant)
```

---

## Error Budget Policy

### Budget Consumption Tiers

**Green (0-50% consumed)**:
- Normal operations
- Continue feature development
- Planned maintenance allowed

**Yellow (50-80% consumed)**:
- Increased caution
- Defer risky changes
- Focus on reliability improvements

**Orange (80-100% consumed)**:
- Feature freeze
- All hands on reliability
- Root cause analysis required

**Red (100%+ consumed)**:
- Critical incident
- Postmortem required
- Executive notification

### Budget Reset

- Error budgets reset monthly (availability)
- Latency budget resets weekly
- Correctness budget never resets (always zero)

---

## SLO Alerts

### Critical Alerts

**Availability Budget 80% Consumed**:
```yaml
- alert: SLOAvailabilityBudget80
  expr: error_budget_remaining < 0.2
  for: 15m
  severity: warning
```

**Availability Budget Exhausted**:
```yaml
- alert: SLOAvailabilityBudgetExhausted
  expr: error_budget_remaining <= 0
  for: 5m
  severity: critical
```

**Latency SLO Violation**:
```yaml
- alert: SLOLatencyViolation
  expr: latency_slo < 0.95
  for: 1h
  severity: warning
```

**Security Invariant Violation**:
```yaml
- alert: SLOSecurityViolation
  expr: sentinel_security_invariant_violations > 0
  for: 1m
  severity: critical
```

---

## Incident Response

### When SLO is Violated

**1. Immediate Actions**:
- Acknowledge alert
- Assess impact (how many users affected?)
- Check recent changes (deployment, config)
- Engage on-call engineer

**2. Stabilization**:
- Rollback recent changes if applicable
- Scale up resources if capacity issue
- Enable circuit breakers if dependency issue

**3. Investigation**:
- Collect logs, traces, metrics
- Identify root cause
- Document timeline

**4. Recovery**:
- Implement fix
- Verify SLO returns to compliance
- Monitor for regression

**5. Postmortem**:
- Write incident report
- Identify preventive measures
- Update runbooks

---

## SLO Review Process

### Weekly Review

**Every Monday, 10:00 AM**:
- Review past week's SLO compliance
- Check error budget consumption
- Identify trends
- Plan corrective actions

### Monthly Business Review

**First Friday of month**:
- Present SLO performance to leadership
- Compare to previous month
- Discuss reliability investments
- Update SLO targets if needed

---

## SLO Exceptions

### Planned Maintenance

- Scheduled during low-traffic windows
- Notification sent 24h in advance
- Does not count against error budget

### External Dependencies

- Razorpay outages (if properly detected)
- Cloud provider issues
- DNS failures

**Requirement**: Must be detected and fail-closed properly.

---

## Improving SLOs

### Current vs. Aspirational

| SLO | Current | Target (6mo) | Target (1yr) |
|-----|---------|-------------|-------------|
| Availability | 99.9% | 99.95% | 99.99% |
| Latency (p95) | <30ms | <20ms | <15ms |
| Latency (p99) | <100ms | <50ms | <30ms |
| Security | 0 violations | 0 violations | 0 violations |

### Investments Required

**To achieve 99.95%**:
- Multi-region deployment
- Active-active architecture
- Automated failover

**To achieve <20ms p95**:
- Redis cache warming
- ML model optimization
- Database query optimization
- Connection pooling tuning

---

## References

- **Grafana Dashboards**: `https://grafana.example.com`
- **Prometheus Alerts**: `https://prometheus.example.com`
- **Runbooks**: `docs/runbooks/observability/`
- **Incident Reports**: `docs/incidents/`

---

**Last Updated**: 2026-08-29  
**Owner**: SRE Team  
**Review Cycle**: Monthly
