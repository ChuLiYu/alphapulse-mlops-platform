# ================================================================================
# AlphaPulse MLOps Platform - Makefile
# ================================================================================
# Single entry point for all operations (Maintenance First Principle)
# All commands use docker-compose from the infra/ directory
#
# Quick Start:
#   make init    - Initialize environment
#   make up      - Start all services
#   make health  - Check service health
#   make test    - Run tests
# ================================================================================

.PHONY: help up down logs status health clean backup restore init test build rebuild
.PHONY: test-unit test-integration test-data test-all test-coverage test-fast test-performance
.PHONY: shell ports urls db-shell db-migrate db-reset

# Paths
COMPOSE_FILE := infra/docker-compose.yml
ENV_FILE := .env.local

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
BLUE   := \033[0;34m
NC     := \033[0m # No Color

# Default target - show help
.DEFAULT_GOAL := help

help:
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)  AlphaPulse MLOps Platform - Command Reference$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)🚀 Quick Start:$(NC)"
	@echo "  $(GREEN)make init$(NC)        Initialize environment (first-time setup)"
	@echo "  $(GREEN)make up$(NC)          Start all services"
	@echo "  $(GREEN)make health$(NC)      Check service health"
	@echo "  $(GREEN)make logs$(NC)        View service logs"
	@echo ""
	@echo "$(YELLOW)🛠️  Core Operations:$(NC)"
	@echo "  $(GREEN)make up$(NC)          Start all services in detached mode"
	@echo "  $(GREEN)make down$(NC)        Stop all services"
	@echo "  $(GREEN)make restart$(NC)     Restart all services"
	@echo "  $(GREEN)make status$(NC)      Check service status"
	@echo "  $(GREEN)make health$(NC)      Run detailed health checks"
	@echo "  $(GREEN)make logs$(NC)        View all service logs (tail)"
	@echo "  $(GREEN)make logs-f$(NC)      Follow service logs"
	@echo ""
	@echo "$(YELLOW)🔨 Build Operations:$(NC)"
	@echo "  $(GREEN)make build$(NC)       Build all custom images"
	@echo "  $(GREEN)make rebuild$(NC)     Rebuild and restart services"
	@echo "  $(GREEN)make pull$(NC)        Pull latest base images"
	@echo ""
	@echo "$(YELLOW)💾 Data Management:$(NC)"
	@echo "  $(GREEN)make backup$(NC)      Backup all data"
	@echo "  $(GREEN)make restore$(NC)     Restore from backup"
	@echo "  $(GREEN)make clean$(NC)       Remove containers and volumes"
	@echo "  $(GREEN)make reset$(NC)       Full reset (clean + init)"
	@echo ""
	@echo "$(YELLOW)🗄️  Database Operations:$(NC)"
	@echo "  $(GREEN)make db-shell$(NC)    Open PostgreSQL shell"
	@echo "  $(GREEN)make db-migrate$(NC)  Run database migrations"
	@echo "  $(GREEN)make db-reset$(NC)    Reset database (drop + recreate)"
	@echo "  $(GREEN)make db-backup$(NC)   Backup database"
	@echo ""
	@echo "$(YELLOW)🧪 Testing:$(NC)"
	@echo "  $(GREEN)make test$(NC)              Run smoke tests"
	@echo "  $(GREEN)make test-unit$(NC)         Run unit tests (fast)"
	@echo "  $(GREEN)make test-integration$(NC)  Run integration tests"
	@echo "  $(GREEN)make test-data$(NC)         Run data quality tests"
	@echo "  $(GREEN)make test-all$(NC)          Run all tests"
	@echo "  $(GREEN)make test-coverage$(NC)     Run tests with coverage report"
	@echo "  $(GREEN)make test-fast$(NC)         Run fast tests only"
	@echo "  $(GREEN)make test-performance$(NC)  Run performance tests"
	@echo ""
	@echo "$(YELLOW)🐚 Development:$(NC)"
	@echo "  $(GREEN)make init$(NC)        Initialize environment and create .env.local"
	@echo "  $(GREEN)make shell$(NC)       Open shell in Airflow Scheduler container"
	@echo "  $(GREEN)make shell-api$(NC)   Open shell in FastAPI container"
	@echo "  $(GREEN)make format$(NC)      Format Python code with black"
	@echo "  $(GREEN)make lint$(NC)        Run linters (black, flake8)"
	@echo ""
	@echo "$(YELLOW)📊 Monitoring:$(NC)"
	@echo "  $(GREEN)make ports$(NC)       Show service ports"
	@echo "  $(GREEN)make urls$(NC)        Show service URLs"
	@echo "  $(GREEN)make ps$(NC)          Show running containers"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"

# ================================================================================
# Initialization
# ================================================================================

