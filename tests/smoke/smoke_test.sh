#!/bin/bash

# AlphaPulse MLOps Platform - Smoke Tests
# Basic functionality tests for the local Docker Compose environment

set -e

echo "🧪 AlphaPulse Smoke Tests"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
tests_passed=0
tests_failed=0
tests_skipped=0

# Helper functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    ((tests_passed++))
}

print_failure() {
    echo -e "${RED}✗ $1${NC}"
    ((tests_failed++))
}

print_skipped() {
    echo -e "${YELLOW}⚠ $1${NC}"
    ((tests_skipped++))
}

# Test 1: Check if Docker Compose is running
test_docker_compose_running() {
    echo "1. Testing Docker Compose services..."
    
    if docker-compose ps | grep -q "Up"; then
        print_success "Docker Compose services are running"
    else
        print_failure "Docker Compose services are not running"
        echo "   Run 'make up' to start services"
        return 1
    fi
}

# Test 2: Check PostgreSQL connectivity
test_postgres_connectivity() {
    echo "2. Testing PostgreSQL connectivity..."
    
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL is accessible"
    else
        print_failure "PostgreSQL is not accessible"
    fi
}

# Test 3: Check MinIO health
test_minio_health() {
    echo "3. Testing MinIO health..."
    
    if docker-compose exec -T minio curl -s -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        print_success "MinIO is healthy"
    else
        print_failure "MinIO health check failed"
    fi
}

# Test 4: Check MLflow accessibility
test_mlflow_accessibility() {
    echo "4. Testing MLflow accessibility..."
    
    if curl -s -f http://localhost:5000 > /dev/null 2>&1; then
        print_success "MLflow UI is accessible"
    else
        print_skipped "MLflow UI is not accessible (may still be starting)"
    fi
}

# Test 5: Check Mage.ai accessibility
test_mage_accessibility() {
    echo "5. Testing Mage.ai accessibility..."
    
    if curl -s -f http://localhost:6789 > /dev/null 2>&1; then
        print_success "Mage.ai UI is accessible"
    else
        print_skipped "Mage.ai UI is not accessible (may still be starting)"
    fi
}

# Test 6: Check MinIO bucket exists
test_minio_bucket() {
    echo "6. Testing MinIO bucket..."
    
    if docker-compose exec -T mc /usr/bin/mc ls alphapulse/alphapulse > /dev/null 2>&1; then
        print_success "MinIO bucket 'alphapulse' exists"
    else
        print_failure "MinIO bucket 'alphapulse' does not exist"
        echo "   Run 'make init' to initialize bucket"
    fi
}

# Test 7: Check environment variables
test_environment_variables() {
    echo "7. Testing environment variables..."
    
    required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "MINIO_ROOT_USER" "MINIO_ROOT_PASSWORD")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ] && ! grep -q "^$var=" .env 2>/dev/null; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -eq 0 ]; then
        print_success "Required environment variables are set"
    else
        print_failure "Missing environment variables: ${missing_vars[*]}"
        echo "   Check .env file or run 'make init'"
    fi
}

# Test 8: Check disk space
test_disk_space() {
    echo "8. Testing disk space..."
    
    available_space=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
    
    if (( $(echo "$available_space > 5" | bc -l) )); then
        print_success "Sufficient disk space available (${available_space}G)"
    else
        print_failure "Low disk space (${available_space}G), minimum 5G recommended"
    fi
}

# Test 9: Check Docker resource availability
test_docker_resources() {
    echo "9. Testing Docker resource availability..."
    
    if docker info > /dev/null 2>&1; then
        print_success "Docker daemon is running"
    else
        print_failure "Docker daemon is not running"
    fi
}

# Test 10: Check Makefile commands
test_makefile_commands() {
    echo "10. Testing Makefile commands..."
    
    if make --version > /dev/null 2>&1; then
        if make help > /dev/null 2>&1; then
            print_success "Makefile commands are working"
        else
            print_failure "Makefile 'help' command failed"
        fi
    else
        print_skipped "Make command not available"
    fi
}

# Run all tests
run_all_tests() {
    test_docker_compose_running
    test_postgres_connectivity
    test_minio_health
    test_mlflow_accessibility
    test_mage_accessibility
    test_minio_bucket
    test_environment_variables
    test_disk_space
    test_docker_resources
    test_makefile_commands
}

# Summary function
print_summary() {
    echo ""
    echo "📊 Test Summary"
    echo "=============="
    echo -e "${GREEN}Passed: $tests_passed${NC}"
    echo -e "${RED}Failed: $tests_failed${NC}"
    echo -e "${YELLOW}Skipped: $tests_skipped${NC}"
    echo ""
    
    total_tests=$((tests_passed + tests_failed + tests_skipped))
    
    if [ $tests_failed -eq 0 ]; then
        echo -e "${GREEN}✅ All critical tests passed!${NC}"
        echo "The AlphaPulse environment is ready for development."
        exit 0
    else
        echo -e "${RED}❌ Some tests failed.${NC}"
        echo "Please check the failed tests above and fix the issues."
        echo "Run 'make init' if this is the first setup."
        exit 1
    fi
}

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Main execution
echo "Starting smoke tests..."
echo ""

run_all_tests
print_summary