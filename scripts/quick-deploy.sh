#!/bin/bash
set -euo pipefail

# Sentinel Quick Deploy - Replaces variable placeholders with actual values from Terraform outputs
# Usage: ./scripts/quick-deploy.sh

echo "========================================="
echo "Sentinel Quick Deploy"
echo "========================================="

ENVIRONMENT="${ENVIRONMENT:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Check Terraform outputs exist
if [ ! -f "terraform/terraform.tfstate" ]; then
    echo "ERROR: Terraform state not found. Run 'terraform apply' first."
    exit 1
fi

echo "[1/5] Extracting Terraform outputs..."
cd terraform
RDS_ENDPOINT=$(terraform output -raw rds_endpoint | cut -d: -f1)
REDIS_ENDPOINT=$(terraform output -raw redis_endpoint)
MSK_BOOTSTRAP_BROKERS=$(terraform output -raw msk_bootstrap_brokers)
IRSA_ROLE_ARN=$(terraform output -raw api_irsa_role_arn)
cd ..

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "[2/5] Retrieving secrets from AWS Secrets Manager..."
DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id sentinel-production-rds-password --query SecretString --output text)
API_KEY=$(aws secretsmanager get-secret-value --secret-id sentinel-production-api-key --query SecretString --output text)
ADMIN_API_KEY=$(aws secretsmanager get-secret-value --secret-id sentinel-production-admin-key --query SecretString --output text)
CAPABILITY_SIGNING_KEY=$(openssl rand -hex 32)

echo "[3/5] Generating production values file..."
cat > helm/sentinel/values-production-rendered.yaml <<EOF
global:
  environment: production
  imageRegistry: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

api:
  image:
    repository: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/sentinel/sentinel-api
    tag: ${IMAGE_TAG:-latest}

  env:
    DATABASE_URL: "postgresql://sentinel_admin:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/sentinel"
    REDIS_URL: "redis://${REDIS_ENDPOINT}:6379"
    KAFKA_BOOTSTRAP_SERVERS: "${MSK_BOOTSTRAP_BROKERS}"
    API_KEY: "${API_KEY}"
    ADMIN_API_KEY: "${ADMIN_API_KEY}"
    CAPABILITY_SIGNING_KEY: "${CAPABILITY_SIGNING_KEY}"
    ENABLE_DEMO_ENDPOINTS: "false"

worker:
  image:
    repository: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/sentinel/sentinel-worker
    tag: ${IMAGE_TAG:-latest}

  env:
    DATABASE_URL: "postgresql://sentinel_admin:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/sentinel"
    REDIS_URL: "redis://${REDIS_ENDPOINT}:6379"
    KAFKA_BOOTSTRAP_SERVERS: "${MSK_BOOTSTRAP_BROKERS}"

audit:
  image:
    repository: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/sentinel/sentinel-audit
    tag: ${IMAGE_TAG:-latest}

  env:
    DATABASE_URL: "postgresql://sentinel_admin:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/sentinel"
    KAFKA_BOOTSTRAP_SERVERS: "${MSK_BOOTSTRAP_BROKERS}"

serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: ${IRSA_ROLE_ARN}

redis:
  enabled: false
kafka:
  enabled: false
postgresql:
  enabled: false
EOF

echo "[4/5] Deploying to EKS..."
helm upgrade --install sentinel ./helm/sentinel \
    --namespace sentinel \
    --create-namespace \
    -f helm/sentinel/values.yaml \
    -f helm/sentinel/values-production-rendered.yaml \
    --wait --timeout 10m

echo "[5/5] Verifying deployment..."
kubectl rollout status deployment/sentinel-api -n sentinel --timeout=5m
kubectl rollout status deployment/sentinel-worker -n sentinel --timeout=5m

API_ENDPOINT=$(kubectl get svc sentinel-api -n sentinel -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo "API Endpoint: http://${API_ENDPOINT}"
echo ""
echo "Test health:"
echo "  curl http://${API_ENDPOINT}/health/live"
echo ""
echo "View logs:"
echo "  kubectl logs -f deployment/sentinel-api -n sentinel"
echo ""
echo "Access Grafana:"
echo "  kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
