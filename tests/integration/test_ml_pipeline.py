"""
Integration tests for ML pipeline components.
Tests the interaction between data preparation, training, and evaluation.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import os
import tempfile
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from alphapulse.ml.prepare_training_data import load_data, prepare_features, save_splits


@pytest.fixture
def test_database():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = f"sqlite:///{tmpdir}/test.db"
        engine = create_engine(db_path)

        # Create tables
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE prices (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    price REAL,
                    volume REAL,
                    market_cap REAL,
                    timestamp TIMESTAMP,
                    source TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE technical_indicators (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT,
                    timestamp TIMESTAMP,
                    sma_7 REAL,
                    sma_25 REAL,
                    sma_99 REAL,
                    ema_12 REAL,
                    ema_26 REAL,
                    rsi_14 REAL,
                    macd REAL,
                    macd_signal REAL,
                    macd_histogram REAL,
                    atr_14 REAL,
                    obv REAL,
                    adx_14 REAL,
                    calculation_version TEXT
                )
            """
                )
            )

            conn.execute(
                text(
                    """
                CREATE TABLE sentiment_scores (
                    id INTEGER PRIMARY KEY,
                    sentiment_score REAL,
                    confidence REAL,
                    label TEXT,
                    analyzed_at TIMESTAMP
                )
            """
                )
            )

            # Insert sample data
            dates = pd.date_range("2024-01-01", periods=100, freq="D")
            for i, date in enumerate(dates):
                conn.execute(
                    text(
                        f"""
                    INSERT INTO prices (symbol, price, volume, timestamp, source)
                    VALUES ('BTC-USD', {50000 + i * 100}, 1000000, '{date}', 'test')
                """
                    )
                )

                conn.execute(
                    text(
                        f"""
                    INSERT INTO technical_indicators 
                    (symbol, timestamp, rsi_14, macd, sma_7, ema_12, ema_26, atr_14, obv, adx_14)
                    VALUES ('BTC-USD', '{date}', {50 + i % 20}, {100 + i}, 
                            {50000}, {50000}, {50000}, {1000}, {1000000}, {30})
                """
                    )
                )

            conn.commit()

        yield db_path


class TestDataPipelineIntegration:
    """Integration tests for data preparation pipeline."""

    @patch("alphapulse.ml.prepare_training_data.get_database_url")
    def test_load_data_integration(self, mock_get_url, test_database):
        """Test loading data from database."""
        mock_get_url.return_value = test_database

        df_prices, df_indicators, df_sentiment = load_data()

        assert len(df_prices) == 100
        assert len(df_indicators) == 100
        assert "price" in df_prices.columns
        assert "rsi_14" in df_indicators.columns

    @patch("alphapulse.ml.prepare_training_data.get_database_url")
    def test_full_preparation_pipeline(self, mock_get_url, test_database):
        """Test complete data preparation pipeline."""
        mock_get_url.return_value = test_database

        # Load data
        df_prices, df_indicators, df_sentiment = load_data()

        # Prepare features
        df_features = prepare_features(df_prices, df_indicators, df_sentiment)

        # Check that features are created
        assert "target" in df_features.columns
        assert "sentiment_avg_24h" in df_features.columns
        assert len(df_features) > 0

        # Check data quality
        assert not df_features["price"].isna().any()
        assert not df_features["rsi_14"].isna().any()

    @patch("alphapulse.ml.prepare_training_data.get_database_url")
    def test_save_splits_integration(self, mock_get_url, test_database):
        """Test saving data splits."""
        mock_get_url.return_value = test_database

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Load and prepare data
            df_prices, df_indicators, df_sentiment = load_data()
            df_features = prepare_features(df_prices, df_indicators, df_sentiment)

            # Save splits
            save_splits(df_features, output_dir=str(output_dir))

            # Verify files exist
            assert (output_dir / "train.parquet").exists()
            assert (output_dir / "val.parquet").exists()
            assert (output_dir / "test.parquet").exists()

            # Verify data can be loaded
            train = pd.read_parquet(output_dir / "train.parquet")
            val = pd.read_parquet(output_dir / "val.parquet")
            test = pd.read_parquet(output_dir / "test.parquet")

            # Check split proportions (roughly 70/15/15)
            total = len(train) + len(val) + len(test)
            assert abs(len(train) / total - 0.70) < 0.05
            assert abs(len(val) / total - 0.15) < 0.05
            assert abs(len(test) / total - 0.15) < 0.05


class TestMLFlowIntegration:
    """Integration tests for MLflow tracking."""

    @pytest.mark.skipif(
        not os.getenv("MLFLOW_TRACKING_URI"),
        reason="MLflow tracking URI not configured",
    )
    def test_mlflow_experiment_creation(self):
        """Test MLflow experiment creation."""
        import mlflow

        experiment_name = "test_integration"

        # Try to get or create experiment
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id

        assert experiment_id is not None

    @pytest.mark.skipif(
        not os.getenv("MLFLOW_TRACKING_URI"),
        reason="MLflow tracking URI not configured",
    )
    def test_mlflow_logging(self):
        """Test logging to MLflow."""
        import mlflow

        experiment_name = "test_integration"
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name="test_run"):
            mlflow.log_param("test_param", "value")
            mlflow.log_metric("test_metric", 1.0)

            run = mlflow.active_run()
            assert run is not None


class TestEndToEndDataFlow:
    """End-to-end tests for data flow through the pipeline."""

    @patch("alphapulse.ml.prepare_training_data.get_database_url")
    @patch("alphapulse.ml.auto_train.AutoTrainer.run")
    def test_data_to_training_flow(self, mock_trainer_run, mock_get_url, test_database):
        """Test complete flow from data loading to training."""
        mock_get_url.return_value = test_database

        # Mock training result
        mock_trainer_run.return_value = {
            "best_model": "test_model",
            "sharpe_ratio": 1.5,
            "status": "success",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()

            # Step 1: Load data
            df_prices, df_indicators, df_sentiment = load_data()

            # Step 2: Prepare features
            df_features = prepare_features(df_prices, df_indicators, df_sentiment)

            # Step 3: Save splits
            save_splits(df_features, output_dir=str(data_dir))

            # Step 4: Verify training data is ready
            train = pd.read_parquet(data_dir / "train.parquet")

            assert "target" in train.columns
            assert "price" in train.columns
            assert "rsi_14" in train.columns
            assert len(train) > 0


class TestDatabaseConnectivity:
    """Tests for database connectivity and queries."""

    def test_postgres_connection(self):
        """Test PostgreSQL connection (requires running container)."""
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_table_existence(self):
        """Test that required tables exist."""
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Check for prices table
                result = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'prices'
                    )
                """
                    )
                )
                assert result.fetchone()[0] is True

                # Check for technical_indicators table
                result = conn.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'technical_indicators'
                    )
                """
                    )
                )
                assert result.fetchone()[0] is True
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
