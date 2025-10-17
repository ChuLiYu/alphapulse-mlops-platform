# AlphaPulse Testing Strategy

## Overview

This document describes the comprehensive testing strategy for the AlphaPulse MLOps platform, covering unit tests, integration tests, and end-to-end (E2E) tests.

## Testing Hierarchy

### 1. Unit Tests

**Location**: `tests/unit/`

**Purpose**: Test the functionality of individual functions and classes in isolation.

**Coverage**:

- ✅ `test_prepare_training_data.py` - Data preparation logic
  - Sentiment feature calculation
  - News frequency feature calculation
  - Interaction feature calculation
  - Data quality validation
- ✅ `test_auto_train.py` - Automated training functionality
  - Model configuration
  - Training pipeline logic
  - Best model selection
  - Model saving/loading
- ✅ `test_backtest.py` - Backtesting functionality
  - Trade signal generation
  - Performance metric calculation
  - Sharpe Ratio calculation
- ✅ `test_validation.py` - Walk-Forward validation
- ✅ `test_sentiment.py` - Sentiment analysis
- ✅ `test_api_schemas.py` - API data schema validation

**Execution**:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_prepare_training_data.py -v

# Run specific test class or function
pytest tests/unit/test_auto_train.py::TestAutoTrainer::test_initialization -v
```

### 2. Integration Tests

**Location**: `tests/integration/`

**Purpose**: Test interactions between different system components.

**Coverage**:

- ✅ `test_ml_pipeline.py` - ML Pipeline integration
  - Database connectivity
  - Data loading to feature preparation
  - Training data generation
  - MLflow integration
- ✅ `test_docker_services.py` - Docker service integration
  - PostgreSQL connectivity
  - Airflow/Mage UI accessibility
  - MLflow API accessibility
  - FastAPI health checks
- ✅ `test_rss_pipeline_integration.py` - RSS pipeline integration
- ✅ `test_pipeline_api_integration.py` - Pipeline API integration

**Execution**:

```bash
# Run all integration tests
pytest tests/integration/ -v

# Requires Docker containers to be running
docker-compose up -d
pytest tests/integration/test_ml_pipeline.py -v
```

### 3. End-to-End Tests (E2E)

**Location**: `tests/e2e/`

**Purpose**: Test complete business workflows from start to finish.

**Coverage**:

- ✅ `test_complete_workflow.py` - Full workflow
  - Data ingestion to prediction
  - Service health checks
  - Model training workflow
  - MLflow tracking
  - Pipeline execution
  - End-to-end data quality validation
  - Model performance verification
  - System resilience testing

**Execution**:

```bash
# E2E tests require all services to be running
docker-compose up -d

# Wait for services to initialize
sleep 30

# Run E2E tests
pytest tests/e2e/ -v -m e2e

# Run slow tests (including full training)
pytest tests/e2e/ -v -m "e2e and slow"
```

## Testing Markers

We use pytest markers to categorize tests:

```python
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Slow tests (> 30s)
@pytest.mark.integration  # Integration tests
@pytest.mark.skipif       # Conditional skip
```

Configured in `pytest.ini`:

```ini
[pytest]
markers =
    e2e: End-to-end tests
    slow: Slow running tests
    integration: Integration tests
```

## Quick Test Scripts

Use convenient scripts to run tests:

```bash
# Run all fast tests (unit + integration)
./scripts/run_tests.sh

# Run unit tests only
./scripts/run_tests.sh --unit-only

# Run integration tests only
./scripts/run_tests.sh --integration-only

# Run all tests (including E2E)
./scripts/run_tests.sh --all --e2e

# Verbose output
./scripts/run_tests.sh -v
```

## Test Coverage

Generate coverage reports:

```bash
# Run tests and generate coverage
pytest tests/unit/ --cov=src/alphapulse --cov-report=html

# View coverage report
open htmlcov/index.html
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
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

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov

      - name: Run integration tests
        run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
```

## Testing Best Practices

### 1. Write Testable Code

- Use dependency injection
- Avoid global state
- Separate business logic from I/O

### 2. Use Fixtures

```python
@pytest.fixture
def sample_data():
    return pd.DataFrame({
        'price': [50000, 51000, 49000],
        'volume': [1000000, 1100000, 900000]
    })

def test_feature_calculation(sample_data):
    result = calculate_features(sample_data)
    assert 'target' in result.columns
```

### 3. Mock External Dependencies

```python
from unittest.mock import patch

@patch('alphapulse.ml.prepare_training_data.create_engine')
def test_with_mock(mock_engine):
    mock_engine.return_value = Mock()
    # Test code here
```

### 4. Parameterized Testing

```python
@pytest.mark.parametrize("threshold,expected_trades", [
    (0.001, 25),
    (0.005, 10),
    (0.01, 5),
])
def test_threshold_effects(threshold, expected_trades):
    result = run_backtest(threshold=threshold)
    assert result.total_trades == expected_trades
```

## Test Data Management

### Fixture Data

- Use `tests/fixtures/` to store static test data
- Use `conftest.py` for shared fixtures

### Database Testing

- Use SQLite in-memory for fast unit tests
- Use Docker PostgreSQL for integration tests
- Clean up test data after execution to avoid state pollution

## Performance Testing

```bash
# Use pytest-benchmark
pip install pytest-benchmark

# Run benchmarks
pytest tests/performance/ --benchmark-only
```

## Troubleshooting

### Common Issues

1. **Database Connection Failure**

   ```bash
   # Ensure PostgreSQL container is running
   docker ps | grep postgres
   docker-compose up -d postgres
   ```

2. **Import Errors**

   ```bash
   # Ensure PYTHONPATH is correctly set
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   ```

3. **MLflow Connection Failure**
   ```bash
   # Ensure MLflow service is running
   docker ps | grep mlflow
   export MLFLOW_TRACKING_URI=http://localhost:5001
   ```

## Continuous Improvement

### Coverage Targets

- Unit Tests: > 80%
- Integration Tests: > 60%
- Critical Paths: 100%

### Regular Reviews

- Review test coverage monthly
- Remove deprecated tests
- Add regression tests for fixed bugs
- Keep test documentation updated

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

# Validation Checklist: MLOps Production Ready

## 1. Data Integrity ✅
- [x] BTC Price data (8 years hourly) available in `btc_price_data`.
- [x] Sentiment data (10 years synthetic + live Reddit) available.
- [x] No `price_change_1d` KeyError during training.
- [x] Non-numeric columns (loaded_at, etc.) filtered before model input.

## 2. Infrastructure & Networking ✅
- [x] Airflow container can reach Trainer API via `http://trainer:8080`.
- [x] MLflow tracking URI properly mapped to external port 5001.
- [x] Fernet keys and passwords decoupled to environment variables.

## 3. Training & Inference ✅
- [x] `model_training_pipeline` executes multiple algorithm iterations.
- [x] Overfitting protection detects train-val gap thresholds.
- [x] `InferenceEngine` can load `best_model.pkl` and save `HOLD/BUY/SELL` signals.

## 4. Documentation ✅
- [x] All technical reports and guides translated to English.
- [x] Mermaid diagrams fixed for GitHub rendering.
- [x] PLAN.md updated with CT/CD roadmap.

---
**Status**: Ready for Production Deployment
**Date**: 2026-01-13