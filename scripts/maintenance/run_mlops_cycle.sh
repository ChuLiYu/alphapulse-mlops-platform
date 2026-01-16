#!/bin/bash
# run_mlops_cycle.sh
# Manually triggers the full MLOps lifecycle: Training -> Inference -> Monitoring

echo "🚀 Starting Full MLOps Cycle..."

# 1. Trigger Training
echo "1. Triggering iterative training..."
curl -X POST http://localhost:8181/train -H "Content-Type: application/json" -d '{"mode": "ultra_fast", "experiment_name": "full_cycle_test"}'

echo "⏳ Waiting for training to complete (30s)..."
sleep 30

# 2. Run Inference (Manual trigger if training still running)
echo "2. Running Inference Engine..."
docker exec -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/alphapulse trainer python /app/src/alphapulse/ml/inference/engine.py

# 3. Run Monitoring (Drift Detection)
echo "3. Running Evidently AI Drift Detection..."
docker exec -e DATABASE_URL=postgresql://postgres:postgres@postgres:5432/alphapulse trainer python /app/src/alphapulse/monitoring/drift_detector.py

echo "✅ Full Cycle Complete!"
echo "Check MLflow (Port 5001) for results and drift reports."
