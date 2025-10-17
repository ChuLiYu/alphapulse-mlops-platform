# Phase 1: Testing Framework Implementation

**Timeline**: Week 2 (5 days)  
**Goal**: Establish foundational testing infrastructure with 60% unit test coverage  
**Status**: 🟡 Not Started

---

## 📋 Overview

This document outlines the **concrete tasks** for implementing Phase 1 of the AlphaPulse testing strategy. By the end of this phase, we should have:

- ✅ Proper pytest configuration
- ✅ Shared test fixtures in [`conftest.py`](../../tests/conftest.py)
- ✅ Unit tests for core modules
- ✅ Test coverage tracking (target: 60%)
- ✅ Updated [`Makefile`](../../Makefile) with test commands

---

## 🎯 Phase 1 Tasks

### Day 1: Infrastructure Setup

#### Task 1.1: Create pytest Configuration

**File**: [`pytest.ini`](../../pytest.ini)

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests

# Markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires Docker services)
    e2e: End-to-end tests (slow, full workflow)
    slow: Tests that take > 1 minute
    performance: Performance/latency tests
    model: Model-related tests
    data: Data quality tests

# Coverage
addopts =
    -v
    --strict-markers
    --tb=short
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-config=.coveragerc

# Logging
log_cli = false
log_cli_level = INFO
```

**Acceptance Criteria**:

- [ ] `pytest.ini` created
- [ ] Markers properly defined
- [ ] Coverage reporting configured

---

#### Task 1.2: Create Coverage Configuration

**File**: [`.coveragerc`](../../.coveragerc)

```ini
[run]
source = src/alphapulse
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*
    */setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    @abstractmethod

precision = 2
show_missing = True

[html]
directory = htmlcov
```

**Acceptance Criteria**:

- [ ] `.coveragerc` created
- [ ] Source paths configured
- [ ] Exclusions defined

---

#### Task 1.3: Create Shared Fixtures

**File**: [`tests/conftest.py`](../../tests/conftest.py)

```python
"""
Shared pytest fixtures for AlphaPulse tests.
"""
import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from unittest.mock import MagicMock


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        'POSTGRES_URL': os.getenv('TEST_POSTGRES_URL', 'postgresql://test:test@localhost:5432/test_db'),
        'MINIO_ENDPOINT': os.getenv('TEST_MINIO_ENDPOINT', 'localhost:9000'),
        'OLLAMA_ENDPOINT': os.getenv('TEST_OLLAMA_ENDPOINT', 'http://localhost:11434'),
    }


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def sample_rss_feed():
    """Sample RSS feed data for testing"""
    return [
        {
            'title': 'Bitcoin Hits $50,000 Milestone',
            'url': 'https://example.com/btc-50k',
            'published_date': '2026-01-10T12:00:00Z',
            'source': 'CoinDesk',
            'description': 'Bitcoin reaches new all-time high...'
        },
        {
            'title': 'Ethereum Network Upgrade Successful',
            'url': 'https://example.com/eth-upgrade',
            'published_date': '2026-01-10T11:30:00Z',
            'source': 'Cointelegraph',
            'description': 'Ethereum completes major network upgrade...'
        }
    ]


