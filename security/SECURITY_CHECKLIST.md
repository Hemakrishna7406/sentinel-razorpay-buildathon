# Production Security Checklist

## Pre-Deployment

### Infrastructure Security

- [ ] **VPC Isolation**: Verify private subnets for workloads
- [ ] **Security Groups**: Implement least-privilege ingress/egress
- [ ] **Encryption at Rest**: Enable for RDS, ElastiCache, MSK, EBS
- [ ] **Encryption in Transit**: TLS 1.3 for all inter-service communication
- [ ] **Secrets Management**: Use AWS Secrets Manager + IRSA
- [ ] **IAM Roles**: Follow least-privilege principle
- [ ] **VPC Flow Logs**: Enable for audit trail
- [ ] **GuardDuty**: Enable threat detection
- [ ] **AWS Config**: Enable compliance monitoring

### Application Security

- [ ] **API Authentication**: Set strong `API_KEY` and `ADMIN_API_KEY`
- [ ] **Rate Limiting**: Configure per client_id limits
- [ ] **Input Validation**: Pydantic schemas on all endpoints
- [ ] **SQL Injection**: Use parameterized queries only
- [ ] **CORS**: Restrict to known domains
- [ ] **CSP Headers**: Set Content-Security-Policy
- [ ] **Audit Logging**: Enable all writes to audit trail
- [ ] **Capability Tokens**: 5-second TTL, HMAC signing
- [ ] **Circuit Breakers**: Fail-closed on external dependency failure

### Kubernetes Security

- [ ] **Pod Security Policy**: Apply `sentinel-restricted` PSP
- [ ] **Network Policies**: Deny-all default, allow specific
- [ ] **RBAC**: Minimal service account permissions
- [ ] **Image Scanning**: Trivy scan on push to ECR
- [ ] **Resource Limits**: Set CPU/memory limits on all pods
- [ ] **Read-Only Root FS**: `readOnlyRootFilesystem: true`
- [ ] **Non-Root User**: `runAsNonRoot: true`
- [ ] **Drop Capabilities**: `drop: [ALL]`

### Database Security

- [ ] **Strong Password**: 32+ char random password in Secrets Manager
- [ ] **Multi-AZ**: Enable for HA
- [ ] **Automated Backups**: 7-day retention minimum
- [ ] **SSL/TLS**: Require encrypted connections
- [ ] **Parameter Group**: Enforce `log_connections`, `log_statement=all`
- [ ] **Connection Pooling**: Limit connections per service
- [ ] **Delete Protection**: Enable on RDS instance

### Redis Security

- [ ] **Auth Token**: Set strong `AUTH` token
- [ ] **Encryption in Transit**: Enable TLS
- [ ] **Multi-AZ**: Enable automatic failover
- [ ] **Snapshot Encryption**: Enable at-rest encryption
- [ ] **Network Isolation**: Private subnets only

### Kafka Security

- [ ] **TLS**: Client-broker encryption enabled
- [ ] **ACLs**: Restrict topic read/write per service
- [ ] **Encryption at Rest**: KMS key for EBS volumes
- [ ] **CloudWatch Logs**: Enable broker logs

## Post-Deployment

### Monitoring

- [ ] **Security Alerts**: Configure PagerDuty for critical events
- [ ] **Anomaly Detection**: Set baselines for traffic patterns
- [ ] **Audit Trail Review**: Weekly review of high-privilege actions
- [ ] **Failed Auth Attempts**: Alert on >10 failures/min
- [ ] **Certificate Expiry**: Alert 30 days before expiration

### Compliance

- [ ] **Data Retention**: Enforce 90-day audit log retention
- [ ] **Access Logs**: Review S3/ALB access logs monthly
- [ ] **Vulnerability Scanning**: Weekly Trivy scans
- [ ] **Dependency Updates**: Monthly security patch cycle
- [ ] **Penetration Testing**: Quarterly external pentest

### Incident Response

- [ ] **Runbooks**: Document breach response procedures
- [ ] **Rollback Plan**: Test rollback within 5 minutes
- [ ] **Contact List**: Maintain oncall rotation
- [ ] **Backup Restoration**: Test monthly
- [ ] **Key Rotation**: Rotate API keys quarterly

## Critical Production Settings

### Environment Variables

```bash
# MUST be set in production
ENVIRONMENT=production
ENABLE_DEMO_ENDPOINTS=false

# MUST be strong random values
API_KEY=<64-char-hex>
ADMIN_API_KEY=<64-char-hex>
DATABASE_PASSWORD=<32-char-random>
REDIS_PASSWORD=<32-char-random>

# MUST use production endpoints
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/sentinel
REDIS_URL=redis://:pass@elasticache-endpoint:6379
KAFKA_BOOTSTRAP_SERVERS=msk-broker-1:9094,msk-broker-2:9094
```

### Validation Script

```bash
# Run before deploy
./scripts/security-validator.sh

# Checks:
# - API keys != "test" / "demo" / ""
# - ENABLE_DEMO_ENDPOINTS=false
# - TLS certificates valid
# - No plaintext secrets in code
# - Image CVE count < threshold
```

## Zero-Trust Architecture

### Network Segmentation

```
Internet → ALB → API Pods (Public subnet)
                    ↓
                Worker Pods (Private subnet)
                    ↓
            RDS/Redis/MSK (Database subnet)
```

### Authentication Layers

1. **ALB**: WAF rules for DDoS protection
2. **API Gateway**: Rate limiting by IP
3. **Application**: API key validation
4. **Service Mesh**: mTLS between services
5. **Database**: Connection pooling + auth

## Audit & Compliance

### SOC 2 Requirements

- [ ] Access control logs retained 1 year
- [ ] Change management process documented
- [ ] Encryption at rest and in transit
- [ ] Annual security training for engineers
- [ ] Vendor risk assessment (AWS services)

### PCI DSS (if handling cards)

- [ ] Tokenize card data immediately
- [ ] Never log full PAN
- [ ] Quarterly vulnerability scans
- [ ] Annual penetration test
- [ ] Firewall rules documented

## Emergency Contacts

**Security Incident**: `security@company.com`  
**PagerDuty**: https://company.pagerduty.com  
**AWS Support**: Enterprise tier with TAM  

## Security Review Cadence

- **Daily**: Failed auth alerts, CVE feeds
- **Weekly**: Access log review, failed deployment analysis
- **Monthly**: Dependency updates, backup restoration test
- **Quarterly**: Pentest, key rotation, DR drill
- **Annually**: SOC 2 audit, policy review
