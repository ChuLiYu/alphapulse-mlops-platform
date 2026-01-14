#!/bin/bash
# Complete automated pipeline: Data -> Features -> Training -> Deployment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

LOGFILE="/tmp/alphapulse_auto_train_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOGFILE"
}

log "=================================================================="
log "${CYAN}🤖 AlphaPulse Automated Training Pipeline${NC}"
log "=================================================================="
log "$(date)"
log ""

# Parse arguments
SKIP_FEATURES=false
SKIP_DEPLOY=false
TRAINING_MODE="ultra_fast"

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-features)
            SKIP_FEATURES=true
            shift
            ;;
        --skip-deploy)
            SKIP_DEPLOY=true
            shift
            ;;
        --mode)
            TRAINING_MODE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-features] [--skip-deploy] [--mode ultra_fast|standard|full]"
            exit 1
            ;;
    esac
done

log "${BLUE}Configuration:${NC}"
log "  Training Mode: $TRAINING_MODE"
log "  Skip Features: $SKIP_FEATURES"
log "  Skip Deploy: $SKIP_DEPLOY"
log ""

# Step 1: Check containers
log "${BLUE}[1/6] Checking Docker containers${NC}"
if ! docker ps | grep -q "alphapulse-trainer"; then
    log "${RED}❌ Trainer container not running${NC}"
    exit 1
fi
if ! docker ps | grep -q "alphapulse-postgres"; then
    log "${RED}❌ Postgres container not running${NC}"
    exit 1
fi
log "${GREEN}✅ All containers running${NC}"
log ""

# Step 2: Check data availability
log "${BLUE}[2/6] Checking data availability${NC}"
PRICE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM prices" 2>/dev/null | xargs || echo "0")
log "  Price records: $PRICE_COUNT"

if [ "$PRICE_COUNT" -lt 100 ]; then
    log "${RED}❌ Insufficient price data (need at least 100 rows)${NC}"
    log "  Run data collection pipeline first"
    exit 1
fi
log "${GREEN}✅ Sufficient data available${NC}"
log ""

# Step 3: Generate features
log "${BLUE}[3/6] Feature engineering${NC}"
if [ "$SKIP_FEATURES" = true ]; then
    log "${YELLOW}⚠️  Skipping feature generation (--skip-features)${NC}"
    FEATURE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM model_features" 2>/dev/null | xargs || echo "0")
    log "  Existing features: $FEATURE_COUNT rows"
    
    if [ "$FEATURE_COUNT" -lt 300 ]; then
        log "${RED}❌ Not enough features in database${NC}"
        exit 1
    fi
else
    log "  Generating features from price data..."
    docker cp scripts/generate_features.py alphapulse-trainer:/app/src/ >> "$LOGFILE" 2>&1
    
    if docker exec alphapulse-trainer python /app/src/generate_features.py >> "$LOGFILE" 2>&1; then
        FEATURE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM model_features" 2>/dev/null | xargs || echo "0")
        log "${GREEN}✅ Features generated: $FEATURE_COUNT rows${NC}"
    else
        log "${RED}❌ Feature generation failed${NC}"
        log "  Check log: $LOGFILE"
        exit 1
    fi
fi
log ""

# Step 4: Install dependencies
log "${BLUE}[4/6] Installing training dependencies${NC}"
# Trainer should typically have dependencies, but we can run this just in case or skip
# docker exec alphapulse-trainer pip install -q evidently scipy psutil >> "$LOGFILE" 2>&1
log "${GREEN}✅ Dependencies check skipped (Trainer container assumed ready)${NC}"
log ""

# Step 5: Train model
log "${BLUE}[5/6] Training model (mode: $TRAINING_MODE)${NC}"

case $TRAINING_MODE in
    ultra_fast)
        SCRIPT="ultra_fast_train.py"
        EXPECTED_TIME="2-3 minutes"
        ;;
    standard)
        SCRIPT="quick_production_train.py"
        EXPECTED_TIME="5-10 minutes"
        ;;
    full)
        SCRIPT="src/alphapulse/ml/training/iterative_trainer.py"
        EXPECTED_TIME="10-20 minutes"
        ;;
    *)
        log "${RED}❌ Unknown training mode: $TRAINING_MODE${NC}"
        exit 1
        ;;
esac

log "  Script: $SCRIPT"
log "  Expected time: $EXPECTED_TIME"
log "  Started: $(date +%H:%M:%S)"
log ""

START_TIME=$(date +%s)

# Copy training script
docker cp scripts/$SCRIPT alphapulse-trainer:/app/src/ >> "$LOGFILE" 2>&1 || true

# Run training
if docker exec alphapulse-trainer python /app/src/$SCRIPT >> "$LOGFILE" 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    log "${GREEN}✅ Training completed in ${DURATION}s${NC}"
    
    # Show results
    log ""
    log "${CYAN}📊 Training Results:${NC}"
    docker exec alphapulse-trainer python3 << 'PYTHON' 2>/dev/null | tee -a "$LOGFILE" || true
import json
try:
    # Path depends on where script saves it. Assuming /app/models is mounted to ../models
    with open('/app/models/saved/training_summary.json') as f:
        data = json.load(f)
        best = data['best_model']
        print(f"  Model: {best['name']}")
        print(f"  Test MAE: {best['test_mae']:.6f}")
        print(f"  Test R²: {best['test_r2']:.4f}")
        print(f"  Iterations: {data['total_iterations']}")
        print(f"  Overfit models: {data['overfit_count']}")
except Exception as e:
    print(f"  Could not load summary: {e}")
PYTHON
    
else
    log "${RED}❌ Training failed${NC}"
    log "  Check full log: $LOGFILE"
    exit 1
fi
log ""

# Step 6: Deploy model
log "${BLUE}[6/6] Deploying model to production${NC}"
if [ "$SKIP_DEPLOY" = true ]; then
    log "${YELLOW}⚠️  Skipping deployment (--skip-deploy)${NC}"
    log "  Run manually: ./scripts/deploy_model_to_production.sh"
else
    if ./scripts/deploy_model_to_production.sh >> "$LOGFILE" 2>&1; then
        log "${GREEN}✅ Model deployed successfully${NC}"
    else
        log "${RED}❌ Deployment failed${NC}"
        log "  Model trained but not deployed"
        log "  Deploy manually: ./scripts/deploy_model_to_production.sh"
    fi
fi
log ""

# Summary
log "=================================================================="
log "${GREEN}🎉 Pipeline Complete!${NC}"
log "=================================================================="
log ""
log "${CYAN}📋 Summary:${NC}"
log "  Duration: ${DURATION}s"
log "  Features: $FEATURE_COUNT rows"
log "  Log file: $LOGFILE"
log ""
log "${CYAN}🌐 Next Steps:${NC}"
log "  1. View MLflow: http://localhost:5001"
log "  2. Test prediction:"
log "     curl http://localhost:8000/api/v1/predictions/predict/BTC-USD"
log "  3. Check model info:"
log "     curl http://localhost:8000/api/v1/predictions/model/info"
log ""
log "${CYAN}🔄 Retraining:${NC}"
log "  Run this script again anytime to retrain with latest data"
log "  Add to cron for automated daily retraining:"
log "  0 2 * * * cd $(pwd) && ./scripts/auto_train_and_deploy.sh"
log ""
log "$(date)"
log "=================================================================="