@pytest.fixture
def sample_sentiment_results():
    """Sample sentiment analysis results"""
    return [
        {
            'text': 'Bitcoin to the moon! 🚀',
            'sentiment': 'positive',
            'score': 0.85,
            'confidence': 0.92
        },
        {
            'text': 'BTC crashed 20% today',
            'sentiment': 'negative',
            'score': -0.75,
            'confidence': 0.88
        },
        {
            'text': 'Bitcoin stable at $40k',
            'sentiment': 'neutral',
            'score': 0.05,
            'confidence': 0.65
        }
    ]


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def postgres_engine(test_config):
    """PostgreSQL database engine for tests"""
    engine = create_engine(test_config['POSTGRES_URL'])
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def clean_database(postgres_engine):
    """Clean database before each test"""
    # Drop and recreate test tables
    with postgres_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS news_articles CASCADE")
        conn.execute("DROP TABLE IF EXISTS sentiment_scores CASCADE")
    yield
    # Cleanup after test
    with postgres_engine.connect() as conn:
        conn.execute("DROP TABLE IF EXISTS news_articles CASCADE")
        conn.execute("DROP TABLE IF EXISTS sentiment_scores CASCADE")


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response"""
    return {
        'sentiment': 'positive',
        'score': 0.85,
        'confidence': 0.92,
        'reasoning': 'Text contains strong positive indicators'
    }


@pytest.fixture
def mock_rss_fetcher(monkeypatch, sample_rss_feed):
    """Mock RSS feed fetcher to avoid network calls"""
    def mock_fetch(*args, **kwargs):
        return sample_rss_feed

    monkeypatch.setattr('feedparser.parse', lambda url: MagicMock(entries=sample_rss_feed))
    return mock_fetch


# ============================================================================
# Performance Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer for performance tests"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

    return Timer()
```

**Acceptance Criteria**:

- [ ] `tests/conftest.py` created
- [ ] Common fixtures defined
- [ ] Fixtures documented

---

### Day 2: Refactor Existing Tests

#### Task 2.1: Refactor Sentiment Tests

**File**: [`tests/unit/test_sentiment_classifier.py`](../../tests/unit/test_sentiment_classifier.py)

Convert [`test_sentiment.py`](../../tests/unit/test_sentiment.py) from manual script to proper pytest tests.

**Before** (current):

```python
# Manual print-based verification
def test_ollama_connection():
    print("🔍 Testing Ollama connection...")
    # ... lots of print statements
```

**After** (pytest format):

```python
import pytest
from alphapulse.ml.sentiment import classify_sentiment

@pytest.mark.unit
def test_positive_sentiment():
    """Test positive sentiment classification"""
    result = classify_sentiment("Bitcoin to the moon! 🚀")

    assert result['sentiment'] == 'positive'
    assert 0 < result['score'] <= 1.0
    assert 0 <= result['confidence'] <= 1.0

@pytest.mark.unit
@pytest.mark.parametrize("text,expected", [
    ("Bitcoin moon 🚀", "positive"),
    ("BTC crashed 20%", "negative"),
    ("Bitcoin stable $40k", "neutral"),
])
def test_sentiment_classification_cases(text, expected):
    """Test various sentiment cases"""
    result = classify_sentiment(text)
    assert result['sentiment'] == expected
```

**Acceptance Criteria**:

- [ ] Remove print statements
- [ ] Add proper assertions
- [ ] Use pytest markers
- [ ] Parameterize test cases

---

#### Task 2.2: Refactor RSS Tests

**File**: [`tests/unit/test_rss_parser.py`](../../tests/unit/test_rss_parser.py)

Convert [`test_rss_basic.py`](../../tests/integration/test_rss_basic.py) to unit tests.

```python
import pytest
from unittest.mock import Mock
from alphapulse.data.collectors.rss_parser import parse_rss_feed

@pytest.mark.unit
def test_parse_rss_feed_valid_data(sample_rss_feed):
    """Test RSS parser with valid feed"""
    result = parse_rss_feed(sample_rss_feed)

    assert len(result) > 0
    assert all('title' in article for article in result)
    assert all('url' in article for article in result)

@pytest.mark.unit
def test_parse_rss_feed_handles_missing_fields():
    """Test parser handles missing optional fields"""
    incomplete_feed = [{'title': 'Test', 'url': 'http://test.com'}]
    result = parse_rss_feed(incomplete_feed)

    assert result is not None
    assert result[0]['description'] == ''  # Default value
```

**Acceptance Criteria**:

- [ ] Separate unit from integration tests
- [ ] Mock external dependencies
- [ ] Test edge cases

---

### Day 3: Create Unit Tests for Core Modules

#### Task 3.1: Sentiment Classifier Unit Tests

**Coverage Target**: 80%

```python
# tests/unit/test_sentiment_classifier.py

@pytest.mark.unit
class TestSentimentClassifier:
    """Test suite for sentiment classification"""

    def test_classify_positive_sentiment(self):
        """Test positive sentiment classification"""
        pass

    def test_classify_negative_sentiment(self):
        """Test negative sentiment classification"""
        pass

    def test_classify_neutral_sentiment(self):
        """Test neutral sentiment classification"""
        pass

    def test_handles_empty_string(self):
        """Test error handling for empty input"""
        pass

    def test_handles_very_long_text(self):
        """Test handling of very long text"""
        pass

    def test_handles_unicode_characters(self):
        """Test Unicode/emoji handling"""
        pass
```

**Acceptance Criteria**:

- [ ] 10+ test cases
- [ ] Edge cases covered
- [ ] 80% code coverage

---

#### Task 3.2: RSS Parser Unit Tests

**Coverage Target**: 80%

```python
# tests/unit/test_rss_parser.py

@pytest.mark.unit
class TestRSSParser:
    """Test suite for RSS feed parsing"""

    def test_parse_valid_feed(self, sample_rss_feed):
        """Test parsing valid RSS feed"""
        pass

    def test_parse_empty_feed(self):
        """Test handling of empty feed"""
        pass

    def test_parse_malformed_feed(self):
        """Test error handling for malformed feed"""
        pass

    def test_extract_title(self, sample_rss_feed):
        """Test title extraction"""
        pass

    def test_extract_url(self, sample_rss_feed):
        """Test URL extraction"""
        pass

    def test_parse_date_formats(self):
        """Test various date format parsing"""
        pass
```

**Acceptance Criteria**:

- [ ] 8+ test cases
- [ ] Edge cases covered
- [ ] 80% code coverage

---

#### Task 3.3: Data Transformation Unit Tests

**Coverage Target**: 70%

```python
# tests/unit/test_data_transformers.py

@pytest.mark.unit
class TestDataTransformers:
    """Test suite for data transformation utilities"""

    def test_clean_text(self):
        """Test text cleaning function"""
        pass

    def test_normalize_date(self):
        """Test date normalization"""
        pass

    def test_deduplicate_articles(self):
        """Test article deduplication logic"""
        pass
```

**Acceptance Criteria**:

- [ ] 6+ test cases
- [ ] 70% code coverage

---

### Day 4: Data Quality Tests

#### Task 4.1: Create Pydantic Schemas

**File**: [`src/alphapulse/data/schemas.py`](../../src/alphapulse/data/schemas.py)

```python
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from typing import Literal

class NewsArticle(BaseModel):
    """Schema for news article"""
    title: str
    url: HttpUrl
    published_date: datetime
    source: str
    description: str = ""

    @validator('title')
    def title_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v.strip()

class SentimentResult(BaseModel):
    """Schema for sentiment analysis result"""
    sentiment: Literal['positive', 'negative', 'neutral']
    score: float
    confidence: float

    @validator('score')
    def score_in_range(cls, v):
        if not -1.0 <= v <= 1.0:
            raise ValueError('Score must be between -1.0 and 1.0')
        return v

    @validator('confidence')
    def confidence_in_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
```

**Acceptance Criteria**:

- [ ] NewsArticle schema defined
- [ ] SentimentResult schema defined
- [ ] Validators implemented

---

#### Task 4.2: Schema Validation Tests

**File**: [`tests/data/test_schemas.py`](../../tests/data/test_schemas.py)

```python
import pytest
from pydantic import ValidationError
from alphapulse.data.schemas import NewsArticle, SentimentResult

@pytest.mark.data
class TestNewsArticleSchema:
    """Test NewsArticle schema validation"""

    def test_valid_article(self, sample_rss_feed):
        """Test valid article passes validation"""
        article = NewsArticle(**sample_rss_feed[0])
        assert article.title is not None

    def test_invalid_url_raises_error(self):
        """Test invalid URL raises ValidationError"""
        with pytest.raises(ValidationError):
            NewsArticle(
                title="Test",
                url="not-a-valid-url",
                published_date="2026-01-10T12:00:00Z",
                source="Test"
            )

    def test_empty_title_raises_error(self):
        """Test empty title raises ValidationError"""
        with pytest.raises(ValidationError):
            NewsArticle(
                title="",
                url="https://example.com",
                published_date="2026-01-10T12:00:00Z",
                source="Test"
            )

@pytest.mark.data
class TestSentimentResultSchema:
    """Test SentimentResult schema validation"""

    def test_valid_sentiment(self):
        """Test valid sentiment result"""
        result = SentimentResult(
            sentiment='positive',
            score=0.85,
            confidence=0.92
        )
        assert result.sentiment == 'positive'

    def test_invalid_sentiment_raises_error(self):
        """Test invalid sentiment value raises error"""
        with pytest.raises(ValidationError):
            SentimentResult(
                sentiment='very_positive',  # Not in Literal
                score=0.85,
                confidence=0.92
            )

    def test_score_out_of_range_raises_error(self):
        """Test score out of range raises error"""
        with pytest.raises(ValidationError):
            SentimentResult(
                sentiment='positive',
                score=2.0,  # > 1.0
                confidence=0.92
            )
```

**Acceptance Criteria**:

- [ ] 8+ schema validation tests
- [ ] Both valid and invalid cases tested

---

### Day 5: Integration & Documentation

#### Task 5.1: Update Makefile

**File**: [`Makefile`](../../Makefile)

Add test commands:

```makefile
# Testing commands
test-unit:
	@echo "Running unit tests..."
	@pytest tests/unit/ -v -m unit

test-integration:
	@echo "Running integration tests (requires Docker)..."
	@pytest tests/integration/ -v -m integration

test-data:
	@echo "Running data quality tests..."
	@pytest tests/data/ -v -m data

test-all:
	@echo "Running all tests..."
	@pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage report..."
	@pytest tests/unit/ --cov=src/alphapulse --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	@echo "Running fast tests only (no slow/integration)..."
	@pytest tests/ -v -m "not slow and not integration"

test-watch:
	@echo "Running tests in watch mode..."
	@pytest-watch tests/unit/ -- -v
```

**Acceptance Criteria**:

- [ ] Test commands added to Makefile
- [ ] Commands documented in `make help`
- [ ] Verified working

---

#### Task 5.2: Create Test Documentation

**File**: [`tests/README.md`](../../tests/README.md)

````markdown
# AlphaPulse Test Suite

## Quick Start

```bash
# Run all tests
make test-all

# Run specific test types
make test-unit        # Fast unit tests
make test-integration # Slower integration tests
make test-data        # Data quality tests

# Generate coverage report
make test-coverage
```
````

## Test Structure

- `unit/` - Unit tests (50% of tests)
- `data/` - Data quality tests (30% of tests)
- `integration/` - Integration tests (15% of tests)
- `e2e/` - End-to-end tests (5% of tests)
- `fixtures/` - Test data files
- `conftest.py` - Shared fixtures

## Writing Tests

See [Testing Strategy](../docs/testing/TESTING_STRATEGY.md) for guidelines.

```

**Acceptance Criteria**:
- [ ] README.md created
- [ ] Quick start guide included
- [ ] Test structure documented

---

## 📊 Success Criteria

### Phase 1 Complete When:

- [ ] All Day 1-5 tasks completed
- [ ] Test coverage ≥ 60% for core modules
- [ ] All tests passing in local environment
- [ ] Makefile test commands working
- [ ] Documentation complete

### Metrics:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Unit Test Coverage | ≥ 60% | `make test-coverage` |
| Unit Tests | ≥ 30 tests | `pytest --collect-only` |
| Test Execution Time | < 30 seconds | CI logs |
| Passing Tests | 100% | `make test-all` |

---

## 🚀 Next Steps (Phase 2)

After Phase 1 completion:
1. Implement Great Expectations for advanced data validation
2. Add integration tests for Mage → Postgres flow
3. Set up GitHub Actions CI/CD
4. Add pre-commit hooks

---

## 📚 References

- [Testing Strategy](./TESTING_STRATEGY.md)
- [ADR-004: Testing Framework](../architecture/adr-004-testing-framework-strategy.md)
- [pytest Documentation](https://docs.pytest.org/)
```
