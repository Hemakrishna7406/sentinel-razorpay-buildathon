#!/bin/bash
# Sentinel Load Testing Script
# Runs comprehensive load tests and generates reports

set -e

echo "========================================="
echo "Sentinel Load Testing Suite"
echo "========================================="
echo ""

# Check if locust is installed
if ! command -v locust &> /dev/null; then
    echo "❌ Locust is not installed."
    echo "Install with: pip install locust"
    exit 1
fi

# Check if server is running
if ! curl -s http://localhost:8000/health/live > /dev/null; then
    echo "❌ Sentinel API is not running on localhost:8000"
    echo "Start it with: uvicorn api.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

echo "✅ Sentinel API is healthy"
echo ""

# Create output directory
mkdir -p benchmarks/load-tests
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="benchmarks/load-tests/${TIMESTAMP}"
mkdir -p "${OUTPUT_DIR}"

echo "📊 Running load tests..."
echo "Output directory: ${OUTPUT_DIR}"
echo ""

# Test 1: Baseline - Moderate load
echo "Test 1: Baseline (50 users, 60s)"
locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 60s \
    --headless \
    --html "${OUTPUT_DIR}/baseline_report.html" \
    --csv "${OUTPUT_DIR}/baseline" \
    --only-summary

echo ""

# Test 2: Stress - High load
echo "Test 2: Stress Test (200 users, 90s)"
locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --users 200 \
    --spawn-rate 20 \
    --run-time 90s \
    --headless \
    --html "${OUTPUT_DIR}/stress_report.html" \
    --csv "${OUTPUT_DIR}/stress" \
    --only-summary

echo ""

# Test 3: Spike - Sudden load increase
echo "Test 3: Spike Test (500 users, 30s)"
locust -f tests/load/locustfile.py \
    --host http://localhost:8000 \
    --users 500 \
    --spawn-rate 50 \
    --run-time 30s \
    --headless \
    --html "${OUTPUT_DIR}/spike_report.html" \
    --csv "${OUTPUT_DIR}/spike" \
    --only-summary

echo ""
echo "========================================="
echo "✅ Load tests complete!"
echo "========================================="
echo ""
echo "Reports generated in: ${OUTPUT_DIR}"
echo ""
echo "View reports:"
echo "  - Baseline: ${OUTPUT_DIR}/baseline_report.html"
echo "  - Stress:   ${OUTPUT_DIR}/stress_report.html"
echo "  - Spike:    ${OUTPUT_DIR}/spike_report.html"
echo ""
echo "Summary CSVs:"
ls -lh "${OUTPUT_DIR}"/*.csv 2>/dev/null || true
echo ""
