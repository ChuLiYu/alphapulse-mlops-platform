# AlphaPulse MLOps 平台架構提示詞

## 專案概述

**專案名稱**: AlphaPulse  
**類型**: 生產級 MLOps 平台（加密貨幣量化交易）  
**當前狀態**: Phase 4.5 完成（2026年1月）  
**目標**: 零成本、高效能的 MLOps 基礎設施

---

## 🏗️ 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CI/CD & Provisioning                             │
│                    Terraform + GitHub Actions                           │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Oracle Cloud (Always Free ARM64)                      │
│                         K3s Single Node Cluster                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Application Namespace                      │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │  │
│  │  │ Airflow │  │ MLflow  │  │ FastAPI │  │ Frontend│            │  │
│  │  │(Orchest)│  │(Registry)│  │(Inference)│ │ (React) │            │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │  │
│  │  │ Trainer │  │ Ollama  │  │ Grafana │                         │  │
│  │  │(Training)│ │(LLM Inf)│  │(Monitor)│                         │  │
│  │  └─────────┘  └─────────┘  └─────────┘                         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         Data Namespace                             │  │
│  │              PostgreSQL              MinIO (S3)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      External Services                                  │
│                  AWS S3 / Cloudflare R2 (Backup)                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 技術棧

| 類別 | 技術 |
|------|------|
| **後端 API** | Python 3.12, FastAPI, AsyncIO, SQLAlchemy 2.0, Pydantic v2 |
| **資料庫** | PostgreSQL 16, MinIO (S3 相容) |
| **ML/AI** | CatBoost, Scikit-learn, XGBoost, LightGBM, Optuna, PyTorch, LangChain, Ollama, Groq |
| **MLOps** | Apache Airflow, MLflow, Evidently AI |
| **前端** | React 18, TypeScript 5.x, Vite 5, Redux Toolkit, Material-UI, TailwindCSS, Recharts, Framer Motion |
| **基礎設施** | Docker, Docker Compose, K3s, Terraform, GitHub Actions, Traefik |
| **監控** | Grafana, Prometheus |

---

## 📂 目錄結構

```
alphapulse-mlops-platform/
├── .github/workflows/     # CI/CD 管線
├── airflow/               # ETL 與協調 (DAGs)
├── docs/                  # 架構決策記錄 (ADRs)
├── frontend/              # React 前端
├── infra/                 # Terraform + K8s
├── src/alphapulse/        # 核心 Python 邏輯
├── tests/                 # 測試套件 (Unit/Integration/E2E)
├── training/              # 獨立訓練腳本
└── scripts/               # 工具腳本
```

---

## 🔌 後端模組 (src/alphapulse/)

### API 路由 (api/routes/)

| 檔案 | 功能 |
|------|------|
| `auth.py` | 認證端點（登入、註冊、API Keys、 |
| `prices角色）.py` | 價格數據管理 |
| `signals.py` | 交易訊號 CRUD |
| `indicators.py` | 技術指標端點 |
| `ops.py` | MLOps 操作（模型註冊、Pipeline 狀態） |
| `health.py` | 健康檢查與系統狀態 |
| `security.py` | 安全監控與訪問日誌 |
| `simulation.py` | 交易模擬端點 |

### API 端點 (api/endpoints/)

| 檔案 | 功能 |
|------|------|
| `predictions.py` | 模型預測端點 |

### 資料模型 (api/)

| 檔案 | 功能 |
|------|------|
| `models.py` | 核心資料庫模型（Price, TradingSignal, TechnicalIndicator） |
| `models_user.py` | 用戶認證模型（User, APIKey, Role, UserRole, AuditLog） |
| `database.py` | 資料庫配置與會話管理 |

### Schema 驗證 (api/schemas/)

- `price.py`, `signal.py`, `indicator.py`, `ops.py`, `health.py`, `security.py`, `simulation.py`, `xai.py`

### 核心服務

| 檔案 | 功能 |
|------|------|
| `security/auth.py` | 認證服務 (JWT, API Keys) |
| `api/model_predictor.py` | 模型預測服務 |
| `monitoring/data_drift.py` | 資料漂移監控 |

### ML 模組 (ml/)

| 檔案 | 功能 |
|------|------|
| `training/iterative_trainer.py` | 迭代訓練器（AutoML, Optuna, Walk-Forward CV） |
| `prepare_training_data.py` | 訓練數據準備 |

---

## 🎨 前端模組 (frontend/src/)

### 頁面 (pages/)

| 檔案 | 功能 |
|------|------|
| `Dashboard.tsx` | Material-UI 儀表板，包含市場圖表、訊號、Pipeline 狀態 |
| `MLOpsConsole.tsx` | MLOps 管理介面 |

### 組件 (components/)

