# AlphaPulse - Project File Structure

## 🎯 Purpose

This document defines the file organization strategy for AlphaPulse MLOps platform, ensuring maintainability, scalability, and adherence to MLOps best practices.

## 📊 Current State Analysis

### Problems Identified

1. **Root Directory Clutter**: Test files (`test_*.py`) scattered in project root
2. **Missing Core Application Layer**: No dedicated `src/` or `app/` directory
3. **Incomplete Documentation Structure**: Missing ADR index, deployment guides
4. **Infrastructure Fragmentation**: Terraform configs need better organization
5. **No Configuration Management**: Missing centralized config directory
6. **No Exploratory Workspace**: Missing `notebooks/` for data exploration

## 🏗️ Proposed Directory Structure

```
alphapulse-mlops-platform/
├── .github/                    # CI/CD workflows (future)
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── config/                     # 🆕 Centralized configuration
│   ├── dev/
│   │   ├── mage.yaml
│   │   └── mlflow.yaml
│   ├── prod/
│   │   ├── mage.yaml
│   │   └── mlflow.yaml
│   └── README.md
│
├── docs/                       # Documentation hub
│   ├── architecture/           # Architecture Decision Records
│   │   ├── README.md          # ADR index
│   │   ├── adr-001-*.md
│   │   ├── adr-002-*.md
│   │   └── adr-003-training-hardware-evaluation.md
│   ├── deployment/            # 🆕 Deployment guides
│   │   ├── local-setup.md
│   │   ├── k3s-deployment.md
│   │   └── aws-setup.md
│   ├── runbooks/              # Operational guides
│   │   ├── MAINTENANCE.md
│   │   ├── disaster-recovery.md
│   │   └── monitoring.md
│   ├── api/                   # 🆕 API documentation
│   │   └── fastapi-endpoints.md
│   ├── FILE_STRUCTURE.md      # This file
│   └── CONTRIBUTING.md        # 🆕 Contribution guidelines
│
├── infra/                     # Infrastructure as Code
│   ├── terraform/             # 🆕 Terraform modules
│   │   ├── modules/
│   │   │   ├── s3/
│   │   │   ├── ec2/
│   │   │   └── networking/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   └── prod/
│   │   └── README.md
│   ├── k3s/                   # 🆕 Kubernetes manifests
│   │   ├── base/
│   │   └── overlays/
│   ├── docker/                # Dockerfiles
│   │   ├── Dockerfile.airflow
│   │   ├── Dockerfile.mlflow
│   │   ├── Dockerfile.fastapi
│   │   └── Dockerfile.trainer
│   └── docker-compose.yml     # Local dev environment
│
├── airflow/                   # Airflow DAGs and Plugins
│   ├── dags/                  # DAG definitions
│   │   ├── btc_price_dag.py
│   │   ├── news_ingestion_dag.py
│   │   └── sentiment_analysis_dag.py
│   ├── plugins/               # Custom operators/hooks
│   └── config/                # Airflow configuration
│
├── mlflow/                    # MLflow tracking
│   ├── artifacts/             # 🔒 Ignored in .rooignore
│   └── models/
│
├── notebooks/                 # 🆕 Jupyter notebooks for exploration
│   ├── exploratory/
│   │   ├── 01_data_exploration.ipynb
│   │   └── 02_sentiment_testing.ipynb
│   ├── experiments/
│   └── README.md
│
├── scripts/                   # Automation scripts
│   ├── setup/
│   │   ├── init.sh
│   │   └── install_deps.sh
│   ├── deployment/           # 🆕 Deployment automation
│   │   ├── deploy_k3s.sh
│   │   └── rollback.sh
│   ├── data/                 # 🆕 Data management
│   │   ├── backfill.py
│   │   └── cleanup.py
│   └── monitoring/           # 🆕 Monitoring utilities
│       └── check_health.sh
│
├── src/                      # 🆕 Core application code
│   ├── alphapulse/
│   │   ├── __init__.py
│   │   ├── api/              # FastAPI application
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   └── schemas/
│   │   ├── core/             # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── sentiment.py
│   │   │   └── prediction.py
│   │   ├── data/             # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── collectors/   # Reddit, RSS collectors
│   │   │   └── storage/      # DB/S3 handlers
│   │   ├── ml/               # ML model code
│   │   │   ├── __init__.py
│   │   │   ├── training/
│   │   │   └── inference/
│   │   ├── monitoring/       # Evidently AI integration
│   │   │   └── drift_detection.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── config.py
│   └── setup.py              # Package installation
│
├── tests/                    # Test suite
│   ├── unit/                 # 🆕 Unit tests
│   │   ├── test_sentiment.py
│   │   └── test_collectors.py
│   ├── integration/          # 🆕 Integration tests
│   │   ├── test_reddit.py
│   │   ├── test_rss_basic.py
│   │   ├── test_rss_news.py
│   │   └── test_rss_pipeline_integration.py
│   ├── smoke/                # Smoke tests
│   │   └── smoke_test.sh
│   ├── e2e/                  # 🆕 End-to-end tests
│   └── conftest.py           # Pytest configuration
│
├── .clinerules               # 🔒 AI coding rules
├── .env.example              # Environment variables template
├── .env.local                # Local environment (gitignored)
├── .gitignore
├── .rooignore                # 🔒 AI file access rules
├── docker-compose.yml        # -> Move to infra/
├── Makefile                  # Development shortcuts
├── README.md                 # Project overview
├── README_zh-TW.md           # Chinese documentation
└── requirements.txt          # 🆕 Root dependencies
```

