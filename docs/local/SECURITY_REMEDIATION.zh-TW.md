# 安全修正與驗收 — 2026-10-18

## 目標與邊界

本次針對 OrbStack 核心 API、React 前端、獨立 LLM agent 與相關 CI／部署腳本檢查已知依賴漏洞與具體的中高風險程式碼。第三方套件的漏洞通知代表特定版本存在已知問題，不代表本專案已遭入侵；是否可被利用還取決於執行路徑、設定與對外暴露方式。

主代理負責規格、整合與文件；三個低用量代理分別處理前端套件、後端依賴、API 安全修正。這是有明確範圍的檢查，不能稱為全庫滲透測試或安全認證。

## 驗收標準

- 前端完整 lockfile 的 npm audit 不得有 moderate／high／critical。
- 已建置 API 與測試映像的完整 Python 安裝清單使用隔離的 pip-audit 掃描；不得隱藏問題或使用 ignore-vuln。
- 新增安全回歸測試；實際 PostgreSQL、登入／權限、價格 Decimal 寫入讀回、前端代理與頁面檢查均需通過。
- 不把密碼插入程式碼、shell 指令或可見的命令參數；產生的 secret 檔案必須私有、忽略追蹤且不可覆寫。
- 本機所有專案依賴仍留在容器內。主分支整合前保留現有 README 更新並通過新 CI。

## 操作

```bash
./alphapulse setup
./alphapulse test
./alphapulse audit
```

`audit` 透過網路查詢當時的公告資料；npm 使用 lockfile，Python 掃描建置映像實際安裝清單。Python 掃描工具裝在臨時容器內的獨立環境，避免安裝掃描工具時順便升級目標套件而遮蔽原本的漏洞。

## CI 與部署

新增核心容器建置／整合測試／依賴掃描工作流。歷史完整 ML 訓練流程因尚有獨立的依賴衝突，保留為手動觸發，不能把核心測試通過說成完整 ML 測試通過。歷史 k3s 部署亦改為手動觸發並使用 production environment，避免合併原始碼就意外部署。

## 資料與功能限制

Agent 仍使用明確標示的 synthetic fixtures，不進行交易或資料庫寫入。Dashboard 保留 mock／fallback 行為。Airflow、MLflow、訓練環境、歷史雲端映像與完整 Git 歷史不屬於本次漏洞清零範圍；本次不部署任何雲端服務。

## 實際修正

| 發現 | 修正與驗證 |
| --- | --- |
| 前端 35 項依賴公告（25 high、9 moderate、1 low） | 升級 Vite、React Router、TypeScript ESLint 與 Tailwind；調整 PostCSS/CSS；乾淨容器安裝、audit 與 build 通過，公告數 0 |
| Python JWT／Starlette 等已知漏洞 | python-jose 改為 PyJWT，明確限定 HS256 與必要 claims；升級 FastAPI/Pydantic 2 與相容套件；API/test 實際安裝清單掃描均無已知漏洞 |
| refresh token 可重播 | 隨機 jti 只存 SHA-256 digest；條件 UPDATE 與新 token 在同一 transaction 提交；重播 401，含 PostgreSQL HTTP 回歸 |
| ops 未認證、health 洩漏原始 DB 錯誤 | ops 必須 bearer 認證；health 回傳固定錯誤訊息 |
| 密碼插入遠端腳本／指令參數 | bcrypt helper 由 stdin 收密碼；secret 檔案 0600、不覆寫、不追蹤；真實 htpasswd 與特殊字元測試通過 |
| 歷史 k3s 固定憑證與加密金鑰 | 改為必要 Secret 引用／移除固定值；既有安裝必須輪替，詳見 infra/k3s/README.md；只做 render，沒有部署 |

## 驗收證據

- `./alphapulse setup`：最終 API、frontend、test 映像重建成功。
- `./alphapulse test`：**36 passed、1 skipped、0 failed**（agent 15+1 skipped、security 17、PostgreSQL/core 4）。[完整輸出](security-test-output.txt)。
- `./alphapulse audit`：前端 **0**；API/test Python 套件均 **No known vulnerabilities found**。[統一指令輸出](security-audit-output.txt)、[前端前後比較](frontend-security-output.txt)、[後端前後比較](backend-security-output.txt)。
- 瀏覽器人工檢查：升級後 dashboard 能呈現卡片、圖表／demo 資料、展開架構區塊，未見整頁樣式失效。沒有宣稱覆蓋所有 UI。
- `kubectl kustomize infra/k3s/base` 與 `git diff --check` 通過；沒有連線雲端叢集。

## 保留限制

「0」僅代表當次公告服務對指定套件清單的結果；不包含容器 OS、Ollama binary、完整 Git 歷史或歷史訓練依賴。登入尚需共享的帳戶/IP rate limit 才可公開暴露；已發出的 access token 最長 30 分鐘內仍有效。歷史 Airflow Deployment 不完整，不能直接視為可部署。JS bundle 仍有體積建議警告，並非安全掃描失敗。先前真實 LLM 工具鏈證據保留於 VERIFICATION.zh-TW.md；本次安全測試不冒充新的 live-model 評估。

CI 相容性修正：設定檔生成容器使用呼叫者的 UID/GID，確保 Linux runner 上的 0600 檔案由執行者擁有；保留私有權限。首次 CI 曾因 root 擁有檔案而失敗，修正後以最新 CI 結果為準。
