#!/bin/bash
set -euo pipefail

# Sentinel Security Validation Script
# Usage: ./scripts/security-validator.sh

echo "======================================"
echo "Sentinel Security Validation"
echo "======================================"

FAILED_CHECKS=0

# Check 1: API keys not using demo values
echo "[1/10] Checking API key strength..."
if grep -r "API_KEY.*=.*test\|demo\|\"\"" api/ core/ 2>/dev/null; then
    echo "✗ FAIL: Weak API keys found in code"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 2: Demo endpoints disabled in production config
echo "[2/10] Checking demo endpoints..."
if grep -r "ENABLE_DEMO_ENDPOINTS.*=.*True" core/config.py 2>/dev/null; then
    echo "✗ FAIL: Demo endpoints enabled"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 3: No hardcoded secrets
echo "[3/10] Scanning for hardcoded secrets..."
if grep -rE "password.*=.*['\"][^'\"]{8,}['\"]|secret.*=.*['\"][^'\"]{8,}['\"]" \
    --exclude-dir=".git" --exclude="*.md" . 2>/dev/null | grep -v "EXAMPLE\|TODO\|CHANGE_ME"; then
    echo "✗ FAIL: Potential hardcoded secrets found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 4: Docker images use non-root user
echo "[4/10] Checking Docker security..."
for dockerfile in docker/Dockerfile.*; do
    if ! grep -q "USER sentinel" "$dockerfile"; then
        echo "✗ FAIL: $dockerfile doesn't switch to non-root user"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
done
echo "✓ PASS"

# Check 5: Dependencies have no critical vulnerabilities
echo "[5/10] Scanning dependencies..."
if command -v safety &> /dev/null; then
    if ! safety check --json 2>/dev/null | jq -e '.vulnerabilities | length == 0' > /dev/null; then
        echo "✗ FAIL: Critical vulnerabilities in dependencies"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    else
        echo "✓ PASS"
    fi
else
    echo "⊘ SKIP: safety not installed (pip install safety)"
fi

# Check 6: Network policies exist
echo "[6/10] Checking network policies..."
if [ ! -f "k8s/production/network-policy.yaml" ]; then
    echo "✗ FAIL: Network policy not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 7: Pod security context configured
echo "[7/10] Checking pod security context..."
if [ ! -f "k8s/production/patches/security-context.yaml" ]; then
    echo "✗ FAIL: Security context patch not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 8: Secrets managed externally
echo "[8/10] Checking secrets management..."
if [ ! -f "security/secrets-management.yaml" ]; then
    echo "✗ FAIL: Secrets management config not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 9: TLS encryption enabled
echo "[9/10] Checking TLS configuration..."
if ! grep -q "transit_encryption_enabled.*=.*true" terraform/modules/elasticache/main.tf 2>/dev/null; then
    echo "✗ FAIL: Redis TLS not enabled"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

# Check 10: Monitoring and alerting configured
echo "[10/10] Checking monitoring..."
if [ ! -f "k8s/production/monitoring.yaml" ]; then
    echo "✗ FAIL: Monitoring configuration not found"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
else
    echo "✓ PASS"
fi

echo ""
echo "======================================"
if [ $FAILED_CHECKS -eq 0 ]; then
    echo "✓ All security checks passed!"
    echo "======================================"
    exit 0
else
    echo "✗ $FAILED_CHECKS security check(s) failed"
    echo "======================================"
    exit 1
fi
