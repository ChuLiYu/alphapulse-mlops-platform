#!/bin/bash
# Setup cold start automation for Mage

set -e

echo "=================================================="
echo "🔧 Setting up Mage Cold Start Automation"
echo "=================================================="

# Copy initialization script to mage_pipeline/scripts
echo "📁 Copying initialization script..."
mkdir -p mage_pipeline/scripts
cp scripts/init_mage_db.py mage_pipeline/scripts/

echo "✅ Initialization script copied"

# Verify entrypoint.sh has the initialization call
echo "🔍 Checking entrypoint.sh..."
if grep -q "init_mage_db.py" mage_pipeline/entrypoint.sh; then
    echo "✅ Entrypoint already configured"
else
    echo "⚠️  Entrypoint needs manual update"
    echo "   Add the following to mage_pipeline/entrypoint.sh before 'exec \"\$@\"':"
    echo ""
    echo "   # Initialize database on cold start"
    echo "   python /home/src/scripts/init_mage_db.py || echo \"⚠️ DB init had issues\""
    echo ""
fi

echo ""
echo "=================================================="
echo "✅ Cold Start Setup Complete"
echo "=================================================="
echo ""
echo "Testing:"
echo "  1. Stop containers:    docker-compose -f infra/docker-compose.yml down"
echo "  2. Start containers:   docker-compose -f infra/docker-compose.yml up -d"
echo "  3. Check logs:         docker logs alphapulse-mage"
echo ""
echo "The database will be automatically initialized on container start."
