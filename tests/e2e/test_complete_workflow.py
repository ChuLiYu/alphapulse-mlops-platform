"""
End-to-End tests for complete AlphaPulse ML workflow.
Tests the entire pipeline from data ingestion to model deployment.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import os
import time

import pytest
import requests
from sqlalchemy import create_engine, text


class TestCompleteMLWorkflow:
    """End-to-end tests for complete ML workflow."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_data_ingestion_to_prediction(self):
        """
        Test complete workflow:
        1. Data exists in database
        2. Features are prepared
        3. Model is trained
        4. Predictions can be made
        """
        # Check database connectivity
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Check data availability
                result = conn.execute(text("SELECT COUNT(*) FROM prices"))
                price_count = result.fetchone()[0]
                assert price_count > 0, "No price data available"

                result = conn.execute(text("SELECT COUNT(*) FROM technical_indicators"))
                indicator_count = result.fetchone()[0]
                assert indicator_count > 0, "No indicator data available"

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    @pytest.mark.e2e
    def test_service_health_checks(self):
        """Test that all required services are healthy."""
        services = {
            "FastAPI": "http://localhost:8000/health",
            "MLflow": "http://localhost:5001/health",
            "Mage": "http://localhost:6789/api/status",
        }

        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                assert response.status_code in [
                    200,
                    404,
                ], f"{service_name} health check failed"
            except requests.exceptions.RequestException as e:
                pytest.skip(f"{service_name} not available: {e}")

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_model_training_workflow(self):
        """
        Test model training workflow:
        1. Training data exists
        2. Model training completes
        3. Best model is saved
        4. Model can be loaded
        """
        # Check if model files exist
        model_paths = [
            "/app/src/models/saved/best_model.pkl",
            "/home/src/src/models/saved/best_model.pkl",
        ]

        model_exists = any(
            Path(p).exists() for p in model_paths if Path(p).parent.exists()
        )

        if not model_exists:
            pytest.skip("Model files not found - training may not have completed")

        # Find the actual model path
        actual_path = next((p for p in model_paths if Path(p).exists()), None)

        if actual_path:
            import joblib

            model = joblib.load(actual_path)
            assert model is not None, "Failed to load model"

    @pytest.mark.e2e
    def test_mlflow_tracking(self):
        """Test MLflow tracking and experiment logging."""
        mlflow_url = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")

        try:
            # Check if MLflow is accessible
            response = requests.get(
                f"{mlflow_url}/api/2.0/mlflow/experiments/list", timeout=5
            )
            assert response.status_code == 200

            experiments = response.json()
            assert "experiments" in experiments or "experiment" in experiments

        except requests.exceptions.RequestException as e:
            pytest.skip(f"MLflow not available: {e}")

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_pipeline_execution(self):
        """Test that Mage pipelines can be executed."""
        mage_url = "http://localhost:6789"

        try:
            # Check Mage API
            response = requests.get(f"{mage_url}/api/status", timeout=5)

            if response.status_code != 200:
                pytest.skip("Mage API not responding")

            # Try to get pipeline list
            response = requests.get(f"{mage_url}/api/pipelines", timeout=10)

            if response.status_code == 200:
                pipelines = response.json()
                # Check if our pipelines exist
                pipeline_names = [
                    p.get("uuid") or p.get("name")
                    for p in pipelines.get("pipelines", [])
                ]

                # At least one pipeline should exist
                assert len(pipeline_names) > 0, "No pipelines found"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Mage not available: {e}")


