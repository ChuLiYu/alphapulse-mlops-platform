# FinOps & Multi-Cloud Cost Strategy

AlphaPulse implements a **Budget-Aware MLOps** strategy, leveraging multiple cloud provider tiers to minimize overhead while maintaining production standards.

## 📊 Monthly Cost Comparison

| Tier | Resource | Provider | Traditional (AWS Only) | AlphaPulse (Multi-Cloud) | Savings |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Compute** | 4vCPU, 24GB RAM | Oracle Free | $120 (m5.xlarge) | **$0.00** | 100% |
| **Compute (Failover)** | 2vCPU, 4GB RAM | Hetzner CPX21 | $15 (t3.small) | **$9.50** | 37% |
| **Storage** | 50GB Object Storage | AWS S3 | $1.15 | **$0.00** (Free Tier) | 100% |
| **Registry** | MLflow Backend | Postgres | $15 (RDS) | **$0.00** (Self-host) | 100% |
| **Total** | | | **~$151 / mo** | **$0.00 - $11.00** | **92% - 100%** |

---

## 💡 Cost Optimization Pillars

### 1. The "Oracle-First" Compute Strategy
We prioritize **Oracle Cloud Always Free** instances (ARM64). This provides massive memory (24GB) which is critical for:
- Large-scale **CatBoost/XGBoost** training.
- Running **Apache Airflow**'s multiple scheduler and worker processes.

### 2. AWS S3 Persistence
While compute is moved to cheaper providers, critical assets (Model Weights, Parquet Snapshots) are kept in **AWS S3** to ensure:
- 99.999999999% durability.
- Industry-standard API compatibility for future scale-up.

### 3. Serverless Inference (Future Optimization)
Planned migration of the Inference Engine to AWS Lambda or K8s Job patterns to achieve **Scale-to-Zero** billing during low-volatility market periods.

---
**Last Updated**: 2026-01-13