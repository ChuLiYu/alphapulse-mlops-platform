"""
Training Server for AlphaPulse ML Models

Provides HTTP API endpoints for triggering model training from Mage ETL pipeline.
Separated from Mage container for cleaner architecture and dependency management.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, "/app/src")

from alphapulse.ml.training.iterative_trainer import IterativeTrainer, TrainingConfig

app = FastAPI(
    title="AlphaPulse Training Service",
    description="ML model training service for AlphaPulse",
    version="1.0.0",
)


class TrainingRequest(BaseModel):
    """Training request payload"""

    mode: str = "ultra_fast"  # Options: ultra_fast, quick_production, full
    experiment_name: Optional[str] = None
    n_iterations: Optional[int] = None
    cv_splits: Optional[int] = None


class TrainingStatus:
    """Shared training status tracker"""

    def __init__(self):
        self.is_training = False
        self.current_job: Optional[Dict] = None
        self.last_result: Optional[Dict] = None


training_status = TrainingStatus()


def get_training_config(mode: str, **kwargs) -> TrainingConfig:
    """Get training configuration based on mode"""

    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    output_dir = os.getenv("MODEL_OUTPUT_DIR", "/app/models/saved")

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    if mode == "ultra_fast":
        return TrainingConfig(
            data_source="model_features",
            target_column="target_return",
            min_samples_required=300,
            n_iterations=kwargs.get("n_iterations") or 3,
            cv_splits=kwargs.get("cv_splits") or 3,
            early_stopping_rounds=20,
            early_stopping_patience=1,
            max_train_val_gap=10.0,
            max_val_test_gap=10.0,
            min_val_r2=-1.0,
            mlflow_uri=mlflow_uri,
            experiment_name=kwargs.get("experiment_name", "ultra_fast_production"),
            output_dir=output_dir,
            save_all_iterations=False,
        )
    elif mode == "quick_production":
        return TrainingConfig(
            data_source="model_features",
            target_column="target_return",
            min_samples_required=500,
            n_iterations=kwargs.get("n_iterations") or 6,
            test_size=0.15,
            validation_size=0.15,
            cv_splits=kwargs.get("cv_splits") or 3,
            early_stopping_rounds=30,
            early_stopping_patience=2,
            max_train_val_gap=0.15,
            max_val_test_gap=0.10,
            min_val_r2=0.05,
            mlflow_uri=mlflow_uri,
            experiment_name=kwargs.get("experiment_name", "quick_production_training"),
            output_dir=output_dir,
            save_all_iterations=False,
        )
    elif mode == "full":
        return TrainingConfig(
            data_source="feature_store",
            target_column="target_return",
            min_samples_required=1000,
            n_iterations=kwargs.get("n_iterations") or 10,
            test_size=0.15,
            validation_size=0.15,
            cv_splits=kwargs.get("cv_splits") or 5,
            early_stopping_rounds=50,
            early_stopping_patience=3,
            max_train_val_gap=0.40,
            max_val_test_gap=0.30,
            min_val_r2=-1.0,
            mlflow_uri=mlflow_uri,
            experiment_name=kwargs.get("experiment_name", "full_training"),
            output_dir=output_dir,
            save_all_iterations=True,
        )
    elif mode == "adaptive":
        return TrainingConfig(
            data_source="feature_store",
            target_column="target_return",
            min_samples_required=300,
            use_optuna=True,
            optuna_n_trials=kwargs.get("n_trials", 20),
            optuna_timeout=kwargs.get("timeout", 1800),
            max_train_val_gap=0.40,
            mlflow_uri=mlflow_uri,
            experiment_name=kwargs.get("experiment_name", "adaptive_automl"),
            output_dir=output_dir,
        )
    else:
        raise ValueError(f"Unknown training mode: {mode}")


async def run_training(request: TrainingRequest):
    """Run training in background"""
    try:
        training_status.is_training = True
        training_status.current_job = {
            "mode": request.mode,
            "started_at": datetime.now().isoformat(),
            "status": "running",
        }

        print(f"🚀 Starting training in {request.mode} mode...")

        # Get configuration
        config = get_training_config(
            mode=request.mode,
            experiment_name=request.experiment_name,
            n_iterations=request.n_iterations,
            cv_splits=request.cv_splits,
        )

        # Create trainer and run
        trainer = IterativeTrainer(config)

        # Force sanitize data in trainer's config or handle it during load
        # Actually, let's inject a data cleaning step right here if possible, 
        # but IterativeTrainer loads its own data.
        
        # Let's override the trainer's prepare_features method right here to be absolutely sure
        original_prepare = trainer.prepare_features
        def safe_prepare(df):
            import numpy as np
            # Select only numbers
            X = df.select_dtypes(include=[np.number]).copy()
            # Drop known bad columns
            bad = ["id", "loaded_at", "processed_at", "price_change_1d", "price_change_3d", "price_change_7d", config.target_column]
            X = X.drop(columns=[c for c in bad if c in X.columns])
            y = df[config.target_column].copy()
            print(f"🛠️ [SERVER DEBUG] Cleaned features: {X.columns.tolist()[:5]}... ({len(X.columns)} total)")
            return X, y
        
        trainer.prepare_features = safe_prepare

        # For ultra_fast mode, apply optimized model configs
        if request.mode == "ultra_fast":
            import xgboost as xgb
            from sklearn.ensemble import RandomForestRegressor

            best_configs = [
                {
                    "name": "xgboost_balanced",
                    "class": xgb.XGBRegressor,
                    "params": {
                        "n_estimators": 100,
                        "max_depth": 3,
                        "learning_rate": 0.05,
                        "reg_alpha": 0.1,
                        "reg_lambda": 1.0,
                        "subsample": 0.8,
                        "colsample_bytree": 0.8,
                        "random_state": 42,
                    },
                },
                {
                    "name": "xgboost_conservative",
                    "class": xgb.XGBRegressor,
                    "params": {
                        "n_estimators": 80,
                        "max_depth": 2,
                        "learning_rate": 0.03,
                        "reg_alpha": 0.2,
                        "reg_lambda": 2.0,
                        "subsample": 0.8,
                        "colsample_bytree": 0.8,
                        "random_state": 42,
                    },
                },
                {
                    "name": "random_forest_balanced",
                    "class": RandomForestRegressor,
                    "params": {
                        "n_estimators": 100,
                        "max_depth": 5,
                        "min_samples_leaf": 10,
                        "min_samples_split": 20,
                        "max_features": "sqrt",
                        "n_jobs": -1,
                        "random_state": 42,
                    },
                },
            ]
            trainer.generate_model_configs = lambda: best_configs

            trainer.generate_model_configs = lambda: best_configs
        
        if config.use_optuna:
            summary = trainer.run_optuna_optimization()
        else:
            summary = trainer.run_iterative_training()

        training_status.last_result = {
            "mode": request.mode,
            "started_at": training_status.current_job["started_at"],
            "completed_at": datetime.now().isoformat(),
            "status": "success",
            "summary": summary,
        }

        print(f"✅ Training completed successfully!")
        
        # AUTOMATIC DEPLOYMENT / SIGNAL GENERATION
        if summary.get("best_iteration"):
            print("🚀 Promoting model to production and generating signals...")
            try:
                from alphapulse.ml.inference.engine import InferenceEngine
                engine = InferenceEngine()
                signal = engine.generate_signals()
                print(f"📡 Automatic deployment successful! Latest signal: {signal}")
            except Exception as deploy_err:
                print(f"⚠️ Training succeeded but auto-deployment failed: {deploy_err}")
        
        print(f"   Best model: {summary.get('best_model', {}).get('name', 'N/A')}")

    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"❌ Training failed: {error_msg}")
        traceback.print_exc()
        training_status.last_result = {
            "mode": request.mode,
            "started_at": training_status.current_job.get("started_at"),
            "completed_at": datetime.now().isoformat(),
            "status": "failed",
            "error": error_msg,
        }

    finally:
        training_status.is_training = False
        training_status.current_job = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "alphapulse-trainer",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/status")
async def get_status():
    """Get current training status"""
    return {
        "is_training": training_status.is_training,
        "current_job": training_status.current_job,
        "last_result": training_status.last_result,
    }


@app.post("/train")
async def trigger_training(request: TrainingRequest, background_tasks: BackgroundTasks):
    """
    Trigger model training

    Modes:
    - ultra_fast: 3 iterations, 3-fold CV, optimized models only
    - quick_production: 6 iterations, 3-fold CV, balanced speed/quality
    - full: 10 iterations, 5-fold CV, comprehensive search
    """
    if training_status.is_training:
        raise HTTPException(
            status_code=409,
            detail="Training already in progress. Check /status for details.",
        )

    # Validate mode
    if request.mode not in ["ultra_fast", "quick_production", "full", "adaptive"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Must be one of: ultra_fast, quick_production, full, adaptive",
        )

    # Start training in background
    background_tasks.add_task(run_training, request)

    return {
        "status": "accepted",
        "message": f"Training started in {request.mode} mode",
        "mode": request.mode,
        "check_status_at": "/status",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AlphaPulse Training Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "train": "/train (POST)",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    print("=" * 80)
    print("🚂 AlphaPulse Training Server")
    print("=" * 80)
    print(f"Starting server on http://0.0.0.0:8080")
    print(f"API Documentation: http://0.0.0.0:8080/docs")
    print("=" * 80)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
    )