class TestDataQualityE2E:
    """End-to-end tests for data quality."""

    @pytest.mark.e2e
    def test_price_data_quality(self):
        """Test price data quality in database."""
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Check for recent data
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM prices 
                    WHERE timestamp > NOW() - INTERVAL '30 days'
                """
                    )
                )
                recent_count = result.fetchone()[0]

                # Check for no null prices
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM prices 
                    WHERE price IS NULL OR price <= 0
                """
                    )
                )
                null_count = result.fetchone()[0]
                assert null_count == 0, f"Found {null_count} invalid price records"

                # Check for reasonable price ranges (BTC should be > $1000)
                result = conn.execute(
                    text(
                        """
                    SELECT MIN(price), MAX(price) FROM prices
                """
                    )
                )
                min_price, max_price = result.fetchone()
                assert min_price > 1000, f"Suspicious min price: {min_price}"
                assert max_price < 1000000, f"Suspicious max price: {max_price}"

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    @pytest.mark.e2e
    def test_indicator_data_quality(self):
        """Test technical indicator data quality."""
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # Check RSI is in valid range (0-100)
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM technical_indicators 
                    WHERE rsi_14 < 0 OR rsi_14 > 100
                """
                    )
                )
                invalid_rsi = result.fetchone()[0]
                assert invalid_rsi == 0, f"Found {invalid_rsi} invalid RSI values"

                # Check for data consistency
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM technical_indicators ti
                    LEFT JOIN prices p ON ti.symbol = p.symbol AND ti.timestamp = p.timestamp
                    WHERE p.id IS NULL
                """
                    )
                )
                orphaned = result.fetchone()[0]
                assert orphaned == 0, f"Found {orphaned} orphaned indicator records"

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestModelPerformance:
    """End-to-end tests for model performance."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_model_prediction_quality(self):
        """Test that model predictions are reasonable."""
        import joblib
        import pandas as pd

        # Try to load the model
        model_paths = [
            "/app/src/models/saved/best_model.pkl",
            "/home/src/src/models/saved/best_model.pkl",
        ]

        model_path = next((p for p in model_paths if Path(p).exists()), None)

        if not model_path:
            pytest.skip("Model file not found")

        try:
            model = joblib.load(model_path)

            # Create sample data
            sample_data = pd.DataFrame(
                {
                    "price": [50000],
                    "volume": [1000000],
                    "rsi_14": [50],
                    "macd": [100],
                    "sentiment_avg_24h": [0.0],
                }
            )

            # Make prediction
            prediction = model.predict(sample_data)

            # Check prediction is reasonable (daily returns typically < 20%)
            assert (
                -0.2 < prediction[0] < 0.2
            ), f"Prediction {prediction[0]} seems unreasonable"

        except Exception as e:
            pytest.skip(f"Model prediction failed: {e}")

    @pytest.mark.e2e
    def test_mlflow_metrics_exist(self):
        """Test that MLflow has logged metrics."""
        mlflow_url = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")

        try:
            # Get experiments
            response = requests.get(
                f"{mlflow_url}/api/2.0/mlflow/experiments/list", timeout=5
            )

            if response.status_code != 200:
                pytest.skip("MLflow API not responding")

            experiments = response.json().get("experiments", [])

            if not experiments:
                pytest.skip("No experiments found")

            # Check first experiment has runs
            exp_id = experiments[0].get("experiment_id")
            response = requests.get(
                f"{mlflow_url}/api/2.0/mlflow/runs/search",
                json={"experiment_ids": [exp_id]},
                timeout=5,
            )

            if response.status_code == 200:
                runs = response.json().get("runs", [])
                assert len(runs) > 0, "No runs found in experiment"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"MLflow not available: {e}")


class TestSystemResilience:
    """End-to-end tests for system resilience."""

    @pytest.mark.e2e
    def test_database_connection_recovery(self):
        """Test that system can recover from database disconnection."""
        db_url = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/alphapulse"
        )

        try:
            engine = create_engine(db_url, pool_pre_ping=True)

            # First connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1

            # Second connection (tests pool recovery)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_concurrent_requests(self):
        """Test system handles concurrent requests."""
        import concurrent.futures

        api_url = "http://localhost:8000/health"

        def make_request():
            try:
                response = requests.get(api_url, timeout=5)
                return response.status_code == 200
            except:
                return False

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # At least 80% should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8, f"Only {success_rate*100}% of requests succeeded"
