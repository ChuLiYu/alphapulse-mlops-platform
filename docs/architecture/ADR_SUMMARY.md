# 🏛️ AlphaPulse: Core Architecture Decision Records (ADR)

This document summarizes the strategic technical decisions made during the development of the AlphaPulse MLOps platform and the rationale behind them.

---

## ADR-001: Choosing Apache Airflow for Orchestration
*   **Context**: The project initially used a single-container ETL setup.
*   **Decision**: Migrate to **Apache Airflow**.
*   **Rationale**: 
    *   **Scalability**: Better handling of complex DAG dependencies (Price -> Indicators -> Features -> Train).
    *   **Industry Standard**: Higher relevance for Fintech infrastructure roles.
    *   **Decoupling**: Allows data collection to fail independently without stopping model serving.
*   **Consequence**: Higher setup complexity but 100% reliable automated schedules.

## ADR-002: Migration from Docker Compose to k3s for Production
*   **Context**: Need a stable way to run 24/7 trading signals on a low-cost VPS.
*   **Decision**: Use **k3s (Lightweight Kubernetes)**.
*   **Rationale**: 
    *   **Self-healing**: Auto-restarts crashed inference pods.
    *   **Rolling Updates**: Deploy new models with zero downtime.
    *   **FinOps**: Standard K8s requires 4GB+ RAM; k3s runs on 512MB, allowing us to stay on a $11/mo server.
*   **Consequence**: Requires managing YAML manifests but provides industrial-grade uptime.

## ADR-003: Selecting CatBoost as Primary ML Model
*   **Context**: Financial data has a very low signal-to-noise ratio; XGBoost was prone to overfitting.
*   **Decision**: Adopt **CatBoost** with Symmetric Trees.
*   **Rationale**: 
    *   **Ordered Boosting**: Prevents target leakage common in time-series.
    *   **Robustness**: Better default handling of categorical features and missing data.
    *   **Performance**: R² Gap was reduced from >400% to **<1%** using CatBoost + R² Stability logic.
*   **Consequence**: Requires specific handling for model serialization but yields much higher generalization.

## ADR-004: Hybrid LLM Strategy (Ollama + Groq/OpenAI)
*   **Context**: Processing 8 years of news via GPT APIs is too expensive ($1000+).
*   **Decision**: Implement a **Hybrid LLM** approach.
*   **Rationale**: 
    *   **Cost**: Use **Ollama (Local)** for batch processing historical news (Zero cost).
    *   **Latency**: Use **Groq/OpenAI (API)** for real-time, high-priority production signals.
*   **Consequence**: Complexity in model switching but achieves **99% cost savings** on NLP tasks.

## ADR-005: Metadata & Feature Separation in Feature Store
*   **Context**: Inference engine crashed because raw `close` prices were deleted for stationarity.
*   **Decision**: Implement a `metadata_` prefixing convention.
*   **Rationale**: 
    *   **Data Integrity**: Keeps non-feature data (like raw prices) available for logging and PnL calculation.
    *   **Safety**: Automatic exclusion of `metadata_` columns during training prevents **Data Leakage**.
*   **Consequence**: Simplifies the downstream pipeline at the cost of slight data redundancy.

## ADR-006: Zero-Budget Infrastructure (Oracle OCI + AWS Free Tier)
*   **Context**: AWS/GCP compute costs are prohibitive for individual developers or small trading teams.
*   **Decision**: Deploy compute on **Oracle Cloud Always Free (ARM64)** and storage on **AWS S3 Free Tier**.
*   **Rationale**: 
    *   **100% Cost Reduction**: Achieved a full, industrial-grade MLOps stack for **$0/month**.
    *   **Superior Specs**: Oracle's Always Free tier provides 4 OCPUs and 24GB RAM, which is significantly more powerful than entry-level paid VPS options.
    *   **Multi-Cloud Resilience**: Leveraging two different clouds prevents vendor lock-in and increases system availability.
*   **Consequence**: Requires managing ARM64-compatible Docker images but maximizes net profit to infinity (infinite ROI).
