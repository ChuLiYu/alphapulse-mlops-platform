# AlphaPulse MLOps Engineering Report

## 1. Architectural Evolution: Monolith to Decoupled
Successfully transitioned the platform from a single-container Mage AI setup to a professional, microservice-oriented MLOps architecture.

### Key Refactorings:
- **Container Separation**: Isolated ETL (Airflow), Training (Trainer API), and Serving (FastAPI) to eliminate dependency conflicts.
- **Orchestration**: Standardized on Apache Airflow for robust, hourly data pipelines.
- **Unified Feature Store**: Created a shared `FeatureProducer` to ensure 100% consistency between training and real-time inference (Zero Serving Skew).

## 2. Advanced Machine Learning Operations
### Model Registry & Shadow Deployment
- Implemented a **Champion-Challenger** framework using MLflow.
- New models are deployed in **Shadow Mode** (`is_shadow=True`), generating signals in the background without incurring financial risk.
- Automated model promotion logic based on performance thresholds.

### Robust Feature Engineering
- **52 Stationary Features**: Replaced absolute prices with Log Returns, Relative Moving Averages, and Volatility Z-Scores.
- **Anti-Overfitting Gates**: Integrated 7 layers of protection, including Walk-Forward Cross-Validation and strict Train-Val gap monitoring.
- **Engines**: Leveraged **XGBoost** and **CatBoost** for superior non-linear pattern recognition in noisy financial markets.

## 3. FinOps & Multi-Cloud Strategy
Achieved a 91%+ cost reduction ($11/mo vs $123/mo) by utilizing:
- **Oracle Cloud Always Free**: Primary compute tier (4vCPU, 24GB RAM).
- **Hetzner Cloud**: High-performance x86 failover.
- **AWS S3**: Durable persistence for models and data snapshots.

---
**Status**: Fully Operational | **Last Updated**: 2026-01-13
