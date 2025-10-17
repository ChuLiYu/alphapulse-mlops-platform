# Comprehensive Testing Guide

> **Strategic Companion**: [`TESTING_STRATEGY.md`](./TESTING_STRATEGY.md)

This guide provides detailed instructions for executing and extending the AlphaPulse test suite.

## 🏗️ Test Pyramid

1. **Unit Tests**: Logic validation for indicators and sentiment scoring.
2. **Data Tests**: Schema validation and data freshness.
3. **Integration Tests**: Docker service connectivity and pipeline execution.
4. **E2E Tests**: The full "News → Signal" workflow.

## 🚀 Execution Commands

### Local Environment
```bash
# Run unit tests
pytest tests/unit/

# Run specific category
pytest -m unit
pytest -m integration
pytest -m data

# Run with coverage report
pytest --cov=src/alphapulse tests/
```

### Docker Environment (Production-like)
```bash
# Run all tests inside the Airflow environment
docker exec alphapulse-airflow-scheduler pytest /opt/airflow/tests/ -v
```

## 🧪 Detailed Test Categories

### 1. Data Quality (P0)
Ensures our financial models aren't learning from "junk" data.
- **Schema**: Validates Pydantic models.
- **Freshness**: Checks if BTC prices and News are up-to-date.
- **Integrity**: Ensures no NULL values in critical columns.

### 2. Pipeline Orchestration (P1)
- **Scheduling**: Verifies Airflow DAGs are active.
- **Execution**: Simulates a manual trigger and waits for DB updates.

### 3. Model Performance (P2)
- **MAE/RMSE**: Threshold checks for inference accuracy.
- **Drift**: Monitors if current market distributions match the training set (via Evidently AI).

## 🛠️ Adding New Tests

When adding a new feature (e.g., a new technical indicator):
1. Create a file in `tests/unit/test_new_feature.py`.
2. Add a `pytest.fixture` if you need complex mock data.
3. Use `@pytest.mark.unit` to categorize it.
4. Run `make test-all` to ensure no regressions.

---
**Author**: AlphaPulse Team
**Date**: 2026-01-12