init:
	@echo "$(BLUE)Initializing AlphaPulse environment...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(YELLOW)Creating .env.local from .env.example...$(NC)"; \
		cp .env.example $(ENV_FILE); \
		echo "$(GREEN)✓ Created $(ENV_FILE)$(NC)"; \
	else \
		echo "$(GREEN)✓ $(ENV_FILE) already exists$(NC)"; \
	fi
	@echo "$(YELLOW)Creating required directories...$(NC)"
	@mkdir -p logs data/raw data/processed data/features models/saved models/experiments
	@echo "$(GREEN)✓ Directories created$(NC)"
	@echo "$(YELLOW)Creating MinIO bucket...$(NC)"
	@cd infra && docker compose up -d minio mc
	@echo "$(GREEN)✓ MinIO initialized$(NC)"
	@echo ""
	@echo "$(GREEN)✓ Initialization complete!$(NC)"
	@echo ""
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit $(ENV_FILE) if needed"
	@echo "  2. Run: $(GREEN)make up$(NC)"
	@echo "  3. Run: $(GREEN)make health$(NC)"

# ================================================================================
# Build Operations
# ================================================================================

build:
	@echo "$(BLUE)Building custom images...$(NC)"
	@cd infra && docker compose build
	@echo "$(GREEN)✓ Images built successfully$(NC)"

rebuild:
	@echo "$(BLUE)Rebuilding and restarting services...$(NC)"
	@cd infra && docker compose down
	@cd infra && docker compose build --no-cache
	@cd infra && docker compose up -d
	@echo "$(GREEN)✓ Services rebuilt and restarted$(NC)"

pull:
	@echo "$(BLUE)Pulling latest base images...$(NC)"
	@cd infra && docker compose pull
	@echo "$(GREEN)✓ Images pulled successfully$(NC)"

# ================================================================================
# Service Operations
# ================================================================================

up:
	@echo "$(BLUE)Starting all services...$(NC)"
	@cd infra && docker compose --env-file ../$(ENV_FILE) up -d
	@echo "$(GREEN)✓ All services started$(NC)"
	@echo ""
	@echo "$(YELLOW)Service URLs:$(NC)"
	@make urls

down:
	@echo "$(BLUE)Stopping all services...$(NC)"
	@cd infra && docker compose down
	@echo "$(GREEN)✓ All services stopped$(NC)"

restart:
	@echo "$(BLUE)Restarting all services...$(NC)"
	@cd infra && docker compose restart
	@echo "$(GREEN)✓ All services restarted$(NC)"

ps:
	@cd infra && docker compose ps

status:
	@echo "$(BLUE)Service Status:$(NC)"
	@cd infra && docker compose ps --format "table {{.Name}}	{{.Status}}	{{.Ports}}"

logs:
	@cd infra && docker compose logs --tail=100

logs-f:
	@cd infra && docker compose logs -f

logs-api:
	@cd infra && docker compose logs -f fastapi

logs-airflow:
	@cd infra && docker compose logs -f airflow-webserver airflow-scheduler

logs-db:
	@cd infra && docker compose logs -f postgres

# ================================================================================
# Health Checks
# ================================================================================

health:
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Health Check Status$(NC)"
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking PostgreSQL...$(NC)"
	@docker exec alphapulse-postgres pg_isready -U postgres && echo "$(GREEN)✓ PostgreSQL is healthy$(NC)" || echo "$(RED)✗ PostgreSQL is down$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking MinIO...$(NC)"
	@curl -sf http://localhost:9000/minio/health/live > /dev/null && echo "$(GREEN)✓ MinIO is healthy$(NC)" || echo "$(RED)✗ MinIO is down$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking FastAPI...$(NC)"
	@curl -sf http://localhost:8000/health > /dev/null && echo "$(GREEN)✓ FastAPI is healthy$(NC)" || echo "$(RED)✗ FastAPI is down$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking Airflow...$(NC)"
	@curl -sf http://localhost:8080/health > /dev/null && echo "$(GREEN)✓ Airflow is healthy$(NC)" || echo "$(RED)✗ Airflow is down$(NC)"
	@echo ""
	@echo "$(YELLOW)Checking MLflow...$(NC)"
	@curl -sf http://localhost:5002/health > /dev/null && echo "$(GREEN)✓ MLflow is healthy$(NC)" || echo "$(RED)✗ MLflow is down$(NC)"
	@echo ""
	@echo "$(BLUE)════════════════════════════════════════════════════════════════$(NC)"

# ================================================================================
# Database Operations
# ================================================================================

db-shell:
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	@docker exec -it alphapulse-postgres psql -U postgres -d alphapulse

db-migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	@docker exec -i alphapulse-postgres psql -U postgres -d alphapulse < infra/scripts/init-db.sql
	@echo "$(GREEN)✓ Migrations completed$(NC)"

db-reset:
	@echo "$(RED)⚠️  This will delete all data! Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@echo "$(BLUE)Resetting database...$(NC)"
	@cd infra && docker compose stop postgres
	docker volume rm alphapulse-postgres_data || true
	@cd infra && docker compose up -d postgres
	@sleep 5
	@make db-migrate
	@echo "$(GREEN)✓ Database reset complete$(NC)"

