# OrbStack 驗證紀錄

驗證日期：2026-10-18（America/Vancouver）。環境：macOS 上的 OrbStack、`orbstack` Docker context、Linux aarch64。來源為分支 `feat/llm-tool-calling-poc`，HEAD `be0e8f7a4eabb9c80f9051669e76408f3691a6dd` **加上尚未提交的工作目錄變更**；此 SHA 單獨不包含本次遷移。

## 安全升級後的最終驗證

本頁下方保留較早的遷移快照與模型 trace。後續依賴升級與安全修正已重新 build：`./alphapulse setup`、`./alphapulse test`、`./alphapulse audit` 均 exit 0。最終測試 **36 passed、1 skipped**（agent 15+1 skipped、security 17、local 4）；local 4 項包含 PostgreSQL HTTP refresh 輪替及舊 token 重播 401。前端 lockfile 掃描 0 項；API/test 實際安裝 Python 套件均未發現已知漏洞。Pydantic 已升級為 **2.12.5**，FastAPI **0.146.0**。

[安全測試原始輸出](security-test-output.txt) · [套件掃描輸出](security-audit-output.txt) · [修正範圍與剩餘限制](SECURITY_REMEDIATION.zh-TW.md)

最終本機映像：

| Image | Image ID |
| --- | --- |
| API | `sha256:752471d8a33ea7e3c77ee6748bb1e49ddfbc0f9492bc8be8b544b67968b23612` |
| Frontend | `sha256:36c9e10cef58dfede2a6b23ebebd61d3993c170757decb31ddd5059201df860e` |
| Test | `sha256:58d146b7ec6679b802eedf391db3d0c6a514b60308f720987806c2a4f8f892fe` |

