# Sentinel Analytics — Quick Start

Get analytics up and running in 5 minutes.

## 1. Initialize Database (1 min)

```bash
# Create analytics tables
psql $DATABASE_URL < analytics/schema.sql

# Verify
psql $DATABASE_URL -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'decisions_aggregated';"
```

## 2. Run Initial Aggregation (2 min)

```bash
# Backfill last 7 days
for day in {0..6}; do
  date=$(date -d "$day days ago" +%Y-%m-%d)
  echo "Processing $date..."
  python -m analytics.pipeline --period daily --target $date
done

# Run hourly for today
python -m analytics.pipeline --period hourly
```

## 3. Start Services (1 min)

```bash
# API (if not already running)
uvicorn api.main:app --host 0.0.0.0 --port 8000 &

# Frontend
cd frontend && npm run dev
```

## 4. Access Dashboards (1 min)

Open in browser:
- Executive: http://localhost:5173/analytics/executive
- Agents: http://localhost:5173/analytics/agents
- Financial: http://localhost:5173/analytics/financial

## 5. Test API

```bash
# Get KPIs
curl http://localhost:8000/api/analytics/kpis | jq

# Get trends
curl "http://localhost:8000/api/analytics/trends/decisions?days=7" | jq

# Get agents
curl "http://localhost:8000/api/analytics/agents?days=7" | jq
```

## Schedule Pipeline (Cron)

```bash
# Edit crontab
crontab -e

# Add these lines
5 * * * * cd /path/to/sentinel && python -m analytics.pipeline --period hourly
0 1 * * * cd /path/to/sentinel && python -m analytics.pipeline --period daily
0 2 * * * cd /path/to/sentinel && python -m analytics.reports --type daily
```

## Generate Reports

```bash
# Daily report
python -m analytics.reports --type daily

# Weekly report
python -m analytics.reports --type weekly

# Monthly report (for August 2026)
python -m analytics.reports --type monthly --date 2026-08
```

## Troubleshooting

### No Data in Dashboard
```bash
# Check aggregated data
psql $DATABASE_URL -c "SELECT COUNT(*) FROM decisions_aggregated;"

# If empty, run pipeline
python -m analytics.pipeline --period hourly
```

### API Returns Empty
```bash
# Check API logs
tail -f logs/api.log

# Test database connection
psql $DATABASE_URL -c "SELECT 1"
```

### Frontend Not Loading
```bash
# Check if API is running
curl http://localhost:8000/health/live

# Check if frontend is running
curl http://localhost:5173
```

## Docker Compose (Alternative)

```yaml
# Add to docker-compose.yml
services:
  analytics-pipeline:
    image: sentinel:latest
    command: >
      sh -c "while true; do
        sleep 3600;
        python -m analytics.pipeline --period hourly;
      done"
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

## Key Commands Reference

| Task | Command |
|------|---------|
| Initialize DB | `psql $DATABASE_URL < analytics/schema.sql` |
| Hourly pipeline | `python -m analytics.pipeline --period hourly` |
| Daily pipeline | `python -m analytics.pipeline --period daily` |
| Backfill date | `python -m analytics.pipeline --period daily --target 2026-08-29` |
| Daily report | `python -m analytics.reports --type daily` |
| Check data | `psql $DATABASE_URL -c "SELECT * FROM decisions_aggregated LIMIT 10;"` |
| Test API | `curl http://localhost:8000/api/analytics/kpis` |

## Default Credentials / Config

- API Port: `8000`
- Frontend Port: `5173`
- Database: `$DATABASE_URL` from `.env`
- Reports Output: `./reports/`
- Retention: 1 year (aggregated), 2 years (fraud events)

## Production Deployment

### Step 1: Configure Environment
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/sentinel"
```

### Step 2: Run Migrations
```bash
psql $DATABASE_URL < analytics/schema.sql
```

### Step 3: Deploy Services
```bash
# Using systemd
sudo systemctl start sentinel-api
sudo systemctl start sentinel-analytics-hourly
sudo systemctl start sentinel-analytics-daily
```

### Step 4: Verify
```bash
# Check services
systemctl status sentinel-*

# Check logs
journalctl -u sentinel-analytics-hourly -f
```

## Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/health/ready

# Database health
psql $DATABASE_URL -c "SELECT 1"
```

### Metrics
```bash
# Check pipeline runs
psql $DATABASE_URL -c "
  SELECT aggregation_period, total_decisions
  FROM decisions_aggregated
  ORDER BY aggregation_period DESC
  LIMIT 10;
"

# Check fraud events
psql $DATABASE_URL -c "
  SELECT COUNT(*), SUM(prevented_loss)
  FROM fraud_events
  WHERE detected_at >= NOW() - INTERVAL '24 hours';
"
```

---

**That's it!** Analytics is now running. Visit the dashboards to see your metrics.

For detailed documentation, see [`docs/analytics.md`](../docs/analytics.md).
