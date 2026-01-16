# Quick Production Model Training Guide with Docker

## 🚀 Three Training Modes

### 1. Ultra-Fast Training (⚡ Recommended - 3-5 mins)

The fastest way, training only the 3 best model configurations:

```bash
# Method A: One-click execution
./scripts/quick_train_docker.sh

# Method B: Manual execution in container
docker cp scripts/ultra_fast_train.py trainer:/app/src/
# Dependencies are pre-installed in the trainer container
docker exec trainer python /app/src/ultra_fast_train.py
```

**Features**:

- ⚡ 3 Iterations (Best XGBoost × 2 + Random Forest)
- ⚡ 3-fold Cross-Validation
- ⚡ Fast Early Stopping
- 🎯 Output: Production-ready model

---

### 2. Standard Quick Training (⏱️ 5-10 mins)

Balances speed and performance, training 6 model configurations:

```bash
# Using script
docker cp scripts/quick_production_train.py trainer:/app/src/
docker exec trainer python /app/src/quick_production_train.py
```

**Features**:

- 📊 6 Iterations (Diverse models)
- 📊 3-fold Cross-Validation
- 🛡️ Full Overfitting Detection
- 📈 Evidently Monitoring Report

---

### 3. Full Training (🔬 10-20 mins)

Comprehensive training with all monitoring enabled:

```bash
docker exec trainer python -m alphapulse.ml.training.iterative_trainer
```

**Features**:

- 🔬 10 Iterations (Comprehensive test)
- 🔬 5-fold Cross-Validation
- 📊 Full Evidently Report
- 🎯 Optimal Model Selection

---

## 📋 Pre-checks

### 1. Check Container Status

```bash
docker ps --filter "name=alphapulse"
```

Ensure `trainer` and `postgres` are running.

### 2. Check Data

```bash
docker exec postgres psql -U postgres -d alphapulse -c \
  "SELECT COUNT(*) FROM model_features"
```

Requires at least **300 rows** (Ultra-Fast) or **500 rows** (Standard) of data.

### 3. Verify Dependencies

The `trainer` container comes with `evidently`, `scipy`, and `psutil` pre-installed.

---

## 🎯 Quick Start (Recommended Flow)

### Step 1: Run Ultra-Fast Training

```bash
# One-click execution
chmod +x scripts/quick_train_docker.sh
./scripts/quick_train_docker.sh
```

### Step 2: View Results

```bash
# View best model
docker exec trainer cat /app/models/saved/training_summary.json | jq '.best_model'

# View model files
docker exec trainer ls -lh /app/models/saved/
```

### Step 3: Verify Model

```python
# Enter container
docker exec -it trainer bash

# Load and test model
python3
>>> import joblib
>>> model = joblib.load('/app/models/saved/best_model.pkl')
>>> print(f"Model Type: {type(model).__name__}")
>>> print(f"Feature Count: {model.n_features_in_}")
```

### Step 4: View MLflow

Access: http://localhost:5001

- Look for experiments: `ultra_fast_production` or `quick_production_training`
- Compare model performance
- Download models

---

## 📊 Output Files

After training completes, in `/app/models/saved/`:

```
models/saved/
├── best_model.pkl              # 🎯 Best Model (For Production)
├── training_summary.json       # 📊 Training Summary
├── training_alerts.jsonl       # ⚠️  Alert Logs
├── training_metrics.jsonl      # 📈 Metrics Time Series
└── evidently_reports/          # 📑 Evidently Reports
    ├── comprehensive_*.html
    ├── data_drift_*.html
    └── monitoring_dashboard.html
```

---

## 🔍 Result Inspection

### View Training Summary

```bash
docker exec trainer cat /app/models/saved/training_summary.json
```

### View Best Model Metrics

```bash
docker exec trainer cat /app/models/saved/training_summary.json | \
  jq '.best_model | {name, val_mae, test_mae, test_r2}'
```

### View Overfitting Stats

```bash
docker exec trainer cat /app/models/saved/training_summary.json | \
  jq '.overfitting_stats'
```

### Download Model Locally

```bash
docker cp trainer:/app/models/saved/best_model.pkl ./
docker cp trainer:/app/models/saved/training_summary.json ./
```

---

## 💡 Optimization Tips

### If Training is Too Slow

1. Use Ultra-Fast Training (3 iterations)
2. Reduce data volume: Add `LIMIT 5000` in SQL query
3. Reduce features: Remove unimportant features

### If Model Overfits

1. Increase regularization: `reg_alpha=0.5, reg_lambda=3.0`
2. Decrease depth: `max_depth=2`
3. Increase min samples: `min_samples_leaf=20`

### If Performance is Poor

1. Check data quality: Missing values, outliers
2. Increase training data volume
3. Try feature engineering
4. Use Full Training (10 iterations)

---

## 🎯 Production Deployment Flow

### 1. Validate Model

```bash
# Validate on test data
docker exec trainer python -c "
import joblib
import pandas as pd
from sqlalchemy import create_engine, text

model = joblib.load('/app/models/saved/best_model.pkl')
engine = create_engine('postgresql://postgres:postgres@postgres:5432/alphapulse')

# Load test data
with engine.connect() as conn:
    df = pd.read_sql(text('SELECT * FROM model_features LIMIT 100'), conn)

# Predict
# ... run prediction tests
print('✅ Model validation passed')
"
```

### 2. Export to Production

```bash
# Copy model and summary
docker cp trainer:/app/models/saved/best_model.pkl ./production/
docker cp trainer:/app/models/saved/training_summary.json ./production/

# Or upload to S3/Cloud Storage
```

### 3. Integrate into API

```python
# Usage in FastAPI
import joblib
from pathlib import Path

model = joblib.load(Path("production/best_model.pkl"))

@app.post("/predict")
async def predict(features: dict):
    # Prepare features
    X = prepare_features(features)
    # Predict
    prediction = model.predict(X)
    return {"prediction": float(prediction[0])}
```

---

## 🐛 Troubleshooting

### Error: "model_features table does not exist"

```bash
# Run feature integration DAG
docker exec airflow-scheduler airflow dags trigger feature_integration_dag
```

### Error: "Insufficient data"

```bash
# Check data volume
docker exec postgres psql -U postgres -d alphapulse -c \
  "SELECT COUNT(*) FROM model_features"

# If data is insufficient, run data pipelines:
# 1. Price Data
# 2. News and Sentiment
# 3. Feature Integration
```

### Error: "MLflow connection failed"

```bash
# Check MLflow status
docker logs mlflow

# Restart MLflow
docker restart mlflow
```

### Poor Performance (R² < 0.1)

- Check target variable distribution
- Verify feature quality
- Increase data volume
- Try different target variables (e.g., `price_change_7d`)

---

## 📚 Related Documentation

- [Full Training Guide](./ITERATIVE_TRAINING_GUIDE.md)
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md)
- [Overfitting Prevention](../src/alphapulse/ml/training/overfitting_prevention.py)
- [Evidently Monitoring](../src/alphapulse/ml/training/evidently_monitoring.py)

---

## ⏱️ Expected Duration

| Training Mode | Time       | Models | Use Case       |
| ------------- | ---------- | ------ | -------------- |
| Ultra-Fast    | 3-5 mins   | 3      | Validation, POC|
| Standard      | 5-10 mins  | 6      | Production     |
| Full          | 10-20 mins | 10     | Optimal Perf   |

---

**Last Updated**: 2026-01-12
**Recommendation**: Use Ultra-Fast training to validate the flow first, then choose Standard or Full based on needs.