#!/bin/bash
# Automated data collection workflow
# This script runs the complete data collection pipeline

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

LOG_DIR="/tmp/alphapulse_logs"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/auto_collect_$TIMESTAMP.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

echo "============================================================" | tee "$LOG_FILE"
echo "🤖 Automated Data Collection - $(date)" | tee -a "$LOG_FILE"
echo "============================================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Step 1: Check containers
log "Step 1/4: Checking containers..."
if ! docker ps | grep -q trainer; then
    log "❌ Trainer container not running"
    exit 1
fi

log "🚀 Starting data collection..."

# 1. Update Price Data
log "1. Updating BTC price data..."
docker cp scripts/update_price_data.py trainer:/app/src/ >> "$LOG_FILE" 2>&1
if docker exec trainer python /app/src/update_price_data.py >> "$LOG_FILE" 2>&1; then
    log "   ✅ Price data updated"
else
    log "   ❌ Failed to update price data"
    exit 1
fi

# 2. Collect News & Sentiment
log "2. Collecting news and sentiment..."
docker cp scripts/collect_news_and_sentiment.py trainer:/app/src/ >> "$LOG_FILE" 2>&1
if docker exec trainer python /app/src/collect_news_and_sentiment.py >> "$LOG_FILE" 2>&1; then
    log "   ✅ News & sentiment collected"
else
    log "   ❌ Failed to collect news"
    # Continue anyway
fi

# 3. Feature Integration
log "3. Integrating features..."
docker cp scripts/integrate_sentiment_features.py trainer:/app/src/ >> "$LOG_FILE" 2>&1
if docker exec trainer python /app/src/integrate_sentiment_features.py >> "$LOG_FILE" 2>&1; then
    log "   ✅ Features integrated"
else
    log "   ❌ Failed to integrate features"
    exit 1
fi

# Summary
log "============================================================"
log "📊 Collection Summary"
log "============================================================"

PRICE_COUNT=$(docker exec postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM prices" 2>/dev/null | xargs || echo "0")
NEWS_COUNT=$(docker exec postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM market_news" 2>/dev/null | xargs || echo "0")
SENTIMENT_COUNT=$(docker exec postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM sentiment_scores" 2>/dev/null | xargs || echo "0")

log "  Prices: $PRICE_COUNT records"
log "  News: $NEWS_COUNT articles"
log "  Sentiment: $SENTIMENT_COUNT analyzed"
log ""
log "✅ Automated collection completed"
log "📄 Log: $LOG_FILE"
echo ""
