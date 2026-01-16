import mlflow
import mlflow.sklearn
import pandas as pd
from sqlalchemy import create_engine, text
import os
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class InferenceEngine:
    def __init__(self):
        # Use 'postgres' host if in Docker, else 'localhost'
        default_db = "postgresql://postgres:postgres@postgres:5432/alphapulse"
        self.db_url = os.getenv("DATABASE_URL", default_db)
        self.mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
        mlflow.set_tracking_uri(self.mlflow_uri)
        self.engine = create_engine(self.db_url)

    def load_model_by_stage(self, stage: str):
        """Load model from MLflow Registry or fallback to latest pkl"""
        try:
            path_map = {
                "Production": "/app/models/production/best_model.pkl",
                "Staging": "/app/models/saved/best_model.pkl",
            }

            path = path_map.get(stage)
            if os.path.exists(path):
                import joblib

                model = joblib.load(path)
                logger.info(f"Loaded {stage} model from {path}")
                return model

            # EMERGENCY FALLBACK: Load ANY latest pkl in the directory
            import glob

            search_dir = (
                "/app/models/production"
                if stage == "Production"
                else "/app/models/saved"
            )
            available = glob.glob(f"{search_dir}/*.pkl")
            if available:
                latest = max(available, key=os.path.getmtime)
                import joblib

                model = joblib.load(latest)
                logger.info(
                    f"Fallback: Loaded latest available {stage} model from {latest}"
                )
                return model
            return None

            path = path_map.get(stage)
            if os.path.exists(path):
                import joblib

                model = joblib.load(path)
                logger.info(f"Loaded {stage} model from {path}")
                return model
            return None
        except Exception as e:
            logger.error(f"Error loading {stage} model: {e}")
            return None

    def generate_signals(self):
        """Generate dual signals: one from Champion (Prod) and one from Challenger (Shadow)"""
        # Load models
        champion = self.load_model_by_stage("Production")
        challenger = self.load_model_by_stage("Staging")

        if not champion and not challenger:
            logger.warning("No models available for inference.")
            return

        # Load latest features from the FEATURE STORE (Single source of truth)
        # We look for the most recent record where price is available
        query = "SELECT * FROM feature_store WHERE metadata_close > 0 ORDER BY date DESC LIMIT 1"
        df = pd.read_sql(query, self.engine)

        if df.empty:
            logger.warning("No features with valid price available in Feature Store.")
            return

        # Prepare features:
        # 1. Select only columns starting with 'feat_'
        feature_cols = [c for c in df.columns if c.startswith("feat_")]
        X = df[feature_cols].copy()

        # 2. Force conversion to numeric (critical for XGBoost)
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        # 3. Fill any last-minute NaNs
        X = X.fillna(0)

        results = []
        current_price = (
            float(df["metadata_close"].iloc[0])
            if "metadata_close" in df.columns
            else 0.0
        )

        # 1. Champion Inference (The real deal)
        if champion:
            pred = champion.predict(X)[0]
            self._save_signal(
                pred, "Champion_Prod", is_shadow=False, price=current_price
            )
            results.append("Champion_Active")

        # 2. Challenger Inference (Shadow testing)
        if challenger:
            pred = challenger.predict(X)[0]
            self._save_signal(
                pred, "Challenger_Staging", is_shadow=True, price=current_price
            )
            results.append("Challenger_Shadow")

        return results

    def _save_signal(self, prediction, model_ver, is_shadow, price):
        """Helper to persist signals to DB"""
        confidence = min(max(float(abs(prediction) * 10), 0.0), 1.0)
        signal_type = "HOLD"
        if prediction > 0.005:
            signal_type = "BUY"
        elif prediction < -0.005:
            signal_type = "SELL"

        with self.engine.connect() as conn:
            insert_query = text(
                """
                INSERT INTO trading_signals (symbol, signal_type, confidence, price_at_signal, timestamp, is_shadow, model_version)
                VALUES (:symbol, :signal_type, :confidence, :price, :ts, :shadow, :ver)
            """
            )
            conn.execute(
                insert_query,
                {
                    "symbol": "BTC",
                    "signal_type": signal_type,
                    "confidence": Decimal(str(round(confidence, 4))),
                    "price": price,
                    "ts": datetime.now(),
                    "shadow": is_shadow,
                    "ver": model_ver,
                },
            )
            conn.commit()
        logger.info(f"📡 Saved {model_ver} signal: {signal_type} (Shadow={is_shadow})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = InferenceEngine()
    engine.generate_signals()