| 檔案 | 功能 |
|------|------|
| `layout/Sidebar.tsx` | 導航側邊欄（路由已規劃但未啟用） |
| `DemoModeBanner.tsx` | Demo 模式指示器 |

### 功能模組 (features/)

| 目錄 | 組件 |
|------|------|
| `mlops/` | PipelineFlow, DriftMonitor, ModelRegistry |
| `strategy/` | StrategyPlayground, StrategyChart, StrategyControlPanel |

### API 整合 (api/)

| 檔案 | 功能 |
|------|------|
| `client.ts` | Axios API 客戶端（含 Demo 模式回退） |
| `dashboard.ts` | 儀表板專用 API 端點 |

### 狀態管理

- **Redux Toolkit**: 已安裝但未廣泛使用
- **Custom Hooks**: `useAuth()`, `useDashboardData()`

---

## 🏢 基礎設施

### Docker 服務 (docker-compose.yml)

12 個服務：
- `postgres` - 主資料庫
- `minio` - S3 相容儲存
- `fastapi` - 推理 API
- `mlflow` - 實驗追蹤
- `airflow-webserver` - 工作流程排程
- `airflow-scheduler` - 排程器
- `airflow-worker` - 工作者
- `trainer` - 訓練引擎
- `frontend` - React 應用
- `grafana` - 監控儀表板

### Terraform

- `infra/terraform/environments/prod/main.tf` - Oracle Cloud 基礎設施
- 跨雲端策略：Oracle Cloud (Compute) + AWS S3 (Storage)

### CI/CD

- `.github/workflows/deploy-k3s.yml` - K3s 部署管線
- 4 個 workflow：測試、部署、成本監控、Terraform 驗證

---

## ⚠️ 已知限制與待辦事項

### 未完成的功能

1. **健康檢查端點** (`src/alphapulse/api/routes/health.py`)
   ```python
   # TODO: 尚未實作
   "uptime": "TODO: Implement uptime tracking",
   "memory_usage": "TODO: Implement memory tracking",
   "cpu_usage": "TODO: Implement CPU tracking",
   "active_connections": "TODO: Implement connection tracking",
   ```

2. **警報系統** (`src/alphapulse/monitoring/data_drift.py`)
   ```python
   # TODO: Integrate with alerting system (Slack, Email, etc.)
   ```

### 前端限制

1. **路由未啟用**: React Router 已安裝但未實作多頁面路由
2. **空的功能模組**: `features/auth/`, `features/market/`, `features/signals/` 目錄存在但為空
3. **Redux 未充分使用**: Redux Toolkit 已安裝但主要使用 local state

### 架構限制

1. **單節點 K3s**: 、生產環境使用單節點集群，無 HA
2. **Demo 模式回退**: 前端依賴 mock data，當後端離線時仍可運作
3. **同步資料庫會話**: 部分代碼使用同步 SQLAlchemy Session

---

## 🚀 發展藍圖 (ROADMAP)

| Phase | 狀態 | 內容 |
|-------|------|------|
| Phase 1-4 | ✅ 完成 | 基礎設施、後端核心、資料 Pipeline、監控 |
| Phase 4.5 | ✅ 完成 | 容器分離、測試重構 |
| Phase 5 | 🔄 進行中 | K3s 叢集遷移 |
| Phase 5.5 | 🚀 計畫中 | CatBoost 整合、Model Promotion |
| Phase 5.6 | 🚀 計畫中 | FinOps 優化 |
| Phase 6 | 📋 計畫中 | 文檔與作品集 |

---

## 🔧 開發環境

### 本地啟動
```bash
./local_dev.sh up
```

### 服務端點
- Frontend: http://localhost:5173
- Airflow: http://localhost:8080 (admin/admin)
- MLflow: http://localhost:5000
- API Docs: http://localhost:8000/docs

---

## 請求重構與擴展建議

請基於以上架構分析，提供：

1. **架構改進建議** - 當前架構的弱點與優化方向
2. **模組擴展建議** - 如何擴展現有模組（前端路由、Redux 充分使用）
3. **技術債務清單** - 優先順序排列的技術債務
4. **效能優化方向** - 可能的效能瓶頸與優化策略
5. **MLOps 成熟度提升** - 從 Phase 4.5 前進到 Phase 5.5/6 的建議路徑
6. **代碼品質改進** - 測試覆蓋、類型安全、錯誤處理的建議

---

## 關鍵檔案位置參考

| 類別 | 檔案 |
|------|------|
| 主入口 | `src/alphapulse/main.py` |
| 訓練伺服器 | `training/train_server.py` |
| 前端入口 | `frontend/src/App.tsx` |
| Docker Compose | `infra/docker-compose.yml` |
| Terraform | `infra/terraform/environments/prod/main.tf` |
| K3s 部署 | `infra/k3s/base/kustomization.yaml` |
| 測試配置 | `pytest.ini` |
| 環境變數 | `.env.example` |
