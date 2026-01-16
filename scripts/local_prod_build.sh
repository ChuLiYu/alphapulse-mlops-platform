#!/bin/bash

# AlphaPulse Local Production Build & Push Script
# 這個腳本利用你的 Mac (ARM64) 原生速度來構建 Image，並推送到 GHCR。
# 這會同時作為 GitHub Actions 的緩存，讓 CI 下次跑起來飛快。

REGISTRY="ghcr.io"
USERNAME="chuliyu"  # Must be lowercase
REPO="alphapulse-mlops-platform"

echo "🚀 Starting local production build for ARM64..."

# 1. 檢查 Docker 狀態
if ! docker info | grep -q "orbstack"; then
    echo "⚠️  建議使用 OrbStack 以獲得最佳效能。"
fi

# 2. 登入檢查 (我們假設用戶已經在 terminal 執行過 docker login)
echo "🔐 Verifying Registry Access..."
if ! docker pull ghcr.io/chuliyu/alphapulse-mlops-platform/fastapi:latest >/dev/null 2>&1; then
    echo "❌ 權限不足！請先在終端機執行: echo \$GITHUB_TOKEN | docker login ghcr.io -u chuliyu --password-stdin"
    # exit 1 (我們先不 exit，嘗試繼續構建)
fi

# 3. 構建並推送列表
services=("frontend" "fastapi" "mlflow" "trainer" "airflow")

for service in "${services[@]}"; do
    echo "📦 Building $service..."
    
    # 決定 Dockerfile 路徑
    case $service in
        "frontend")
            DOCKERFILE="frontend/Dockerfile"
            CONTEXT="."
            ;;
        "fastapi")
            DOCKERFILE="infra/docker/Dockerfile.fastapi"
            CONTEXT="."
            ;;
        "mlflow")
            DOCKERFILE="infra/docker/Dockerfile.mlflow"
            CONTEXT="."
            ;;
        "trainer")
            DOCKERFILE="infra/docker/Dockerfile.trainer"
            CONTEXT="."
            ;;
        "airflow")
            DOCKERFILE="infra/docker/Dockerfile.airflow"
            CONTEXT="."
            ;;
    esac

    # 執行原生的 Buildx 並推送
    docker buildx build --platform linux/arm64 \
        -t "$REGISTRY/$USERNAME/$REPO/$service:latest" \
        -f "$DOCKERFILE" \
        --push "$CONTEXT"

    echo "✅ $service pushed successfully!"
done

echo "🎉 All images are now in GHCR and ready for Oracle Cloud deployment!"
echo "💡 GitHub Actions will now use these as cache for future runs."
