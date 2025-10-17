# AlphaPulse Testing Strategy

> **Companion to**: [`ADR-004: Testing Framework Strategy`](../architecture/adr-004-testing-framework-strategy.md)

**Version**: 1.0  
**Last Updated**: 2026-01-10  
**Owner**: MLOps Team

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Testing Layers](#testing-layers)
3. [Quick Start Guide](#quick-start-guide)
4. [Test Development Workflow](#test-development-workflow)
5. [MLOps-Specific Testing](#mlops-specific-testing)
6. [CI/CD Integration](#cicd-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### Why Testing Matters for AlphaPulse

AlphaPulse is an **Automated Quantitative Trading** platform where:

- **Data Integrity is Critical**: Inaccurate features lead to flawed trading signals and financial risk.
- **Model Reliability is Paramount**: Silent model failures or performance degradation can cause significant capital drawdown.
- **System Stability is Essential**: Continuous 24/7 operation requires robust pipelines and error-handling mechanisms.

### Testing Philosophy

```
Traditional Software: Code → Test → Deploy
ML Systems:           Code + Data + Model → Test → Deploy
```

We test **3 layers**:

1. **Code** (traditional unit/integration tests)
2. **Data** (schema validation, freshness checks)
3. **Model** (accuracy thresholds, inference latency)

---

## 🏗️ Testing Layers

### Layer 1: Unit Tests (50% of tests)

**What**: Individual functions/classes  
**When**: Every commit  
**Speed**: < 30 seconds total

```python
# Example: tests/unit/test_sentiment_classifier.py
import pytest
from alphapulse.ml.sentiment import classify_sentiment

def test_positive_sentiment():
    result = classify_sentiment("Bitcoin to the moon! 🚀")
    assert result['sentiment'] == 'positive'
    assert 0 < result['score'] <= 1.0

def test_negative_sentiment():
    result = classify_sentiment("BTC crashed 20% today")
    assert result['sentiment'] == 'negative'
    assert -1.0 <= result['score'] < 0
```

### Layer 2: Data Quality Tests (30% of tests) ⭐

**What**: Input/output data validation  
**When**: Every pipeline run  
**Speed**: < 2 minutes

```python
# Example: tests/data/test_rss_schema.py
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime

class NewsArticle(BaseModel):
    title: str
    url: HttpUrl
    published_date: datetime
    source: str

    @validator('title')
    def title_not_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v

def test_rss_feed_schema(sample_rss_data):
    """Validate every article conforms to schema"""
    for article in sample_rss_data:
        NewsArticle(**article)  # Will raise error if invalid
```

### Layer 3: Integration Tests (15% of tests)

**What**: Multiple services working together  
**When**: Every PR merge  
**Speed**: < 5 minutes

```python
# Example: tests/integration/test_airflow_to_postgres.py
import pytest
import pandas as pd
from sqlalchemy import create_engine

@pytest.mark.integration
def test_news_pipeline_saves_to_postgres():
    """Test complete flow: RSS → Airflow → Postgres"""
    # 1. Trigger Airflow DAG (mock or real)
    # 2. Wait for completion
    # 3. Query Postgres
    engine = create_engine(os.getenv('POSTGRES_URL'))
    df = pd.read_sql("SELECT * FROM news_articles", engine)

    assert len(df) > 0, "No data in Postgres"
    assert 'title' in df.columns
    assert df['title'].notna().all()
```

### Layer 4: E2E Tests (5% of tests)

**What**: Complete user workflows  
**When**: Nightly builds  
**Speed**: < 15 minutes

```python
# Example: tests/e2e/test_news_to_signal.py
@pytest.mark.e2e
@pytest.mark.slow
def test_complete_trading_workflow():
    """RSS → Sentiment → Trading Signal"""
    # 1. Ingest news
    # 2. Run sentiment analysis
    # 3. Generate trading signal
    # 4. Verify signal quality
    pass
```

---

## 🚀 Quick Start Guide

### Prerequisites

```bash
# Install dependencies
pip install pytest pytest-cov pytest-mock pytest-benchmark

# Or use project requirements
cd airflow
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
make test-all

# Run specific layers
make test-unit           # Fast, run often
make test-integration    # Slower, needs Docker
make test-data          # Data quality checks

# Run with coverage
make test-coverage

# Run specific file
pytest tests/unit/test_sentiment_classifier.py -v

# Run tests matching pattern
pytest -k "sentiment" -v
```

### Test Markers

```python
@pytest.mark.unit           # Fast unit test
@pytest.mark.integration    # Needs Docker/external services
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Takes > 1 minute
@pytest.mark.performance   # Latency/throughput test
@pytest.mark.model         # Model-related test
```

---

## 🔧 Test Development Workflow

### 1. Write Test First (TDD)

```python
# Step 1: Write failing test
def test_sentiment_classifier_handles_emojis():
    result = classify_sentiment("Bitcoin 🚀🚀🚀")
    assert result['sentiment'] == 'positive'

# Step 2: Run test (should fail)
# pytest tests/unit/test_sentiment.py::test_sentiment_classifier_handles_emojis

# Step 3: Write implementation
def classify_sentiment(text):
    # ... implementation ...
    pass

# Step 4: Run test (should pass)
```

### 2. Use Fixtures for Reusable Data

```python
# conftest.py
import pytest

@pytest.fixture
def sample_rss_feed():
    """Shared RSS feed data"""
    return [
        {
            'title': 'Bitcoin hits $50k',
            'url': 'https://example.com/btc-50k',
            'published_date': '2026-01-10T12:00:00Z',
            'source': 'CoinDesk'
        },
        # ... more articles ...
    ]

@pytest.fixture
def postgres_connection():
    """Database connection for tests"""
    engine = create_engine('postgresql://test:test@localhost:5432/test_db')
    yield engine
    engine.dispose()

# Use in tests
def test_save_to_postgres(sample_rss_feed, postgres_connection):
    save_articles(sample_rss_feed, postgres_connection)
    # ... assertions ...
```

### 3. Mock External Services

```python
import pytest
from unittest.mock import patch, MagicMock

@patch('requests.get')
def test_rss_fetch_handles_timeout(mock_get):
    """Test RSS fetcher handles network timeout"""
    mock_get.side_effect = requests.Timeout("Connection timeout")

    with pytest.raises(RSSFetchError):
        fetch_rss_feed("https://example.com/rss")
```

---

## 🎓 MLOps-Specific Testing

### 1. Data Drift Detection

```python
# tests/data/test_drift_detection.py
from evidently.metrics import DataDriftMetric
import pandas as pd

def test_no_significant_data_drift(baseline_data, current_data):
    """Detect if new data has drifted from baseline"""
    drift_report = DataDriftMetric().calculate(baseline_data, current_data)

    assert drift_report.drift_detected is False, \
        f"Data drift detected in {drift_report.drifted_features}"
```

### 2. Model Performance Thresholds

```python
# tests/model/test_model_performance.py
@pytest.mark.model
def test_sentiment_accuracy_above_baseline():
    """Model accuracy must not drop below 75%"""
    accuracy = evaluate_model(test_dataset)

    assert accuracy >= 0.75, \
        f"Model accuracy {accuracy:.2%} below 75% threshold"

@pytest.mark.model
def test_model_inference_latency():
    """Inference must complete in < 100ms (Production API SLA)"""
    import time

    start = time.time()
    predict_sentiment("Sample text")
    latency_ms = (time.time() - start) * 1000

    assert latency_ms < 100, \
        f"Inference latency {latency_ms:.1f}ms exceeds 100ms SLA"
```

### 3. Data Freshness Checks

```python
# tests/data/test_data_freshness.py
from datetime import datetime, timedelta

def test_news_data_is_fresh():
    """News data must be within 5 minutes"""
    latest_news = get_latest_news_from_db()
    age = datetime.utcnow() - latest_news['timestamp']

    assert age < timedelta(minutes=5), \
        f"News data is {age.total_seconds()/60:.1f} minutes old"
```

### 4. Schema Validation

```python
# tests/data/test_schemas.py
from pydantic import ValidationError

def test_sentiment_output_schema():
    """Ensure sentiment analysis output has correct schema"""
    result = {
        'sentiment': 'positive',
        'score': 0.85,
        'confidence': 0.92
    }

    # Should not raise error
    SentimentResult(**result)

    # Invalid data should raise error
    with pytest.raises(ValidationError):
        SentimentResult(sentiment='invalid', score=2.0)
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r airflow/requirements.txt

      - name: Run unit tests
        run: make test-unit

      - name: Check coverage
        run: |
          pytest tests/unit --cov=src/alphapulse --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: make test-integration
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: Run Unit Tests
        entry: pytest tests/unit -x
        language: system
        pass_filenames: false
        always_run: true
```

---

## 💡 Best Practices

### 1. Test Naming Convention

```python
# ✅ Good: Clear, descriptive
def test_sentiment_classifier_returns_positive_for_bullish_text():
    pass

def test_rss_parser_handles_missing_published_date():
    pass

# ❌ Bad: Vague
def test_sentiment():
    pass

def test_parser():
    pass
```

### 2. One Assertion Per Test (when possible)

```python
# ✅ Good: Focused, easy to debug
def test_sentiment_is_positive():
    result = classify_sentiment("Bitcoin moon 🚀")
    assert result['sentiment'] == 'positive'

def test_sentiment_score_in_range():
    result = classify_sentiment("Bitcoin moon 🚀")
    assert -1.0 <= result['score'] <= 1.0

# ⚠️ Acceptable: Related assertions
def test_sentiment_output_structure():
    result = classify_sentiment("Bitcoin moon 🚀")
    assert 'sentiment' in result
    assert 'score' in result
    assert 'confidence' in result
```

### 3. Use Parameterization for Multiple Cases

```python
@pytest.mark.parametrize("text,expected_sentiment", [
    ("Bitcoin to the moon! 🚀", "positive"),
    ("BTC crashed 20%", "negative"),
    ("Bitcoin stable at $40k", "neutral"),
    ("Best crypto investment", "positive"),
])
def test_sentiment_classification(text, expected_sentiment):
    result = classify_sentiment(text)
    assert result['sentiment'] == expected_sentiment
```

### 4. Test Edge Cases

```python
def test_sentiment_handles_empty_string():
    with pytest.raises(ValueError):
        classify_sentiment("")

def test_sentiment_handles_very_long_text():
    long_text = "Bitcoin " * 10000
    result = classify_sentiment(long_text)
    assert result is not None

def test_sentiment_handles_unicode():
    result = classify_sentiment("比特幣 🚀 Bitcoin 📈")
    assert result is not None
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: Tests pass locally but fail in CI

```bash
# Possible causes:
# 1. Missing environment variables
# 2. Different Python version
# 3. Missing services (Postgres, MinIO)

# Solution: Use Docker for consistent environment
docker-compose -f infra/docker-compose.yml up -d
pytest tests/integration/
```

#### Issue: Tests are too slow

```bash
# Run only fast tests
pytest -m "not slow"

# Run in parallel
pytest -n auto  # Requires pytest-xdist

# Profile slow tests
pytest --durations=10
```

#### Issue: Flaky tests (intermittent failures)

```python
# Add retry decorator
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_external_api():
    # Test that sometimes fails due to network
    pass

# Or add timeout
@pytest.mark.timeout(10)
def test_long_running_operation():
    pass
```

### Getting Help

- Check test logs: `pytest -v --tb=short`
- Run single test: `pytest tests/unit/test_file.py::test_function -vv`
- Enable debug: `pytest --pdb` (drops into debugger on failure)
- See coverage gaps: `pytest --cov=src --cov-report=html`

---

## 📊 Test Metrics Dashboard

| Metric                    | Current | Target | Status         |
| ------------------------- | ------- | ------ | -------------- |
| Unit Test Coverage        | 45%     | 80%    | 🟡 In Progress |
| Integration Test Coverage | 20%     | 60%    | 🟡 In Progress |
| Test Execution Time       | 2m 15s  | < 5m   | ✅ Good        |
| Flaky Test Rate           | 0%      | < 1%   | ✅ Good        |
| Tests Added (this week)   | 12      | 20     | 🟡 In Progress |

---

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Testing Best Practices (Google)](https://testing.googleblog.com/)
- [ML Testing Guide (Chip Huyen)](https://huyenchip.com/ml-interviews-book/)
- [Great Expectations Tutorial](https://docs.greatexpectations.io/docs/tutorials/)

---

## 🔗 Related Documentation

- [`ADR-004: Testing Framework Strategy`](../architecture/adr-004-testing-framework-strategy.md)
- [`Makefile`](../../Makefile) - Test commands
- [`.github/workflows/`](../../.github/workflows/) - CI/CD pipelines (to be created)

---

**Next Steps**: See [Phase 1 Implementation](./phase1-implementation.md) for detailed task list.
