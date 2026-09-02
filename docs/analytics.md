# Sentinel Analytics & Business Intelligence

## Overview

The Sentinel Analytics system provides comprehensive business intelligence, security metrics, and financial analysis for the authorization system. It transforms raw audit log data into actionable insights for executives, security teams, and business stakeholders.

## Architecture

```
┌─────────────────┐
│  Audit Ledger   │  PostgreSQL (source of truth)
│  (Raw Events)   │
└────────┬────────┘
         │
         ├─► Analytics Pipeline (Python)
         │   • Hourly aggregation
         │   • Daily rollups
         │   • Fraud detection
         │   • Anomaly detection
         │
         ▼
┌─────────────────┐
│  Analytics DB   │  PostgreSQL (aggregated metrics)
│  (Metrics)      │
└────────┬────────┘
         │
         ├─► Analytics API (FastAPI)
         │   • /api/analytics/kpis
         │   • /api/analytics/trends/*
         │   • /api/analytics/agents/*
         │   • /api/analytics/financial/*
         │
         ▼
┌─────────────────┐
│  Frontend       │  React + TypeScript
│  (Dashboards)   │
└─────────────────┘
```

## Business Metrics

### Security Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Prevented Fraud Value** | Total value blocked by CONTAIN decisions | Sum of all CONTAIN transaction amounts |
| **False Positive Rate** | ESCALATE decisions that were safe | (False Escalates / Total Escalates) × 100 |
| **True Positive Rate** | CONTAIN decisions that were actual fraud | (True Contains / Total Contains) × 100 |
| **Detection Latency** | Time to detect fraud | Timestamp(Detection) - Timestamp(Intent) |
| **Response Time** | Time to CONTAIN after detection | Timestamp(CONTAIN) - Timestamp(Detection) |

### Operational Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| **Transaction Volume** | Authorizations per hour/day | `decisions_aggregated.total_decisions` |
| **Agent Activity** | Transactions per agent | `agent_metrics.total_transactions` |
| **Decision Distribution** | % ALLOW/ESCALATE/CONTAIN | Calculated from decision counts |
| **Average Risk Score** | Mean risk across all intents | `decisions_aggregated.avg_risk_score` |
| **Policy Violation Rate** | % of transactions violating policy | (Violations / Total) × 100 |

### Financial Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Total Transaction Value** | Sum of all processed transactions | Sum of all `amount` fields |
| **Average Transaction Value** | Mean transaction amount | Total Value / Total Transactions |
| **Transaction Value by Decision** | Value segmented by ALLOW/ESCALATE/CONTAIN | Sum grouped by `decision` |
| **Fraud Prevention Ratio** | Prevented fraud vs. processed value | Prevented Value / Total Value |
| **Cost per Authorization** | Operational cost per decision | Total Cost / Total Decisions |

### Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Authorization Latency (p50)** | Median response time | < 50ms |
| **Authorization Latency (p95)** | 95th percentile | < 100ms |
| **Authorization Latency (p99)** | 99th percentile | < 200ms |
| **Throughput** | Requests per second | > 1000 RPS |
| **Error Rate** | Failed authorizations | < 0.1% |
| **Uptime (SLO)** | Service availability | > 99.9% |

## Analytics Database Schema

### Key Tables

#### `decisions_aggregated`
Hourly and daily rollups of authorization decisions.

**Columns:**
- `aggregation_period` — Timestamp of aggregation window
- `period_type` — 'hour' or 'day'
- `total_decisions`, `allow_count`, `escalate_count`, `contain_count`
- `total_value`, `allow_value`, `escalate_value`, `contain_value`
- `avg_risk_score`, `max_risk_score`, `min_risk_score`
- `high_risk_count`, `medium_risk_count`, `low_risk_count`

**Retention:** 1 year

#### `agent_metrics`
Per-agent performance and behavioral tracking.

**Columns:**
- `agent_id` — Agent identifier
- `aggregation_period`, `period_type`
- `total_transactions`, `total_value`
- `allow_count`, `escalate_count`, `contain_count`
- `avg_risk_score`, `behavioral_drift_score`
- `unique_recipients`, `policy_violations`

**Retention:** 1 year

#### `fraud_events`
Detected fraud attempts and containment actions.

**Columns:**
- `intent_id` — Unique intent identifier
- `detected_at` — Detection timestamp
- `agent_id`, `amount`, `currency`, `recipient`
- `risk_score`, `fraud_type`, `detection_method`
- `investigated`, `investigation_outcome`

**Retention:** 2 years (compliance)

#### `financial_metrics`
Daily financial rollups and cost analysis.

**Columns:**
- `date` — Calendar date
- `total_value_processed`, `total_transactions`
- `fraud_prevented_value`, `operational_cost`
- `roi_percentage`, `net_value`

**Retention:** Permanent

## Analytics Pipeline

### Running the Pipeline

**Hourly Aggregation:**
```bash
python -m analytics.pipeline --period hourly
```

**Daily Aggregation:**
```bash
python -m analytics.pipeline --period daily
```

