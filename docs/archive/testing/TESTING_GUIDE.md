ㄣ# Testing Guide - AlphaPulse

## 📋 Overview

AlphaPulse uses a **two-tier testing approach**:

1. **Shell Script (health_check.sh)** - Fast environment verification
2. **pytest Framework** - Comprehensive integration and unit tests

---

## 🎯 Quick Start

### 1. Quick Health Check (5 seconds)

```bash
# Fast verification that Docker services are running
make health-check
```

**What it checks:**

- ✅ Docker daemon running
- ✅ All containers are up (Postgres, MinIO, Mage, MLflow, FastAPI)
- ✅ Basic endpoint connectivity

**Use when:**

- Just started services (`make up`)
- Quick sanity check before running tests
- CI/CD pre-flight checks

---

### 2. Comprehensive Integration Tests (30 seconds)

```bash
# Full pytest integration test suite
make test-docker-services
```

**What it tests:**

- ✅ PostgreSQL connection and DECIMAL support
- ✅ Database schema and table structure
- ✅ Airflow UI accessibility
- ✅ MLflow API functionality
- ✅ MinIO health
- ✅ FastAPI health endpoint and Swagger docs
- ✅ Pipeline module imports

**Use when:**

- After code changes
- Before committing
- Phase 4.5 validation

---

### 3. Full Test Suite (2-5 minutes)

```bash
# Run all tests (unit + integration)
make test-all
```

---

## 🏗️ Testing Architecture

### Why Two Approaches?

#### Shell Script (`health_check.sh`)

**Purpose:** Fast environment verification  
**Speed:** 5-10 seconds  
**Checks:**

- Container status
- Basic endpoint reachability
- Quick pass/fail for CI/CD

**Analogy:** Like checking if your car's engine starts - quick, binary result.

#### pytest Framework (`test_docker_services.py`)

**Purpose:** Comprehensive functional testing  
**Speed:** 30-60 seconds  
**Checks:**

- Data integrity (Decimal precision)
- Database schema validation
- API response formats
- Error handling
- Data flow end-to-end

**Analogy:** Like a full car inspection - checks engine, brakes, transmission, etc.

---

## 📂 Test Organization

```
tests/
├── integration/
│   ├── test_docker_services.py       # Docker environment tests (NEW)
│   ├── test_pipeline_api_integration.py  # API + Pipeline integration
│   ├── test_rss_*.py                 # RSS pipeline tests
│   └── test_reddit.py                # Reddit pipeline tests
├── unit/
│   └── test_*.py                     # Unit tests for individual functions
├── performance/
│   └── test_*.py                     # Load/latency tests
└── conftest.py                       # pytest fixtures and configuration
```

---

## 🛠️ Available Test Commands

### Core Test Commands

| Command                      | Description               | Speed | When to Use           |
| ---------------------------- | ------------------------- | ----- | --------------------- |
| `make health-check`          | Shell script health check | 5s    | Quick validation      |
| `make test-docker-services`  | pytest Docker integration | 30s   | Phase 4.5 validation  |
| `make test-integration-full` | Health check + pytest     | 40s   | Complete workflow     |
| `make test-unit`             | Unit tests only           | 10s   | Fast feedback loop    |
| `make test-all`              | All tests                 | 2-5m  | Pre-commit validation |

### Specialized Test Commands

```bash
# Unit tests only (fast)
make test-unit

# Integration tests only
make test-integration

# Performance/load tests
make test-performance

# Tests with coverage report
make test-coverage

# Fast tests (exclude slow/integration)
make test-fast
```

---

## 🔬 Test Markers (pytest)

Tests are organized with pytest markers:

```python
@pytest.mark.integration  # Requires Docker
@pytest.mark.unit         # Fast, no dependencies
@pytest.mark.slow         # Takes > 1 minute
@pytest.mark.performance  # Load/latency tests
@pytest.mark.data         # Data quality tests
```

**Run specific markers:**

```bash
# Only integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Only unit tests
pytest -m unit
```

---

## 🚀 Phase 4.5 Testing Workflow

