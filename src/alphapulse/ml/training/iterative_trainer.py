"""
Iterative Model Training System with Anti-Overfitting Mechanisms.

This module provides a comprehensive iterative training framework that:
1. Automatically integrates sentiment and price data
2. Runs multiple training iterations with different hyperparameters
3. Implements cross-validation, early stopping, and regularization
4. Monitors and prevents overfitting
5. Tracks all experiments in MLflow
"""

import json
import os
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import mlflow.sklearn
import numpy as np
import pandas as pd
import xgboost as xgb

try:
    from catboost import CatBoostRegressor

    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("⚠️  CatBoost not available. CatBoost models will be skipped.")
from scipy import stats
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from sqlalchemy import create_engine, text

import mlflow
import optuna
from optuna.trial import TrialState

warnings.filterwarnings("ignore")

# Check for optional monitoring dependencies
try:
    from alphapulse.ml.training.evidently_monitoring import EvidentlyMonitor
    from alphapulse.ml.training.monitoring import TrainingMonitor

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    print(
        "⚠️  Monitoring modules not available. Training will continue without detailed monitoring."
    )


@dataclass
class TrainingConfig:
    """Configuration for iterative training."""

    # Data settings
    data_source: str = "feature_store"  # Use centralized feature store
    target_column: str = "target_return"  # What we're predicting
    min_samples_required: int = 1000
    db_connection_string: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )
    )

    # Training settings
    n_iterations: int = 10  # Number of training iterations
    test_size: float = 0.15
    validation_size: float = 0.15

    # Cross-validation settings
    cv_splits: int = 5  # Time series cross-validation splits

    # Early stopping settings
    early_stopping_rounds: int = 50
    early_stopping_patience: int = 3  # Iterations without improvement

    # Overfitting detection thresholds
    max_train_val_gap: float = 0.15  # Max acceptable gap between train/val metrics
    max_val_test_gap: float = 0.10  # Max acceptable gap between val/test metrics
    min_val_r2: float = 0.1  # Minimum R² on validation set

    # Model diversity settings
    ensemble_top_k: int = 3  # Number of top models to ensemble

    # MLflow settings
    mlflow_uri: str = field(
        default_factory=lambda: os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    )
    experiment_name: str = "iterative_training"

    # Output settings
    output_dir: str = "/app/models/saved"
    save_all_iterations: bool = False  # Save all models or just the best

    # Optuna settings
    use_optuna: bool = False
    optuna_n_trials: int = 50
    optuna_timeout: int = 3600  # 1 hour


