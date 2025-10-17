# AlphaPulse Testing Framework

**Status**: 📋 Planned  
**Owner**: MLOps Team  
**Last Updated**: 2026-01-10

---

## 📚 Documentation Structure

This directory contains the complete testing strategy and implementation plan for AlphaPulse:

1. **[ADR-004: Testing Framework Strategy](../architecture/adr-004-testing-framework-strategy.md)**  
   → High-level architectural decisions and rationale

2. **[Testing Strategy](./TESTING_STRATEGY.md)**  
   → Comprehensive testing guide with examples and best practices

3. **[Phase 1 Implementation Plan](./phase1-implementation.md)**  
   → Concrete tasks and acceptance criteria for Week 2

---

## 🎯 Quick Summary

### Testing Pyramid (Distribution)

```
           E2E Tests (5%)
         /              \
    Integration (15%)
   /                     \
  Data Quality (30%)   Unit Tests (50%)
```

### Why Testing Matters for Quantitative Trading Platform

- **Latency-sensitive decisions** require fast, reliable inference
- **Silent model failures** lead to bad trading signals
- **Data corruption** causes incorrect market sentiment analysis

### Key Testing Layers

| Layer            | Focus                | Speed | Frequency          |
| ---------------- | -------------------- | ----- | ------------------ |
| **Unit**         | Individual functions | < 30s | Every commit       |
| **Data Quality** | Schema validation    | < 2m  | Every pipeline run |
| **Integration**  | Service interactions | < 5m  | Every PR           |
| **E2E**          | Complete workflows   | < 15m | Nightly            |

---

## 🚀 Getting Started

### Installation

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock pytest-benchmark pydantic

# Or use project requirements
pip install -r airflow/requirements.txt
```

### Running Tests

```bash
# Run all tests
make test-all

# Run specific test types
make test-unit          # Fast unit tests only
make test-integration   # Integration tests (needs Docker)
make test-data          # Data quality tests
make test-coverage      # With coverage report
make test-fast          # Skip slow/integration tests
```

### Required Makefile Updates

**Add to [`Makefile`](../../Makefile) in "Testing" section:**

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

test-performance:
	@echo "Running performance tests (latency/throughput)..."
	@pytest tests/performance/ -v -m performance
```

**Update `.PHONY` line:**

```makefile
.PHONY: help up down logs status health clean backup restore init test build rebuild test-unit test-integration test-data test-all test-coverage test-fast test-performance
```

**Update `help` target to include:**

```makefile
@echo "Testing:"
@echo "  make test-unit         Run unit tests (fast)"
@echo "  make test-integration  Run integration tests (needs Docker)"
@echo "  make test-data         Run data quality tests"
@echo "  make test-all          Run all tests"
@echo "  make test-coverage     Run tests with coverage report"
@echo "  make test-fast         Run fast tests only"
@echo "  make test-performance  Run performance/latency tests"
```

---

## 📁 Test Directory Structure

```
tests/
├── unit/                           # Unit tests (50%)
│   ├── test_sentiment_classifier.py
│   ├── test_rss_parser.py
│   ├── test_data_transformers.py
│   └── test_api_schemas.py
│
├── data/                           # Data quality tests (30%)
│   ├── test_rss_schema.py
│   ├── test_sentiment_output.py
│   ├── test_data_freshness.py
│   └── expectations/
│
├── integration/                    # Integration tests (15%)
│   ├── test_airflow_to_postgres.py
│   ├── test_mlflow_tracking.py
│   ├── test_api_inference.py
│   └── test_hybrid_cloud_sync.py
│
├── e2e/                            # End-to-end tests (5%)
│   ├── test_news_to_signal.py
│   └── test_model_lifecycle.py
│
├── performance/                    # Performance tests
│   ├── test_inference_latency.py
│   └── test_pipeline_throughput.py
│
├── fixtures/                       # Test data
│   ├── sample_rss_feed.xml
│   ├── sample_reddit_posts.json
│   └── sample_sentiment_results.csv
│
├── conftest.py                     # Shared fixtures
└── README.md                       # This file
```

---

## 🎓 Writing Your First Test

### Example: Unit Test

```python
# tests/unit/test_sentiment_classifier.py
import pytest
from alphapulse.ml.sentiment import classify_sentiment

@pytest.mark.unit
def test_positive_sentiment():
    """Test positive sentiment classification"""
    result = classify_sentiment("Bitcoin to the moon! 🚀")

    assert result['sentiment'] == 'positive'
    assert 0 < result['score'] <= 1.0
    assert 0 <= result['confidence'] <= 1.0
```

### Example: Data Quality Test

```python
# tests/data/test_rss_schema.py
from pydantic import ValidationError
from alphapulse.data.schemas import NewsArticle

@pytest.mark.data
def test_valid_article_passes_validation(sample_rss_feed):
    """Test valid article passes schema validation"""
    article = NewsArticle(**sample_rss_feed[0])
    assert article.title is not None
```

### Example: Integration Test

