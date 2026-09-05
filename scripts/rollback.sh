#!/bin/bash
set -euo pipefail

# Sentinel Rollback Script
# Usage: ./scripts/rollback.sh [revision-number]

ENVIRONMENT="${ENVIRONMENT:-production}"
NAMESPACE="sentinel"

echo "======================================"
echo "Sentinel Rollback"
echo "======================================"

# Show deployment history
echo "Deployment history:"
helm history sentinel -n "$NAMESPACE"

# Get revision to rollback to
if [ $# -eq 0 ]; then
    echo ""
    read -p "Enter revision number to rollback to (or 0 for previous): " REVISION
else
    REVISION="$1"
fi

if [ "$REVISION" = "0" ]; then
    echo "Rolling back to previous revision..."
    helm rollback sentinel -n "$NAMESPACE" --wait --timeout 5m
else
    echo "Rolling back to revision $REVISION..."
    helm rollback sentinel "$REVISION" -n "$NAMESPACE" --wait --timeout 5m
fi

# Verify rollback
echo "Verifying rollback..."

kubectl rollout status deployment/sentinel-api -n "$NAMESPACE" --timeout=5m
kubectl rollout status deployment/sentinel-worker -n "$NAMESPACE" --timeout=5m

echo ""
echo "✓ Rollback complete!"
echo ""
echo "Current deployment:"
helm list -n "$NAMESPACE"
