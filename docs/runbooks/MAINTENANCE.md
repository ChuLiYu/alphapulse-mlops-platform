# AlphaPulse MLOps Platform - Maintenance Runbook

## Overview
This runbook provides step-by-step procedures for maintaining the AlphaPulse MLOps platform in the local Docker Compose environment.

## Daily Tasks

### 1. Service Health Check
```bash
# Check service status
make status

# Run detailed health checks
make health
```

**Expected Output:**
- All services should show "Up" status
- Health checks should pass for all services

**Troubleshooting:**
- If a service is down: `docker-compose logs [service_name]`
- Restart service: `docker-compose restart [service_name]`

### 2. Log Review
```bash
# View recent logs
docker-compose logs --tail=100

# Follow logs in real-time
make logs
```

**What to look for:**
- ERROR or WARNING messages
- Service startup failures
- Connection issues between services

## Weekly Tasks

### 1. Data Backup
```bash
# Create backup of all data
make backup
```

**Backup Location:** `backups/YYYYMMDD_HHMMSS/`

**Contents:**
- `postgres_backup.sql` - PostgreSQL database dump
- `minio_data/` - MinIO object storage data

### 2. Resource Cleanup
```bash
# Remove old Docker images and containers
docker system prune -f

# Check disk usage
docker system df
```

### 3. Dependency Updates
```bash
# Check for updated Docker images
docker-compose pull

# Update Python dependencies in Mage pipeline
docker-compose exec mage pip list --outdated
```

## Monthly Tasks

### 1. Security Review
- Review `.env` file for sensitive data
- Check Docker container security: `docker scan [image_name]`
- Review access logs if applicable

### 2. Performance Monitoring
```bash
# Check resource usage
docker stats

# Check container performance
docker-compose top
```

### 3. Documentation Update
- Update this runbook with new procedures
- Review and update `README.md`
- Update troubleshooting guides

## Service-Specific Maintenance

### PostgreSQL Maintenance
```bash
# Access PostgreSQL shell
docker-compose exec postgres psql -U postgres -d alphapulse

# Common maintenance commands:
-- Check database size
SELECT pg_database_size('alphapulse');

-- List tables and sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema') 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum analyze (maintenance)
VACUUM ANALYZE;
```

### MinIO Maintenance
```bash
# Access MinIO client
docker-compose exec mc /usr/bin/mc alias list

# Check bucket usage
docker-compose exec mc /usr/bin/mc du alphapulse/alphapulse

# List objects
docker-compose exec mc /usr/bin/mc ls alphapulse/alphapulse
```

### MLflow Maintenance
```bash
# Clean up old experiments (older than 30 days)
# This requires custom script - see scripts/setup/mlflow_cleanup.sh
```

### Mage.ai Maintenance
```bash
# Check pipeline status
# Access Mage UI at http://localhost:6789

# View pipeline logs
docker-compose logs mage
```

## Troubleshooting Common Issues

### Issue: Services won't start
**Symptoms:** `make up` fails or services exit immediately

**Resolution:**
1. Check logs: `docker-compose logs`
2. Check port conflicts: `lsof -i :5432,5000,6789,9000,9001`
3. Check disk space: `df -h`
4. Check Docker daemon: `docker info`

### Issue: Database connection errors
**Symptoms:** "Connection refused" or "authentication failed"

**Resolution:**
1. Check PostgreSQL is running: `docker-compose ps postgres`
2. Check credentials in `.env` file
3. Restart services: `docker-compose restart`

### Issue: MinIO bucket not accessible
**Symptoms:** MLflow or Mage can't write to S3

**Resolution:**
1. Check MinIO health: `docker-compose exec minio curl http://localhost:9000/minio/health/live`
2. Check bucket exists: `docker-compose exec mc /usr/bin/mc ls alphapulse`
3. Check credentials match between services

### Issue: High resource usage
**Symptoms:** System slow, containers using high CPU/memory

**Resolution:**
1. Identify resource hog: `docker stats`
2. Adjust resource limits in `docker-compose.yml`
3. Consider adding resource constraints:
   ```yaml
   services:
     postgres:
       deploy:
         resources:
           limits:
             cpus: '1.0'
             memory: 2G
   ```

## Backup and Recovery Procedures

### Full Backup
```bash
# Automated backup
make backup

# Manual backup
mkdir -p backups/manual_$(date +%Y%m%d)
docker-compose exec -T postgres pg_dump -U postgres alphapulse > backups/manual_$(date +%Y%m%d)/postgres.sql
docker cp alphapulse-minio:/data backups/manual_$(date +%Y%m%d)/minio_data
```

### Recovery from Backup
**Important:** Recovery stops all services and may cause data loss

1. Stop services: `make down`
2. Restore PostgreSQL:
   ```bash
   docker-compose up -d postgres
   # Wait for PostgreSQL to start
   sleep 10
   cat backups/[backup_date]/postgres.sql | docker-compose exec -T postgres psql -U postgres -d alphapulse
   ```
3. Restore MinIO data:
   ```bash
   docker-compose stop minio
   docker cp backups/[backup_date]/minio_data/. alphapulse-minio:/data
   docker-compose start minio
   ```
4. Start all services: `make up`

## Upgrade Procedures

### Docker Image Updates
```bash
# Pull latest images
docker-compose pull

# Recreate containers with new images
docker-compose up -d
```

### Configuration Changes
1. Update `docker-compose.yml` or `.env`
2. Test changes: `docker-compose config`
3. Apply changes: `docker-compose up -d`

### Database Schema Updates
**Important:** Always backup before schema changes

1. Create backup: `make backup`
2. Apply migration scripts (if any)
3. Test application functionality

## Monitoring Checklist

### Daily Monitoring
- [ ] All services running (`make status`)
- [ ] No error logs (`docker-compose logs --tail=50`)
- [ ] Disk space adequate (`df -h .`)
- [ ] Memory usage acceptable (`docker stats --no-stream`)

### Weekly Monitoring
- [ ] Backup successful (`ls -la backups/`)
- [ ] Resource usage trends
- [ ] Security scan results
- [ ] Dependency updates available

### Monthly Monitoring
- [ ] Performance benchmarks
- [ ] Storage growth analysis
- [ ] Cost analysis (if applicable)
- [ ] Documentation review

## Emergency Contacts
- Primary Maintainer: [Your Name]
- Backup Maintainer: [Team Member]
- Infrastructure Support: [If applicable]

## Change Log
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-01-09 | 1.0 | Initial runbook creation | System |
| 2026-01-09 | 1.1 | Added troubleshooting sections | System |