## 🎨 Design Principles

### 1. **Separation of Concerns**

- **`src/`**: Application code (reusable, tested, production-ready)
- **`airflow/`**: Orchestration logic (Airflow DAGs)
- **`infra/`**: Infrastructure definitions (Terraform, Docker, K8s)
- **`scripts/`**: Operational automation (deployment, data ops)

### 2. **Environment Isolation**

```
config/
├── dev/     # Local Docker Compose
├── staging/ # Optional staging environment
└── prod/    # K3s + AWS production
```

### 3. **Test Organization**

```
tests/
├── unit/         # Fast, isolated tests
├── integration/  # Tests with dependencies (DB, APIs)
├── e2e/         # Full pipeline tests
└── smoke/       # Quick health checks
```

### 4. **Documentation Hierarchy**

- **`docs/architecture/`**: High-level design decisions (ADRs)
- **`docs/deployment/`**: Step-by-step operational guides
- **`docs/runbooks/`**: Incident response procedures
- **`docs/api/`**: API contracts and examples

## 🔄 Migration Plan

### Phase 1: Core Structure (Current Task)

```bash
# Create missing directories
mkdir -p config/{dev,prod}
mkdir -p docs/{deployment,api}
mkdir -p infra/terraform/{modules,environments/{dev,prod}}
mkdir -p infra/k3s/{base,overlays}
mkdir -p notebooks/{exploratory,experiments}
mkdir -p scripts/{deployment,data,monitoring}
mkdir -p src/alphapulse/{api,core,data,ml,monitoring,utils}
mkdir -p tests/{unit,integration,e2e}
```

### Phase 2: File Relocation

```bash
# Move test files to proper locations
mv test_sentiment.py tests/unit/
mv test_reddit.py tests/integration/
mv test_rss_*.py tests/integration/

# Move Docker Compose to infra
mv docker-compose.yml infra/
```

### Phase 3: Documentation

- Create README files in each major directory
- Write ADR index at [`docs/architecture/README.md`](docs/architecture/README.md)
- Document deployment procedures

## 📏 Naming Conventions

### Files

- **Python Modules**: `snake_case.py`
- **Config Files**: `lowercase.yaml` or `lowercase.json`
- **Documentation**: `UPPERCASE.md` (major) or `lowercase-with-hyphens.md` (specific)
- **Scripts**: `snake_case.sh` or `snake_case.py`

### Directories

- **lowercase with underscores**: `data_loaders/`
- **Avoid nested depth > 4 levels** for maintainability

### Python Packages

```python
# Package import structure
from alphapulse.core import sentiment
from alphapulse.data.collectors import RedditCollector
from alphapulse.ml.inference import SentimentModel
```

## 🚫 Anti-Patterns to Avoid

1. **❌ Root Directory Pollution**: Never place application code in project root
2. **❌ Mixed Concerns**: Don't mix Airflow DAGs with FastAPI routes
3. **❌ Hardcoded Configs**: Always use environment-specific config files
4. **❌ Monolithic Scripts**: Break down large scripts into modular utilities
5. **❌ Missing Tests**: Every new feature must have corresponding tests

## 🔐 Security Considerations

### Never Commit

- `.env.local` (use `.env.example` as template)
- Credentials in any form
- Large data files (use `.rooignore`)

### Access Control

```
# .rooignore prevents AI from reading:
- mlflow/artifacts/
- postgres_data/
- *.csv, *.parquet
- .env
```

## 📚 References

- **Cookiecutter Data Science**: https://drivendata.github.io/cookiecutter-data-science/
- **MLOps Best Practices**: https://ml-ops.org/content/references
- **12-Factor App**: https://12factor.net/

## 🔄 Maintenance

**Document Owner**: MLOps Team  
**Last Updated**: 2026-01-10  
**Review Cycle**: Monthly or when major structural changes occur

---

## Next Steps

1. ✅ Review and approve this structure
2. 🔄 Execute Phase 1 directory creation
3. 🔄 Relocate existing files (Phase 2)
4. 📝 Create README files in new directories
5. 🔄 Update [`Makefile`](../Makefile) with new paths
6. 🧪 Verify all tests still pass after migration
