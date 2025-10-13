# AlphaPulse Production Deployment Checklist

## Overview

This checklist ensures all components are ready for production deployment to the hybrid cloud infrastructure (Hetzner CPX21 + AWS S3).

## Pre-Deployment Verification

### ✅ 1. Infrastructure as Code (Terraform)

- [x] Terraform modules validated (`terraform validate`)
- [x] Multi-provider configuration (AWS + Hetzner) tested
- [x] Cost optimization verified: $11.15/month total
- [x] Cloud-init configuration for Docker Compose deployment
- [x] SSH key generation and secure access configured
- [x] Network security groups and firewall rules defined

### ✅ 2. Docker Services

- [x] All services running locally: PostgreSQL, MinIO, MLflow, Mage.ai
- [x] Health checks passing for all services
- [x] Service ports correctly mapped
- [x] Volume persistence configured
- [x] Environment variables properly set

### ✅ 3. Data Pipeline

- [x] BTC price pipeline functional with pandas-ta integration
- [x] Feature integration pipeline fully implemented
- [x] Decimal migration completed (no Float types in financial data)
- [x] PostgreSQL schema uses DECIMAL types with appropriate precision
- [x] Data quality checks implemented

### ✅ 4. FastAPI Backend

- [x] FastAPI application starts successfully
- [x] Decimal JSON encoder working correctly
- [x] API endpoints functional: health, prices, signals, indicators
- [x] Database integration with SQLAlchemy
- [x] CORS middleware configured
- [x] OpenAPI documentation available at `/docs` and `/redoc`

### ✅ 5. Security

- [x] JWT authentication implemented
- [x] Role-based access control (RBAC) configured
- [x] Password hashing with bcrypt
- [x] API key management with scopes and expiration
- [x] Audit logging for security events
- [x] Default roles created: viewer, trader, data_scientist, admin

### ✅ 6. Monitoring & Observability

- [x] Evidently AI data drift detection implemented
- [x] Performance testing baseline established
- [x] API response time thresholds defined
- [x] Database query performance benchmarks
- [x] Alerting configuration for critical issues

### ✅ 7. CI/CD Pipeline

- [x] GitHub Actions workflows configured:
  - [x] Terraform validation
  - [x] Terraform deployment
  - [x] Cost monitoring
  - [x] Python testing and deployment
- [x] Automated testing on push to main/develop branches
- [x] Docker image building and pushing to registry
- [x] Slack notifications configured

## Deployment Steps

### Phase 1: Infrastructure Provisioning

1. **Initialize Terraform**

   ```bash
   cd infra/terraform/environments/prod
   terraform init
   ```

2. **Plan Deployment**

   ```bash
   terraform plan -var-file="production.tfvars"
   ```

3. **Apply Infrastructure**

   ```bash
   terraform apply -var-file="production.tfvars" -auto-approve
   ```

4. **Verify Infrastructure**
   - SSH access to Hetzner CPX21 server
   - AWS S3 bucket created
   - Network connectivity verified

### Phase 2: Service Deployment

1. **Copy Docker Compose Configuration**

   ```bash
   scp infra/docker-compose.yml root@<hetzner-ip>:/opt/alphapulse/
   scp .env.production root@<hetzner-ip>:/opt/alphapulse/.env
   ```

2. **Start Services**

   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose up -d"
   ```

3. **Verify Service Health**
   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose ps"
   ```

### Phase 3: Data Pipeline Initialization

1. **Initialize MinIO Buckets**

   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose exec mc /bin/sh -c 'mc mb alphapulse/alphapulse --ignore-existing'"
   ```

2. **Run Initial Data Pipeline**

   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose exec mage mage run alphapulse/pipelines/btc_price_pipeline"
   ```

3. **Verify Data Population**
   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose exec postgres psql -U postgres -d alphapulse -c 'SELECT COUNT(*) FROM prices;'"
   ```

### Phase 4: FastAPI Deployment

1. **Start FastAPI Service**

   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose exec -d mage python -m src.alphapulse.main"
   ```

2. **Verify API Accessibility**
   ```bash
   curl http://<hetzner-ip>:8000/health
   curl http://<hetzner-ip>:8000/docs
   ```

### Phase 5: Monitoring Setup

1. **Configure Evidently AI Monitoring**

   ```bash
   ssh root@<hetzner-ip> "cd /opt/alphapulse && docker compose exec mage python -c 'from src.alphapulse.monitoring.data_drift import DataDriftMonitor; monitor = DataDriftMonitor(); monitor.initialize_reference_data()'"
   ```

2. **Set Up Alerting**
   - Configure Slack webhook for alerts
   - Set up email notifications for critical issues
   - Configure PagerDuty for on-call alerts

## Post-Deployment Verification

### Service Health Checks

