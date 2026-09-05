# CI/CD Pipeline Guide

## Overview

Sentinel uses GitHub Actions for continuous integration and deployment:

1. **CI Pipeline** (`ci.yml`) - Lint, test, security scan, build
2. **CD Pipeline** (`cd.yml`) - Deploy to EKS production
3. **Terraform Pipeline** (`terraform.yml`) - Infrastructure changes

## Setup

### 1. Configure GitHub Secrets

Navigate to: `Settings` → `Secrets and variables` → `Actions`

**Required Secrets:**

```bash
AWS_ACCESS_KEY_ID         # IAM user with ECR + EKS permissions
AWS_SECRET_ACCESS_KEY     # Corresponding secret key
AWS_ACCOUNT_ID            # Your AWS account ID
SLACK_WEBHOOK            # Slack webhook for notifications
```

**Optional Secrets:**

```bash
CODECOV_TOKEN            # For coverage reporting
PAGERDUTY_SERVICE_KEY    # For critical alerts
```

### 2. Create IAM User for CI/CD

**Policy Document** (`ci-cd-policy.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "eks:DescribeCluster",
        "eks:ListClusters"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

**Create User:**

```bash
aws iam create-user --user-name sentinel-ci-cd

aws iam put-user-policy \
  --user-name sentinel-ci-cd \
  --policy-name SentinelCICDPolicy \
  --policy-document file://ci-cd-policy.json

aws iam create-access-key --user-name sentinel-ci-cd
```

### 3. Configure kubectl Access for CI/CD

Add to EKS ConfigMap:

```bash
kubectl edit configmap aws-auth -n kube-system
```

Add entry:

```yaml
mapUsers: |
  - userarn: arn:aws:iam::ACCOUNT_ID:user/sentinel-ci-cd
    username: sentinel-ci-cd
    groups:
      - system:masters
```

## CI Pipeline

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Stages:**

### 1. Lint and Test

```yaml
- black --check .           # Code formatting
- ruff check .             # Linting
- mypy api/ core/          # Type checking
- pytest tests/ --cov      # Unit + integration tests
```

**Local Testing:**

```bash
# Run all checks locally before pushing
make lint
make typecheck
make test
```

### 2. Security Scan

```yaml
- trivy fs .                    # Vulnerability scanning
- bandit -r api/ core/         # Security linting
```

**Fix Common Issues:**

```bash
# Update dependencies with vulnerabilities
pip install --upgrade package-name

# Review Bandit findings
bandit -r . -f json | jq '.results'
```

### 3. Build and Push

Builds Docker images for:
- `sentinel-api`
- `sentinel-worker`
- `sentinel-audit`
- `sentinel-frontend`

Tags:
- `<git-sha>` (immutable)
- `latest` (rolling)

## CD Pipeline

**Triggers:**
- Push to `main` (auto-deploy)

**Stages:**

### 1. Deploy to EKS

```bash
helm upgrade --install sentinel ./helm/sentinel \
  --set image.tag=$IMAGE_TAG \
  --wait --timeout 10m
```

**Deployment Strategy**: Rolling update
- Max surge: 1
- Max unavailable: 0

### 2. Verify Deployment

```bash
kubectl rollout status deployment/sentinel-api
curl -f http://API_URL/health
```

### 3. Rollback on Failure

**Manual Rollback:**

```bash
# List revisions
helm history sentinel -n sentinel

# Rollback to previous
helm rollback sentinel -n sentinel

# Rollback to specific revision
helm rollback sentinel 5 -n sentinel
```

**Automatic Rollback** (configured in CD pipeline):
- Health check fails → automatic rollback
- Deployment timeout (10min) → automatic rollback

## Terraform Pipeline

**Triggers:**
- Push to `main` with changes in `terraform/**`
- Pull requests with terraform changes

**Stages:**

### 1. Terraform Validate

```bash
terraform fmt -check
terraform validate
```

### 2. Terraform Plan

Generates plan artifact for review.

### 3. Terraform Apply

**Only on** `main` push. Requires manual approval via GitHub Environment protection.

**Protection Rules:**

```yaml
environment: production
required_reviewers: 2
wait_timer: 5  # minutes
```

## Monitoring CI/CD

### GitHub Actions Dashboard

View workflow runs: `Actions` tab

### Slack Notifications

Configure in `.github/workflows/cd.yml`:

```yaml
- uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### CloudWatch Logs

EKS deployment logs:

```bash
aws logs tail /aws/eks/sentinel-production/cluster --follow
```

## Troubleshooting

### Build Fails - "denied: Your authorization token has expired"

**Fix**: Refresh ECR login in CI:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

### Deploy Fails - "error: You must be logged in to the server"

**Fix**: Update kubeconfig in CD:

```bash
aws eks update-kubeconfig \
  --name sentinel-production \
  --region us-east-1
```

### Helm Upgrade Timeout

**Fix**: Increase timeout or check pod status:

```bash
kubectl get pods -n sentinel
kubectl describe pod POD_NAME -n sentinel
kubectl logs POD_NAME -n sentinel
```

### Test Failures in CI

**Debug locally with act**:

```bash
# Install act: https://github.com/nektos/act
act -j lint-and-test
```

## Best Practices

1. **Never skip tests**: All PRs must pass CI
2. **Immutable tags**: Use git SHA for production deploys
3. **Gradual rollout**: Deploy to staging → canary → production
4. **Rollback plan**: Always test rollback procedures
5. **Secrets rotation**: Rotate AWS keys quarterly
6. **Monitor deployments**: Watch metrics for 15min post-deploy

## Advanced: Multi-Environment Setup

**Structure:**

```
.github/workflows/
├── ci.yml                    # All environments
├── cd-staging.yml           # Auto-deploy to staging
├── cd-production.yml        # Manual approval for prod
└── terraform-{env}.yml      # Per-environment infra
```

**Branch Strategy:**

- `develop` → auto-deploy to **staging**
- `main` → manual deploy to **production**
- `feature/*` → run CI only

**Helm Values per Environment:**

```bash
helm upgrade --install sentinel ./helm/sentinel \
  -f helm/sentinel/values-staging.yaml    # or values-production.yaml
```
