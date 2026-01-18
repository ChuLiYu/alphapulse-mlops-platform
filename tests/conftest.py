"""
Shared fixtures and configuration for AlphaPulse tests.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

## Airflow 相关 mock 代码

import json
import os
import tempfile
from datetime import datetime, timedelta

import pandas as pd
import pytest
from pydantic import BaseModel, Field

# ============================================================================
# Data Schemas for testing
# ============================================================================


class NewsArticle(BaseModel):
    """Schema for news article validation."""

    title: str = Field(..., min_length=1, max_length=500)
    url: str = Field(..., pattern=r"^https?://")
    source: str = Field(..., min_length=1, max_length=100)
    published_at: datetime
    summary: str | None = None
    content: str | None = None
    sentiment_score: float | None = Field(None, ge=-1.0, le=1.0)
    sentiment_label: str | None = Field(None, pattern=r"^(positive|negative|neutral)$")


class SentimentResult(BaseModel):
    """Schema for sentiment analysis results."""

    sentiment: str = Field(..., pattern=r"^(positive|negative|neutral)$")
    score: float = Field(..., ge=-1.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str | None = None
    model: str | None = None


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_rss_feed():
    """Sample RSS feed data for testing."""
    return [
        {
            "title": "Bitcoin Surges Past $50,000 as Institutional Adoption Grows",
            "url": "https://coindesk.com/bitcoin-surges-past-50000",
            "source": "CoinDesk",
            "published_at": datetime.utcnow() - timedelta(hours=1),
            "summary": "Bitcoin price reaches new highs amid increased institutional investment.",
            "content": "Full article content here...",
            "sentiment_score": 0.8,
            "sentiment_label": "positive",
        },
        {
            "title": "Regulatory Concerns Weigh on Crypto Markets",
            "url": "https://cointelegraph.com/regulatory-concerns",
            "source": "Cointelegraph",
            "published_at": datetime.utcnow() - timedelta(hours=2),
            "summary": "New regulations create uncertainty in cryptocurrency markets.",
            "content": "Full article content here...",
            "sentiment_score": -0.3,
            "sentiment_label": "negative",
        },
    ]


@pytest.fixture
def sample_sentiment_results():
    """Sample sentiment analysis results for testing."""
    return [
        {
            "sentiment": "positive",
            "score": 0.85,
            "confidence": 0.92,
            "reasoning": "Text expresses strong optimism about market growth.",
            "model": "llama3.2:3b",
        },
        {
            "sentiment": "negative",
            "score": -0.65,
            "confidence": 0.78,
            "reasoning": "Text mentions losses and disappointment.",
            "model": "llama3.2:3b",
        },
        {
            "sentiment": "neutral",
            "score": 0.05,
            "confidence": 0.65,
            "reasoning": "Text is factual without emotional tone.",
            "model": "llama3.2:3b",
        },
    ]


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        df = pd.DataFrame(
            {
                "title": ["Test Article 1", "Test Article 2"],
                "url": ["https://example.com/1", "https://example.com/2"],
                "source": ["TestSource", "TestSource"],
                "published_at": [datetime.utcnow(), datetime.utcnow()],
                "sentiment_score": [0.5, -0.3],
            }
        )
        df.to_csv(f.name, index=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_json_file():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        data = {
            "articles": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/test",
                    "source": "TestSource",
                    "published_at": datetime.utcnow().isoformat(),
                }
            ]
        }
        json.dump(data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response for testing."""
    return {
        "sentiment": "positive",
        "score": 0.75,
        "confidence": 0.88,
        "reasoning": "Text shows optimism about cryptocurrency.",
        "raw_output": '{"sentiment": "positive", "score": 0.75, "confidence": 0.88, "reasoning": "Text shows optimism about cryptocurrency."}',
    }


# ============================================================================
# Helper Functions
# ============================================================================


def validate_news_article(article_data: dict) -> bool:
    """Validate news article against schema."""
    try:
        NewsArticle(**article_data)
        return True
    except Exception:
        return False


def validate_sentiment_result(result_data: dict) -> bool:
    """Validate sentiment result against schema."""
    try:
        SentimentResult(**result_data)
        return True
    except Exception:
        return False


def assert_data_freshness(timestamp: datetime, max_age_minutes: int = 5):
    """Assert that data is fresh (within max_age_minutes)."""
    age = datetime.utcnow() - timestamp
    assert (
        age.total_seconds() < max_age_minutes * 60
    ), f"Data is too old: {age.total_seconds() / 60:.1f} minutes"


def assert_latency_under_threshold(start_time: float, max_ms: int = 100):
    """Assert that operation completed within latency threshold."""
    elapsed_ms = (datetime.utcnow().timestamp() - start_time) * 1000
    assert (
        elapsed_ms < max_ms
    ), f"Latency too high: {elapsed_ms:.1f}ms (max: {max_ms}ms)"


# ============================================================================
# Test Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires Docker)"
    )
    config.addinivalue_line("markers", "e2e: End-to-end tests (slow)")
    config.addinivalue_line("markers", "performance: Performance/latency tests")
    config.addinivalue_line("markers", "data: Data quality tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Skip integration tests if DOCKER_SKIP environment variable is set
    if os.getenv("DOCKER_SKIP") == "1":
        skip_integration = pytest.mark.skip(
            reason="Docker tests skipped via DOCKER_SKIP=1"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