- [ ] PostgreSQL: `http://<hetzner-ip>:5432` (connection test)
- [ ] MinIO: `http://<hetzner-ip>:9001` (console login)
- [ ] MLflow: `http://<hetzner-ip>:5001` (UI accessible)
- [ ] Mage.ai: `http://<hetzner-ip>:6789` (UI accessible)
- [ ] FastAPI: `http://<hetzner-ip>:8000/health` (returns healthy)

### API Endpoint Tests

- [ ] Health endpoint: `GET /health`
- [ ] Prices endpoint: `GET /api/v1/prices`
- [ ] Signals endpoint: `GET /api/v1/signals`
- [ ] Indicators endpoint: `GET /api/v1/indicators`
- [ ] Authentication: `POST /api/v1/auth/login`

### Performance Validation

- [ ] API response times within thresholds:
  - Health: < 100ms
  - Prices: < 200ms
  - Indicators: < 200ms
- [ ] Database queries:
  - Price query (100 records): < 50ms
  - Indicator query (100 records): < 50ms
- [ ] Concurrent users: 5+ users with < 500ms response time

### Security Validation

- [ ] JWT token generation and validation
- [ ] Role-based access control working
- [ ] API key authentication
- [ ] Audit logging functional
- [ ] HTTPS/SSL configured (if using domain)

### Data Pipeline Validation

- [ ] BTC price pipeline executes successfully
- [ ] Technical indicators calculated correctly
- [ ] Feature integration pipeline functional
- [ ] Data quality checks passing
- [ ] Decimal precision maintained throughout pipeline

## Monitoring & Alerting

### Dashboard Configuration

- [ ] Grafana dashboard for system metrics
- [ ] Prometheus metrics collection
- [ ] Service uptime monitoring
- [ ] Performance metrics tracking
- [ ] Data quality monitoring

### Alert Thresholds

- [ ] CPU usage > 80% for 5 minutes
- [ ] Memory usage > 85% for 5 minutes
- [ ] Disk usage > 90%
- [ ] API response time > 500ms
- [ ] Service downtime > 2 minutes
- [ ] Data drift detected > 0.05 threshold

## Disaster Recovery

### Backup Configuration

- [ ] PostgreSQL automated backups (daily)
- [ ] MinIO data backup to AWS S3
- [ ] Configuration backup
- [ ] Docker volume backup

### Recovery Procedures

- [ ] Database restore procedure documented
- [ ] Service restart procedures
- [ ] Data recovery from backups
- [ ] Failover procedures (if multi-region)

## Documentation

### Operational Runbooks

- [ ] Service startup/shutdown procedures
- [ ] Troubleshooting guide
- [ ] Performance tuning guide
- [ ] Security incident response
- [ ] Backup and restore procedures

### User Documentation

- [ ] API documentation (OpenAPI/Swagger)
- [ ] Authentication guide
- [ ] Data pipeline usage guide
- [ ] Monitoring dashboard guide
- [ ] Support contact information

## Cost Monitoring

### Monthly Budget: $15.00

- [ ] Hetzner CPX21: $9.50/month
- [ ] AWS S3: $1.65/month
- [ ] Monitoring/Alerting: $3.85/month buffer

### Cost Optimization

- [ ] Right-size resources based on usage
- [ ] Implement auto-scaling if needed
- [ ] Monitor and eliminate unused resources
- [ ] Use reserved instances for cost savings

## Sign-off

### Deployment Approval

- [ ] Infrastructure Team Lead: ********\_\_\_\_********
- [ ] Security Team Lead: ********\_\_\_\_********
- [ ] Operations Team Lead: ********\_\_\_\_********
- [ ] Product Owner: ********\_\_\_\_********

### Post-Deployment Review

**Scheduled for**: 7 days after deployment  
**Review Items**:

- System performance vs baseline
- Incident response effectiveness
- User feedback
- Cost vs budget
- Security audit findings

---

**Last Updated**: 2026-01-10  
**Version**: 1.0  
**Next Review**: After production deployment  
**Owner**: AlphaPulse Operations Team
\n---
# AlphaPulse - Installation & Local Development

## Prerequisites
- Docker & Docker Compose
- Terraform >= 1.6
- AWS CLI (configured)
- Python 3.12 (for local testing)

## Setup Steps
1. **Clone & Config**
   ```bash
   git clone <repo-url>
   cp .env.example .env.local
   ```
2. **Launch Services**
   ```bash
   cd infra
   docker compose up -d
   ```
3. **Verify**
   - Airflow: http://localhost:8080
   - MLflow: http://localhost:5001
   - API: http://localhost:8000

## Data Backfill
To populate the system with 8 years of data:
```bash
docker exec -it alphapulse-trainer python /app/scripts/data/backfill_prices.py
```
