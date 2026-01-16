# Quick Start & ML Training Guide

This guide covers the local setup and training workflows for the AlphaPulse MLOps platform.

## 🚀 Quick Start

### Prerequisites

```bash
# Install required tools
brew install terraform  # >= 1.6.0
brew install awscli     # AWS CLI
brew install docker     # Docker Desktop
brew install docker-compose
```

### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/alphapulse-mlops-platform.git
cd alphapulse-mlops-platform

# 2. Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# 3. Start services locally
cd infra
docker compose up -d

# 4. Verify services are running
docker compose ps
# Expected: postgres, fastapi, airflow, mlflow, minio all "Up"

# 5. Access services
# - FastAPI: http://localhost:8000/docs
# - Airflow UI: http://localhost:8080
# - MLflow: http://localhost:5001
# - PostgreSQL: localhost:5432

# 6. Run tests (verify ML libraries installed)
docker exec airflow-scheduler pytest /opt/airflow/tests/unit/ -v
docker exec airflow-scheduler pytest /opt/airflow/tests/integration/ -v

# 7. Check ML library versions
docker exec trainer python -c "import xgboost, lightgbm, sklearn; \
  print(f'XGBoost: {xgboost.__version__}'); \
  print(f'LightGBM: {lightgbm.__version__}'); \
  print(f'scikit-learn: {sklearn.__version__}')"
```

## 🌪️ ML Training Workflow

### 1. Data Preparation
Prepare the dataset for training:
```bash
docker exec trainer python /app/src/alphapulse/ml/prepare_training_data.py
```

### 2. Automated Training
Train models using Walk-Forward Cross-Validation:
```bash
docker exec trainer python /app/src/alphapulse/ml/auto_train.py
```

### 3. Tracking & Versioning
View training results in MLflow:
- Open `http://localhost:5001`
- Navigate to the "auto_training_runs" experiment.
- Compare metrics (Accuracy, F1-score, Precision).

### 4. Artifact Management
Check the best model and summary:
```bash
ls -lh src/models/saved/best_model.pkl
cat src/results/training_summary.json
```

### 5. Model Validation
Verify the trained model:
```bash
docker exec trainer python -c "
import joblib
model = joblib.load('/app/models/saved/best_model.pkl')
print('Model loaded successfully:', type(model))
"
```

---

## 🏗️ Production Deployment (Hybrid Cloud)

```bash
# 1. Configure cloud provider credentials
aws configure
export HCLOUD_TOKEN="your_hetzner_api_token"

# 2. Deploy infrastructure
cd infra/terraform/environments/prod
terraform init
terraform apply
```