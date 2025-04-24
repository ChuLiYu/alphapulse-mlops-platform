import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error
import mlflow
import mlflow.xgboost
import os
import joblib

def load_data(data_dir='/app/src/data/processed'):
    """Load train/val/test data."""
    print(f"Loading data from {data_dir}...")
    train = pd.read_parquet(f"{data_dir}/train.parquet")
    val = pd.read_parquet(f"{data_dir}/val.parquet")
    test = pd.read_parquet(f"{data_dir}/test.parquet")
    return train, val, test

def train_xgboost(train, val, target_col='target'):
    """Train XGBoost model."""
    print("Training XGBoost...")
    
    # Drop non-feature columns
    # Dropping 'created_at', 'updated_at' (datetime64) as XGBoost doesn't support them
    drop_cols = ['timestamp', 'symbol', 'source', target_col, 'created_at', 'updated_at']
    X_train = train.drop(columns=drop_cols, errors='ignore')
    y_train = train[target_col]
    
    X_val = val.drop(columns=drop_cols, errors='ignore')
    y_val = val[target_col]
    
    # Enable MLflow Autologging
    mlflow.xgboost.autolog()
    
    with mlflow.start_run(run_name="xgboost_baseline"):
        # Params with L1/L2 regularization
        params = {
            'objective': 'reg:squarederror',
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 5,
            'eval_metric': 'rmse',
            'reg_alpha': 0.1,   # L1 regularization
            'reg_lambda': 1.0,  # L2 regularization
        }
        mlflow.log_params(params)
        
        # Train
        model = xgb.XGBRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_val, y_val)],
            verbose=False
        )
        
        # Evaluate
        val_preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, val_preds)
        mse = mean_squared_error(y_val, val_preds)
        
        # RMSE calculation (squared=False deprecated in sklearn 1.4)
        rmse = np.sqrt(mse)
        
        print(f"Validation MAE: {mae:.6f}")
        print(f"Validation RMSE: {rmse:.6f}")
        mlflow.log_metric("val_mae", mae)
        mlflow.log_metric("val_rmse", rmse)
        
        # Save model
        os.makedirs("/app/src/models/saved", exist_ok=True)
        joblib.dump(model, "/app/src/models/saved/btc_predictor_v1.pkl")
        print("Model saved to /app/src/models/saved/btc_predictor_v1.pkl")
        
    return model

def main():
    # Set MLflow S3 Endpoint from existing S3_ENDPOINT_URL if not set
    if "MLFLOW_S3_ENDPOINT_URL" not in os.environ and "S3_ENDPOINT_URL" in os.environ:
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = os.environ["S3_ENDPOINT_URL"]
        print(f"Set MLFLOW_S3_ENDPOINT_URL to {os.environ['S3_ENDPOINT_URL']}")

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)
    print(f"MLflow Tracking URI: {tracking_uri}")
    mlflow.set_experiment("btc_price_prediction")
    
    train, val, test = load_data()
    train_xgboost(train, val)

if __name__ == "__main__":
    main()
