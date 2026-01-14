#!/bin/bash
# AlphaPulse Test Environment Setup Script
# Provides both local venv and Docker test environment setup

set -e  # Stop execution on error

echo "========================================="
echo "AlphaPulse Test Environment Setup Script"
echo "========================================="

# Detect operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    OS="Other"
fi

echo "Detected OS: $OS"

# Display menu
echo ""
echo "Please select test environment setup method:"
echo "1. Local virtual environment (venv) - Fast development testing"
echo "2. Docker container environment - Full integration testing"
echo "3. Hybrid mode - Setup both"
echo "4. Validate existing environment only"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        setup_local_venv
        ;;
    2)
        setup_docker_env
        ;;
    3)
        setup_hybrid_env
        ;;
    4)
        validate_environment
        ;;
    *)
        echo "Invalid choice, using default: Hybrid mode"
        setup_hybrid_env
        ;;
esac

# Function definitions
setup_local_venv() {
    echo ""
    echo "🔧 Setting up local virtual environment (venv)..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 not installed, please install Python 3.12+"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python version: $python_version"
    
    # Check if already in virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "⚠️  Already in virtual environment: $VIRTUAL_ENV"
        read -p "Create new virtual environment? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            deactivate 2>/dev/null || true
        else
            echo "Using existing virtual environment"
        fi
    fi
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        echo "Creating new virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    if [[ "$OS" == "macOS" || "$OS" == "Linux" ]]; then
        source .venv/bin/activate
    else
        source .venv/Scripts/activate
    fi
    
    echo "✅ Virtual environment activated: $(which python)"
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    # Install test packages
    echo "Installing test packages..."
    if [ -f "airflow/requirements.txt" ]; then
        pip install -r airflow/requirements.txt
    else
        echo "⚠️  requirements.txt not found, installing basic test packages"
        pip install pytest pytest-cov pytest-mock pydantic pandas feedparser
    fi
    
    # Install additional test packages
    echo "Installing additional test packages..."
    pip install pytest-benchmark  # Performance testing
    
    echo ""
    echo "🎉 Local virtual environment setup complete!"
    echo ""
    echo "Available test commands:"
    echo "  make test-unit      # Unit tests (fast)"
    echo "  make test-data      # Data quality tests"
    echo "  make test-fast      # Fast tests (skip integration)"
    echo "  make test-coverage  # Test coverage report"
    echo ""
    echo "Note: These tests don't require Docker and run quickly"
}

setup_docker_env() {
    echo ""
    echo "🐳 Setting up Docker test environment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker not installed, please install Docker"
        echo "   macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "   Linux: https://docs.docker.com/engine/install/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "⚠️  docker-compose not installed, trying docker compose"
        if ! docker compose version &> /dev/null; then
            echo "❌ Docker Compose not installed"
            exit 1
        fi
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker-compose"
    fi
    
    echo "✅ Docker version: $(docker --version)"
    echo "✅ Docker Compose available"
    
    # Check if Docker service is running
    if ! docker info &> /dev/null; then
        echo "❌ Docker service not running, please start Docker Desktop"
        exit 1
    fi
    
    # Create test-specific docker-compose file
    echo "Creating test-specific configuration..."
    cat > docker-compose.test.yml << 'EOF'
version: '3.8'

services:
  # Test-specific database
  test-postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: alphapulse_test
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
    ports:
      - "5433:5432"  # Avoid conflict with dev environment
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U testuser"]
      interval: 5s
      timeout: 5s
      retries: 5
  
  # Test-specific MinIO
  test-minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: testadmin
      MINIO_ROOT_PASSWORD: testadmin123
    ports:
      - "9002:9000"  # API port
      - "9003:9001"  # Console port
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 5s
      timeout: 5s
      retries: 5
  
  # Test runner container
  test-runner:
    build:
      context: .
      dockerfile: infra/docker/Dockerfile.trainer
    depends_on:
      test-postgres:
        condition: service_healthy
      test-minio:
        condition: service_healthy
    environment:
      POSTGRES_HOST: test-postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: alphapulse_test
      POSTGRES_USER: testuser
      POSTGRES_PASSWORD: testpass
      MINIO_ENDPOINT: test-minio:9000
      MINIO_ACCESS_KEY: testadmin
      MINIO_SECRET_KEY: testadmin123
    volumes:
      - ./tests:/app/tests
      - ./airflow:/app/airflow
    command: >
      sh -c "pip install pytest pytest-cov pytest-mock &&
             echo 'Waiting for services to be ready...' &&
             sleep 10 &&
             pytest tests/ -v -m 'integration or data'"
EOF
    
    echo "✅ Test-specific docker-compose file created"
    
    echo ""
    echo "🎉 Docker test environment setup complete!"
    echo ""
    echo "Run integration tests:"
    echo "  1. Start test services: docker-compose -f docker-compose.test.yml up -d"
    echo "  2. Run tests: docker-compose -f docker-compose.test.yml run test-runner"
    echo "  3. View logs: docker-compose -f docker-compose.test.yml logs"
    echo "  4. Stop services: docker-compose -f docker-compose.test.yml down"
    echo ""
    echo "Or use Makefile commands:"
    echo "  make test-integration  # Integration tests (requires services to be running)"
}

