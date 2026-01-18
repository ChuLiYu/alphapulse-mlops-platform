#!/bin/bash

# AlphaPulse MLOps Platform - Initialization Script
# Idempotent: safe to run multiple times

set -e

echo "🚀 AlphaPulse MLOps Platform Initialization"
echo "=========================================="

# Check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker first."
        exit 1
    fi
    echo "✓ Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    echo "✓ Docker Compose is installed"
    
    # Check Make
    if ! command -v make &> /dev/null; then
        echo "⚠️  Make is not installed. Some commands may not work."
    else
        echo "✓ Make is installed"
    fi
}

# Create environment file
setup_environment() {
    echo "📝 Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo "✓ Created .env file from .env.example"
            echo "⚠️  Please review and edit .env file with your configuration"
        else
            echo "⚠️  .env.example not found, creating basic .env file"
            cat > .env << EOF
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=alphapulse

# MinIO Configuration
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
EOF
        fi
    else
        echo "✓ .env file already exists"
    fi
}

# Initialize MinIO bucket
setup_minio() {
    echo "🪣 Setting up MinIO bucket..."
    
    # Start MinIO and MC services
    docker-compose up -d minio mc
    
    echo "⏳ Waiting for MinIO to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose exec -T minio curl -s -f http://localhost:9000/minio/health/live > /dev/null 2>&1; then
            echo "✓ MinIO is ready"
            break
        fi
        
        echo "  Attempt $attempt/$max_attempts: MinIO not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [ $attempt -gt $max_attempts ]; then
        echo "❌ MinIO failed to start within timeout"
        exit 1
    fi
    
    # Check if bucket was created by MC service
    echo "✓ MinIO bucket initialization should be complete"
}

# Create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    
    mkdir -p \
        mlflow/artifacts \
        backups \
        logs \
        tmp
    
    echo "✓ Directories created"
}

# Set permissions
set_permissions() {
    echo "🔒 Setting permissions..."
    
    # Make scripts executable
    chmod +x scripts/setup/*.sh 2>/dev/null || true
    
    echo "✓ Permissions set"
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Initialization Complete!"
    echo "=========================="
    echo ""
    echo "Next steps:"
    echo "1. Review and edit .env file if needed"
    echo "2. Start all services:"
    echo "   $ make up"
    echo ""
    echo "3. Check service status:"
    echo "   $ make status"
    echo ""
    echo "4. Access the services:"
    echo "   - Airflow: http://localhost:8080"
    echo "   - MLflow: http://localhost:5001"
    echo "   - MinIO Console: http://localhost:9001"
    echo "     (user: minioadmin, password: minioadmin)"
    echo ""
    echo "5. Run health checks:"
    echo "   $ make health"
    echo ""
    echo "For more commands, run:"
    echo "   $ make help"
}

# Main execution
main() {
    check_prerequisites
    setup_environment
    create_directories
    setup_minio
    set_permissions
    show_next_steps
}

# Run main function
main "$@"