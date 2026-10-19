# OrbStack 本地整合方案

狀態：**核定範圍已完成本機遷移與驗收**。核心服務、容器測試、真實 LLM、停止／重啟保留與核准環境清理均完成；詳細證據與限制見[驗證紀錄](VERIFICATION.zh-TW.md)。變更尚未提交或推送。

## 目標與範圍

以 OrbStack 的 Docker Engine 管理 AlphaPulse 開發環境；Python、Node 套件只安裝在 image build 中。主機僅需 OrbStack、其 Docker/Compose CLI 與 shell。保留現有架構圖與歷史部署設定。

本次包含 PostgreSQL、既有 FastAPI 應用程式、React 靜態前端、容器內回歸與整合測試，以及可選啟動的 Ollama tool-calling agent。Airflow、MLflow、Trainer、MinIO 與 Grafana 的完整流程不在本次驗收範圍；既有設定不等於已遷移驗證。

## 使用介面

專案根目錄新增單一可執行入口 `./alphapulse`：

| 指令 | 行為 |
| --- | --- |
| `setup` | 檢查 OrbStack context、產生本地秘密、build 核心與測試 images |
| `up` | 啟動資料庫、API 與前端，等待健康檢查 |
| `test` | 在容器內跑 agent/security 回歸測試及 API／資料庫／前端 smoke tests；失敗回傳非零 |
| `agent` | 啟動容器 Ollama、按需下載模型，執行真實模型 tool-calling |
| `status` / `logs` | 查看本專案服務狀態與日誌 |
| `down` | 停止並移除本專案容器，保留資料與模型 volumes |
| `help` | 顯示操作說明及支援參數 |

所有 Docker 操作明確使用 `--context orbstack` 與獨立 Compose project，避免切換全域 context 或誤操作其他服務。可支援明確環境變數覆寫埠號、模型，但不可允許秘密被輸出至終端。

## 邊界與安全

- 核心直接依賴使用獨立版本清單，避免透過 legacy `setup.py` 安裝整套 ML；不刪除或假裝已修復歷史 ML 依賴衝突。
- 僅以 loopback 發布必要 API／前端埠；資料庫及 Ollama 儘量不發布主機埠。
- 不使用固定管理密碼或自動建立公開管理者；秘密儲存於被 git 忽略的私有檔案。
- Agent 與容器 Ollama 共用 network namespace，使用容器內 `127.0.0.1`，不放寬既有 transport allowlist。
- 模型結果使用 synthetic fixtures；不得稱為真實行情或完整平台整合。
- 資料庫、模型使用專案專屬具名 volumes；預設操作不刪資料、不執行全域 prune、不掛載 Docker socket 進容器。
- macOS OrbStack 內的 Linux Ollama 需實測 CPU 推論；不得將原生 macOS GPU 效能宣稱為容器效能。

## 驗收與遷移順序

1. Compose config 驗證、shell 語法檢查、image build 成功。
2. 核心服務健康；API health、未授權路由拒絕、資料庫讀寫與前端 HTTP 回應有自動化證據。
3. Agent 與既有選定 security 回歸測試在容器內通過，保留 opt-in live 測試的明確 skip。
4. 真實 Ollama 多步 tool-calling 成功，記錄模型／來源版本與 synthetic 資料性質；失敗不得以 replay 替代宣稱成功。
5. `down` 後重新 `up`，確認資料保留；重複 setup／up 不破壞資料。
6. 最後才移除經使用者核准的兩個工作環境：`../quality-env` 與 `../security-env`。保留共用 Ollama、模型、Node 與 Python。若任一容器驗收失敗，先保留本機環境以利修復。
7. 更新 README、本地使用說明與實際驗證結果，清楚列出通過／未通過／未執行項目。

使用者已核定：本次先完成核心與 LLM；驗收後刪除兩個工作環境，保留共用 Ollama 與模型。後續使用者已授權完成安全修正、驗證後提交並合併主分支；整合結果以 GitHub PR 與主分支紀錄為準。
