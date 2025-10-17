# Cost Optimization Decision: Hetzner CPX11 vs CPX21

## Decision Date

2026-01-10

## Decision

**Use Hetzner CPX11 (€4.51/month) for development environment**

## Context

AlphaPulse is transitioning from local Docker Compose to hybrid cloud deployment (Hetzner + AWS S3). Initial architecture specified CPX21 (€9.50/month), but analysis shows CPX11 (€4.51/month) is sufficient for development phase.

## Analysis

### Service Stack Resource Requirements

| Service      | Estimated RAM | Notes                                     |
| ------------ | ------------- | ----------------------------------------- |
| PostgreSQL   | 384MB         | Alpine version with reduced buffers       |
| MinIO        | 256MB         | Lightweight object storage                |
| MLflow       | 384MB         | Python service with limited concurrency   |
| Mage.ai      | 768MB         | Data pipeline engine with resource limits |
| Evidently AI | 256MB         | Monitoring service                        |
| OS & Buffer  | 512MB         | System overhead                           |
| **Total**    | **~2.5GB**    | With resource constraints                 |

### Hetzner Pricing Comparison

| Server Type | vCPU | RAM | SSD   | Monthly Cost    | Total Cost (with AWS S3) |
| ----------- | ---- | --- | ----- | --------------- | ------------------------ |
| **CPX11**   | 2    | 2GB | 40GB  | €4.51 ($4.51)   | **$6.16**                |
| CPX21       | 3    | 4GB | 80GB  | €9.50 ($9.50)   | $11.15                   |
| CPX31       | 4    | 8GB | 160GB | €18.10 ($18.10) | $19.75                   |

### Risk Assessment

#### Risks with CPX11

1. **Memory Pressure**: 2GB RAM is tight for 2.5GB estimated requirement
2. **Limited Headroom**: No buffer for unexpected memory usage
3. **Performance Impact**: May need swap space affecting I/O performance

#### Mitigation Strategies

1. **Resource Limits**: Implement Docker memory limits for each service
2. **Monitoring**: Deploy Prometheus/Grafana for real-time monitoring
3. **Vertical Scaling**: Design for easy upgrade to CPX21 if needed
4. **Optimization**: Tune PostgreSQL buffers, limit Mage.ai concurrency

## Technical Implementation

### Terraform Configuration

```hcl
variable "server_type" {
  description = "Hetzner server type (cpx11 for dev, cpx21 for prod)"
  type        = string
  default     = "cpx11"
}

resource "hcloud_server" "main" {
  server_type = var.server_type  # cpx11 or cpx21
  # ... other configuration
}
```

### Docker Compose Resource Limits

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 384M

  mage:
    deploy:
      resources:
        limits:
          memory: 768M

  mlflow:
    deploy:
      resources:
        limits:
          memory: 384M
```

## Interview Perspective

### Potential Interview Questions

1. "How do you decide cloud resource specifications?"
2. "What's your approach to cost vs performance trade-offs?"
3. "How do you optimize infrastructure costs for ML projects?"

### Answer Framework

1. **Quantify Requirements**: Measure actual resource usage of each service
2. **Cost-Benefit Analysis**: Compare different specifications and their TCO
3. **Scalability Design**: Plan for vertical/horizontal scaling based on metrics
4. **Monitoring-Driven Optimization**: Use monitoring data to make informed decisions
5. **Risk Management**: Have contingency plans for resource constraints

## Success Metrics

### Monitoring Metrics

1. **Memory Usage**: Should stay below 80% of 2GB (1.6GB)
2. **CPU Usage**: Should stay below 70% on average
3. **Swap Usage**: Should be minimal (< 100MB)
4. **Service Health**: All services should maintain healthy status

### Upgrade Triggers

Upgrade to CPX21 when:

1. Memory usage consistently > 80% for 7 days
2. CPU usage consistently > 70% for 7 days
3. Service health degradation due to resource constraints
4. Business requirements increase (more concurrent users/data)

## Cost Savings

### Development Phase (6 months)

- **CPX21**: $11.15 × 6 = $66.90
- **CPX11**: $6.16 × 6 = $36.96
- **Savings**: $29.94 (45% reduction)

### Annual Projection

- **CPX21**: $133.80/year
- **CPX11**: $73.92/year
- **Savings**: $59.88/year (45% reduction)

## Next Steps

1. **Update Terraform**: Change default server_type to "cpx11"
2. **Implement Monitoring**: Deploy Prometheus/Grafana stack
3. **Set Alerts**: Configure alerts for resource thresholds
4. **Document Procedures**: Create runbook for upgrading to CPX21
5. **Review Monthly**: Monthly cost and performance review

## Decision Makers

- Infrastructure Team
- MLOps Engineer
- Project Manager

## Review Date

2026-02-10 (30 days after implementation)

---

**Key Takeaway**: This decision demonstrates cost optimization skills while maintaining technical feasibility. It shows ability to balance budget constraints with technical requirements, a valuable skill for MLOps roles in cost-conscious organizations.