setup_hybrid_env() {
    echo ""
    echo "🔄 Setting up hybrid test environment..."
    
    # Setup local virtual environment
    setup_local_venv
    
    echo ""
    echo "-----------------------------------------"
    
    # Setup Docker environment
    setup_docker_env
    
    echo ""
    echo "🎉 Hybrid test environment setup complete!"
    echo ""
    echo "📋 Testing strategy recommendations:"
    echo "  Development phase → Use local venv (fast)"
    echo "     make test-unit    # Unit tests"
    echo "     make test-data    # Data quality tests"
    echo "     make test-fast    # Fast tests"
    echo ""
    echo "  Pre-commit/CI → Use Docker (complete)"
    echo "     make up           # Start all services"
    echo "     make test-all     # Run all tests"
    echo "     make test-integration  # Integration tests"
    echo ""
    echo "  Performance testing → Requires special environment"
    echo "     make test-performance  # Performance tests"
}

validate_environment() {
    echo ""
    echo "🔍 Validating existing test environment..."
    
    # Check Python environment
    echo "1. Checking Python environment..."
    if command -v python3 &> /dev/null; then
        echo "   ✅ Python3: $(python3 --version)"
    else
        echo "   ❌ Python3 not installed"
    fi
    
    # Check virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        echo "   ✅ In virtual environment: $VIRTUAL_ENV"
    elif [ -d ".venv" ]; then
        echo "   ⚠️  Virtual environment exists but not activated: .venv/"
    else
        echo "   ℹ️  Not using virtual environment"
    fi
    
    # Check test packages
    echo "2. Checking test packages..."
    if python3 -c "import pytest" &> /dev/null; then
        echo "   ✅ pytest installed"
    else
        echo "   ❌ pytest not installed"
    fi
    
    if python3 -c "import pydantic" &> /dev/null; then
        echo "   ✅ pydantic installed"
    else
        echo "   ❌ pydantic not installed"
    fi
    
    if python3 -c "import pandas" &> /dev/null; then
        echo "   ✅ pandas installed"
    else
        echo "   ❌ pandas not installed"
    fi
    
    # Check Docker
    echo "3. Checking Docker environment..."
    if command -v docker &> /dev/null; then
        echo "   ✅ Docker: $(docker --version | cut -d' ' -f3- | cut -d',' -f1)"
        
        if docker info &> /dev/null; then
            echo "   ✅ Docker service running"
        else
            echo "   ❌ Docker service not running"
        fi
    else
        echo "   ❌ Docker not installed"
    fi
    
    # Check test file structure
    echo "4. Checking test file structure..."
    test_dirs=("tests/unit" "tests/data" "tests/integration" "tests/fixtures")
    for dir in "${test_dirs[@]}"; do
        if [ -d "$dir" ]; then
            file_count=$(find "$dir" -name "test_*.py" -type f | wc -l)
            echo "   ✅ $dir/ ($file_count test files)"
        else
            echo "   ❌ $dir/ does not exist"
        fi
    done
    
    # Check configuration files
    echo "5. Checking configuration files..."
    config_files=("pytest.ini" ".coveragerc" "Makefile")
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file"
        else
            echo "   ❌ $file does not exist"
        fi
    done
    
    echo ""
    echo "📊 Environment validation complete!"
    echo ""
    echo "Recommendations:"
    echo "  1. If packages missing, run: pip install -r airflow/requirements.txt"
    echo "  2. If Docker not running, start Docker Desktop"
    echo "  3. Run tests: make test-unit or make test-fast"
}

# Execute selected function
echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="

# Show next steps
echo ""
echo "🚀 Next steps:"
echo "1. Run quick test validation:"
echo "   make test-fast"
echo ""
echo "2. Run unit tests:"
echo "   make test-unit"
echo ""
echo "3. Run data quality tests:"
echo "   make test-data"
echo ""
echo "4. Check test coverage:"
echo "   make test-coverage"
echo "   # Then open htmlcov/index.html"
echo ""
echo "💡 Tips:"
echo "- Local testing (venv) is good for fast development iteration"
echo "- Docker testing is good for integration tests and CI/CD"
echo "- Hybrid mode provides the most complete test coverage"