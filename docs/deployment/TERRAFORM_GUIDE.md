# Terraform Deployment Guide

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** v1.5+ installed
3. **AWS CLI** configured with credentials
4. **S3 Bucket** for Terraform state: `sentinel-terraform-state`
5. **DynamoDB Table** for state locking: `sentinel-terraform-locks`

## Initial Setup

### 1. Create State Backend

```bash
# Create S3 bucket for state
aws s3api create-bucket \
  --bucket sentinel-terraform-state \
  --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket sentinel-terraform-state \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket sentinel-terraform-state \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name sentinel-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. Initialize Terraform

```bash
cd terraform
terraform init
```

## Deployment

### Plan Changes

```bash
terraform plan -out=tfplan
```

### Apply Infrastructure

```bash
terraform apply tfplan
```

**Expected Duration**: 25-35 minutes
- VPC: ~2 min
- EKS Cluster: ~15-20 min
- RDS: ~5-8 min
- ElastiCache: ~3-5 min
- MSK: ~8-12 min

### Output Connection Details

```bash
terraform output
```

Save these outputs:
- `eks_cluster_endpoint`
- `rds_endpoint`
- `redis_endpoint`
- `msk_bootstrap_brokers`

## Post-Deployment

### 1. Configure kubectl

```bash
aws eks update-kubeconfig \
  --name sentinel-production \
  --region us-east-1
```

### 2. Verify Cluster Access

```bash
kubectl get nodes
kubectl get namespaces
```

### 3. Install Core Add-ons

```bash
# AWS Load Balancer Controller
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=sentinel-production \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Metrics Server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Cluster Autoscaler
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm install cluster-autoscaler autoscaler/cluster-autoscaler \
  --namespace kube-system \
  --set autoDiscovery.clusterName=sentinel-production \
  --set awsRegion=us-east-1
```

### 4. Install Monitoring Stack

```bash
# Prometheus + Grafana
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring \
  --create-namespace \
  -f ../monitoring/prometheus/values.yaml
```

## Cost Estimate

**Monthly AWS Costs** (us-east-1):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| EKS Control Plane | 1 cluster | $73 |
| EC2 (EKS Nodes) | 3x t3.xlarge | ~$450 |
| RDS PostgreSQL | db.r6g.xlarge Multi-AZ | ~$550 |
| ElastiCache Redis | 3x cache.r6g.large | ~$450 |
| MSK Kafka | 3x kafka.m5.large | ~$540 |
| NAT Gateway | 3x AZ | ~$100 |
| Data Transfer | 1TB egress | ~$90 |
| **TOTAL** | | **~$2,253/month** |

## Teardown

**WARNING**: This will destroy ALL infrastructure.

```bash
# Delete Helm releases first
helm uninstall sentinel -n sentinel
helm uninstall prometheus -n monitoring

# Destroy Terraform resources
terraform destroy
```

## Troubleshooting

### EKS Node Group Fails

```bash
# Check IAM role permissions
aws iam get-role --role-name sentinel-production-eks-node-role
```

### RDS Connection Issues

```bash
# Verify security group rules
aws ec2 describe-security-groups \
  --filters Name=tag:Name,Values=sentinel-production-rds-sg
```

### State Lock Issues

```bash
# Force unlock if stuck
terraform force-unlock <LOCK_ID>
```

## Security Hardening

1. **Enable VPC Flow Logs**:
```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids $(terraform output -raw vpc_id) \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/sentinel-production
```

2. **Enable GuardDuty**:
```bash
aws guardduty create-detector --enable
```

3. **Enable AWS Config**:
```bash
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::ACCOUNT:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig \
  --recording-group allSupported=true,includeGlobalResourceTypes=true
```

## Maintenance

### Upgrade EKS Cluster

```bash
# Update cluster version in variables.tf
# Then apply
terraform apply -target=module.eks
```

### Scale Node Group

```bash
# Update in terraform/variables.tf or via CLI
aws eks update-nodegroup-config \
  --cluster-name sentinel-production \
  --nodegroup-name sentinel-production-ng \
  --scaling-config minSize=3,maxSize=15,desiredSize=5
```
