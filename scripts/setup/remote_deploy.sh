#!/bin/bash
# scripts/setup/remote_deploy.sh
# Final automation script for AlphaPulse production deployment

set -e

echo "🚀 Starting AlphaPulse Production Deployment..."

# 1. Wait for K3s readiness
echo "⏳ Waiting for K3s to initialize..."
MAX_RETRIES=30
COUNT=0
until [ -f /usr/local/bin/kubectl ] && kubectl get nodes | grep -q "Ready"; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Timeout waiting for K3s."
        exit 1
    fi
    sleep 5
    echo "Check count: $COUNT/$MAX_RETRIES..."
    ((COUNT++))
done
echo "✅ K3s is Ready!"

# 2. Setup Namespace
kubectl create namespace alphapulse 2>/dev/null || true

# 3. Setup Credentials (Account: admin, Pass: AlphaPulse2026)
if ! command -v htpasswd &> /dev/null; then
    echo "📦 Installing security tools..."
    dnf install httpd-tools -y
fi

echo "🔐 Configuring Admin Credentials..."
htpasswd -bc auth admin AlphaPulse2026
kubectl create secret generic admin-credentials --from-file=auth -n alphapulse --dry-run=client -o yaml | kubectl apply -f -
rm auth # Clean up temporary file

# 4. Clone or Update Repository
DEPLOY_DIR="$HOME/deploy"
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "🔄 Updating existing deployment files..."
    cd "$DEPLOY_DIR"
    git pull origin main
else
    echo "📥 Cloning deployment files..."
    git clone https://github.com/ChuLiYu/alphapulse-mlops-platform.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# 5. Apply Kubernetes Manifests
echo "🚢 Deploying all microservices..."
kubectl apply -k infra/k3s/base

echo "📊 Current Pod Status:"
kubectl get pods -n alphapulse

echo "🎉 Deployment initiated! Use 'kubectl get pods -n alphapulse -w' to watch progress."
