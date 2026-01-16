#!/bin/bash
# 在 Docker 容器中快速訓練生產模型

set -e

echo "=================================================="
echo "🚀 AlphaPulse 快速生產模型訓練"
echo "=================================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 檢查容器狀態
echo "📋 檢查 Docker 容器..."
if ! docker ps | grep -q "trainer"; then
    echo -e "${RED}❌ Trainer 容器未運行${NC}"
    echo "請先啟動容器: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Trainer 容器運行中${NC}"

# 檢查數據庫
echo ""
echo "🔍 檢查數據庫..."
DB_CHECK=$(docker exec postgres psql -U postgres -d alphapulse -t -c "SELECT COUNT(*) FROM model_features" 2>/dev/null || echo "0")
DB_COUNT=$(echo $DB_CHECK | xargs)

if [ "$DB_COUNT" -lt 500 ]; then
    echo -e "${YELLOW}⚠️  警告: model_features 只有 $DB_COUNT 行 (建議 > 500)${NC}"
    echo "是否繼續? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ 訓練取消"
        exit 1
    fi
else
    echo -e "${GREEN}✅ 數據庫有 $DB_COUNT 行數據${NC}"
fi

# 通過 API 觸發訓練（新架構）
echo ""
echo "🔧 使用新的訓練容器架構..."
echo -e "${GREEN}✅ 訓練容器運行中${NC}"

# 運行訓練
echo ""
echo "=================================================="
echo "🎯 開始訓練 (這可能需要 5-15 分鐘)..."
echo "=================================================="
echo ""

docker exec -it trainer python /app/training/quick_production_train.py

TRAIN_EXIT_CODE=$?

# 檢查結果
echo ""
echo "=================================================="
if [ $TRAIN_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 訓練成功完成！${NC}"
    echo "=================================================="
    echo ""
    echo "📊 下一步:"
    echo "  1. 查看模型: docker exec trainer ls -lh /app/models/saved/"
    echo "  2. 查看摘要: docker exec trainer cat /app/models/saved/training_summary.json"
    echo "  3. 訪問 MLflow: http://localhost:5001"
    echo "  4. 訪問訓練 API: http://localhost:8080/docs"
    echo ""
    echo "🎉 模型已準備好用於生產！"
else
    echo -e "${RED}❌ 訓練失敗 (exit code: $TRAIN_EXIT_CODE)${NC}"
    echo "=================================================="
    echo ""
    echo "🔍 故障排除:"
    echo "  1. 檢查日誌: docker logs trainer"
    echo "  2. 檢查數據: docker exec postgres psql -U postgres -d alphapulse -c 'SELECT COUNT(*) FROM model_features'"
    echo "  3. 檢查容器健康: docker ps"
    echo "  4. 進入容器調試: docker exec -it trainer bash"
    exit 1
fi
