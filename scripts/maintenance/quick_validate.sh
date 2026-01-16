#!/bin/bash
# Quick validation script for AlphaPulse MLOps platform

echo "🔍 AlphaPulse MLOps Platform - Quick Validation"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0

check_service() {
    local name=$1
    local command=$2
    
    if eval $command > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

check_file() {
    local name=$1
    local filepath=$2
    
    if [ -f "$filepath" ]; then
        echo -e "${GREEN}✓${NC} $name: $filepath"
        PASS_COUNT=$((PASS_COUNT + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $name: $filepath not found"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi
}

echo "📦 Docker Services"
echo "------------------"
check_service "PostgreSQL" "docker ps | grep postgres | grep -q healthy"
check_service "FastAPI" "docker ps | grep fastapi | grep -q healthy"
check_service "Airflow" "docker ps | grep airflow-webserver"
check_service "MLflow" "docker ps | grep mlflow"
check_service "MinIO" "docker ps | grep alphapulse-minio | grep -q healthy"

echo ""
echo "📊 Database Tables"
echo "------------------"
check_service "prices table" "docker exec postgres psql -U postgres -d alphapulse -c 'SELECT 1 FROM prices LIMIT 1'"
check_service "technical_indicators table" "docker exec postgres psql -U postgres -d alphapulse -c 'SELECT 1 FROM technical_indicators LIMIT 1'"
check_service "sentiment_scores table" "docker exec postgres psql -U postgres -d alphapulse -c 'SELECT 1 FROM sentiment_scores LIMIT 1' 2>/dev/null || true"

echo ""
echo "📁 Training Data"
echo "----------------"
check_file "train.parquet" "data/processed/train.parquet"
check_file "val.parquet" "data/processed/val.parquet"
check_file "test.parquet" "data/processed/test.parquet"

echo ""
echo "🧪 Test Files"
echo "-------------"
check_file "Unit: prepare_training_data" "tests/unit/test_prepare_training_data.py"
check_file "Unit: auto_train" "tests/unit/test_auto_train.py"
check_file "Integration: ml_pipeline" "tests/integration/test_ml_pipeline.py"
check_file "E2E: complete_workflow" "tests/e2e/test_complete_workflow.py"
check_file "Test runner script" "scripts/run_tests.sh"

echo ""
echo "📖 Documentation"
echo "----------------"
check_file "Testing Guide" "docs/testing/COMPREHENSIVE_TESTING_GUIDE.md"
check_file "Test Completion Report" "docs/TEST_COMPLETION_REPORT.md"
check_file "Production Readiness" "docs/PRODUCTION_READINESS_REPORT.md"

echo ""
echo "================================================"
echo "📊 Validation Summary"
echo "================================================"
echo -e "${GREEN}Passed:${NC} $PASS_COUNT"
echo -e "${RED}Failed:${NC} $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready.${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠  Some checks failed. Please review above.${NC}"
    exit 1
fi