**Specific Date/Time:**
```bash
# Hourly for specific hour
python -m analytics.pipeline --period hourly --target "2026-08-29T14:00:00"

# Daily for specific date
python -m analytics.pipeline --period daily --target "2026-08-29"
```

### Scheduling

**Recommended Cron Schedule:**
```cron
# Hourly aggregation (run 5 minutes after each hour)
5 * * * * cd /path/to/sentinel && python -m analytics.pipeline --period hourly

# Daily aggregation (run at 1 AM)
0 1 * * * cd /path/to/sentinel && python -m analytics.pipeline --period daily
```

**Docker Compose:**
```yaml
services:
  analytics-hourly:
    image: sentinel:latest
    command: ["sh", "-c", "while true; do sleep 3600; python -m analytics.pipeline --period hourly; done"]
    depends_on:
      - postgres

  analytics-daily:
    image: sentinel:latest
    command: ["sh", "-c", "while true; do sleep 86400; python -m analytics.pipeline --period daily; done"]
    depends_on:
      - postgres
```

## Analytics API

### Base URL
```
http://localhost:8000/api/analytics
```

### Endpoints

#### GET `/kpis`
Get Key Performance Indicators for executive dashboard.

**Response:**
```json
{
  "total_transactions_24h": 125847,
  "fraud_prevented_value": 235000000,
  "detection_rate": 0.978,
  "system_uptime": 0.9995,
  "avg_latency_ms": 42.3,
  "allow_rate": 0.892,
  "escalate_rate": 0.065,
  "contain_rate": 0.043
}
```

#### GET `/trends/decisions?days=7&granularity=hour`
Get time-series trend of authorization decisions.

**Query Parameters:**
- `days` — Number of days (1-90)
- `granularity` — 'hour' or 'day'

#### GET `/agents?days=7&order_by=transactions&limit=100`
Get per-agent performance metrics.

**Query Parameters:**
- `days` — Number of days to aggregate (1-90)
- `order_by` — 'transactions', 'risk', 'violations'
- `limit` — Max agents to return (1-1000)

#### GET `/agents/{agent_id}/details?days=30`
Get detailed metrics for a specific agent.

**Response:**
```json
{
  "agent_id": "agent-001",
  "time_series": [...],
  "fraud_summary": {
    "fraud_attempts": 12,
    "prevented_value": 3450000
  },
  "recent_anomalies": [...]
}
```

#### GET `/financial/summary?start_date=2026-08-01&end_date=2026-08-31`
Get financial metrics and ROI analysis.

**Response:**
```json
{
  "period_start": "2026-08-01",
  "period_end": "2026-08-31",
  "total_value_processed": 458000000000,
  "total_transactions": 2584230,
  "fraud_prevented_value": 1250000000,
  "operational_cost": 25842.30,
  "roi_percentage": 494.2,
  "net_value": 127814.70
}
```

#### GET `/fraud/events?days=7&investigated=false&limit=100`
Get detected fraud events.

#### GET `/anomalies?days=7&severity=high&acknowledged=false`
Get detected anomalies and alerts.

#### POST `/anomalies/{anomaly_id}/acknowledge`
Acknowledge an anomaly alert.

**Body:**
```json
{
  "acknowledged_by": "security-team",
  "notes": "False positive due to known agent behavior pattern"
}
```

#### POST `/export`
Export analytics data in various formats.

**Body:**
```json
{
  "export_type": "decisions",
  "format": "csv",
  "start_date": "2026-08-01",
  "end_date": "2026-08-31",
  "filters": {
    "decision": "CONTAIN"
  }
}
```

## Frontend Dashboards

### Executive Dashboard
**Route:** `/analytics/executive`

**Features:**
- Real-time KPIs (24h window)
- Transaction volume trend (7 days)
- Decision distribution pie chart
- Recent fraud events
- Active anomaly alerts

**Refresh:** Auto-refresh every 30 seconds

### Agent Analytics
**Route:** `/analytics/agents`

**Features:**
- Agent list with key metrics
- Sortable by transactions, risk, violations
- Click-through to agent details
- Agent comparison view
- Behavioral drift detection

### Financial Analytics
**Route:** `/analytics/financial`

**Features:**
- Transaction value analysis
- Fraud prevention savings
- ROI calculation
- Cost-benefit analysis
- Export to PDF/CSV/Excel

### ROI Calculator
**Component:** `<ROICalculator />`

**Inputs:**
- Monthly transaction volume
- Average transaction value
- Expected fraud rate (%)
- Cost per authorization ($)
- Detection rate (%)

**Outputs:**
- Fraud prevented value
- Operational cost
- Net monthly savings
- ROI percentage
- Breakeven fraud rate
- Annual projection

## Reports

### Daily Report
Generated at 1 AM UTC.

**Contents:**
- Transaction summary (volume, value)
- Security events (fraud detected, violations)
- Performance metrics (latency, throughput)
- System health (uptime, errors)

**Delivery:** Email, Slack, stored in `reports` table

### Weekly Report
Generated every Monday at 8 AM UTC.

**Contents:**
- Week-over-week trends
- Agent performance comparison
- Anomalies detected
- Policy effectiveness analysis