```python
# tests/integration/test_airflow_to_postgres.py
import pytest

@pytest.mark.integration
def test_news_pipeline_saves_to_postgres(postgres_engine):
    """Test Airflow DAG saves data to Postgres"""
    # 1. Trigger DAG
    # 2. Verify data in Postgres
    pass
```

---

## 🔧 Required Configuration Files

### 1. pytest.ini

Create [`pytest.ini`](../../pytest.ini) in project root:

```ini
[pytest]
python_files = test_*.py
python_classes = Test*
python_functions = test_*

testpaths = tests

markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (requires Docker)
    e2e: End-to-end tests (slow)
    slow: Tests that take > 1 minute
    performance: Performance/latency tests
    model: Model-related tests
    data: Data quality tests

addopts =
    -v
    --strict-markers
    --tb=short

log_cli = false
log_cli_level = INFO
```

### 2. .coveragerc

Create [`.coveragerc`](../../.coveragerc) in project root:

```ini
[run]
source = src/alphapulse
omit =
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

precision = 2
show_missing = True
```

---

## 📊 Phase 1 Milestones

### Week 2 Goals

- [ ] **Day 1**: Infrastructure setup (pytest.ini, .coveragerc, conftest.py)
- [ ] **Day 2**: Refactor existing tests to pytest format
- [ ] **Day 3**: Create unit tests for core modules (sentiment, RSS parser)
- [ ] **Day 4**: Implement data quality tests with Pydantic schemas
- [ ] **Day 5**: Update Makefile and documentation

### Success Criteria

| Metric              | Target | Status         |
| ------------------- | ------ | -------------- |
| Unit Test Coverage  | ≥ 60%  | 🔴 Not Started |
| Number of Tests     | ≥ 30   | 🔴 Not Started |
| Test Execution Time | < 30s  | 🔴 Not Started |
| Passing Tests       | 100%   | 🔴 Not Started |

---

## 🚨 Critical Tests for Quantitative Trading Platform

### 1. Latency SLA

```python
@pytest.mark.performance
def test_inference_latency():
    """Inference should be fast for trading decisions"""
    start = time.time()
    predict_sentiment("text")
    latency_ms = (time.time() - start) * 1000
    assert latency_ms < 500  # Acceptable for hourly trading
```

### 2. Data Freshness

```python
def test_news_freshness():
    """News data should be reasonably fresh"""
    age = datetime.utcnow() - latest_news['timestamp']
    assert age.total_seconds() < 3600  # Within 1 hour for hourly pipeline
```

### 3. Model Accuracy Threshold

```python
@pytest.mark.model
def test_accuracy_above_baseline():
    """Model accuracy must not drop below 75%"""
    accuracy = evaluate_model(test_data)
    assert accuracy >= 0.75
```

### 4. No Silent Failures

```python
def test_error_on_invalid_input():
    """Empty input should raise error, not return None"""
    with pytest.raises(ValueError):
        classify_sentiment("")
```

---

## 🔗 Related Documentation

- **Architecture**: [`ADR-004: Testing Framework Strategy`](../architecture/adr-004-testing-framework-strategy.md)
- **Implementation**: [`Phase 1 Implementation Plan`](./phase1-implementation.md)
- **Best Practices**: [`Testing Strategy Guide`](./TESTING_STRATEGY.md)
- **Main README**: [`Project README`](../../README.md)

---

## 💡 Pro Tips

1. **Run fast tests frequently**: `make test-fast` after every code change
2. **Check coverage**: `make test-coverage` before committing
3. **Use markers**: `pytest -m unit` to run specific test types
4. **Debug failures**: `pytest --pdb` to drop into debugger
5. **Profile slow tests**: `pytest --durations=10`

---

## 🆘 Getting Help

**Test failing locally?**

```bash
# Run with more verbose output
pytest tests/unit/test_file.py::test_function -vv

# Show full traceback
pytest --tb=long

# Drop into debugger on failure
pytest --pdb
```

**Need to skip integration tests?**

```bash
# Skip tests that need Docker
pytest -m "not integration"
```

**Coverage too low?**

```bash
# See which lines are not covered
pytest --cov=src/alphapulse --cov-report=term-missing

# Generate HTML report
make test-coverage
# Open htmlcov/index.html in browser
```

---

## 📈 Roadmap

### Phase 1: Foundation (Week 2) - Current

- Establish testing infrastructure
- Refactor existing tests
- Achieve 60% unit test coverage

### Phase 2: Data Quality (Week 3)

- Implement Great Expectations
- Advanced schema validation
- Data drift detection

### Phase 3: CI/CD Integration (Week 4)

- GitHub Actions workflows
- Pre-commit hooks
- Automated coverage reporting

### Phase 4: Advanced Testing (Week 5+)

- Model performance monitoring
- Load testing with locust
- Chaos engineering (optional)

---

**Last Updated**: 2026-01-10  
**Maintained By**: MLOps Team  
**Questions?** See [Testing Strategy](./TESTING_STRATEGY.md) or ask in #mlops-testing
