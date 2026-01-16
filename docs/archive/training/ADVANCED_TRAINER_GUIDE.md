# AlphaPulse Advanced Trainer - Comprehensive Guide

**Version**: 2.0  
**Date**: January 12, 2026  
**Status**: Production Ready ✅

---

## Table of Contents

1. [Anti-Overfitting Measures](#anti-overfitting-measures)
2. [Architecture Overview](#architecture-overview)
3. [Training Pipeline](#training-pipeline)
4. [Validation & Testing](#validation--testing)
5. [Container Setup](#container-setup)
6. [Quick Start](#quick-start)
7. [Troubleshooting](#troubleshooting)

---

## Anti-Overfitting Measures

### What is Overfitting?

Overfitting occurs when a model learns the training data too well, including its noise and quirks, resulting in:
- **Excellent training performance** (R² ≈ 1.0, MAE ≈ 0.0)
- **Poor test performance** (R² drops significantly, MAE increases)
- Model fails on unseen real-world data

Previous training achieved **R² = 1.0 (perfect fit)**, which indicates severe overfitting. The advanced trainer fixes this.

### 1. **Train/Validation/Test Split (60/20/20)**

```
Total Data (100%)
├── Training Set (60%) ────────► Used for model fitting
├── Validation Set (20%) ───────► Used for hyperparameter tuning & early stopping
└── Test Set (20%) ─────────────► Used ONLY for final evaluation (never seen during training)
```

**Why Three Sets?**
- **Train**: Model learns patterns
- **Validation**: Tune hyperparameters without overfitting to training data
- **Test**: Honest evaluation of generalization capability

**Previous approach**: Only train/test split, no validation set = hyperparameters tuned on test data = overfitting to test metrics.

---

### 2. **Cross-Validation (K-Fold = 5)**

```
Data Split into 5 Folds:
Fold 1: [TRAIN TRAIN TRAIN TRAIN | VALIDATE]
Fold 2: [TRAIN TRAIN TRAIN | VALIDATE | TRAIN]
Fold 3: [TRAIN TRAIN | VALIDATE | TRAIN TRAIN]
Fold 4: [TRAIN | VALIDATE | TRAIN TRAIN TRAIN]
Fold 5: [VALIDATE | TRAIN TRAIN TRAIN TRAIN]

Average of 5 scores = Robust estimate of generalization
```

**Benefits**:
- Multiple estimates of model performance
- Detects if model is unstable across different data subsets
- Better use of limited data
- Standard deviation shows robustness

---

### 3. **Regularization Techniques**

#### A. Ridge Regression (L2 Regularization)

Adds penalty for large coefficients:
```
Loss = MSE + alpha * Σ(coefficient²)
```

- **Low alpha** (≈0): No regularization (original model - may overfit)
- **High alpha**: Strong regularization (simpler model - may underfit)
- **Optimal alpha**: Balance between bias and variance

**Effect**: Reduces coefficient magnitudes, preventing model from fitting to noise.

#### B. Lasso Regression (L1 Regularization)

Adds penalty for coefficient absolute values:
```
Loss = MSE + alpha * Σ|coefficient|
```

**Unique feature**: Forces some coefficients to exactly 0, performing automatic feature selection.

**Output**: Only most important features selected (ignores noisy features).

#### C. Gradient Boosting with Early Stopping

```
Iteration 1: Add weak learner to model
Iteration 2: Fit residuals with another learner
...
Iteration N: ✋ STOP - Validation score stopped improving
```

**Early Stopping prevents overfitting** by stopping before model memorizes training data.

**Regularization parameters**:
- `max_depth`: Tree depth (lower = simpler model)
- `learning_rate`: Step size (lower = more conservative)
- `subsample`: Fraction of samples (< 1.0 adds randomness = less overfitting)
- `min_samples_leaf`: Minimum samples in leaf (prevents noise fitting)

---

### 4. **Feature Scaling with RobustScaler**

```
Scaled_value = (x - median) / IQR
```

**Why RobustScaler instead of StandardScaler?**
- StandardScaler affected by outliers
- RobustScaler uses median/IQR, robust to extreme values
- Important for stock market data with sudden price movements

**Applied independently**:
- **Fit**: Only on training data
- **Transform**: Applied to validation and test data
- **Prevents data leakage**: Test data statistics don't influence scaling

---

### 5. **Learning Curves for Overfitting Detection**

```
Model Performance vs Training Set Size

Perfect Fit (Underfitting):
  both curves at bottom ──────────────────┐
                                           │
Learning Well:                             │
  curves converge at high score ───┐       │
                                   ↓       ↓
Overfitting:
  training ≈ 1.0, validation ≈ 0.5 (large gap)
```

The trainer computes:
- **Train curve**: Performance as training set grows
- **Validation curve**: Performance on held-out validation set
- **Overfitting gap**: `mean(train_scores - val_scores)`
  - Gap > 0.1 = Significant overfitting detected ⚠️
  - Gap ≈ 0 = Model learns without memorizing ✅

---

### 6. **Hyperparameter Tuning with GridSearchCV**

Automatically tests combinations of parameters:

```
Parameters to tune:
├── max_depth: [3, 4, 5]
├── learning_rate: [0.01, 0.05, 0.1]
├── subsample: [0.8, 0.9, 1.0]
└── min_samples_leaf: [1, 2, 4]

Total combinations: 3 × 3 × 3 × 4 = 108 models tested

Best parameters selected on validation set (never test set)
```

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Training Pipeline                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Data Loading                                              │
│     └─ Query PostgreSQL (model_features table)               │
│        ├─ 350+ records with 2+ features                      │
│        └─ Filter: price_change_1d IS NOT NULL                │
│                                                               │
│  2. Feature Preparation                                       │
│     └─ Remove near-constant features                          │
│     └─ Handle missing values (forward/backward fill)          │
│     └─ Output: 350 samples × 8 features                       │
│                                                               │
│  3. Data Splitting (60/20/20)                                │
│     ├─ Train: 210 samples (for fitting)                      │
│     ├─ Val:   70 samples (for tuning)                        │
│     └─ Test:  70 samples (for final evaluation)              │
│                                                               │
│  4. Feature Scaling                                           │
│     └─ RobustScaler fit on train, applied to val/test        │
│                                                               │
│  5. Model Training (3 Models)                                │
│     ├─ Ridge Regression                                       │
│     │  └─ L2 Regularization (alpha tuning)                   │
│     ├─ Lasso Regression                                       │
│     │  └─ L1 Regularization + Feature Selection              │
│     └─ Gradient Boosting                                      │
│        └─ Early Stopping + Parameter Tuning                  │
│                                                               │
│  6. Validation                                                │
│     ├─ K-Fold Cross-Validation (5 folds)                     │
│     ├─ Learning Curves                                        │
│     └─ Overfitting Detection                                 │
│                                                               │
│  7. Evaluation (Train/Val/Test)                              │
│     └─ Metrics: MAE, RMSE, R², MAPE                          │
│                                                               │
│  8. Model Selection                                           │
│     └─ Best model chosen based on TEST R² (generalization)   │
│                                                               │
│  9. Artifact Saving                                           │
│     ├─ Model (pickle)                                         │
│     ├─ Scaler (pickle)                                        │
│     ├─ Feature names (JSON)                                  │
│     └─ Complete results (JSON)                                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Files Generated

```
/tmp/alphapulse_models/
├── best_model_2026-01-12T15-38-30.pkl         (Trained model)
├── scaler_2026-01-12T15-38-30.pkl              (Feature scaler)
├── feature_names_2026-01-12T15-38-30.json      (Feature list)
├── training_results_2026-01-12T15-38-30.json   (Complete results)
├── training.log                                  (Execution log)
└── validation_report_20260112_153830.json       (Validation results)
```

---

## Training Pipeline

### Step-by-Step Execution

Complete pipeline detailed in code comments in `train_model_advanced.py`.

---

## Validation & Testing

### Validation Module (`validate_model.py`)

Five comprehensive tests:

1. **Artifact Validation**: Check model files load correctly
2. **Recent Data Testing**: Test on last 30 days (unseen data)
3. **Robustness Testing**: Add noise (1%, 5%, 10%) and verify stability
4. **Regression Testing**: Compare with baseline metrics
5. **Batch Prediction**: Test with different batch sizes (10, 50, 100, 200)

---

## Container Setup

### Multi-Stage Docker Build

**Stage 1 (Builder)**:
- Installs build tools and Python packages
- Creates virtual environment
- ~2GB intermediate image

**Stage 2 (Runtime)**:
- Copies only virtual environment
- Minimal dependencies
- ~600MB final image

### Security Features

- Non-root user (`trainer:1000`)
- Minimal attack surface
- No build tools in production image
- Health checks included

---

## Quick Start

### Docker Execution (Recommended)

```bash
# Build image
cd /tmp
docker build -f Dockerfile.trainer -t trainer:2.0 .

# Run training
docker run --rm \
  --network alphapulse-network \
  -e DATABASE_URL="postgresql://postgres:postgres@postgres:5432/alphapulse" \
  -v /tmp/alphapulse_models:/models \
  trainer:2.0

# Run validation
docker run --rm \
  --network alphapulse-network \
  -e DATABASE_URL="postgresql://postgres:postgres@postgres:5432/alphapulse" \
  -v /tmp/alphapulse_models:/models \
  trainer:2.0 \
  python validate_model.py
```

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  trainer:
    build:
      context: /tmp
      dockerfile: Dockerfile.trainer
    image: trainer:2.0
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/alphapulse
    volumes:
      - alphapulse_models:/models
    networks:
      - alphapulse-network

volumes:
  alphapulse_models:

networks:
  alphapulse-network:
    external: true
```

---

## Troubleshooting

### Extreme Overfitting (R² train = 1.0, test = 0.5)

```python
# Increase regularization
Ridge(alpha=10.0)
GradientBoosting(max_depth=3)

# Collect more data
# Engineer new features
```

### Underfitting (All predictions = mean value)

```python
# Reduce regularization
Ridge(alpha=0.01)

# Try different model
# Verify feature-target correlation
```

### Database Connection Errors

```bash
# Verify connection
psql -h localhost -U postgres -d alphapulse

# Check container network
docker network inspect alphapulse-network

# Verify DATABASE_URL
echo $DATABASE_URL
```

### Out of Memory

```python
# Reduce hyperparameter combinations
# Load data in chunks
# Increase Docker memory limit
docker run --memory 4g trainer:2.0
```

---

**End of Guide**
