#!/bin/bash

# ================================================================================
# AlphaPulse Quick Start Script
# ================================================================================
# This script provides a quick way to start the AlphaPulse platform
#
# Usage:
#   ./quick-start.sh        - Initialize and start services
#   ./quick-start.sh stop   - Stop all services
#   ./quick-start.sh status - Check service status
# ================================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env.local"
COMPOSE_FILE="infra/docker-compose.yml"

# ================================================================================
# Functions
# ================================================================================

print_banner() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  AlphaPulse MLOps Platform${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Dependencies satisfied${NC}"
}

init_environment() {
    echo -e "${YELLOW}Initializing environment...${NC}"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Creating $ENV_FILE from .env.example...${NC}"
        cp .env.example "$ENV_FILE"
        echo -e "${GREEN}✓ Created $ENV_FILE${NC}"
    else
        echo -e "${GREEN}✓ $ENV_FILE already exists${NC}"
    fi
    
    # Create required directories
    mkdir -p logs data/raw data/processed data/features models/saved models/experiments backups
    echo -e "${GREEN}✓ Directories created${NC}"
}

start_services() {
    echo -e "${YELLOW}Starting services...${NC}"
    cd infra && docker compose --env-file ../"$ENV_FILE" up -d
    echo -e "${GREEN}✓ Services started${NC}"
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    cd infra && docker compose down
    echo -e "${GREEN}✓ Services stopped${NC}"
}

check_health() {
    echo -e "${YELLOW}Checking service health...${NC}"
    echo ""
    
    sleep 5  # Give services time to start
    
    # PostgreSQL
    if docker exec postgres pg_isready -U postgres &> /dev/null; then
        echo -e "${GREEN}✓ PostgreSQL${NC}"
    else
        echo -e "${RED}✗ PostgreSQL${NC}"
    fi
    
    # MinIO
    if curl -sf http://localhost:9000/minio/health/live &> /dev/null; then
        echo -e "${GREEN}✓ MinIO${NC}"
    else
        echo -e "${RED}✗ MinIO${NC}"
    fi
    
    # Wait a bit more for application services
    sleep 10
    
    # FastAPI
    if curl -sf http://localhost:8000/health &> /dev/null; then
        echo -e "${GREEN}✓ FastAPI${NC}"
    else
        echo -e "${YELLOW}⚠ FastAPI (may still be starting)${NC}"
    fi
    
    # Airflow
    if curl -sf http://localhost:8080/health &> /dev/null; then
        echo -e "${GREEN}✓ Airflow${NC}"
    else
        echo -e "${YELLOW}⚠ Airflow (may still be starting)${NC}"
    fi
    
    # MLflow
    if curl -sf http://localhost:5001/health &> /dev/null; then
        echo -e "${GREEN}✓ MLflow${NC}"
    else
        echo -e "${YELLOW}⚠ MLflow (may still be starting)${NC}"
    fi
}

show_urls() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  Service URLs${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}FastAPI Docs:${NC}      http://localhost:8000/docs"
    echo -e "${GREEN}Airflow UI:${NC}        http://localhost:8080"
    echo -e "${GREEN}MLflow:${NC}           http://localhost:5001"
    echo -e "${GREEN}MinIO Console:${NC}    http://localhost:9001"
    echo ""
    echo -e "${YELLOW}Default credentials:${NC}"
    echo -e "  MinIO:   minioadmin / minioadmin"
    echo -e "  Airflow: admin / admin"
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

show_status() {
    echo -e "${YELLOW}Service Status:${NC}"
    cd infra && docker compose ps
}

# ================================================================================
# Main Script
# ================================================================================

print_banner

case "${1:-start}" in
    start)
        check_dependencies
        init_environment
        start_services
        echo ""
        echo -e "${YELLOW}Waiting for services to be ready...${NC}"
        check_health
        show_urls
        echo ""
        echo -e "${GREEN}✓ AlphaPulse is ready!${NC}"
        echo ""
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "  1. Open FastAPI docs: ${GREEN}http://localhost:8000/docs${NC}"
        echo -e "  2. View logs: ${GREEN}make logs${NC}"
        echo -e "  3. Run tests: ${GREEN}make test${NC}"
        ;;
    
    stop)
        stop_services
        ;;
    
    status)
        show_status
        echo ""
        check_health
        ;;
    
    health)
        check_health
        ;;
    
    restart)
        stop_services
        start_services
        echo ""
        check_health
        show_urls
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        echo "Usage:"
        echo "  $0 [start|stop|status|health|restart]"
        exit 1
        ;;
esac