### Monthly Report
Generated on the 1st of each month.

**Contents:**
- Executive summary
- Financial impact and ROI
- Compliance metrics
- Recommendations for next month

## Data Export

### Supported Formats
- **CSV** — Comma-separated values (Excel-compatible)
- **JSON** — API-friendly structured data
- **Excel** — .xlsx with multiple sheets
- **PDF** — Formatted reports for presentations

### Export Endpoints
```bash
# Export decisions
GET /api/analytics/export?type=decisions&format=csv&start=2026-08-01&end=2026-08-31

# Export agent metrics
GET /api/analytics/export?type=agents&format=excel&days=30

# Export fraud events
GET /api/analytics/export?type=fraud_events&format=json&investigated=false
```

## Anomaly Detection

### Anomaly Types

| Type | Description | Detection Method |
|------|-------------|------------------|
| **Volume** | Unusual transaction volume spike/drop | Standard deviation (2σ threshold) |
| **Velocity** | Rapid transaction frequency from agent | Time-series analysis |
| **Pattern** | Unusual recipient/amount patterns | Clustering |
| **Behavioral** | Agent behavior drift | Behavioral risk scores |

### Severity Levels
- **Critical** — Immediate investigation required
- **High** — Review within 24 hours
- **Medium** — Review within 7 days
- **Low** — Informational only

### Alert Workflow
1. Anomaly detected by pipeline
2. Record inserted into `anomaly_detections`
3. Alert sent (email, Slack, PagerDuty)
4. Security team acknowledges
5. Investigation outcome recorded

## Compliance Reporting

### Audit Trail Export
All authorization decisions are permanently logged in the audit ledger with:
- Intent details (agent, action, amount, recipient)
- Risk assessment (ML scores, policy evaluation)
- Decision and reasoning
- Execution status

**Compliance Standards:**
- PCI-DSS — Payment card data protection
- SOC 2 — Security, availability, confidentiality
- GDPR — Data privacy (no PII in analytics)

### Retention Policy
| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Raw audit logs | 90 days | Operational |
| Aggregated metrics | 1 year | Business intelligence |
| Fraud events | 2 years | Compliance |
| Financial metrics | Permanent | Accounting |

## Performance Considerations

### Database Indexes
All analytics tables have optimized indexes for common query patterns:
- Time-range queries (e.g., last 7 days)
- Agent lookups
- Severity filtering
- Aggregation windows

### Query Optimization
- Use aggregated tables instead of raw audit log
- Partition large tables by date
- Materialize frequently-accessed views
- Cache dashboard responses (30s TTL)

### Cost Optimization
- Archive old data to cold storage (S3, Glacier)
- Compress historical reports
- Use read replicas for analytics queries
- Sample high-volume streams

## Troubleshooting

### Pipeline Not Running
```bash
# Check pipeline logs
docker logs sentinel-analytics-hourly

# Verify database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_ledger;"

# Manually run pipeline
python -m analytics.pipeline --period hourly
```

### Missing Metrics
```bash
# Check for gaps in aggregated data
SELECT aggregation_period
FROM generate_series('2026-08-01'::date, '2026-08-31'::date, '1 hour'::interval) AS aggregation_period
LEFT JOIN decisions_aggregated USING (aggregation_period)
WHERE decisions_aggregated.id IS NULL;

# Backfill missing hours
for hour in $(seq 0 23); do
  python -m analytics.pipeline --period hourly --target "2026-08-15T${hour}:00:00"
done
```

### Slow Dashboard Queries
```bash
# Check query performance
EXPLAIN ANALYZE
SELECT * FROM decisions_aggregated
WHERE aggregation_period >= NOW() - INTERVAL '7 days';

# Rebuild indexes
REINDEX TABLE decisions_aggregated;

# Update statistics
ANALYZE decisions_aggregated;
```

## Development

### Adding New Metrics

1. **Define metric in schema:**
   ```sql
   ALTER TABLE decisions_aggregated
   ADD COLUMN new_metric_count INTEGER DEFAULT 0;
   ```

2. **Update pipeline logic:**
   ```python
   def _aggregate_decisions(self, records, period, period_type):
       metrics['new_metric_count'] = calculate_new_metric(records)
       return metrics
   ```

3. **Add API endpoint:**
   ```python
   @router.get("/metrics/new")
   async def get_new_metric(db: Session = Depends(get_db)):
       # Implementation
   ```

4. **Create frontend component:**
   ```tsx
   function NewMetricCard() {
     const [metric, setMetric] = useState(null);
     // Implementation
   }
   ```

### Testing

```bash
# Unit tests
pytest tests/test_analytics_pipeline.py

# Integration tests
pytest tests/test_analytics_api.py

# Load testing
ab -n 10000 -c 100 http://localhost:8000/api/analytics/kpis
```

## References

- [Sentinel Architecture](../README.md)
- [Audit Ledger Schema](../db/models.py)
- [API Documentation](../api/README.md)
- [Frontend Components](../frontend/README.md)

---

**Questions or issues?** Contact the Sentinel team or file an issue on GitHub.
