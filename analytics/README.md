# Sentinel Analytics

Business Intelligence and Metrics Aggregation for Sentinel RC1.

## Overview

The Analytics module transforms raw audit log data into actionable business intelligence. It provides:

- **Real-time KPIs** — Transaction volume, fraud prevention, system health
- **Executive Dashboards** — Visual insights for stakeholders
- **Agent Analytics** — Per-agent performance and behavioral tracking
- **Financial Analysis** — ROI calculation and cost-benefit analysis
- **Anomaly Detection** — Behavioral drift and pattern detection
- **Reports** — Daily, weekly, and monthly automated reports

## Quick Start

### 1. Initialize Analytics Database

```bash
# Create analytics tables
psql $DATABASE_URL < analytics/schema.sql

# Verify tables created
psql $DATABASE_URL -c "\dt"
```

### 2. Run Analytics Pipeline

```bash
# Hourly aggregation (run every hour)
python -m analytics.pipeline --period hourly

# Daily aggregation (run once per day)
python -m analytics.pipeline --period daily

# Backfill specific date
python -m analytics.pipeline --period daily --target 2026-08-29
```

### 3. Generate Reports

```bash
# Daily report
python -m analytics.reports --type daily

# Weekly report
python -m analytics.reports --type weekly

# Monthly report
python -m analytics.reports --type monthly --date 2026-08
```

### 4. Access Dashboards

Visit:
- Executive Dashboard: http://localhost:5173/analytics/executive
- Agent Analytics: http://localhost:5173/analytics/agents
- Financial Analytics: http://localhost:5173/analytics/financial

### 5. API Access

```bash
# Get KPIs
curl http://localhost:8000/api/analytics/kpis

# Get decision trends
curl "http://localhost:8000/api/analytics/trends/decisions?days=7&granularity=day"

# Get agent metrics
curl "http://localhost:8000/api/analytics/agents?days=7&order_by=transactions"

# Get financial summary
curl "http://localhost:8000/api/analytics/financial/summary?start_date=2026-08-01&end_date=2026-08-31"
```

## Architecture

```
Raw Audit Log → Analytics Pipeline → Analytics DB → Analytics API → Frontend Dashboards
                (Hourly/Daily)      (Aggregated)    (REST)         (React)
```

## Module Structure

```
analytics/
├── __init__.py              # Module initialization
├── README.md                # This file
├── schema.sql               # Database schema for analytics tables
├── pipeline.py              # Data aggregation pipeline
├── reports.py               # Report generation
└── anomaly_detection.py     # Anomaly detection (future)
```

## Metrics Tracked

### Security Metrics
- Prevented fraud value (₹ blocked by CONTAIN)
- False positive rate
- True positive rate
- Detection latency
- Response time

### Operational Metrics
- Transaction volume (per hour/day)
- Agent activity
- Decision distribution (% ALLOW/ESCALATE/CONTAIN)
- Average risk score
- Policy violation rate

### Financial Metrics
- Total transaction value processed
- Average transaction value
- Transaction value by decision type
- Fraud prevented vs. processed value ratio
- Cost per authorization decision

### Performance Metrics
- Authorization latency (p50/p95/p99)
- Throughput (RPS)
- Error rate
- Uptime (SLO compliance)

## Scheduling

### Cron (Recommended)

Add to crontab:

```cron
# Hourly aggregation (5 minutes past each hour)
5 * * * * cd /path/to/sentinel && python -m analytics.pipeline --period hourly

# Daily aggregation (1 AM)
0 1 * * * cd /path/to/sentinel && python -m analytics.pipeline --period daily

# Daily report (2 AM)
0 2 * * * cd /path/to/sentinel && python -m analytics.reports --type daily

# Weekly report (Monday 8 AM)
0 8 * * 1 cd /path/to/sentinel && python -m analytics.reports --type weekly

# Monthly report (1st of month, 9 AM)
0 9 1 * * cd /path/to/sentinel && python -m analytics.reports --type monthly
```

### Docker Compose

```yaml
services:
  analytics-hourly:
    image: sentinel:latest
    command: >
      sh -c "while true; do
        sleep 3600;
        python -m analytics.pipeline --period hourly;
      done"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}

  analytics-daily:
    image: sentinel:latest
    command: >
      sh -c "while true; do
        sleep 86400;
        python -m analytics.pipeline --period daily;
        python -m analytics.reports --type daily;
      done"
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

## Data Retention

| Data Type | Retention Period | Reason |
|-----------|-----------------|---------|
| Raw audit logs | 90 days | Operational |
| Aggregated metrics (hourly) | 1 year | Business intelligence |
| Aggregated metrics (daily) | Permanent | Long-term analysis |
| Fraud events | 2 years | Compliance |
| Financial metrics | Permanent | Accounting |
| Reports | 2 years | Historical reference |

## Performance

### Database Indexes

All analytics tables have optimized indexes:
- Time-range queries (e.g., last 7 days)
- Agent lookups
- Severity filtering
- Aggregation windows

### Query Optimization

- Use aggregated tables instead of raw audit log
- Partition large tables by date
- Cache frequently-accessed queries (30s TTL)
- Use read replicas for analytics queries

## Troubleshooting

### Pipeline Not Running

```bash
# Check logs
tail -f /var/log/sentinel/analytics.log

# Verify database connection
psql $DATABASE_URL -c "SELECT 1"

# Test pipeline manually
python -m analytics.pipeline --period hourly
```

### Missing Data

```bash
# Check for gaps in aggregated data
psql $DATABASE_URL << EOF
SELECT aggregation_period
FROM generate_series(
  NOW() - INTERVAL '7 days',
  NOW(),
  '1 hour'::interval
) AS aggregation_period
LEFT JOIN decisions_aggregated USING (aggregation_period)
WHERE decisions_aggregated.id IS NULL;
EOF

# Backfill missing hours
python -m analytics.pipeline --period hourly --target "2026-08-29T14:00:00"
```

### Slow Queries

```bash
# Analyze query performance
psql $DATABASE_URL << EOF
EXPLAIN ANALYZE
SELECT * FROM decisions_aggregated
WHERE aggregation_period >= NOW() - INTERVAL '7 days';
EOF

# Rebuild indexes
psql $DATABASE_URL -c "REINDEX TABLE decisions_aggregated;"

# Update statistics
psql $DATABASE_URL -c "ANALYZE decisions_aggregated;"
```

## Development

### Adding New Metrics

1. **Update schema:**
   ```sql
   ALTER TABLE decisions_aggregated
   ADD COLUMN new_metric_count INTEGER DEFAULT 0;
   ```

2. **Update pipeline:**
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

## Documentation

- [Analytics Documentation](../docs/analytics.md)
- [API Reference](../docs/api.md)
- [Database Schema](./schema.sql)

## License

Part of Sentinel RC1 - Razorpay Buildathon 2026
