"""
Docker services integration tests.

Tests that all Docker services are running and accessible.
This replaces the shell script approach with proper pytest tests.
"""

import sys
import os
import time
from decimal import Decimal

# Add src to sys.path to allow local imports during testing
sys.path.append(os.path.join(os.path.dirname(__file__), "../../src"))

import psycopg2
import pytest
import requests
from sqlalchemy import create_engine, text


@pytest.mark.integration
class TestDockerServices:
    """Test Docker services availability and connectivity."""

    @pytest.fixture(scope="class", autouse=True)
    def wait_for_services(self):
        """Wait for services to be ready before running tests."""
        print("\n⏳ Waiting for Docker services to be ready...")
        time.sleep(5)  # Give services time to start
        yield

    def test_postgresql_connection(self):
        """Test PostgreSQL database is accessible."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="alphapulse",
                user="postgres",
                password="postgres",
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "PostgreSQL query failed"

            cursor.close()
            conn.close()
            print("✅ PostgreSQL connection successful")

        except Exception as e:
            pytest.fail(f"❌ PostgreSQL connection failed: {e}")

    def test_postgresql_decimal_support(self):
        """Test PostgreSQL supports DECIMAL types correctly."""
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="alphapulse",
                user="postgres",
                password="postgres",
            )
            cursor = conn.cursor()

            # Test Decimal precision
            cursor.execute("SELECT NUMERIC '123.456789'")
            result = cursor.fetchone()
            assert result[0] == Decimal("123.456789"), "Decimal precision lost"

            cursor.close()
            conn.close()
            print("✅ PostgreSQL Decimal support verified")

        except Exception as e:
            pytest.fail(f"❌ PostgreSQL Decimal test failed: {e}")

    def test_airflow_ui_accessible(self):
        """Test Airflow UI is accessible."""
        try:
            response = requests.get("http://localhost:8080/health", timeout=10)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ Airflow UI accessible")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ Airflow UI not accessible: {e}")

    def test_mlflow_api_accessible(self):
        """Test MLflow tracking server is accessible."""
        try:
            response = requests.get("http://localhost:5002/", timeout=10)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ MLflow API accessible")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ MLflow API not accessible: {e}")

    def test_trainer_health(self):
        """Test Trainer service health."""
        try:
            response = requests.get("http://localhost:8181/health", timeout=10)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ Trainer service healthy")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ Trainer service not accessible: {e}")

    def test_ollama_accessible(self):
        """Test Ollama service is accessible."""
        try:
            response = requests.get("http://localhost:11434/", timeout=10)
            # Ollama root usually returns 200 "Ollama is running"
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ Ollama service accessible")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ Ollama service not accessible: {e}")

    def test_minio_health(self):
        """Test MinIO (S3-compatible storage) is healthy."""
        try:
            response = requests.get(
                "http://localhost:9000/minio/health/live", timeout=10
            )
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ MinIO health check passed")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ MinIO health check failed: {e}")

    def test_fastapi_health_endpoint(self):
        """Test FastAPI health endpoint."""
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"

            data = response.json()
            assert data["status"] == "healthy", "API not healthy"
            # Optional: check detailed health if it exists
            # assert "database" in data or data["service"] == "AlphaPulse API", "Invalid health response"
            print(f"✅ FastAPI health: {data}")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ FastAPI health endpoint failed: {e}")

    def test_fastapi_swagger_docs(self):
        """Test FastAPI Swagger documentation is accessible."""
        try:
            response = requests.get("http://localhost:8000/api/docs", timeout=10)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            print("✅ FastAPI Swagger docs accessible")

        except requests.exceptions.RequestException as e:
            pytest.fail(f"❌ FastAPI Swagger docs not accessible: {e}")


@pytest.mark.integration
class TestDatabaseSchema:
    """Test database schema and tables exist."""

    def test_database_tables_exist(self):
        """Test that required tables exist in database."""
        try:
            engine = create_engine(
                "postgresql://postgres:postgres@localhost:5432/alphapulse"
            )

            with engine.connect() as conn:
                # Check for key tables
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                tables = [row[0] for row in result]

                # Expected tables from pipelines
                expected_tables = [
                    "market_news",  # RSS news ingestion
                    "btc_prices",  # BTC price pipeline (if run)
                ]

                # Check at least market_news exists (from Phase 1)
                assert "market_news" in tables, "market_news table missing"
                print(f"✅ Database tables exist: {', '.join(tables)}")

        except Exception as e:
            pytest.fail(f"❌ Database schema check failed: {e}")

    def test_market_news_table_structure(self):
        """Test market_news table has correct structure."""
        try:
            engine = create_engine(
                "postgresql://postgres:postgres@localhost:5432/alphapulse"
            )

            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'market_news'
                    ORDER BY ordinal_position
                """))
                columns = {row[0]: row[1] for row in result}

                # Check key columns exist
                assert "id" in columns, "id column missing"
                assert "title" in columns, "title column missing"
                assert "url" in columns, "url column missing"
                assert "source" in columns, "source column missing"

                print(f"✅ market_news table structure: {columns}")

        except Exception as e:
            pytest.fail(f"❌ Table structure check failed: {e}")


@pytest.mark.integration
class TestPipelineImports:
    """Test pipeline modules can be imported."""

    def test_import_alphapulse_core(self):
        """Test AlphaPulse core modules import."""
        try:
            from alphapulse.utils.logging import logger

            print("✅ AlphaPulse core modules import successfully")
        except ImportError as e:
            pytest.fail(f"❌ Cannot import AlphaPulse core: {e}")

    def test_pandas_ta_available(self):
        """Test pandas-ta library is available."""
        try:
            import pandas_ta

            print(f"✅ pandas-ta version: {pandas_ta.__version__}")

        except ImportError:
            pytest.fail("❌ pandas-ta not installed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
