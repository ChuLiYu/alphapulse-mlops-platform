"""
Production Model Predictor for AlphaPulse Trading System.

This module provides a production-ready interface for making predictions
using trained models with proper error handling and logging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


class ModelPredictor:
    """
    Production-ready model predictor with automatic feature engineering.
    """

    def __init__(
        self,
        model_path: str = "/app/src/models/saved/best_model.pkl",
        db_connection_string: str = "postgresql://postgres:postgres@postgres:5432/alphapulse",
    ):
        """
        Initialize the predictor.

        Args:
            model_path: Path to the trained model file
            db_connection_string: Database connection string
        """
        self.model_path = model_path
        self.db_connection_string = db_connection_string
        self.model = None
        self.feature_columns = None
        self.model_metadata = None

        self._load_model()

    def _load_model(self):
        """Load the trained model and metadata."""
        try:
            logger.info(f"Loading model from {self.model_path}")
            self.model = joblib.load(self.model_path)

            # Load training summary for metadata
            summary_path = Path(self.model_path).parent / "training_summary.json"
            if summary_path.exists():
                with open(summary_path, "r") as f:
                    self.model_metadata = json.load(f)
                    logger.info(
                        f"Model metadata loaded: {self.model_metadata.get('best_model', {}).get('name')}"
                    )

            logger.info("Model loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise

    def _fetch_latest_features(
        self, ticker: str = "BTC-USD", lookback_days: int = 100
    ) -> pd.DataFrame:
        """
        Fetch latest features from database.

        Args:
            ticker: Asset ticker symbol
            lookback_days: Number of days to look back

        Returns:
            DataFrame with latest features
        """
        engine = create_engine(self.db_connection_string)

        query = text("""
            SELECT *
            FROM model_features
            WHERE ticker = :ticker
            ORDER BY date DESC
            LIMIT :limit
        """)

        with engine.connect() as conn:
            df = pd.read_sql(
                query, conn, params={"ticker": ticker, "limit": lookback_days}
            )

        if len(df) == 0:
            raise ValueError(f"No features found for ticker {ticker}")

        return df.sort_values("date")

    def predict_next_day(self, ticker: str = "BTC-USD") -> Dict:
        """
        Predict next day price change for given ticker.

        Args:
            ticker: Asset ticker symbol

        Returns:
            Dictionary with prediction results
        """
        try:
            # Fetch latest features
            df = self._fetch_latest_features(ticker)
            latest_row = df.iloc[-1:]

            # Get current price
            current_price = latest_row["close"].values[0]
            current_date = latest_row["date"].values[0]

            # Prepare features for prediction
            feature_cols = [
                col for col in df.columns if col not in ["date", "ticker", "close"]
            ]
            X = latest_row[feature_cols]

            # Make prediction
            prediction = self.model.predict(X)[0]

            # Calculate predicted price
            predicted_price = current_price * (1 + prediction)

            result = {
                "ticker": ticker,
                "current_date": str(current_date),
                "current_price": float(current_price),
                "predicted_change": float(prediction),
                "predicted_price": float(predicted_price),
                "predicted_direction": "UP" if prediction > 0 else "DOWN",
                "confidence": self._calculate_confidence(prediction),
                "model_name": (
                    self.model_metadata.get("best_model", {}).get("name", "unknown")
                    if self.model_metadata
                    else "unknown"
                ),
                "timestamp": datetime.now().isoformat(),
            }

            logger.info(f"Prediction made: {result}")
            return result

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise

    def _calculate_confidence(self, prediction: float) -> str:
        """
        Calculate confidence level based on prediction magnitude.

        Args:
            prediction: Predicted price change

        Returns:
            Confidence level (HIGH, MEDIUM, LOW)
        """
        abs_pred = abs(prediction)

        if abs_pred > 0.03:  # >3% change
            return "HIGH"
        elif abs_pred > 0.01:  # >1% change
            return "MEDIUM"
        else:
            return "LOW"

    def predict_batch(self, tickers: List[str]) -> List[Dict]:
        """
        Make predictions for multiple tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            List of prediction results
        """
        results = []
        for ticker in tickers:
            try:
                result = self.predict_next_day(ticker)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to predict {ticker}: {str(e)}")
                results.append(
                    {
                        "ticker": ticker,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        if self.model_metadata is None:
            return {
                "model_loaded": True,
                "model_path": self.model_path,
                "metadata_available": False,
            }

        best_model = self.model_metadata.get("best_model", {})
        best_result = self.model_metadata.get("best_result", {})

        return {
            "model_loaded": True,
            "model_path": self.model_path,
            "model_name": best_model.get("name"),
            "validation_mae": best_model.get("val_mae"),
            "test_mae": best_model.get("test_mae"),
            "test_r2": best_model.get("test_r2"),
            "hyperparameters": best_model.get("hyperparameters"),
            "training_time": best_result.get("training_time"),
            "trained_at": best_result.get("timestamp"),
            "total_iterations": self.model_metadata.get("total_iterations"),
            "overfit_count": self.model_metadata.get("overfit_count"),
        }

    def reload_model(self):
        """Reload the model from disk."""
        logger.info("Reloading model...")
        self._load_model()
        logger.info("Model reloaded successfully")


# Singleton instance for FastAPI
_predictor_instance: Optional[ModelPredictor] = None


def get_predictor() -> ModelPredictor:
    """
    Get or create singleton predictor instance.

    Returns:
        ModelPredictor instance
    """
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ModelPredictor()
    return _predictor_instance