db-backup:
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p backups
	@docker exec alphapulse-postgres pg_dump -U postgres alphapulse > backups/alphapulse-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up to backups/$(NC)"

# ================================================================================
# Data Management
# ================================================================================

clean:
	@echo "$(RED)⚠️  This will remove all containers and volumes! Are you sure? [y/N]$(NC)" && read ans && [ $${ans:-N} = y ]
	@echo "$(BLUE)Cleaning up...$(NC)"
	@cd infra && docker compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

reset: clean init
	@echo "$(GREEN)✓ Full reset complete$(NC)"

backup:
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@make db-backup
	@echo "$(BLUE)Backing up MinIO data...$(NC)"
	@cd infra && docker cp alphapulse-minio:/data ../backups/$(shell date +%Y%m%d_%H%M%S)/minio_data 2>/dev/null || echo "Warning: MinIO backup may have failed"
	@echo "$(GREEN)✓ Backup complete$(NC)"

restore:
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -lh backups/
	@echo ""
	@echo "$(YELLOW)Enter backup filename for SQL restore:$(NC)"
	@read backup && docker exec -i alphapulse-postgres psql -U postgres alphapulse < backups/$$backup
	@echo "$(GREEN)✓ SQL Restore complete. MinIO data restore requires manual intervention.$(NC)"

# ================================================================================
# Testing & Development
# ================================================================================

test:
	@echo "$(BLUE)Running default test suite (unit + integration)...$(NC)"
	@pytest tests/unit/ tests/integration/ -v

test-unit:
	@echo "$(BLUE)Running unit tests...$(NC)"
	@pytest tests/unit/ -v -m unit

test-integration:
	@echo "$(BLUE)Running integration tests (requires Docker)...$(NC)"
	@pytest tests/integration/ -v -m integration

test-docker-services:
	@echo "$(BLUE)Running Docker services integration tests...$(NC)"
	@pytest tests/integration/test_docker_services.py -v -s

test-data:
	@echo "$(BLUE)Running data quality tests...$(NC)"
	@pytest tests/data/ -v -m data

test-all:
	@echo "$(BLUE)Running all tests...$(NC)"
	@pytest tests/ -v

test-coverage:
	@echo "$(BLUE)Running tests with coverage report...$(NC)"
	@pytest tests/unit/ --cov=src/alphapulse --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

test-fast:
	@echo "$(BLUE)Running fast tests only (no slow/integration)...$(NC)"
	@pytest tests/ -v -m \"not slow and not integration\"

test-performance:
	@echo "$(BLUE)Running performance tests (latency/throughput)...$(NC)"
	@pytest tests/performance/ -v -m performance

shell:
	@echo "$(BLUE)Opening shell in Airflow Scheduler...$(NC)"
	@cd infra && docker compose exec airflow-scheduler bash

shell-api:
	@echo "$(BLUE)Opening shell in FastAPI...$(NC)"
	@cd infra && docker compose exec fastapi bash

ports:
	@echo "Service Ports:"
	@echo "  FastAPI: 8000"
	@echo "  PostgreSQL: 5432"
	@echo "  MinIO API: 9000"
	@echo "  MinIO Console: 9001"
	@echo "  MLflow: 5002"
	@echo "  Airflow: 8080"

urls:
	@echo "Service URLs:"
	@echo "  FastAPI: http://localhost:8000"
	@echo "  FastAPI Docs: http://localhost:8000/docs"
	@echo "  MLflow UI: http://localhost:5002"
	@echo "  Airflow UI: http://localhost:8080"
	@echo "  MinIO Console: http://localhost:9001 (user: minioadmin, pass: minioadmin)"

# ================================================================================
# ML Training Automation
# ================================================================================

.PHONY: train-auto train-quick train-prepare train-status

train-auto:
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@echo "$(BLUE)  Auto Training Pipeline (6 models × 5 thresholds)$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════$(NC)"
	@cd infra && docker compose exec -T trainer python -m alphapulse.ml.auto_train
	@echo ""
	@echo "$(GREEN)✓ Training complete! Check models/saved/best_model_config.json$(NC)"

train-quick:
	@echo "$(BLUE)Quick training with best known config...$(NC)"
	@cd infra && docker compose exec -T trainer python -m alphapulse.ml.train_best
	@echo "$(GREEN)✓ Quick training complete!$(NC)"

train-prepare:
	@echo "$(BLUE)Preparing training data from database...$(NC)"
	@cd infra && docker compose exec -T trainer python -m alphapulse.ml.prepare_training_data
	@echo "$(GREEN)✓ Training data prepared!$(NC)"

train-status:
	@echo "$(BLUE)Current Best Model:$(NC)"
	@cat src/models/saved/best_model_config.json 2>/dev/null || echo "No model trained yet. Run: make train-auto"
	@echo ""
	@echo "$(BLUE)Saved Models:$(NC)"
	@ls -lh src/models/saved/*.pkl 2>/dev/null || echo "No models saved yet. Run: make train-auto"