@dataclass
class IterationResult:
    """Results from a single training iteration."""

    iteration: int
    model_name: str
    hyperparameters: Dict[str, Any]

    # Metrics
    train_mae: float
    train_rmse: float
    train_r2: float

    val_mae: float
    val_rmse: float
    val_r2: float

    test_mae: float
    test_rmse: float
    test_r2: float

    # Cross-validation metrics
    cv_mean_mae: float
    cv_std_mae: float
    cv_scores: List[float]

    # Overfitting indicators
    train_val_gap: float  # (train_metric - val_metric) / train_metric
    val_test_gap: float
    is_overfit: bool

    # Training metadata
    training_time: float
    mlflow_run_id: Optional[str] = None
    model_path: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class IterativeTrainer:
    """
    Iterative training system with automatic overfitting prevention.
    """

    def __init__(self, config: TrainingConfig):
        """
        Initialize the iterative trainer.

        Args:
            config: Training configuration
        """
        self.config = config
        self.results: List[IterationResult] = []
        self.best_model = None
        self.best_result = None

        # Set up MLflow
        mlflow.set_tracking_uri(config.mlflow_uri)
        experiment_name = config.experiment_name or "default_experiment"
        mlflow.set_experiment(experiment_name)

        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

        # Initialize monitoring
        self.monitor = None
        self.evidently_monitor = None

        if MONITORING_AVAILABLE:
            try:
                self.monitor = TrainingMonitor(output_dir=config.output_dir)
                reports_dir = os.path.join(config.output_dir, "evidently_reports")
                self.evidently_monitor = EvidentlyMonitor(
                    output_dir=reports_dir, mlflow_uri=config.mlflow_uri
                )
                print("✅ Monitoring systems enabled (Basic + Evidently)")
            except Exception as e:
                print(f"⚠️  Could not initialize Evidently: {str(e)}")
        else:
            print("⚠️  Evidently not available. Install with: pip install evidently")

    def load_data(self) -> pd.DataFrame:
        """Load data from database"""
        print(f"📥 Loading data from {self.config.data_source}...")

        engine = create_engine(self.config.db_connection_string)
        query = f"""
            SELECT * FROM {self.config.data_source}
            WHERE date IS NOT NULL
            ORDER BY date ASC
        """

        with engine.connect() as conn:
            df = pd.read_sql(query, conn.connection)

        print(f"✅ Loaded {len(df)} rows")

        if len(df) < self.config.min_samples_required:
            raise ValueError(
                f"Insufficient data: {len(df)} rows < {self.config.min_samples_required} required"
            )

        # Split data chronologically (critical for time series)
        n = len(df)
        test_size = int(n * self.config.test_size)
        val_size = int(n * self.config.validation_size)
        train_size = n - test_size - val_size

        train_df = df.iloc[:train_size].copy()
        val_df = df.iloc[train_size : train_size + val_size].copy()
        test_df = df.iloc[train_size + val_size :].copy()

        print(
            f"📈 Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}"
        )

        # Data quality checks
        self._validate_data_quality(train_df, val_df, test_df)

        return train_df, val_df, test_df

    def _validate_data_quality(
        self, train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame
    ):
        """
        Validate data quality and distributions.

        Args:
            train_df: Training data
            val_df: Validation data
            test_df: Test data
        """
        print("\n🔍 Data Quality Checks:")

        # Check for missing values
        for name, df in [("Train", train_df), ("Val", val_df), ("Test", test_df)]:
            missing_pct = (df.isnull().sum() / len(df) * 100).max()
            print(f"  {name}: Max missing = {missing_pct:.2f}%")

            if missing_pct > 20:
                warnings.warn(f"{name} set has > 20% missing values in some columns")

        # Check target distribution
        target = self.config.target_column
        if target in train_df.columns:
            train_mean = train_df[target].mean()
            val_mean = val_df[target].mean()
            test_mean = test_df[target].mean()

            print(f"\n  Target ({target}) distribution:")
            print(f"    Train mean: {train_mean:.6f}")
            print(f"    Val mean: {val_mean:.6f}")
            print(f"    Test mean: {test_mean:.6f}")

            # Warn if distributions are very different
            if abs(train_mean - val_mean) > abs(train_mean) * 0.5:
                warnings.warn(
                    "Train and validation target distributions differ significantly"
                )

        # Check for data leakage (temporal)
        if "date" in train_df.columns:
            train_max_date = train_df["date"].max()
            val_min_date = val_df["date"].min()
            test_min_date = test_df["date"].min()

            if val_min_date <= train_max_date:
                raise ValueError(
                    "Data leakage detected: validation data overlaps with training data"
                )
            if test_min_date <= val_df["date"].max():
                raise ValueError(
                    "Data leakage detected: test data overlaps with validation data"
                )

            print(f"\n  ✅ No temporal data leakage detected")

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features and target for training.
        """
        # 1. Identify Target
        y = df[self.config.target_column].copy()

        # 2. Identify Non-Feature Columns (Blacklist)
        blacklist = [
            "id",
            "date",
            "ticker",
            "created_at",
            "feature_set_version",
            "data_source",
            "price_change_1d",
            "price_change_3d",
            "price_change_7d",
            "loaded_at",
            "processed_at",
            "target_return",
            self.config.target_column,
        ]

        # 3. Create X by selecting only NUMERIC columns and dropping blacklist
        X = df.select_dtypes(include=[np.number]).copy()

        # Drop blacklist columns and any column starting with 'metadata_'
        cols_to_drop = [c for c in blacklist if c in X.columns]
        metadata_cols = [c for c in X.columns if c.startswith("metadata_")]
        cols_to_drop.extend(metadata_cols)

        X = X.drop(columns=list(set(cols_to_drop)))

        print(f"DEBUG: X columns = {X.columns.tolist()}")

        # 4. Handle missing/inf values
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(X.median())

        # Final safety check: ensuring no object/datetime dtypes remain
        non_numeric = X.select_dtypes(exclude=[np.number]).columns
        if not non_numeric.empty:
            print(f"⚠️ Warning: Dropping non-numeric columns: {non_numeric.tolist()}")
            X = X.drop(columns=non_numeric)

        return X, y

    def run_cross_validation(
        self, model, X: pd.DataFrame, y: pd.Series, model_name: str
    ) -> Tuple[float, float, List[float]]:
        """
        Run time series cross-validation.
        """
        # Ensure n_splits is an integer
        n_splits = int(self.config.cv_splits or 5)
        tscv = TimeSeriesSplit(n_splits=n_splits)
        cv_scores = []

        print(f"\n  🔄 Running {n_splits}-fold time series cross-validation...")

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            X_train_cv = X.iloc[train_idx]
            y_train_cv = y.iloc[train_idx]
            X_val_cv = X.iloc[val_idx]
            y_val_cv = y.iloc[val_idx]

            # Train model on this fold
            if hasattr(model, "fit"):
                # Clone model for this fold
                from sklearn.base import clone

                fold_model = clone(model)

                # For XGBoost, remove early_stopping_rounds in CV
                if isinstance(fold_model, xgb.XGBRegressor) and hasattr(
                    fold_model, "early_stopping_rounds"
                ):
                    fold_model.early_stopping_rounds = None

                fold_model.fit(X_train_cv, y_train_cv)

                # Evaluate
                y_pred = fold_model.predict(X_val_cv)
                mae = mean_absolute_error(y_val_cv, y_pred)
                cv_scores.append(mae)

                print(f"    Fold {fold}: MAE = {mae:.6f}")

        mean_mae = np.mean(cv_scores)
        std_mae = np.std(cv_scores)

        print(f"  ✅ CV Mean MAE: {mean_mae:.6f} ± {std_mae:.6f}")

        return mean_mae, std_mae, cv_scores

    def train_single_iteration(
        self,
        iteration: int,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
        model_config: Dict[str, Any],
    ) -> IterationResult:
        """
        Train a single iteration with given hyperparameters.

        Args:
            iteration: Iteration number
            train_df: Training data
            val_df: Validation data
            test_df: Test data
            model_config: Model configuration

        Returns:
            IterationResult with metrics and diagnostics
        """
        import time

        start_time = time.time()

        model_name = model_config["name"]
        model_class = model_config["class"]
        params = model_config["params"]

        print(f"\n{'='*80}")
        print(f"🚀 Iteration {iteration}: {model_name}")
        print(f"{'='*80}")
        print(f"Parameters: {json.dumps(params, indent=2)}")

        # Prepare features
        X_train, y_train = self.prepare_features(train_df)
        X_val, y_val = self.prepare_features(val_df)
        X_test, y_test = self.prepare_features(test_df)

        # Start MLflow run
        with mlflow.start_run(run_name=f"iter_{iteration}_{model_name}") as run:
            mlflow.log_params(params)
            mlflow.log_param("iteration", iteration)
            mlflow.log_param("model_name", model_name)

            # Train model
            print(f"\n📚 Training {model_name}...")
            model = model_class(**params)

            # Add early stopping for compatible models
            if isinstance(model, (xgb.XGBRegressor,)):
                # XGBoost 2.0+ uses early_stopping_rounds in constructor
                if hasattr(model, "early_stopping_rounds"):
                    model.early_stopping_rounds = self.config.early_stopping_rounds

                model.fit(
                    X_train,
                    y_train,
                    eval_set=[(X_val, y_val)],
                    verbose=False,
                )
            elif isinstance(model, CatBoostRegressor):
                model.fit(
                    X_train,
                    y_train,
                    eval_set=(X_val, y_val),
                    early_stopping_rounds=self.config.early_stopping_rounds,
                    verbose=False,
                )
            else:
                model.fit(X_train, y_train)

            # Predictions
            y_train_pred = model.predict(X_train)
            y_val_pred = model.predict(X_val)
            y_test_pred = model.predict(X_test)

            # Calculate metrics
            train_mae = mean_absolute_error(y_train, y_train_pred)
            train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
            train_r2 = r2_score(y_train, y_train_pred)

            val_mae = mean_absolute_error(y_val, y_val_pred)
            val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
            val_r2 = r2_score(y_val, y_val_pred)

            test_mae = mean_absolute_error(y_test, y_test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
            test_r2 = r2_score(y_test, y_test_pred)

            # Log metrics to MLflow
            mlflow.log_metrics(
                {
                    "train_mae": train_mae,
                    "train_rmse": train_rmse,
                    "train_r2": train_r2,
                    "val_mae": val_mae,
                    "val_rmse": val_rmse,
                    "val_r2": val_r2,
                    "test_mae": test_mae,
                    "test_rmse": test_rmse,
                    "test_r2": test_r2,
                }
            )

            # Cross-validation
            cv_mean_mae, cv_std_mae, cv_scores = self.run_cross_validation(
                model, X_train, y_train, model_name
            )

            mlflow.log_metrics({"cv_mean_mae": cv_mean_mae, "cv_std_mae": cv_std_mae})

            # Overfitting detection (More robust version for financial time series)
            # 1. MAE Gap (Still useful but sensitive to scale)
            train_val_gap = abs(train_mae - val_mae) / train_mae if train_mae > 0 else 0
            val_test_gap = abs(val_mae - test_mae) / val_mae if val_mae > 0 else 0

            # 2. R2 Stability (More robust to market regime changes)
            r2_gap = abs(train_r2 - val_r2)

            # 3. Scientific Overfitting Rule:
            # - R2 gap should not be huge
            # - Val R2 must be positive
            # - Allow higher MAE gap if R2 is stable (handles volatility shifts)
            is_overfit = (
                r2_gap > 0.4  # Acceptable R2 spread
                or val_r2 < self.config.min_val_r2
                or (train_val_gap > self.config.max_train_val_gap and r2_gap > 0.3)
            )

            mlflow.log_metrics(
                {
                    "train_val_gap": train_val_gap,
                    "val_test_gap": val_test_gap,
                    "r2_gap": r2_gap,
                    "is_overfit": 1 if is_overfit else 0,
                }
            )

            # Print results
            print(f"\n📊 Results:")
            print(
                f"  Train: MAE={train_mae:.6f}, RMSE={train_rmse:.6f}, R²={train_r2:.4f}"
            )
            print(f"  Val:   MAE={val_mae:.6f}, RMSE={val_rmse:.6f}, R²={val_r2:.4f}")
            print(
                f"  Test:  MAE={test_mae:.6f}, RMSE={test_rmse:.6f}, R²={test_r2:.4f}"
            )
            print(f"  CV:    MAE={cv_mean_mae:.6f} ± {cv_std_mae:.6f}")
            print(f"\n  MAE Gap: {train_val_gap:.2%}, R² Gap: {r2_gap:.4f}")
            print(f"  ⚠️ Overfitting: {'YES' if is_overfit else 'NO'}")

            # Save model
            model_path = None
            if self.config.save_all_iterations or not is_overfit:
                model_filename = f"{model_name}_iter{iteration}.pkl"
                model_path = os.path.join(self.config.output_dir, model_filename)
                joblib.dump(model, model_path)

                try:
                    mlflow.log_artifact(model_path)
                    print(f"\n💾 Model saved to MLflow: {model_path}")
                except Exception as artifact_err:
                    print(
                        f"\n⚠️ Warning: Failed to upload artifact to MLflow: {artifact_err}"
                    )
                    print(f"   Model is still available locally at: {model_path}")

                print(f"✅ Local model saved: {model_path}")

            training_time = time.time() - start_time
            mlflow.log_metric("training_time", training_time)

            # Create result object
            result = IterationResult(
                iteration=iteration,
                model_name=model_name,
                hyperparameters=params,
                train_mae=train_mae,
                train_rmse=train_rmse,
                train_r2=train_r2,
                val_mae=val_mae,
                val_rmse=val_rmse,
                val_r2=val_r2,
                test_mae=test_mae,
                test_rmse=test_rmse,
                test_r2=test_r2,
                cv_mean_mae=cv_mean_mae,
                cv_std_mae=cv_std_mae,
                cv_scores=cv_scores,
                train_val_gap=train_val_gap,
                val_test_gap=val_test_gap,
                is_overfit=is_overfit,
                training_time=training_time,
                mlflow_run_id=run.info.run_id,
                model_path=model_path,
            )

            return result, model

    def generate_model_configs(self) -> List[Dict[str, Any]]:
        """
        Generate different model configurations for iteration.

        Returns:
            List of model configurations
        """
        configs = []

        # XGBoost variants with increasing regularization
        for i, (alpha, lam, depth, lr) in enumerate(
            [
                (0.01, 0.1, 4, 0.1),  # Light regularization
                (0.1, 1.0, 3, 0.05),  # Medium regularization
                (0.5, 3.0, 2, 0.01),  # Heavy regularization
                (0.2, 1.5, 3, 0.05),  # Balanced
                (0.05, 0.5, 5, 0.08),  # Deeper, lighter reg
            ]
        ):
            configs.append(
                {
                    "name": f"xgboost_v{i+1}",
                    "class": xgb.XGBRegressor,
                    "params": {
                        "n_estimators": 100,
                        "max_depth": depth,
                        "learning_rate": lr,
                        "reg_alpha": alpha,
                        "reg_lambda": lam,
                        "subsample": 0.8,
                        "colsample_bytree": 0.8,
                        "random_state": 42,
                    },
                }
            )

        # Random Forest variants
        for i, (n_est, depth, min_samples) in enumerate(
            [
                (100, 5, 10),  # Conservative
                (150, 8, 5),  # Balanced
                (100, 10, 3),  # More flexible
            ]
        ):
            configs.append(
                {
                    "name": f"random_forest_v{i+1}",
                    "class": RandomForestRegressor,
                    "params": {
                        "n_estimators": n_est,
                        "max_depth": depth,
                        "min_samples_leaf": min_samples,
                        "min_samples_split": min_samples * 2,
                        "max_features": "sqrt",
                        "n_jobs": -1,
                        "random_state": 42,
                    },
                }
            )

        # Linear models (baseline)
        configs.extend(
            [
                {
                    "name": "ridge",
                    "class": Ridge,
                    "params": {"alpha": 1.0, "random_state": 42},
                },
                {
                    "name": "lasso",
                    "class": Lasso,
                    "params": {"alpha": 0.1, "random_state": 42, "max_iter": 2000},
                },
            ]
        )

        return configs

    def run_optuna_optimization(self) -> Dict[str, Any]:
        """
        Run Bayesian Optimization using Optuna.
        """
        print("\n" + "=" * 80)
        print("🧬 OPTUNA BAYESIAN OPTIMIZATION")
        print("=" * 80)

        # Load data
        train_df, val_df, test_df = self.load_data()
        X_train, y_train = self.prepare_features(train_df)
        X_val, y_val = self.prepare_features(val_df)
        X_test, y_test = self.prepare_features(test_df)

        def objective(trial):
            # Model Selection
            classifier_name = trial.suggest_categorical(
                "regressor", ["CatBoost", "XGBoost", "RandomForest", "Ridge"]
            )

            model = None
            params = {}

            if classifier_name == "CatBoost":
                params = {
                    "iterations": trial.suggest_int("cat_iterations", 100, 500),
                    "depth": trial.suggest_int("cat_depth", 4, 10),
                    "learning_rate": trial.suggest_float(
                        "cat_learning_rate", 0.01, 0.3, log=True
                    ),
                    "l2_leaf_reg": trial.suggest_float("cat_l2_leaf_reg", 1.0, 10.0),
                    "bootstrap_type": trial.suggest_categorical(
                        "cat_bootstrap", ["Bernoulli", "MVS"]
                    ),
                    "random_state": 42,
                    "logging_level": "Silent",
                    "thread_count": 2,
                }
                if params["bootstrap_type"] == "Bernoulli":
                    params["subsample"] = trial.suggest_float("cat_subsample", 0.1, 1.0)
                model = CatBoostRegressor(**params)

            elif classifier_name == "XGBoost":
                params = {
                    "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                    "max_depth": trial.suggest_int("max_depth", 2, 10),
                    "learning_rate": trial.suggest_float(
                        "learning_rate", 0.01, 0.3, log=True
                    ),
                    "subsample": trial.suggest_float("subsample", 0.5, 1.0),
                    "colsample_bytree": trial.suggest_float(
                        "colsample_bytree", 0.5, 1.0
                    ),
                    "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
                    "reg_lambda": trial.suggest_float(
                        "reg_lambda", 1e-3, 10.0, log=True
                    ),
                    "random_state": 42,
                }
                model = xgb.XGBRegressor(**params)
                if hasattr(model, "early_stopping_rounds"):
                    model.early_stopping_rounds = 20

            elif classifier_name == "RandomForest":
                params = {
                    "n_estimators": trial.suggest_int("rf_n_estimators", 50, 200),
                    "max_depth": trial.suggest_int("rf_max_depth", 3, 20),
                    "min_samples_split": trial.suggest_int(
                        "rf_min_samples_split", 2, 20
                    ),
                    "min_samples_leaf": trial.suggest_int("rf_min_samples_leaf", 1, 10),
                    "random_state": 42,
                    "n_jobs": -1,
                }
                model = RandomForestRegressor(**params)

            elif classifier_name == "Ridge":
                params = {
                    "alpha": trial.suggest_float("ridge_alpha", 0.01, 10.0, log=True),
                    "random_state": 42,
                }
                model = Ridge(**params)

            elif classifier_name == "Lasso":
                params = {
                    "alpha": trial.suggest_float("lasso_alpha", 0.001, 10.0, log=True),
                    "random_state": 42,
                }
                model = Lasso(**params)

            # CV Evaluation
            tscv = TimeSeriesSplit(n_splits=3)
            scores = []

            for train_idx, val_idx in tscv.split(X_train):
                X_t, X_v = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_t, y_v = y_train.iloc[train_idx], y_train.iloc[val_idx]

                if classifier_name == "XGBoost":
                    model.fit(X_t, y_t, eval_set=[(X_v, y_v)], verbose=False)
                else:
                    model.fit(X_t, y_t)

                preds = model.predict(X_v)
                scores.append(mean_absolute_error(y_v, preds))

            return np.mean(scores)

        # Run Optimization
        study = optuna.create_study(direction="minimize")
        study.optimize(
            objective,
            n_trials=self.config.optuna_n_trials,
            timeout=self.config.optuna_timeout,
        )

        print(f"\n🏆 Best trial:")
        print(f"  Value (MAE): {study.best_value:.5f}")
        print(f"  Params: ")
        for key, value in study.best_trial.params.items():
            print(f"    {key}: {value}")

        # Train final best model
        print("\n🏋️ Training final best model...")
        best_params = study.best_trial.params
        model_type = best_params.pop("regressor")

        final_model = None
        # Reconstruct params cleaning prefix if needed (simplified here)
        # Note: Optuna params are flat, we need to map back to specific model construction
        # For simplicity, we re-instantiate based on the best trial's chosen model type

        if model_type == "CatBoost":
            p = {
                k.replace("cat_", ""): v
                for k, v in best_params.items()
                if k.startswith("cat_")
            }
            final_model = CatBoostRegressor(
                **p, random_state=42, logging_level="Silent", thread_count=2
            )
        elif model_type == "XGBoost":
            # Extract XGB params
            p = {
                k: v
                for k, v in best_params.items()
                if not k.startswith("rf_")
                and not k.startswith("ridge_")
                and not k.startswith("lasso_")
            }
            final_model = xgb.XGBRegressor(**p, random_state=42)
        elif model_type == "RandomForest":
            p = {
                k.replace("rf_", ""): v
                for k, v in best_params.items()
                if k.startswith("rf_")
            }
            final_model = RandomForestRegressor(**p, random_state=42, n_jobs=-1)
        elif model_type == "Ridge":
            p = {"alpha": best_params["ridge_alpha"], "random_state": 42}
            final_model = Ridge(**p)
        elif model_type == "Lasso":
            p = {"alpha": best_params["lasso_alpha"], "random_state": 42}
            final_model = Lasso(**p)

        # Final Training
        final_model.fit(X_train, y_train)

        # Evaluate
        y_val_pred = final_model.predict(X_val)
        val_mae = mean_absolute_error(y_val, y_val_pred)

        print(f"✅ Final Validation MAE: {val_mae:.5f}")

        # Save Best Model
        model_path = os.path.join(self.config.output_dir, "best_optuna_model.pkl")
        joblib.dump(final_model, model_path)
        print(f"💾 Model saved to {model_path}")

        return {
            "best_value": study.best_value,
            "best_params": study.best_trial.params,
            "model_path": model_path,
        }

    def run_iterative_training(self) -> Dict[str, Any]:
        """
        Run the complete iterative training process.

        Returns:
            Dictionary with best model and all results
        """
        print("\n" + "=" * 80)
        print("🎯 ITERATIVE TRAINING WITH OVERFITTING PREVENTION")
        print("=" * 80)

        # Load and split data
        train_df, val_df, test_df = self.load_data()

        # Generate model configurations
        model_configs = self.generate_model_configs()
        print(f"\n📋 Generated {len(model_configs)} model configurations")

        # Limit iterations
        model_configs = model_configs[: self.config.n_iterations]

        # Train each configuration
        best_val_mae = float("inf")
        best_iteration = None
        iterations_without_improvement = 0

        for i, config in enumerate(model_configs, 1):
            result, model = self.train_single_iteration(
                iteration=i,
                train_df=train_df,
                val_df=val_df,
                test_df=test_df,
                model_config=config,
            )

            self.results.append(result)

            # Check if this is the best non-overfit model
            if not result.is_overfit and result.val_mae < best_val_mae:
                best_val_mae = result.val_mae
                best_iteration = i
                self.best_result = result
                self.best_model = model
                iterations_without_improvement = 0
                print(f"\n🏆 New best model! (Iteration {i})")
            else:
                iterations_without_improvement += 1

            # Early stopping check
            if iterations_without_improvement >= self.config.early_stopping_patience:
                print(
                    f"\n⏹️  Early stopping: No improvement for {self.config.early_stopping_patience} iterations"
                )
                break

        # Generate summary
        summary = self._generate_summary()

        # Save best model and Register in MLflow
        if self.best_model is not None and self.best_result is not None:
            best_model_path = os.path.join(self.config.output_dir, "best_model.pkl")
            joblib.dump(self.best_model, best_model_path)
            print(f"\n🏆 Best model saved locally: {best_model_path}")

            # Register Model in MLflow Registry
            try:
                model_name = "AlphaPulse_BTC_Model"
                run_id = self.best_result.mlflow_run_id
                model_uri = f"runs:/{run_id}/model"

                print(f"📦 Attempting to register model '{model_name}' in Registry...")
                result = mlflow.register_model(model_uri, model_name)
                print(f"✅ Model registered as version {result.version}")
            except Exception as reg_err:
                print(f"\n⚠️ Warning: Model registration in MLflow failed: {reg_err}")
                print(
                    "   The training process will finish successfully. Use the local best_model.pkl."
                )

            # Save summary
            summary_path = os.path.join(self.config.output_dir, "training_summary.json")
            try:
                with open(summary_path, "w") as f:
                    # Convert dataclasses to dict for JSON serialization
                    summary_dict = {
                        **summary,
                        "best_result": (
                            asdict(self.best_result) if self.best_result else None
                        ),
                        "all_results": [asdict(r) for r in self.results],
                    }
                    json.dump(summary_dict, f, indent=2, default=str)
                print(f"📄 Summary saved: {summary_path}")
            except Exception as summary_err:
                print(
                    f"⚠️ Warning: Could not save training_summary.json: {summary_err}"
                )

        return summary

    def _generate_summary(self) -> Dict[str, Any]:
        """
        Generate training summary.

        Returns:
            Summary dictionary
        """
        print("\n" + "=" * 80)
        print("📊 TRAINING SUMMARY")
        print("=" * 80)

        summary = {
            "total_iterations": len(self.results),
            "best_iteration": self.best_result.iteration if self.best_result else None,
            "overfit_count": sum(1 for r in self.results if r.is_overfit),
            "config": asdict(self.config),
        }

        if self.best_result:
            print(
                f"\n🏆 Best Model: {self.best_result.model_name} (Iteration {self.best_result.iteration})"
            )
            print(f"  Validation MAE: {self.best_result.val_mae:.6f}")
            print(f"  Test MAE: {self.best_result.test_mae:.6f}")
            print(
                f"  CV MAE: {self.best_result.cv_mean_mae:.6f} ± {self.best_result.cv_std_mae:.6f}"
            )
            print(f"  Train-Val Gap: {self.best_result.train_val_gap:.2%}")
            print(f"  Val-Test Gap: {self.best_result.val_test_gap:.2%}")

            summary["best_model"] = {
                "name": self.best_result.model_name,
                "val_mae": self.best_result.val_mae,
                "test_mae": self.best_result.test_mae,
                "val_r2": self.best_result.val_r2,
                "test_r2": self.best_result.test_r2,
                "hyperparameters": self.best_result.hyperparameters,
            }

        print(f"\n📈 Statistics:")
        print(f"  Total models trained: {len(self.results)}")
        print(
            f"  Overfit models: {summary['overfit_count']} ({summary['overfit_count']/len(self.results)*100:.1f}%)"
        )

        # Best models ranking
        non_overfit = [r for r in self.results if not r.is_overfit]
        if non_overfit:
            sorted_results = sorted(non_overfit, key=lambda x: x.val_mae)
            print(f"\n🏅 Top 3 Models (by validation MAE):")
            for i, result in enumerate(sorted_results[:3], 1):
                print(
                    f"  {i}. {result.model_name} (Iter {result.iteration}): MAE={result.val_mae:.6f}"
                )

        print("\n" + "=" * 80)

        return summary


def main():
    """Main entry point for iterative training."""
    # Configuration
    config = TrainingConfig(
        n_iterations=10,
        cv_splits=5,
        early_stopping_patience=3,
        mlflow_uri=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        output_dir=os.getenv("MODEL_OUTPUT_DIR", "/app/models/saved"),
    )

    # Create trainer
    trainer = IterativeTrainer(config)

    # Run training
    summary = trainer.run_iterative_training()

    print("\n✅ Iterative training complete!")
    return summary


if __name__ == "__main__":
    main()
