# AlphaPulse: Production-Grade MLOps for Crypto-Fintech

[![Live Demo](https://img.shields.io/badge/Demo-Live_App-2ea44f?style=for-the-badge&logo=vercel)](https://alphapulse.luichu.dev/)
[![Infrastructure: Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&style=flat-square)](docs/architecture/adr-007-cross-cloud-strategy.md)
[![Runtime: Oracle ARM64](https://img.shields.io/badge/Runtime-Oracle_ARM64-F80000?logo=oracle&style=flat-square)](docs/architecture/adr-008-cpu-first-optimization.md)
[![Cost: $0/mo](https://img.shields.io/badge/FinOps-Zero--Cost-success?style=flat-square)](docs/deployment/COST_FINOPS.md)
[![Fintech: Decimal Precision](https://img.shields.io/badge/Fintech-Decimal_Precision-blue?style=flat-square)](src/alphapulse/data/processor.py)

AlphaPulse is a **Zero-Cost, High-Performance MLOps Platform** built for quantitative crypto trading. It bridges the gap between complex ML research and production-grade stability, optimized for **Oracle Cloud Always Free (ARM64)**.

> **🚀 Live Demo**: [https://alphapulse.luichu.dev/](https://alphapulse.luichu.dev/) (Deployed on Oracle Cloud + Cloudflare)

---

## 🏗️ System Architecture (Production)

```mermaid
%%{init: {'flowchart': {'curve': 'basis'}}}%%
flowchart TD
    %% --- Styles ---
    classDef ci fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#0D47A1;
    classDef infra fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#1B5E20;
    classDef k8s fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#E65100;
    classDef storage fill:#F3E5F5,stroke:#7B1FA2,stroke-width:2px,color:#4A148C;

    %% --- 1. CI/CD & Infra Layer ---
    subgraph CICD ["1. CI/CD & Provisioning"]
        direction TB
        TF["Terraform<br/>(Infrastructure as Code)"]:::infra
        GHA["GitHub Actions<br/>(Build & Deploy)"]:::ci
        TF ~~~ GHA
        GHA -- "SSH (Ed25519)" --> PROD
        TF -- "Provisioning" --> PROD
    end

    %% --- 2. Production Cluster (Oracle Cloud) ---
    subgraph PROD ["2. Oracle Cloud (Always Free ARM64)"]
        direction TB
        subgraph K3S ["K3s Cluster (Single Node)"]
            direction TB
            ING[Traefik Ingress]:::k8s
            subgraph Apps ["Application Namespace"]
                AF["Airflow<br/>(Orchestrator)"]:::k8s
                ML["MLflow<br/>(Model Registry)"]:::k8s
                API["FastAPI<br/>(Inference)"]:::k8s
                WEB["Frontend<br/>(React/Vite)"]:::k8s
                GF["Grafana<br/>(Monitoring)"]:::k8s
                TR["Trainer<br/>(Training Engine)"]:::k8s
                OL["Ollama<br/>(LLM Inference)"]:::k8s
            end
            subgraph Data ["Data Namespace"]
                 PG[(PostgreSQL)]:::storage
                 MI[(MinIO / S3)]:::storage
            end
        end
    end

    %% --- 3. External Storage ---
    subgraph EXT ["3. External Persistence"]
        direction LR
        S3[("AWS S3 / R2")]:::storage
    end

    %% --- Flows ---
    ING --> WEB
    ING --> AF
    ING --> ML
    ING --> GF
    ING --> API
    AF -- "Triggers" --> TR
    AF -- "Data" --> PG
    AF -- "Tasks" --> OL
    TR -- "Logs" --> ML
    TR -- "Metrics" --> PG
    API -- "Inference" --> ML
    WEB -- "UI" --> API
    WEB -- "Charts" --> GF
    ML -.->|Artifacts| MI
    MI -.->|Backup| S3
    PG -.->|Backup| S3
```

---

## 📸 Platform Preview
> **🚀 Live Demo**: [https://alphapulse.luichu.dev/](https://alphapulse.luichu.dev/)

![AlphaPulse Frontend Dashboard](docs/images/frontend.png)

---

## 🛠️ Tech Stack & Tools

| Category | Technologies |
| :--- | :--- |
| **MLOps & Orchestration** | **Apache Airflow**, **MLflow**, **Docker**, **Kubernetes (k3s)**, **Terraform** |
| **Data Engineering** | **PostgreSQL**, **MinIO (S3 Compatible)**, **SQLAlchemy**, **Pydantic v2** |
| **Machine Learning & AI** | **CatBoost**, **Scikit-learn**, **LangChain**, **Ollama**, **Groq** |
| **Backend & API** | **Python 3.12**, **FastAPI**, **AsyncIO**, **Loguru** |
| **Frontend** | **React 18**, **TypeScript**, **Vite**, **Redux Toolkit**, **TailwindCSS**, **Recharts** |
| **DevOps & Quality** | **GitHub Actions** (CI/CD), **Pytest** (Cov), **Black** (Linting), **Traefik** |

---

## 🌟 Senior Engineering Highlights

### 1. Polymorphic Infrastructure (Cross-Cloud Strategy)
*   **Challenge**: Demonstrate senior-level cross-cloud capabilities without multi-cloud overhead or costs.
*   **Solution**: Implemented a **Provider-Agnostic Abstraction** layer using Terraform modules. The system defines a "Compute Module Interface," allowing seamless switching between **AWS EC2** and **GCP Compute Engine** via a single variable.
*   **Impact**: Achieve "Cloud Portability" with zero recurring costs.

### 2. High-Performance ETL & Data Engineering
*   **Challenge**: Processing **8+ years** of high-frequency market data on resource-constrained ARM64 instances (avoiding OOM).
*   **Solution**: Engineered resilient **Apache Airflow** DAGs with a **Chunked SQL Loading** and strict **Type Downcasting** strategy. Implemented **Pydantic** for rigorous schema validation and **SQLAlchemy** for ORM consistency.
*   **Impact**: Reduced memory footprint by **50%**, enabling full-history training on 24GB RAM without disk swapping.

### 3. Industrial-Grade Quality Assurance
*   **Multi-Stage CI/CD**: Enforced by GitHub Actions, featuring Unit Tests (Pytest), Integration Tests (DB/MLflow), and Smoke Tests.
*   **Fintech Precision**: AlphaPulse enforces `Decimal` types for all monetary values to prevent floating-point errors in trading simulations.
*   **Robustness**: Built-in **Anti-Overfitting Gates** and **Walk-Forward Cross-Validation** to ensure model reliability.

### 4. Professional Engineering Standards
*   **Type Safety**: 100% type-hinted codebase enforced by `mypy` and runtime validation via **Pydantic v2**.
*   **Modern Frontend**: Component-driven UI using React/Vite with strictly typed props and state management via Redux Toolkit.

---

## 💰 The FinOps Journey: $11/mo → $0/mo

AlphaPulse was engineered for extreme cost efficiency:
1.  **Phase 1 (AWS)**: Initial deployment on AWS EC2/RDS (~$11/mo).
2.  **Phase 2 (ARM64 Refactor)**: Re-engineered the training engine for ARM64 compatibility.
3.  **Phase 3 (Zero-Cost)**: Migrated the entire stack to **Oracle Cloud Always Free**. Hosting 4 vCPUs and 24GB RAM for **$0/month**.

---

## 🎯 Role-Specific Navigation

| If you are a... | Recommended Deep-Dives |
| :--- | :--- |
| **Hiring Manager** | **[Zero-Cost FinOps Strategy](docs/deployment/COST_FINOPS.md)** (Cost-conscious engineering) |
| **Technical Lead** | **[Architecture Principles](docs/architecture/README.md)** (Rationale behind k3s, CatBoost, and decoupling) |
| **DevOps Engineer** | **[CI/CD Workflow](.github/workflows/python-test-and-deploy.yml)** & **[k3s Setup](infra/k3s/base/)** |
| **ML Engineer** | **[Iterative Trainer Logic](src/alphapulse/ml/training/iterative_trainer.py)** (AutoML, Optuna, Feature Store) |

---

## 📂 Repository Structure
```text
alphapulse-mlops-platform/
├── .github/workflows/   # CI/CD Pipelines (Test, Build, Deploy)
├── airflow/             # ETL & Orchestration (DAGs, Plugins)
├── docs/                # Architecture Decision Records (ADRs) & Manuals
├── frontend/            # React/Vite UI for visualization
├── infra/               # Terraform (IaC) & Kubernetes Manifests
├── src/                 # Core Python Logic (Shared Library)
├── tests/               # Pytest Suite (Unit, Integration, E2E)
└── training/            # Standalone Training Scripts
```

---

## 🚀 Quick Start (Local Development)

### 📋 Prerequisites
*   **Docker & Docker Compose**
*   **Python 3.10+**
*   **Memory**: Min. 4GB RAM allocated to Docker.

### 🏃 Setup
```bash
# Clone the repository
git clone https://github.com/ChuLiYu/alphapulse-mlops-platform.git
cd alphapulse-mlops-platform

# Spin up Postgres, Airflow, MLflow, and API
./local_dev.sh up
```

### 🔍 Accessing Services
*   **Frontend UI**: `http://localhost:5173`
*   **Airflow**: `http://localhost:8080` (Default: `airflow/airflow`)
*   **MLflow**: `http://localhost:5000`
*   **API Docs**: `http://localhost:8000/docs`

---

## 📫 Connect
*   **LinkedIn**: [Li-Yu Chu](https://www.linkedin.com/in/chuliyu/)
*   **Email**: [liyu.chu.work@gmail.com](mailto:liyu.chu.work@gmail.com)
*   **Live App**: [alphapulse.luichu.dev](https://alphapulse.luichu.dev/)

---
**Core Values**: Financial Precision, Cost-Conscious Engineering, Architectural Decoupling.
**Technical Focus**: MLOps, DataOps, ETL, ELT, Data Pipeline, Feature Store, Model Registry, CI/CD for ML, Data Governance, Scalability, Observability, Cost Optimization, Infrastructure as Code (IaC), Monitoring, Alerting, Data Quality, Data Validation, Workflow Orchestration, Batch Processing, Real-time Processing, Data Lake, Data Warehouse.
**Fintech Domain**: Quantitative Trading, Algorithmic Trading, Risk Management, Backtesting, PnL Analysis, Financial Time-series, Technical Indicators, Sentiment Analysis, Market Data Engineering, Decimal Precision, Portfolio Management, Trading Strategy, Crypto-Fintech.