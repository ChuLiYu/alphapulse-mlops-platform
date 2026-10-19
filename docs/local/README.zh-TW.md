# 本地開發：OrbStack 單一入口

本方案把 AlphaPulse 的核心服務與測試工具放進 OrbStack 容器。主機不需要安裝專案用的 pip 或 npm 套件。

## 操作方式

在專案根目錄執行：

```bash
./alphapulse setup
./alphapulse up
./alphapulse test
```

`setup` 負責檢查 Docker／Compose、建立本地設定及 build images；`up` 啟動資料庫、API、前端；`test` 在容器內跑離線回歸與核心服務整合檢查。設定失敗或測試失敗會回傳非零。

預設開啟 [前端](http://127.0.0.1:3000) 與 [API 文件](http://127.0.0.1:8000/api/docs)。API 健康檢查為 `http://127.0.0.1:8000/health`。不會自動建立管理者或預設登入密碼；受保護的資料路由需要授權。整合測試會建立及移除自己的測試使用者，不會留下可登入的共用帳號。

第一次使用須先安裝並啟動 [OrbStack](https://docs.orbstack.dev/install)。此入口明確選用 `orbstack` context，不會替你安裝或切換其他 Docker 環境。

真實 LLM tool-calling 另行啟動：

```bash
./alphapulse agent
```

預設模型為 `qwen3:4b`；可用 `OLLAMA_MODEL=模型名稱 ./alphapulse agent` 覆寫。0.6b 在本次測試未完成完整工具鏈，不建議以它作為已驗證替代。小模型的工具選擇與摘要品質仍須另行驗證，不能由模型大小推定成功。埠號與預設模型可在 `.env.orbstack.local` 調整；修改埠號後重新執行 `up`。

這會使用容器中的 Ollama，模型保存在專案 volume。首次執行需要下載模型，後續可重用；macOS 上 Linux 容器推論主要使用 CPU，因此不要將本機原生 Ollama 的 GPU 速度當成容器速度。模型呼叫與測試會消耗時間；離線測試通過不等於真實模型測試通過。

OrbStack 容器預設使用 2 條推論執行緒，本機實測可完成 4b 工具鏈；速度與可用記憶體仍依主機而異。CPU 推論執行緒可用 `OLLAMA_NUM_THREAD=2 ./alphapulse agent` 設定；接受 1–32，此容器入口未設定時採用 2；直接執行 Python client 而未設定或傳空值時由 Ollama 自動決定。這個參數只影響推論資源，不改變工具權限或時間限制。

日常管理也使用同一入口：

```bash
./alphapulse status
./alphapulse logs
./alphapulse down
./alphapulse help
```

`down` 保留資料與模型；下次用 `up` 重新啟動。不要以 `docker system prune --volumes` 當成專案清理方式，它可能影響其他專案。

第一次使用依序執行 `setup`、`up`、`test`；修改 Python 依賴、前後端程式或測試後，重新執行 `setup` 與 `up`，再跑測試。程式碼會封裝進 image，不掛載主機的套件目錄，也不會即時熱更新。

## 範圍與資料

- 這是 **PostgreSQL＋既有 FastAPI＋React 前端＋容器測試** 的本地核心環境。
- 獨立 agent 與 Ollama 整合，但 agent 仍使用 **synthetic fixtures**，不會讀寫核心資料庫或觸發交易。
- Dashboard 既有 demo／fallback、mock operational responses 仍存在；HTTP 成功不代表每個圖表都接到真實行情。
- 完整 Airflow、MLflow、訓練與歷史雲端部署不屬於本次驗收；其依賴衝突仍須另行處理。
- 本地私密設定由 setup 建立，不應加入 Git，也不要貼到 issue、聊天或截圖。
- 預設停止不刪除 volume。本方案不提供無提示的全域清除操作。

## 遷移與清理

本次已完成核心、離線回歸、真實 LLM 及重啟保留驗收，並移除這次工作所建立的 `../quality-env`、`../security-env`。共用的 Ollama、下載模型、Node、Python 均保留。未來重建只需使用上述容器入口，不必重建主機虛擬環境。

[實際驗證紀錄](VERIFICATION.zh-TW.md)。

完整驗收規格：[OrbStack 遷移計畫](ORBSTACK_MIGRATION.zh-TW.md)。實際通過項目與限制以驗證紀錄為準，不能以這份操作說明推定已測試。

## 依賴安全檢查

重建後執行 `./alphapulse audit`，掃描前端 lockfile 與 API／test 映像實際安裝的 Python 套件；需要連線公告服務。這不包含容器作業系統、Ollama binary 或歷史 ML 訓練環境。[安全修正與驗收](SECURITY_REMEDIATION.zh-TW.md)。
