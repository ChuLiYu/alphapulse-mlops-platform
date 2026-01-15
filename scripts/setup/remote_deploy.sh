#!/bin/bash
# scripts/setup/remote_deploy.sh
# Final automation script for AlphaPulse production deployment (Strict English)

set -e

echo "🚀 Starting AlphaPulse Production Deployment..."

# 1. Wait for K3s readiness
echo "⏳ Waiting for K3s to initialize..."
KUBECTL_PATH="/usr/local/bin/kubectl"
MAX_RETRIES=60
COUNT=0

until [ -f "$KUBECTL_PATH" ] && "$KUBECTL_PATH" get nodes | grep -q "Ready"; do
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Timeout waiting for K3s to become Ready."
        exit 1
    fi
    sleep 5
    echo "Check count: $COUNT/$MAX_RETRIES... (Waiting for K3s)"
    ((COUNT++))
done
echo "✅ K3s is Ready!"

# 2. Setup Namespace
"$KUBECTL_PATH" create namespace alphapulse 2>/dev/null || true

# 3. Setup Credentials (Account: admin, Pass: AlphaPulse2026)
if ! command -v htpasswd &> /dev/null; then
    echo "📦 Installing security tools (httpd-tools)..."
    dnf install httpd-tools -y
fi

echo "🔐 Configuring Admin Credentials..."
htpasswd -bc auth admin AlphaPulse2026
"$KUBECTL_PATH" create secret generic admin-credentials --from-file=auth -n alphapulse --dry-run=client -o yaml | "$KUBECTL_PATH" apply -f -
rm auth # Clean up temporary file

# 4. Clone or Update Repository
DEPLOY_DIR="$HOME/deploy"
if [ -d "$DEPLOY_DIR/.git" ]; then
    echo "🔄 Updating existing deployment files from GitHub..."
    cd "$DEPLOY_DIR"
    git pull origin main
else
    echo "📥 Cloning deployment files from GitHub..."
    git clone https://github.com/ChuLiYu/alphapulse-mlops-platform.git "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

# 5. Apply Kubernetes Manifests
echo "🚢 Deploying all microservices to K3s cluster..."
"$KUBECTL_PATH" apply -k infra/k3s/base

echo "📊 Current Pod Status in 'alphapulse' namespace:"
"$KUBECTL_PATH" get pods -n alphapulse

echo "🎉 Deployment initiated! Run 'kubectl get pods -n alphapulse -w' to watch progress."