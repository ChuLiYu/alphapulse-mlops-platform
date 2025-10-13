#!/usr/bin/env python3
"""
TRAIN_MODEL.PY - Model Training Pipeline Documentation
======================================================

## Module Overview

This module implements the complete machine learning model training pipeline
for the AlphaPulse cryptocurrency trading system. It handles data loading,
feature preparation, model training, and results logging.

## Dependencies

- pandas/numpy: Data manipulation and numerical computation
- sqlalchemy/psycopg2-binary: Database connectivity and ORM
- scikit-learn: Traditional ML models (Random Forest, Linear Regression)
- xgboost/lightgbm: Advanced gradient boosting models
- optuna: Automated hyperparameter tuning
- mlflow: Experiment tracking and model registry

## Configuration

Environment Variables:

- DATABASE_URL: PostgreSQL connection string
- MLFLOW_TRACKING_URI: URI for experiment tracking server
- MODEL_OUTPUT_DIR: Directory to save trained models

## Database Tables

Input Tables:

- model_features: Integrated feature table with 350+ records
  Columns: id, date, ticker, close, volume, price_change_1d,
  rsi_14, rsi_overbought, rsi_oversold, macd_line, ...

Output Tables:

- model_predictions: Stores predictions and confidence scores

"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# ============================================================================

# CONFIGURATION

# ============================================================================

DB_URL = os.getenv(
"DATABASE_URL",
"postgresql://postgres:postgres@localhost:5432/alphapulse"
)
"""
Database URL for PostgreSQL connection.
Format: postgresql://username:password@host:port/database
"""

MODEL_OUTPUT_DIR = Path("/tmp/alphapulse_models")
"""
Directory to store trained model artifacts and metadata.
Created if not exists.
"""

MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================

# STEP 1: LOAD TRAINING DATA

# ============================================================================

print("=" _ 80)
print("🚀 AlphaPulse Model Training Pipeline")
print("=" _ 80)
print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

print("📊 Step 1/4: Loading training data...")

engine = create_engine(DB_URL)
"""
SQLAlchemy engine for database connections.
Manages connection pooling and query execution.
"""

try:
with engine.connect() as conn: # Load model features from database
query = """
SELECT \* FROM model_features
WHERE price_change_1d IS NOT NULL
ORDER BY date DESC
LIMIT 500
"""
X = pd.read_sql(query, conn)
"""
DataFrame with features and target variable.
Query filters: - WHERE price_change_1d IS NOT NULL: Exclude rows without target - ORDER BY date DESC: Sort by most recent first - LIMIT 500: Cap at 500 records for memory efficiency
"""

        # Count total records for validation
        feature_count = pd.read_sql(
            "SELECT COUNT(*) as cnt FROM model_features",
            conn
        ).iloc[0, 0]

    print(f"✅ Loaded {len(X)} training records")
    print(f"📈 Total records in model_features: {feature_count}")

    # Validate sufficient data
    if len(X) < 100:
        print("❌ ERROR: Insufficient data for training (need >= 100 records)")
        sys.exit(1)

except Exception as e:
print(f"❌ ERROR: Database connection failed: {e}")
sys.exit(1)

# ============================================================================

# STEP 2: PREPARE TRAINING DATA

# ============================================================================

print("\n📋 Step 2/4: Preparing training data...")

# Identify feature columns (exclude metadata and target)

target_col = 'price_change_1d'
"""
Target variable: Next-day price change percentage.
Formula: (price_tomorrow - price_today) / price_today \* 100
"""

exclude_cols = [
'id', # Database primary key
'date', # Date index
'ticker', # Asset identifier
'created_at', # Metadata
'feature_set_version', # Version tracking
'data_source', # Data lineage
target_col # Target (excluded from features)
]

# Select only numeric columns not in exclude list

numeric_cols = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
feature_cols = [col for col in numeric_cols if col not in exclude_cols]
"""
Feature Selection Logic:

1. Filter to numeric columns only (int64, float64)
2. Exclude metadata and target columns
3. Result: Features used for model training

Example features:

- rsi_14: Relative Strength Index (momentum)
- volume: Trading volume
- price_change_7d: 7-day price change
- macd_line: MACD indicator value
  """

# Handle missing values - fill NaN with 0 (assumes zero is sensible default)

X_clean = X[feature_cols + [target_col]].fillna(0)
"""
Data Cleaning:

- fillna(0): Replace NaN with 0
- Assumption: Missing values are rare and zero is acceptable
- Alternative: Drop rows with NaN or use forward-fill
  """

# Filter out rows with zero target value (indicates invalid data)

X_clean = X_clean[X_clean[target_col] != 0]
"""
Target Variable Validation:

- Remove rows where price_change_1d == 0
- Reason: Zero target often indicates missing/invalid data
- After filter: Only meaningful predictions remain
  """

print(f"✅ Features: {len(feature_cols)} columns")
print(f"✅ Samples: {len(X_clean)} records")
print(f"✅ Target: {target_col} (price change %)")

# Validate sufficient clean data

if len(X_clean) < 50:
print("❌ ERROR: Not enough valid data for training")
print(f" Available records with non-zero target: {len(X_clean)}")
sys.exit(1)

# ============================================================================

# STEP 3: TRAIN MODELS

# ============================================================================

print("\n🤖 Step 3/4: Training models...")

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# Prepare target and features

y = X_clean[target_col]
"""
Target variable vector (price changes).
Shape: (n_samples,)
"""

X_train_data = X_clean[feature_cols]
"""
Feature matrix (input variables).
Shape: (n_samples, n_features)
"""

# Split data into training and test sets

X_train, X_test, y_train, y_test = train_test_split(
X_train_data, y, test_size=0.2, random_state=42
)
"""
Data Split:

- test_size=0.2: Use 20% for testing (70 samples)
- random_state=42: Fixed seed for reproducibility
- Result: Training set (280), Test set (70)

Purpose of split:

- Training set: Used to fit model parameters
- Test set: Used to evaluate model generalization
  """

# Feature scaling (for linear models)

scaler = StandardScaler()
"""
StandardScaler: Normalize features to zero mean and unit variance.
Formula: z = (x - mean) / std_dev

Why scale?

- Linear models are sensitive to feature magnitude
- Helps with model convergence and stability
- Required for distance-based algorithms
  """

X_train_scaled = scaler.fit_transform(X_train)
"""
Fit on training data only.
fit_transform: Learn mean/std from training set, then scale.

Important: Never fit on test data (leakage prevention)
"""

X_test_scaled = scaler.transform(X_test)
"""
Transform test data using training set statistics.
Uses learned mean/std from training set.
"""

# Define model configurations

models = {
"Linear Regression": LinearRegression(),
"""
Linear Regression: - Model: y = w0 + w1*x1 + w2*x2 + ... + wn\*xn - Pros: Interpretable, fast, baseline model - Cons: Assumes linear relationship
""",

    "Random Forest (n_estimators=50)": RandomForestRegressor(
        n_estimators=50,      # Number of trees in forest
        max_depth=5,          # Maximum tree depth
        random_state=42       # Reproducibility
    ),
    """
    Random Forest (shallow):
      - Model: Ensemble of 50 decision trees
      - max_depth=5: Limit tree complexity to prevent overfitting
      - Pros: Non-linear, handles interactions, robust
      - Cons: Less interpretable than linear models
    """,

    "Random Forest (n_estimators=100)": RandomForestRegressor(
        n_estimators=100,     # More trees for better generalizations
        max_depth=7,          # Allow deeper trees
        random_state=42
    ),
    """
    Random Forest (deeper):
      - Model: Ensemble of 100 decision trees
      - max_depth=7: Deeper trees capture more patterns
      - Pros: Better capacity than shallow model
      - Cons: Risk of overfitting with more depth
    """

}

results = {}
"""
Dictionary to store training results for each model.
Structure:
{
'model_name': {
'mae': float,
'r2': float,
'test_size': int,
'features': int
}
}
"""

for model_name, model in models.items():
print(f"\n Training: {model_name}...")

    # Train model
    if "Linear" in model_name:
        # Linear models use scaled features
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
    else:
        # Tree models don't require scaling
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

    # Evaluate model
    mae = mean_absolute_error(y_test, y_pred)
    """
    Mean Absolute Error:
      - Formula: mean(|y_actual - y_predicted|)
      - Units: Same as target variable (%)
      - Interpretation: Average prediction error in percentage points
      - Lower is better
    """

    r2 = r2_score(y_test, y_pred)
    """
    R² Score (Coefficient of Determination):
      - Formula: 1 - (SS_res / SS_tot)
      - Range: [0, 1] (can be negative for bad models)
      - Interpretation: Proportion of variance explained
      - 1.0 = Perfect fit, 0.0 = Model worse than mean baseline
    """

    results[model_name] = {
        "mae": float(mae),
        "r2": float(r2),
        "test_size": len(X_test),
        "features": len(feature_cols)
    }

    print(f"  ✅ MAE: {mae:.4f}")
    print(f"  ✅ R²: {r2:.4f}")

# ============================================================================

# STEP 4: SAVE RESULTS

# ============================================================================

print("\n💾 Step 4/4: Saving results...")

# Create training summary

summary = {
"timestamp": datetime.now().isoformat(),
"total_records": len(X_clean),
"features_count": len(feature_cols),
"test_split": 0.2,
"models": results,
"best_model": max(results.items(), key=lambda x: x[1]['r2'])[0]
"""
Select best model by R² score: - max(): Find maximum value - key=lambda: Sort by model R² value - [0]: Get model name from tuple (name, metrics)
"""
}

summary_file = MODEL_OUTPUT_DIR / "training_summary.json"
with open(summary_file, 'w') as f:
json.dump(summary, f, indent=2)
"""
Save results as JSON: - indent=2: Pretty-print with indentation - Human-readable format - Machine-readable for downstream tools
"""

print(f"✅ Results saved to {summary_file}")

# ============================================================================

# DISPLAY FINAL SUMMARY

# ============================================================================

print("\n" + "=" _ 80)
print("📊 TRAINING SUMMARY")
print("=" _ 80)
print(f"Training Records: {len(X_clean)}")
print(f"Feature Columns: {len(feature_cols)}")
print(f"\nModel Performance:")

for model_name, metrics in results.items():
print(f"\n {model_name}:")
print(f" MAE: {metrics['mae']:.4f}")
print(f" R²: {metrics['r2']:.4f}")

best_model_name = summary["best_model"]
best_metrics = results[best_model_name]

print(f"\n🏆 BEST MODEL: {best_model_name}")
print(f" R² Score: {best_metrics['r2']:.4f}")
print(f" MAE: {best_metrics['mae']:.4f}")

print(f"\n⏰ Completion Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" \* 80)
print("✅ Training completed successfully!\n")

# ============================================================================

# END OF TRAINING PIPELINE

# ============================================================================

"""
Next Steps:

1. Review model performance in training_summary.json
2. Deploy best model to production
3. Monitor model performance on new data
4. Retrain if performance degrades below threshold

For integration with MLflow:

- Use mlflow.log_model() to save model artifacts
- Use mlflow.log_metrics() to log performance metrics
- Use mlflow.log_params() to log hyperparameters
- Track experiment runs in MLflow UI
  """
