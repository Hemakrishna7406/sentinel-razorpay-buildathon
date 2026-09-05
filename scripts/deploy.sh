#!/bin/bash
set -euo pipefail

# Sentinel Production Deployment Script
# Usage: ./scripts/deploy.sh [environment]

ENVIRONMENT="${1:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
EKS_CLUSTER="sentinel-${ENVIRONMENT}"

echo "======================================"
echo "Sentinel Deployment to ${ENVIRONMENT}"
echo "======================================"

# Preflight checks
echo "[1/7] Running preflight checks..."

if ! command -v kubectl &> /dev/null; then
    echo "ERROR: kubectl not installed"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo "ERROR: helm not installed"
    exit 1
fi

if ! command -v aws &> /dev/null; then
    echo "ERROR: aws CLI not installed"
    exit 1
fi

# Configure kubectl
echo "[2/7] Configuring kubectl..."
aws eks update-kubeconfig \
    --name "$EKS_CLUSTER" \
    --region "$AWS_REGION"

# Verify cluster access
if ! kubectl get nodes &> /dev/null; then
    echo "ERROR: Cannot access EKS cluster"
    exit 1
fi

# Build and push Docker images
echo "[3/7] Building Docker images..."
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$REGISTRY"

for SERVICE in api worker audit; do
    echo "Building sentinel-${SERVICE}:${IMAGE_TAG}..."
    docker build \
        -t "${REGISTRY}/sentinel-${SERVICE}:${IMAGE_TAG}" \
        -f "docker/Dockerfile.${SERVICE}" .

    docker push "${REGISTRY}/sentinel-${SERVICE}:${IMAGE_TAG}"
done

# Apply Kubernetes manifests
echo "[4/7] Applying Kubernetes manifests..."

kubectl apply -f security/secrets-management.yaml
kubectl apply -f security/pod-security-policy.yaml
kubectl apply -f k8s/production/network-policy.yaml
kubectl apply -f k8s/production/monitoring.yaml

# Deploy with Helm
echo "[5/7] Deploying with Helm..."

helm upgrade --install sentinel ./helm/sentinel \
    --namespace sentinel \
    --create-namespace \
    --set image.tag="$IMAGE_TAG" \
    --set image.repository="$REGISTRY" \
    --set environment="$ENVIRONMENT" \
    --wait --timeout 10m

# Verify deployment
echo "[6/7] Verifying deployment..."

kubectl rollout status deployment/sentinel-api -n sentinel --timeout=5m
kubectl rollout status deployment/sentinel-worker -n sentinel --timeout=5m
kubectl rollout status deployment/sentinel-audit -n sentinel --timeout=5m

# Health check
echo "[7/7] Running health checks..."

API_ENDPOINT=$(kubectl get svc sentinel-api -n sentinel -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

if [ -z "$API_ENDPOINT" ]; then
    echo "WARNING: API endpoint not ready yet (LoadBalancer provisioning)"
else
    echo "Waiting for LoadBalancer to be ready..."
    sleep 30

    if curl -f "http://${API_ENDPOINT}/health/live" &> /dev/null; then
        echo "✓ Health check passed"
    else
        echo "✗ Health check failed"
        exit 1
    fi
fi

echo ""
echo "======================================"
echo "Deployment successful!"
echo "======================================"
echo "Environment: ${ENVIRONMENT}"
echo "Image Tag: ${IMAGE_TAG}"
echo "API Endpoint: ${API_ENDPOINT}"
echo ""
echo "Next steps:"
echo "1. kubectl get pods -n sentinel"
echo "2. kubectl logs -f deployment/sentinel-api -n sentinel"
echo "3. Open Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
