#!/bin/bash
# Sentinel Performance Testing Automation Script
# Applies optimizations and runs comprehensive load tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=========================================="
echo "Sentinel Performance Testing Suite"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not found. Please install Docker.${NC}"
    exit 1
fi

if ! command -v locust &> /dev/null; then
    echo -e "${RED}ERROR: Locust not found. Installing...${NC}"
    pip install locust
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}WARNING: jq not found. Install for JSON parsing.${NC}"
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Step 2: Start infrastructure services
echo -e "${YELLOW}Step 2: Starting infrastructure services...${NC}"
cd "$PROJECT_ROOT"

docker-compose up -d postgres redis redpanda
sleep 5

# Wait for services to be ready
echo "Waiting for Postgres..."
for i in {1..30}; do
    if docker exec sentinel-postgres pg_isready -U sentinel &> /dev/null; then
        echo -e "${GREEN}✓ Postgres ready${NC}"
        break
    fi
    sleep 1
done

echo "Waiting for Redis..."
for i in {1..30}; do
    if docker exec sentinel-redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Redis ready${NC}"
        break
    fi
    sleep 1
done

echo ""

# Step 3: Apply database optimizations
echo -e "${YELLOW}Step 3: Applying database indexes...${NC}"

if [ -f "alembic/versions/performance_indexes.sql" ]; then
    docker exec -i sentinel-postgres psql -U sentinel -d sentinel < alembic/versions/performance_indexes.sql
    echo -e "${GREEN}✓ Database indexes applied${NC}"
else
    echo -e "${YELLOW}WARNING: performance_indexes.sql not found${NC}"
fi

echo ""

# Step 4: Apply code optimizations (optional - requires user confirmation)
echo -e "${YELLOW}Step 4: Apply code optimizations?${NC}"
echo "This will replace api/dependencies.py with optimized version."
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "api/dependencies_optimized.py" ]; then
        cp api/dependencies.py api/dependencies.backup.py
        cp api/dependencies_optimized.py api/dependencies.py
        echo -e "${GREEN}✓ Code optimizations applied (backup saved)${NC}"
    else
        echo -e "${RED}ERROR: dependencies_optimized.py not found${NC}"
    fi
else
    echo -e "${YELLOW}Skipping code optimizations${NC}"
fi

echo ""

# Step 5: Start API server
echo -e "${YELLOW}Step 5: Starting API server...${NC}"

# Check if already running
if curl -s http://localhost:8000/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API server already running${NC}"
else
    echo "Starting uvicorn server..."
    echo "Please run in another terminal:"
    echo "  cd $PROJECT_ROOT"
    echo "  source .venv/Scripts/activate"
    echo "  uvicorn api.main:app --host 127.0.0.1 --port 8000"
    echo ""
    read -p "Press ENTER when server is running..."
fi

# Verify API is responding
if curl -s http://localhost:8000/health/live > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API server responding${NC}"
else
    echo -e "${RED}ERROR: API server not responding at http://localhost:8000${NC}"
    exit 1
fi

echo ""

# Step 6: Run load tests
echo -e "${YELLOW}Step 6: Running load tests...${NC}"
echo ""

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
RESULTS_DIR="$PROJECT_ROOT/benchmarks/results-$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

# Baseline test (50 users, 5 min)
echo -e "${YELLOW}Running BASELINE test (50 users, 5 min)...${NC}"
locust -f tests/load/locustfile_enhanced.py \
    --host http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 300s \
    --headless \
    --html "$RESULTS_DIR/baseline-report.html" \
    --csv "$RESULTS_DIR/baseline" \
    2>&1 | tee "$RESULTS_DIR/baseline.log"

echo -e "${GREEN}✓ Baseline test complete${NC}"
echo ""
sleep 10

# Stress test (200 users, 10 min)
echo -e "${YELLOW}Running STRESS test (200 users, 10 min)...${NC}"
locust -f tests/load/locustfile_enhanced.py \
    --host http://localhost:8000 \
    --users 200 \
    --spawn-rate 10 \
    --run-time 600s \
    --headless \
    --html "$RESULTS_DIR/stress-report.html" \
    --csv "$RESULTS_DIR/stress" \
    2>&1 | tee "$RESULTS_DIR/stress.log"

echo -e "${GREEN}✓ Stress test complete${NC}"
echo ""
sleep 10

# Spike test (500 users, 5 min)
echo -e "${YELLOW}Running SPIKE test (500 users, 5 min)...${NC}"
locust -f tests/load/locustfile_enhanced.py \
    --host http://localhost:8000 \
    --users 500 \
    --spawn-rate 50 \
    --run-time 300s \
    --headless \
    --html "$RESULTS_DIR/spike-report.html" \
    --csv "$RESULTS_DIR/spike" \
    2>&1 | tee "$RESULTS_DIR/spike.log"

echo -e "${GREEN}✓ Spike test complete${NC}"
echo ""

# Step 7: Generate summary report
echo -e "${YELLOW}Step 7: Generating summary report...${NC}"

cat > "$RESULTS_DIR/SUMMARY.md" << EOF
# Sentinel Performance Test Results
**Date**: $(date)
**Test ID**: $TIMESTAMP

## Test Configuration
- API Endpoint: http://localhost:8000
- Load Testing Tool: Locust
- Test Script: tests/load/locustfile_enhanced.py

## Test Results

### Baseline Test (50 users, 5 min)
See: baseline-report.html, baseline.log

### Stress Test (200 users, 10 min)
See: stress-report.html, stress.log

### Spike Test (500 users, 5 min)
See: spike-report.html, spike.log

## Analysis

View detailed metrics in:
- HTML reports: *-report.html
- CSV data: *.csv
- Raw logs: *.log
- JSON reports: benchmarks/load-test-*.json

## Next Steps
1. Review HTML reports for detailed metrics
2. Compare with performance targets in PERFORMANCE-OPTIMIZATION-REPORT.md
3. Analyze bottlenecks if targets not met
4. Adjust infrastructure or code as needed
EOF

echo -e "${GREEN}✓ Summary report generated${NC}"
echo ""

# Step 8: Display results
echo "=========================================="
echo -e "${GREEN}Performance Testing Complete!${NC}"
echo "=========================================="
echo ""
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "View reports:"
echo "  - Summary: $RESULTS_DIR/SUMMARY.md"
echo "  - Baseline: $RESULTS_DIR/baseline-report.html"
echo "  - Stress: $RESULTS_DIR/stress-report.html"
echo "  - Spike: $RESULTS_DIR/spike-report.html"
echo ""

# Display quick metrics if jq available
if command -v jq &> /dev/null; then
    echo "Quick Metrics:"
    LATEST_JSON=$(ls -t benchmarks/load-test-*.json 2>/dev/null | head -1)
    if [ -f "$LATEST_JSON" ]; then
        echo "  Throughput: $(jq -r '.throughput_rps' $LATEST_JSON) RPS"
        echo "  p99 Latency: $(jq -r '.latency_p99' $LATEST_JSON) ms"
        echo "  Error Rate: $(jq -r '.error_rate_pct' $LATEST_JSON)%"
    fi
fi

echo ""
echo "Done!"