瀏覽器確認 Tailwind 4 升級後卡片、demo 圖表與架構展開功能可呈現。非全 UI 自動化驗證。雲端沒有部署，主分支整合以 [PR #3](https://github.com/ChuLiYu/alphapulse-mlops-platform/pull/3) 結果為準。

## 較早的遷移檢查（歷史快照）

| 檢查 | 實際結果 |
| --- | --- |
| `sh -n ./alphapulse`、Compose config | 通過 |
| `./alphapulse setup` | 通過；API、前端、測試 images build 成功；再次執行成功 |
| `./alphapulse up` / 核心服務 | PostgreSQL、API、前端健康 |
| `./alphapulse test` | **30 passed、1 skipped、0 failed**；新增 thinking 過濾後完整整合 exit 0 |
| Agent suite | 16 個測試中 15 passed；1 個 opt-in live unittest 預設跳過 |
| Security suite | 11 passed：認證、權限、API key digest、Compose 與 sentiment 邊界 |
| Local stack suite | 4 passed：API health/401、PostgreSQL 寫入讀回、登入後價格寫入讀回、前端代理與 SPA fallback |
| 前端代理 | `/api/v1/health` 成功；`/api/v1/health/detailed` 回報資料庫 healthy |
| 真實 LLM（最終預設指令） | 通過；qwen3:4b、2 threads，跨回合工具鏈與正式摘要完成，使用 synthetic fixtures |
| 私密設定 | `.env.orbstack.local` 為 0600 且被 Git 忽略；拒絕 symlink；不建立預設管理者 |

測試價格為測試臨時建立的 **synthetic** 資料，測試後清理使用者、權限及資料列。它驗證資料流程，不代表抓取過真實行情。

[完整容器測試輸出](test-output.txt)。三個 suite 刻意使用獨立容器程序，避免認證單元測試的 SQLite 設定污染 PostgreSQL 整合測試。

## 真實模型測試

- `qwen3:4b`：容器 CPU 推論超過單次 120 秒限制，回傳 `incomplete / model_response_error:TimeoutError`，尚未取得工具結果。
- `qwen3:0.6b`（預設 thinking）：同樣超時，記為失敗，不使用 replay 取代。
- 後續調整：chat request 明確傳送 `think: false`，並加入請求契約斷言；保留工具順序限制、120 秒逾時及呼叫預算。[Ollama thinking API 說明](https://github.com/ollama/ollama/blob/main/docs/capabilities/thinking.mdx)。關閉 thinking 後，0.6b 曾先呼叫 evaluate_snapshot，被順序檢查拒絕；之後取得 snapshot，但下一回合逾時。[0.6b 失敗 trace](llm-06b-failed.json)。4b 自動執行緒仍在第一回合逾時：[失敗 trace](llm-4b-failed.json)。
- 效能診斷：新增可選 `OLLAMA_NUM_THREAD`（1–32；空值使用 Ollama 自動設定），以 2 threads 測試容器 CPU 推論；**真實測試完成（exit 0）**：第 1 回合 get_snapshot、第 2 回合以回傳 ID 呼叫 evaluate_snapshot、第 3 回合回覆摘要。[完整工具 trace 與正式答案](llm-4b-thread2.json)。人工對照摘要：missing_ratio 0.02 > 0.01、drift_psi 0.31 > 0.2、age_minutes 90 > 60；三項皆超標，status review，來源 synthetic-fixture，未宣稱實際市場資料。
- 模型在 content 欄位混入 thinking 前綴；上述證據明確標記移除該前綴，工具 trace 和指標不變。client 已補上標記過濾：最後一個 `</think>` 前的內容丟棄，未閉合 `<think>` 則丟棄 content；工具呼叫保留。這是已知標記的協定正規化，無法保證辨識沒有標記的推理文字。最終重建映像以不帶額外環境變數的 `./alphapulse agent` 再測 **exit 0 / completed**，再次得到跨回合 get_snapshot → evaluate_snapshot → 正式摘要，無 thinking 標記，三個數值與 review 狀態經人工核對正確。[最終原生輸出](llm-final.json)。

最終容器回報 Ollama `0.40.6`，qwen3:4b（Q4_K_M）完整 model digest：`359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7`。

Agent 資料來源為程式內 `synthetic-fixture`，與 PostgreSQL、前端及真實監控分離。工作完成狀態不等於模型摘要一定正確。

## 映像追溯

以下為本次 build 的 image ID；API / 前端 / test 為本機 image，沒有遠端 RepoDigest。

| Image | 已驗證 ID / digest |
| --- | --- |
| API | `sha256:eb2797914f2af24f5b8a41a3b1a995601e6171b6d898199f8ff0f766c992f897` |
| Frontend | `sha256:75dd08d25e21a3e1c086d8feea2ceebcee57bdd406e4f3d92ccb1953c87fa93d` |
| Test（thinking 過濾與 thread 控制） | `sha256:1c7b9f2da1138c00c91cd1606195371dd4be38cdf79f2802b4f7c1686a46f4e7` |
| `postgres:15-alpine` | `postgres@sha256:f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81` |
| `ollama/ollama:0.40.6` | `ollama/ollama@sha256:265409e1d931028a8f7d5a32bcbafddd7bffbc6cc629d77efe9560adf692a5e7` |

Dockerfile 使用 `node:22-alpine`、`nginx:stable-alpine`、`python:3.12-slim`。這些 tag 會更新，未來 rebuild 可能產生不同結果；依賴版本清單和前端 lockfile不代表所有作業系統與間接依賴都已完整鎖定。

## 資料保留與清理

PostgreSQL 合成 probe 值通過 `down → up` 保留驗證，之後刪除 probe table。修正 `down` 後也確認所有 profile 容器均移除、network 移除；兩個具名 volumes 保留，核心服務重啟健康，Ollama 重啟後模型仍可列出。[持久化檢查紀錄](persistence-output.txt)。

最終容器與真實模型驗收通過後，已再次確認非 symlink、realpath 與 pyvenv.cfg，僅刪除 `../quality-env`、`../security-env`；刪除後確認兩者不存在。共用 Ollama、模型、Python 與 Node 未移除。[清理紀錄](cleanup-output.txt)。

收尾時 PostgreSQL、API 與前端皆 healthy；Ollama 服務保留運行，已卸載記憶體中的 4b 模型釋放資源，模型 volume 不變。

## 歷史快照當時的限制（套件／提交狀態以頁首最新驗證及 PR 為準）

- 前端 `npm ci` 回報 **35 項既有弱點：1 low、9 moderate、25 high**。Build 成功不代表依賴弱點已修復；需要另做相容性升級及安全驗證。
- API 依現有 ORM schemas 使用 Pydantic 1.10.21；本次修正 health schemas 的設定相容性，不代表全專案已完成 Pydantic 2 遷移。
- 目前測試沒有驗證每個 UI 互動或每個 API；dashboard 既有 mock/fallback 仍存在。
- Airflow、MLflow、訓練與歷史雲端部署未在本次遷移驗收。未宣稱 production ready，也未完成全 repo 安全稽核。
- 主機未安裝新的專案 pip/npm 套件。共用 macOS Ollama、原生模型、Python 與 Node 依核准範圍保留。
- 未 commit、push 或 merge；主分支沒有因這次工作而更新。
