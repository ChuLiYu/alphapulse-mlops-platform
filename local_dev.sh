#!/bin/bash

# AlphaPulse Local Development Orchestrator
# Showcase: Senior DX Engineering & Automation

# --- Configuration ---
PROJECT_NAME="alphapulse"
COMPOSE_FILE="infra/docker-compose.yml"
REQUIRED_COMMANDS=("docker" "docker-compose" "curl")

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Helper Functions ---

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_requirements() {
    for cmd in "${REQUIRED_COMMANDS[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is not installed. Please install it to continue."
        fi
    done
}

init_env() {
    if [ ! -f .env ]; then
        log_warn ".env file not found. Cloning from .env.example..."
        cp .env.example .env
        log_success ".env initialized. Please review credentials."
    fi
}

# --- Main Commands ---

start_stack() {
    log_info "Verifying system readiness..."
    check_requirements
    init_env

    log_info "Starting AlphaPulse stack (Detached mode)..."
    docker-compose -f $COMPOSE_FILE up -d

    log_info "Waiting for API Gateway healthcheck..."
    # Demonstration of robust polling logic
    local retries=0
    local max_retries=12
    while [ $retries -lt $max_retries ]; do
        if curl -s http://localhost:8000/health | grep -q "healthy"; then
            log_success "Backend API is online."
            break
        fi
        log_info "Still waiting... ($((retries + 1))/$max_retries)"
        sleep 5
        retries=$((retries + 1))
    done

    if [ $retries -eq $max_retries ]; then
        log_warn "API healthcheck timed out. Check logs with: ./local_dev.sh logs"
    fi

    log_success "Mission Control: http://localhost:3000"
    log_success "Airflow: http://localhost:8080 (admin/admin)"
    log_success "MLflow: http://localhost:5002"
}

stop_stack() {
    log_info "Shutting down system safely..."
    docker-compose -f $COMPOSE_FILE down
    log_success "System offline."
}

show_status() {
    log_info "Current Service Status:"
    docker-compose -f $COMPOSE_FILE ps
}

# --- Execution ---

case "$1" in
    up|start)
        start_stack
        ;;
    down|stop)
        stop_stack
        ;;
    status)
        show_status
        ;;
    logs)
        docker-compose -f $COMPOSE_FILE logs -f --tail=100
        ;;
    restart)
        stop_stack
        start_stack
        ;;
    *)
        echo "Usage: $0 {up|down|status|logs|restart}"
        exit 1
esac
