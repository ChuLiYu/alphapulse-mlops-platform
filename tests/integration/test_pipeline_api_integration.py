"""
End-to-end integration tests for data pipeline to API connection.

Tests the complete flow from:
1. Data pipeline processing with Decimal types
2. PostgreSQL storage with DECIMAL columns
3. API endpoints returning Decimal values as strings
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.alphapulse.api.models import Base, Price, TechnicalIndicator
from src.alphapulse.main import app

# Test database URL (SQLite in-memory for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test database engine
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def test_db():
    """Create test database tables."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def test_client(test_db):
    """Create FastAPI test client with test database."""

    # Override get_db dependency to use test database
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides = {}
    from src.alphapulse.api.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_price_data():
    """Create sample price data with Decimal values."""
    return {
        "symbol": "BTC-USD",
        "price": Decimal("45000.12345678"),
        "volume": Decimal("1000.50000000"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_indicator_data():
    """Create sample technical indicator data with Decimal values."""
    return {
        "symbol": "BTC-USD",
        "timestamp": datetime.utcnow().isoformat(),
        "sma_20": Decimal("44500.12345678"),
        "ema_12": Decimal("44600.98765432"),
        "rsi_14": Decimal("65.4321"),
        "macd": Decimal("125.45678901"),
        "macd_signal": Decimal("120.12345678"),
        "macd_histogram": Decimal("5.33333223"),
        "bb_upper": Decimal("45500.11111111"),
        "bb_middle": Decimal("44500.22222222"),
        "bb_lower": Decimal("43500.33333333"),
        "atr_14": Decimal("500.44444444"),
    }


class TestDecimalPrecisionIntegration:
    """Test Decimal precision preservation through the entire pipeline."""

    def test_price_decimal_precision(self, test_client, sample_price_data):
        """Test that Decimal precision is preserved in price API endpoints."""
        # Create price record
        response = test_client.post("/api/v1/prices", json=sample_price_data)
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal values are returned as strings
        assert data["success"] is True
        price_data = data["data"]
        assert price_data["price"] == "45000.12345678"
        assert price_data["volume"] == "1000.50000000"

        # Verify we can retrieve the same data
        symbol = sample_price_data["symbol"]
        response = test_client.get(f"/api/v1/prices/{symbol}/latest")
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal precision is preserved
        assert data["data"]["price"] == "45000.12345678"
        assert data["data"]["volume"] == "1000.50000000"

    def test_indicator_decimal_precision(self, test_client, sample_indicator_data):
        """Test that Decimal precision is preserved in indicator API endpoints."""
        # Create indicator record
        response = test_client.post("/api/v1/indicators", json=sample_indicator_data)
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal values are returned as strings
        assert data["success"] is True
        indicator_data = data["data"]

        # Check various Decimal fields
        assert indicator_data["sma_20"] == "44500.12345678"
        assert indicator_data["ema_12"] == "44600.98765432"
        assert indicator_data["rsi_14"] == "65.4321"
        assert indicator_data["macd"] == "125.45678901"
        assert indicator_data["macd_signal"] == "120.12345678"
        assert indicator_data["macd_histogram"] == "5.33333223"

        # Verify we can retrieve the same data
        symbol = sample_indicator_data["symbol"]
        response = test_client.get(f"/api/v1/indicators/{symbol}/latest")
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal precision is preserved
        assert data["data"]["sma_20"] == "44500.12345678"
        assert data["data"]["rsi_14"] == "65.4321"

    def test_price_list_endpoint_decimal(self, test_client):
        """Test that price list endpoint returns Decimal values as strings."""
        # Create multiple price records
        prices = []
        for i in range(3):
            price_data = {
                "symbol": "BTC-USD",
                "price": Decimal(f"{45000 + i}.{i:08d}"),
                "volume": Decimal(f"{1000 + i}.{i:08d}"),
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            }
            response = test_client.post("/api/v1/prices", json=price_data)
            assert response.status_code == 200
            prices.append(price_data)

        # Get price list
        response = test_client.get("/api/v1/prices?symbol=BTC-USD&limit=10")
        assert response.status_code == 200
        data = response.json()

        # Verify all prices have Decimal values as strings
        assert data["success"] is True
        assert data["count"] >= 3

        for price in data["data"]:
            assert isinstance(price["price"], str)
            assert "." in price["price"]  # Has decimal point
            # Verify it has 8 decimal places (for price values)
            if price["price"] != "0":
                decimal_places = len(price["price"].split(".")[1])
                assert decimal_places == 8

    def test_indicator_list_endpoint_decimal(self, test_client):
        """Test that indicator list endpoint returns Decimal values as strings."""
        # Create multiple indicator records
        indicators = []
        for i in range(3):
            indicator_data = {
                "symbol": "BTC-USD",
                "timestamp": (datetime.utcnow() - timedelta(hours=i)).isoformat(),
                "sma_20": Decimal(f"{44500 + i}.{i:08d}"),
                "rsi_14": Decimal(f"{60 + i}.{i:04d}"),
                "macd": Decimal(f"{100 + i}.{i:08d}"),
            }
            response = test_client.post("/api/v1/indicators", json=indicator_data)
            assert response.status_code == 200
            indicators.append(indicator_data)

        # Get indicator list
        response = test_client.get("/api/v1/indicators?symbol=BTC-USD&limit=10")
        assert response.status_code == 200
        data = response.json()

        # Verify all indicators have Decimal values as strings
        assert data["success"] is True
        assert data["count"] >= 3

        for indicator in data["data"]:
            if indicator.get("sma_20"):
                assert isinstance(indicator["sma_20"], str)
                assert "." in indicator["sma_20"]
            if indicator.get("rsi_14"):
                assert isinstance(indicator["rsi_14"], str)
                assert "." in indicator["rsi_14"]

    def test_price_stats_endpoint_decimal(self, test_client):
        """Test that price statistics endpoint handles Decimal calculations correctly."""
        # Create price records for statistics
        prices = [
            {"price": Decimal("40000.00000000"), "hours_ago": 72},
            {"price": Decimal("41000.00000000"), "hours_ago": 48},
            {"price": Decimal("42000.00000000"), "hours_ago": 24},
            {"price": Decimal("43000.00000000"), "hours_ago": 0},
        ]

        for price_info in prices:
            price_data = {
                "symbol": "BTC-USD",
                "price": price_info["price"],
                "volume": Decimal("1000.00000000"),
                "timestamp": (
                    datetime.utcnow() - timedelta(hours=price_info["hours_ago"])
                ).isoformat(),
            }
            response = test_client.post("/api/v1/prices", json=price_data)
            assert response.status_code == 200

        # Get price statistics
        response = test_client.get("/api/v1/prices/BTC-USD/stats?days=7")
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal calculations
        assert data["symbol"] == "BTC-USD"
        assert data["prices"]["latest"] == "43000.00000000"
        assert data["prices"]["minimum"] == "40000.00000000"
        assert data["prices"]["maximum"] == "43000.00000000"
        assert data["prices"]["average"] == "41500.00000000"
        assert data["changes"]["absolute"] == "3000.00000000"
        assert data["changes"]["percentage"] == "7.50"  # (3000/40000)*100 = 7.5%

    def test_indicator_stats_endpoint_decimal(self, test_client):
        """Test that indicator statistics endpoint handles Decimal calculations correctly."""
        # Create indicator records for statistics
        indicators = [
            {"rsi_14": Decimal("30.0000"), "hours_ago": 72},
            {"rsi_14": Decimal("50.0000"), "hours_ago": 48},
            {"rsi_14": Decimal("70.0000"), "hours_ago": 24},
            {"rsi_14": Decimal("65.0000"), "hours_ago": 0},
        ]

        for indicator_info in indicators:
            indicator_data = {
                "symbol": "BTC-USD",
                "timestamp": (
                    datetime.utcnow() - timedelta(hours=indicator_info["hours_ago"])
                ).isoformat(),
                "rsi_14": indicator_info["rsi_14"],
                "sma_20": Decimal("44500.00000000"),
            }
            response = test_client.post("/api/v1/indicators", json=indicator_data)
            assert response.status_code == 200

        # Get indicator statistics
        response = test_client.get("/api/v1/indicators/BTC-USD/stats?days=7")
        assert response.status_code == 200
        data = response.json()

        # Verify Decimal calculations in statistics
        assert data["symbol"] == "BTC-USD"
        assert data["period_days"] == 7
        assert data["record_count"] >= 4

        # Check RSI statistics
        rsi_stats = data["indicators_summary"]["rsi_14"]
        assert rsi_stats["display_name"] == "Relative Strength Index (14)"
        assert rsi_stats["record_count"] >= 4
        assert rsi_stats["latest"] == "65.0000"
        assert rsi_stats["minimum"] == "30.0000"
        assert rsi_stats["maximum"] == "70.0000"
        assert rsi_stats["average"] == "53.75000000"  # (30+50+70+65)/4 = 53.75

    def test_decimal_validation(self, test_client):
        """Test that Decimal validation rejects invalid values."""
        # Test with float instead of Decimal string
        invalid_price = {
            "symbol": "BTC-USD",
            "price": 45000.12345678,  # Float instead of Decimal string
            "volume": "1000.50000000",
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = test_client.post("/api/v1/prices", json=invalid_price)
        # Should fail validation because price is float, not Decimal string
        assert response.status_code == 422  # Validation error

        # Test with properly formatted Decimal string
        valid_price = {
            "symbol": "BTC-USD",
            "price": "45000.12345678",  # Decimal as string
            "volume": "1000.50000000",
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = test_client.post("/api/v1/prices", json=valid_price)
        assert response.status_code == 200  # Should succeed

    def test_api_documentation_includes_decimal_examples(self, test_client):
        """Test that API documentation includes Decimal examples."""
        # Get OpenAPI schema
        response = test_client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        openapi_schema = response.json()

        # Check that price schema uses string format for Decimal fields
        price_schema = openapi_schema["components"]["schemas"]["PriceCreate"]
        assert price_schema["properties"]["price"]["type"] == "string"
        assert price_schema["properties"]["volume"]["type"] == "string"

        # Check that indicator schema uses string format for Decimal fields
        indicator_schema = openapi_schema["components"]["schemas"]["IndicatorCreate"]
        assert indicator_schema["properties"]["sma_20"]["type"] == "string"
        assert indicator_schema["properties"]["rsi_14"]["type"] == "string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
