#!/bin/bash
# Deploy trained model to production

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=================================================="
echo "🚀 AlphaPulse Model Production Deployment"
echo "=================================================="
echo ""

# Step 1: Verify model exists
echo -e "${BLUE}Step 1/5: Verify trained model${NC}"
if docker exec alphapulse-trainer test -f /app/models/saved/best_model.pkl; then
    echo -e "${GREEN}✅ Model file found${NC}"
else
    echo -e "${RED}❌ Model not found. Train a model first:${NC}"
    echo "  ./scripts/quick_train_docker.sh"
    exit 1
fi
echo ""

# Step 2: Check model performance
echo -e "${BLUE}Step 2/5: Validate model performance${NC}"
SUMMARY=$(docker exec alphapulse-trainer cat /app/models/saved/training_summary.json 2>/dev/null || echo "{}")

if [ "$SUMMARY" != "{}" ]; then
    TEST_MAE=$(echo "$SUMMARY" | docker exec -i alphapulse-trainer python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('best_model', {}).get('test_mae', 0))")
    TEST_R2=$(echo "$SUMMARY" | docker exec -i alphapulse-trainer python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('best_model', {}).get('test_r2', 0))")
    
    echo "  Test MAE: $TEST_MAE"
    echo "  Test R²: $TEST_R2"
    
    # Performance threshold
    MAE_THRESHOLD=0.02
    R2_THRESHOLD=0.3
    
    MEETS_MAE=$(docker exec alphapulse-trainer python3 -c "print('yes' if $TEST_MAE < $MAE_THRESHOLD else 'no')")
    MEETS_R2=$(docker exec alphapulse-trainer python3 -c "print('yes' if $TEST_R2 > $R2_THRESHOLD else 'no')")
    
    if [ "$MEETS_MAE" = "yes" ] && [ "$MEETS_R2" = "yes" ]; then
        echo -e "${GREEN}✅ Model meets production requirements${NC}"
    else
        echo -e "${YELLOW}⚠️  Model performance below threshold${NC}"
        echo "  Recommended: MAE < $MAE_THRESHOLD, R² > $R2_THRESHOLD"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  No training summary found${NC}"
fi
echo ""

# Step 3: Copy model to production location
echo -e "${BLUE}Step 3/5: Deploy model files${NC}"
docker exec alphapulse-trainer mkdir -p /app/models/production
docker exec alphapulse-trainer cp /app/models/saved/best_model.pkl /app/models/production/
docker exec alphapulse-trainer cp /app/models/saved/training_summary.json /app/models/production/ 2>/dev/null || true

# Also copy to FastAPI container if needed
docker cp alphapulse-trainer:/app/models/saved/best_model.pkl /tmp/best_model.pkl
docker cp /tmp/best_model.pkl alphapulse-fastapi:/app/models/production/ 2>/dev/null || true
rm /tmp/best_model.pkl

echo -e "${GREEN}✅ Model files deployed${NC}"
echo ""

# Step 4: Test prediction endpoint
echo -e "${BLUE}Step 4/5: Test prediction API${NC}"
if docker ps | grep -q "alphapulse-fastapi"; then
    echo "  Testing prediction endpoint..."
    
    # Wait for API to be ready
    sleep 2
    
    # Test prediction
    RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/predictions/predict/BTC-USD" || echo "ERROR")
    
    if [[ "$RESPONSE" != "ERROR" ]] && [[ "$RESPONSE" == *"predicted_price"* ]]; then
        echo -e "${GREEN}✅ API test successful${NC}"
        echo "  Sample prediction:"
        echo "$RESPONSE" | docker exec -i alphapulse-trainer python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"    Ticker: {data.get('ticker')}\"); print(f\"    Current: \\\${data.get('current_price'):.2f}\"); print(f\"    Predicted: \\\\\\${data.get('predicted_price'):.2f}\"); print(f\"    Direction: {data.get('predicted_direction')}\"); print(f\"    Confidence: {data.get('confidence')}\")" 2>/dev/null || echo "  $RESPONSE"
    else
        echo -e "${YELLOW}⚠️  API not responding (may need restart)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  FastAPI container not running${NC}"
fi
echo ""

# Step 5: Create deployment record
echo -e "${BLUE}Step 5/5: Record deployment${NC}"
DEPLOYMENT_INFO=$(cat <<EOF
{
  "deployment_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "model_path": "/app/models/production/best_model.pkl",
  "deployed_by": "$USER",
  "host": "$(hostname)",
  "git_commit": "$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')",
  "performance": {
    "test_mae": $TEST_MAE,
    "test_r2": $TEST_R2
  }
}
EOF
)

echo "$DEPLOYMENT_INFO" | docker exec -i alphapulse-trainer tee /app/models/production/deployment_info.json > /dev/null
echo -e "${GREEN}✅ Deployment recorded${NC}"
echo ""

echo "=================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo "📊 Model Information:"
docker exec alphapulse-trainer cat /app/models/production/deployment_info.json | docker exec -i alphapulse-trainer python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"  Deployed: {data['deployment_time']}\"); print(f\"  Test MAE: {data['performance']['test_mae']:.6f}\"); print(f\"  Test R²: {data['performance']['test_r2']:.4f}\")"
echo ""
echo "🌐 API Endpoints:"
echo "  GET  http://localhost:8000/api/v1/predictions/predict/BTC-USD"
echo "  POST http://localhost:8000/api/v1/predictions/predict/batch"
echo "  GET  http://localhost:8000/api/v1/predictions/model/info"
echo "  POST http://localhost:8000/api/v1/predictions/model/reload"
echo ""
echo "📝 Example Usage:"
echo "  curl http://localhost:8000/api/v1/predictions/predict/BTC-USD"
echo ""
