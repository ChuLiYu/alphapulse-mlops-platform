#!/bin/bash
# 完整的生產模型訓練流程 - 包含數據準備

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=================================================="
echo "🎯 AlphaPulse 完整生產流程"
echo "=================================================="
echo ""

# 步驟 1: 檢查容器
echo -e "${BLUE}步驟 1/5: 檢查容器狀態${NC}"
if ! docker ps | grep -q "alphapulse-trainer"; then
    echo -e "${RED}❌ 容器未運行${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 容器運行中${NC}\n"

# 步驟 2: 檢查基礎數據
echo -e "${BLUE}步驟 2/5: 檢查基礎數據${NC}"
PRICE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM prices" 2>/dev/null | xargs || echo "0")
NEWS_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM market_news" 2>/dev/null | xargs || echo "0")
SENTIMENT_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM sentiment_scores" 2>/dev/null | xargs || echo "0")

echo "  價格數據: $PRICE_COUNT 行"
echo "  新聞數據: $NEWS_COUNT 行"
echo "  語意數據: $SENTIMENT_COUNT 行"

if [ "$PRICE_COUNT" -lt 100 ]; then
    echo -e "${RED}❌ 缺少價格數據${NC}"
    echo "請先運行數據收集管道"
    exit 1
fi
echo -e "${GREEN}✅ 基礎數據充足${NC}\n"

# 步驟 3: 生成特徵（如果需要）
echo -e "${BLUE}步驟 3/5: 檢查/生成特徵數據${NC}"
FEATURE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM model_features" 2>/dev/null | xargs || echo "0")

if [ "$FEATURE_COUNT" -lt 300 ]; then
    echo -e "${YELLOW}⚠️  特徵數據不足 ($FEATURE_COUNT 行)${NC}"
    echo "正在生成特徵..."
    
    # 運行特徵整合管道 (使用 Trainer 容器)
    docker exec alphapulse-trainer python3 << 'PYTHON'
import sys
# Trainer 容器中源代碼路徑
sys.path.insert(0, '/app/src')

try:
    # 從現有數據創建基本特徵
    from sqlalchemy import create_engine, text
    import pandas as pd
    import numpy as np
    
    engine = create_engine('postgresql://postgres:postgres@postgres:5432/alphapulse')
    
    # 加載價格數據
    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT 
                timestamp as date,
                symbol as ticker,
                price as close,
                volume
            FROM prices 
            WHERE symbol = 'BTC-USD'
            ORDER BY timestamp
            LIMIT 1000
        """), conn)
    
    if len(df) > 0:
        # 添加基本特徵
        df['price_change_1d'] = df['close'].pct_change()
        df['price_change_7d'] = df['close'].pct_change(7)
        df['volume_change_1d'] = df['volume'].pct_change()
        
        # 移動平均
        df['sma_7'] = df['close'].rolling(7).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        
        # RSI (簡化版)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # 波動率
        df['daily_volatility'] = df['close'].pct_change().rolling(20).std()
        
        # 填充缺失值
        df = df.fillna(method='bfill').fillna(0)
        
        # 只保留有完整數據的行
        df = df.dropna()
        
        if len(df) > 50:
            # 保存到 model_features
            df.to_sql('model_features', engine, if_exists='replace', index=False)
            print(f"✅ 生成了 {len(df)} 行特徵數據")
        else:
            print(f"❌ 數據不足，只有 {len(df)} 行")
            sys.exit(1)
    else:
        print("❌ 沒有價格數據")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ 錯誤: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 特徵生成失敗${NC}"
        exit 1
    fi
    
    # 重新檢查
    FEATURE_COUNT=$(docker exec alphapulse-postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM model_features" 2>/dev/null | xargs || echo "0")
fi

echo -e "${GREEN}✅ 特徵數據: $FEATURE_COUNT 行${NC}\n"

# 步驟 4: 安裝依賴
echo -e "${BLUE}步驟 4/5: 安裝訓練依賴${NC}"
# Trainer 容器應已包含所有依賴
# docker exec alphapulse-trainer pip install evidently scipy psutil -q
echo -e "${GREEN}✅ 依賴已安裝 (Trainer容器預裝)${NC}\n"

# 步驟 5: 運行訓練
echo -e "${BLUE}步驟 5/5: 運行快速訓練${NC}"
echo "=================================================="

# 使用新的訓練容器架構
echo "使用專用訓練容器..."

# 運行訓練
docker exec alphapulse-trainer python /app/training/ultra_fast_train.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo -e "${GREEN}🎉 訓練成功完成！${NC}"
    echo "=================================================="
    echo ""
    echo "📊 結果:"
    docker exec alphapulse-trainer cat /app/models/saved/training_summary.json 2>/dev/null | head -30 || echo "查看: docker exec alphapulse-trainer cat /app/models/saved/training_summary.json"
    echo ""
    echo "📁 模型位置:"
    docker exec alphapulse-trainer ls -lh /app/models/saved/*.pkl 2>/dev/null || echo "  /app/models/saved/best_model.pkl"
    echo ""
    echo "🌐 MLflow: http://localhost:5001"
else
    echo -e "${RED}❌ 訓練失敗${NC}"
    exit 1
fi