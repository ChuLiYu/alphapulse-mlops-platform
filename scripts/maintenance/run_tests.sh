#!/bin/bash
# Run comprehensive test suite for AlphaPulse MLOps platform

set -e

echo "🧪 AlphaPulse Test Suite Runner"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test categories
UNIT_TESTS="tests/unit/"
INTEGRATION_TESTS="tests/integration/"
E2E_TESTS="tests/e2e/"

# Parse arguments
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_E2E=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            RUN_E2E=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            RUN_E2E=false
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_E2E=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--unit-only|--integration-only|--e2e|--all] [-v|--verbose]"
            exit 1
            ;;
    esac
done

# Set pytest options
PYTEST_OPTS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_OPTS="-vv"
else
    PYTEST_OPTS="-v"
fi

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2
    
    echo -e "${YELLOW}Running $test_name...${NC}"
    
    if pytest $PYTEST_OPTS "$test_path" --tb=short; then
        echo -e "${GREEN}✓ $test_name passed${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
}

# Track results
FAILED_TESTS=0

# Run unit tests
if [ "$RUN_UNIT" = true ]; then
    echo ""
    echo "📦 Unit Tests"
    echo "-------------"
    if ! run_tests "$UNIT_TESTS" "Unit Tests"; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Run integration tests
if [ "$RUN_INTEGRATION" = true ]; then
    echo ""
    echo "🔗 Integration Tests"
    echo "--------------------"
    if ! run_tests "$INTEGRATION_TESTS" "Integration Tests"; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Run E2E tests
if [ "$RUN_E2E" = true ]; then
    echo ""
    echo "🌐 End-to-End Tests"
    echo "-------------------"
    echo "⚠️  Note: E2E tests require all services to be running"
    if ! run_tests "$E2E_TESTS" "E2E Tests" -m e2e; then
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Summary
echo ""
echo "================================"
echo "📊 Test Summary"
echo "================================"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All test suites passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED_TESTS test suite(s) failed${NC}"
    exit 1
fi