### Step 1: Start Services

```bash
cd /Users/liyu/Programing/alphapulse-mlops-platform
make up
```

### Step 2: Quick Health Check

```bash
make health-check
```

**Expected output:**

```
✅ PASS: Docker daemon running
✅ PASS: PostgreSQL container running
✅ PASS: MinIO container running
✅ PASS: Airflow container running
✅ PASS: MLflow container running
✅ All services healthy!
```

### Step 3: Comprehensive Integration Tests

```bash
make test-docker-services
```

**Expected output:**

```
tests/integration/test_docker_services.py::TestDockerServices::test_postgresql_connection PASSED
tests/integration/test_docker_services.py::TestDockerServices::test_postgresql_decimal_support PASSED
tests/integration/test_docker_services.py::TestDockerServices::test_airflow_ui_accessible PASSED
tests/integration/test_docker_services.py::TestDockerServices::test_mlflow_api_accessible PASSED
tests/integration/test_docker_services.py::TestDockerServices::test_minio_health PASSED
tests/integration/test_docker_services.py::TestDockerServices::test_fastapi_health_endpoint PASSED
... (more tests)

✅ 15 passed in 25.43s
```

### Step 4: Run Full Integration Suite (Optional)

```bash
make test-integration-full
```

This runs:

1. `health_check.sh` (quick verification)
2. `test_docker_services.py` (comprehensive tests)

---

## 🐛 Troubleshooting

### Health Check Fails

**Problem:** `❌ FAIL: PostgreSQL container running`

**Solution:**

```bash
# Check container status
docker ps -a | grep alphapulse

# Check logs
docker logs postgres

# Restart services
make down && make up
```

---

### pytest Import Errors

**Problem:** `ModuleNotFoundError: No module named 'alphapulse'`

**Solution:**

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/Users/liyu/Programing/alphapulse-mlops-platform/src:$PYTHONPATH

# Or run from project root
cd /Users/liyu/Programing/alphapulse-mlops-platform
pytest tests/integration/test_docker_services.py -v
```

---

### FastAPI Container Not Running

**Problem:** `⚠️  WARN: FastAPI container not running`

**Solution:**

```bash
# Add FastAPI service to docker-compose.yml (see Phase 4.5 guide)
# Then rebuild
make down
make up
```

---

## 📊 Success Criteria - Phase 4.5

### ✅ Health Check Must Pass

```bash
make health-check
# Expected: All services healthy! (0 failures)
```

### ✅ Integration Tests Must Pass

```bash
make test-docker-services
# Expected: 15+ tests passed, 0 failed
```

### ✅ Complete Integration Suite

```bash
make test-integration-full
# Expected: Health check + pytest both pass
```

---

## 🎓 Best Practices

### 1. Always Run Health Check First

```bash
# Before running any tests
make health-check

# If it fails, investigate before running pytest
```

### 2. Use Shell Script in CI/CD

```yaml
# .github/workflows/test.yml
- name: Health Check
  run: ./health_check.sh

- name: Integration Tests
  run: pytest tests/integration/test_docker_services.py -v
```

### 3. Use pytest for Development

```bash
# During development - fast feedback
pytest tests/integration/test_docker_services.py::TestDockerServices::test_postgresql_connection -v
```

### 4. Run Full Suite Before Commit

```bash
# Before git commit
make test-integration-full
make test-unit
```

---

## 📝 Summary

| Tool                | Purpose                  | Speed            | Depth         |
| ------------------- | ------------------------ | ---------------- | ------------- |
| **health_check.sh** | Environment verification | ⚡ Fast (5s)     | Basic         |
| **pytest**          | Functional testing       | 🐢 Slower (30s+) | Comprehensive |

**Use both:**

1. `health_check.sh` for quick validation
2. `pytest` for thorough testing

**Commands:**

```bash
make health-check              # Quick (5s)
make test-docker-services      # Comprehensive (30s)
make test-integration-full     # Both (40s)
```

---

**Last Updated:** 2026-01-10  
**Phase:** 4.5 - Local Integration Testing
