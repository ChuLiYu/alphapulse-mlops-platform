# AlphaPulse - Backend Infrastructure & MLOps Platform

## Project Overview

AlphaPulse is a **cost-optimized backend infrastructure** for cryptocurrency trading signal systems. This project demonstrates **Infrastructure Engineering** and **MLOps** skills targeting **Backend/DevOps roles at Fintech companies**.

**Current Status (Jan 12, 2026)**: Phase 4.5 Completed (Container Separation & Testing Refactor). Transitioned to Airflow for Orchestration.

## Strategic Direction

- **Backend-First Strategy**: Prioritizing Type Safety (Decimal), IaC (Terraform), and CI/CD over complex ML model research.
- **Container Separation**: Decoupled architecture with specialized containers for ETL (Airflow) and Training (Trainer API).
- **Hybrid Multi-Cloud**: Hetzner (Compute) + AWS (Storage) for 85% cost savings ($11.15/month).
- **Fintech-Grade Quality**: 100% Decimal precision, comprehensive testing (Unit/Integration/E2E), and drift monitoring.

---

## System Architecture

### 1. Infrastructure (IaC)
- **Terraform**: Modular setup for AWS (S3, IAM) and Hetzner (Compute).
- **Docker Compose**: Orchestration for local and production environments.
- **Container Strategy**:
    - `alphapulse-airflow-*`: Robust orchestration for data pipelines (Webserver, Scheduler).
    - `alphapulse-trainer`: Dedicated Training API (Scikit-learn, XGBoost) to isolate heavy dependencies.
    - `alphapulse-fastapi`: Serving Layer for predictions and data access.
    - `alphapulse-mlflow`: Experiment tracking.
    - `alphapulse-postgres`: Centralized storage.

### 2. Backend & Data
- **FastAPI**: Type-safe REST API with Pydantic models.
- **PostgreSQL**: Relational storage with strict `DECIMAL` types for financial data.
- **Apache Airflow**: Orchestrator for data pipelines (Price ingestion, News aggregation, Feature integration).

### 3. Machine Learning
- **Trainer API**: specialized FastAPI service for model training, capable of "Ultra Fast" (Dev) and "Production" (Full CV) modes.
- **Anti-Overfitting**: Implemented 7-layer protection (CV, Ridge/Lasso, Early Stopping, etc.).
- **MLflow**: Tracks all experiments, parameters, and artifacts.

---

## Roadmap & Status

### ✅ Phase 1: Infrastructure Foundation
- [x] Terraform modules for Networking, Compute (Hetzner), and Storage (AWS S3).
- [x] Hybrid Cloud configuration (Hetzner + AWS).
- [x] CI/CD Pipelines (GitHub Actions) for Terraform validation.

### ✅ Phase 2: Backend Core
- [x] FastAPI project setup with strict `Decimal` enforcement.
- [x] Database schema design with SQLAlchemy.
- [x] Health check and basic CRUD endpoints.
- [x] Unit testing suite.

### ✅ Phase 3: Data Pipeline
- [x] Airflow DAGs for BTC price ingestion.
- [x] `pandas-ta` integration for 130+ technical indicators.
- [x] Feature integration pipeline (News + Price + Sentiment).
- [x] Airflow DAGs for RSS News ingestion (DeepSeek Task).

### ✅ Phase 4: Production Readiness & Monitoring
- [x] Evidently AI integration for Data Drift detection.
- [x] Performance testing (API latency, DB throughput).
- [x] Security hardening (JWT, API Keys).

### ✅ Phase 4.5: Architecture Refactor (Jan 2026)
- [x] **Container Separation**: Split Orchestration (Airflow) and Trainer (ML).
- [x] **Testing Framework**: Implemented comprehensive Unit, Integration, and E2E tests.
- [x] **Trainer Improvements**: Added Cross-Validation, Regularization, and Learning Curves.
- [x] **Documentation**: Updated architecture guides and reports.

### 🔄 Phase 5: Production Deployment (k3s Migration)
- [ ] **k3s Cluster Setup**: Provision Hetzner CPX21 with k3s lightweight Kubernetes.
- [ ] **Kubernetes Manifests**: Create Deployments, Services, and Ingress for all tiers.
- [ ] **Persistent Storage**: Configure Local Path Provisioner or S3-backed volumes.
- [ ] **Secret Management**: Move environment variables to K8s Secrets.
- [ ] **Hetzner Cloud Integration**: Configure Floating IP and Load Balancer via HCloud CCM.

### 🚀 Phase 5.5: Continuous MLOps (CT/CD)
- [ ] **CatBoost Integration**: Add CatBoost as a challenger model for better categorical and noise handling.
- [ ] **Model Promotion Logic**: Automated "Champion/Challenger" staging in MLflow Registry.
- [ ] **Inference Engine**: Real-time signal generation from the latest production model.

### 💰 Phase 5.6: FinOps & Multi-Cloud Optimization
- [ ] **Oracle Cloud Migration**: Port k3s cluster to Oracle Always Free ARM64 for $0 compute cost.
- [ ] **S3 Lifecycle Management**: Automate model archiving to reduce AWS storage costs.
- [ ] **ARM64 Compatibility**: Optimize Docker images for multi-architecture support (x86_64 and aarch64).

### 📋 Phase 6: Documentation & Portfolio
- [ ] **Runbooks**: Production operations and disaster recovery.
- [ ] **Interview Prep**: STAR stories and "Talking Points".
- [ ] **Demo Video**: 5-minute technical walkthrough.

---

## Key Technical Decisions

| Decision | Choice | Rationale |
| :--- | :--- | :--- |
| **Compute** | Hetzner CPX21 | High performance (Dedicated vCPU) at low cost (€9.50/mo). |
| **Orchestration** | Airflow + Trainer | Industry standard orchestration + Decoupled training. |
| **Precision** | `Decimal` | Essential for Fintech to avoid floating-point errors. |
| **IaC** | Terraform | Industry standard, provider-agnostic. |
| **CI/CD** | GitHub Actions | "Shift Left" quality with automated testing and linting. |

---

## Quick Links

- **Current Tasks**: [`docs/tasks/current_task.md`](docs/tasks/current_task.md)
- **Refactor Report**: [`docs/reports/REFACTOR_COMPLETE_REPORT.md`](docs/reports/REFACTOR_COMPLETE_REPORT.md)
- **Trainer Guide**: [`docs/training/ADVANCED_TRAINER_GUIDE.md`](docs/training/ADVANCED_TRAINER_GUIDE.md)
- **Testing Strategy**: [`docs/testing/COMPREHENSIVE_TESTING_GUIDE.md`](docs/testing/COMPREHENSIVE_TESTING_GUIDE.md)

---

**Last Updated**: 2026-01-12