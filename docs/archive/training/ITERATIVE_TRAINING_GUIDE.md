# Iterative Training Guide

This guide explains how to use the automated training system to build robust trading models while preventing overfitting.

## Core Concepts

### 1. The Trainer API
The training logic is isolated in a dedicated container (`alphapulse-trainer`) accessible via a REST API. This separates heavy ML dependencies from the data pipeline.

### 2. Training Modes
- **ultra_fast**: 3 iterations, 3-fold CV. Designed for quick logic verification.
- **quick_production**: 6 iterations, 3-fold CV. Balanced performance.
- **full**: 10+ iterations, 5-fold CV. Comprehensive hyperparameter search.

## Automated Workflow

1. **Data Load**: Automatically fetches the latest `model_features` from PostgreSQL.
2. **Sanitation**: Removes non-numeric columns and handles infinity/NaN values.
3. **Iterative Search**:
   - Tests different algorithms (XGBoost, Random Forest, Ridge).
   - Varies regularization (L1/L2) to combat noise.
4. **Overfitting Detection**:
   - Compares Train R² vs. Validation R².
   - If the gap exceeds 15%, the model is flagged as overfit and rejected.
5. **MLflow Tracking**: Every run is logged with parameters, metrics, and artifact paths.

## How to Trigger Training

### Via Airflow (Recommended)
Trigger the `model_training_pipeline` DAG. You can pass a JSON configuration:
```json
{
  "mode": "full"
}
```

### Via CLI (Manual)
```bash
curl -X POST http://localhost:8181/train -H "Content-Type: application/json" -d '{"mode": "ultra_fast"}'
```

## Monitoring
Check training progress at:
- **MLflow UI**: `http://localhost:5001`
- **Trainer Logs**: `docker logs -f alphapulse-trainer`

---
**Version**: 1.0
**Author**: MLOps Team
