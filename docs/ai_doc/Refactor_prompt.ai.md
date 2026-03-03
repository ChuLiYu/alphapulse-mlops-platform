# AlphaPulse — WealthTech DE Repositioning & Refactor Prompt

> **給 AI Agent 的指令文檔**
> 這份文檔描述了針對加拿大 WealthTech Data Engineer 職缺的定位調整任務。
> Agent 請按照順序執行各任務，每個任務完成後輸出變更摘要。

---

## 🎯 背景與目標

### 當前問題

AlphaPulse 目前的定位是「Crypto 量化交易 MLOps 平台」，這對加拿大 WealthTech 公司（Wealthsimple、Questrade、Neo Financial、CI Direct Investing）的 **Data Engineer** 職缺有兩個致命傷：

1. **Crypto 標籤**：讓 Hiring Manager 聯想到高風險/監管灰色地帶
2. **MLOps 標籤**：讓人誤判應徵者是 ML Engineer，不是 Data Engineer

### 目標定位

> **"Production-Grade DataOps & MLOps Platform for Financial Market Data"**

核心轉變：**「懂 FinOps 的 Data Engineer，剛好也會 ML」**，而非「會架 ML 平台的工程師」。

### 不需要改的事

- 核心程式碼架構 ✅
- 技術選型（Airflow、Postgres、MinIO、Terraform）✅
- FinOps 故事（$11/mo → $0/mo）✅
- Pydantic v2 / Decimal 精度設計 ✅

---

## 📋 任務清單

---

### Task 1：重寫 README.md — 開頭定位段落

**目標檔案**：`README.md`

**要求**：
將 README 最頂部的 title 與 description 替換為以下內容（可微調措辭，但核心訊息不能改）：

```markdown
# AlphaPulse — Production-Grade DataOps & MLOps Platform

AlphaPulse is an end-to-end **DataOps & MLOps platform** engineered for financial market data —
featuring production-grade ELT pipelines, financial-precision data modeling, and cloud-agnostic
infrastructure built with Terraform, Airflow, and Kubernetes.

Originally built as a zero-cost alternative to commercial MLOps solutions, AlphaPulse demonstrates
how modern data engineering practices (Medallion Architecture, data contracts, CI/CD for data) can
be applied to high-frequency financial time-series across multiple asset classes (Equities & Crypto).

🚀 Live Demo: https://alphapulse.luichu.dev/
```

**注意**：

- 移除「quantitative crypto trading」這個 phrase，改為「financial market data」或「multi-asset market data」
- 保留 Live Demo 連結

---

### Task 2：重構 README — 🌟 Senior Engineering Highlights 排序

**目標檔案**：`README.md`

**要求**：
將 `🌟 Senior Engineering Highlights` 區塊的排序改為以下順序，並更新各項標題與描述：

#### Highlight 1（原本是 #2）：High-Performance Data Engineering & ELT Pipeline

```markdown
### 1. High-Performance Data Engineering & ELT Pipeline

**Challenge:** Ingesting and processing 8+ years of high-frequency multi-asset market data
on resource-constrained ARM64 instances without OOM failures.

**Solution:**

- Engineered production Apache Airflow DAGs with **Chunked SQL Loading** and strict
  **Type Downcasting**, reducing memory footprint by 50%.
- Implemented **Medallion Architecture** (Bronze → Silver → Gold) using MinIO (raw ingestion),
  PostgreSQL (validated staging), and dbt (feature marts & reporting layers).
- Applied **Pydantic v2** as a Data Contract layer for strict schema validation at every
  pipeline boundary.

**Impact:** Full 8-year history training on 24GB RAM without disk swapping.
Transparent data lineage from raw API response to ML feature.

**Keywords:** ELT, Data Modeling, Airflow DAG, Data Contract, Data Lineage, Idempotency
```

#### Highlight 2（新增）：Industrial-Grade Fintech Data Precision

```markdown
### 2. Industrial-Grade Fintech Data Precision & Data Quality

**Challenge:** Financial calculations are unforgiving — floating-point errors in trading
simulations directly translate to incorrect PnL reporting.

**Solution:**

- Enforced **`Decimal` types** for all monetary values platform-wide, preventing IEEE 754
  floating-point drift in simulations and backtests.
- Used **Pydantic v2** for runtime data validation as a lightweight Data Contract,
  catching schema violations at pipeline ingestion before they propagate downstream.
- Implemented **Walk-Forward Cross-Validation** and Anti-Overfitting Gates to ensure
  no look-ahead bias in model training data.

**Keywords:** Financial Precision, Data Integrity, Data Quality, Data Contracts,
Zero Floating-Point Error, Schema Validation
```

#### Highlight 3（原本是 #1）：Zero-Cost FinOps & Cloud-Agnostic Infrastructure

```markdown
### 3. Zero-Cost FinOps & Cloud-Agnostic Infrastructure

**Challenge:** Demonstrate production-grade cloud infrastructure without multi-cloud costs.

**Solution:**

- Engineered a **Provider-Agnostic Terraform abstraction layer** — the system can be
  migrated from Oracle Cloud to AWS EKS or GCP GKE by changing a single Terraform variable.
- OCI Always Free is used purely as a **zero-cost FinOps sandbox** for validation.
- Achieved full stack hosting (4 vCPUs, 24GB RAM) at **$0/month** (migrated from AWS ~$11/mo).

**FinOps Journey:** AWS EC2/RDS ($11/mo) → ARM64 Refactor → Oracle Cloud Always Free ($0/mo)

**Keywords:** FinOps, IaC, Terraform, Cloud-Agnostic, Cost Optimization, ARM64
```

#### Highlight 4（原本是 #3）：MLOps & Model Orchestration

```markdown
### 4. MLOps & Model Orchestration (Downstream of Data)

> ML is a consumer of the data platform — not the platform itself.

**Solution:**

- **MLflow** for experiment tracking, model registry, and artifact versioning.
- **Iterative Trainer** with AutoML (Optuna hyperparameter search) and
  Walk-Forward Cross-Validation for time-series robustness.
- **Evidently AI** for data drift monitoring in production.
- Multi-model ensemble: CatBoost, XGBoost, LightGBM, Scikit-learn.

**Keywords:** MLOps, Model Registry, Feature Store, Experiment Tracking, Data Drift
```

---

### Task 3：新增 dbt Medallion Architecture 實作

**目標目錄**：`dbt/` （新建目錄）

**要求**：建立以下 dbt 最小可行結構：

```
dbt/
├── dbt_project.yml
├── profiles.yml.example
├── models/
│   ├── staging/               # Silver Layer — cleaned & typed
│   │   ├── stg_ohlcv.sql
│   │   ├── stg_trading_signals.sql
│   │   └── schema.yml         # dbt tests: not_null, unique, accepted_values
│   ├── marts/                 # Gold Layer — feature tables & reporting
│   │   ├── fct_market_features.sql
│   │   ├── fct_signal_performance.sql
│   │   └── schema.yml
│   └── sources.yml            # Bronze → Silver source definition
├── tests/
│   └── assert_no_negative_price.sql   # Custom data quality test
└── README.md
```

**各檔案說明**：

**`dbt_project.yml`**：

```yaml
name: "alphapulse"
version: "1.0.0"
config-version: 2

profile: "alphapulse"

model-paths: ["models"]
test-paths: ["tests"]

models:
  alphapulse:
    staging:
      materialized: view
    marts:
      materialized: table
```

**`models/sources.yml`**（Bronze 層定義）：

```yaml
version: 2
sources:
  - name: raw
    description: "Bronze layer — raw market data ingested by Airflow"
    schema: public
    tables:
      - name: prices
        description: "Raw OHLCV data from market data APIs"
        columns:
          - name: id
            tests: [unique, not_null]
          - name: close_price
            tests: [not_null]
          - name: timestamp
            tests: [not_null]
```

**`models/staging/stg_ohlcv.sql`**（Silver 層）：

```sql
-- Silver Layer: Cleaned & typed OHLCV data
-- Enforces Decimal precision and removes anomalies

with source as (
    select * from {{ source('raw', 'prices') }}
),

cleaned as (
    select
        id,
        symbol,
        timestamp::timestamptz                    as price_timestamp,
        open_price::numeric(20, 8)                as open_price,
        high_price::numeric(20, 8)                as high_price,
        low_price::numeric(20, 8)                 as low_price,
        close_price::numeric(20, 8)               as close_price,
        volume::numeric(30, 8)                    as volume,
        current_timestamp                         as _dbt_updated_at
    from source
    where close_price > 0           -- Basic anomaly filter
      and volume >= 0
      and high_price >= low_price   -- Data integrity check
)

select * from cleaned
```

**`models/staging/schema.yml`**：

```yaml
version: 2
models:
  - name: stg_ohlcv
    description: "Silver layer OHLCV — cleaned, typed, anomaly-filtered"
    columns:
      - name: id
        tests: [unique, not_null]
      - name: close_price
        tests: [not_null]
      - name: price_timestamp
        tests: [not_null]
```

**`models/marts/fct_market_features.sql`**（Gold 層）：

```sql
-- Gold Layer: Feature mart for ML training
-- Computes rolling statistics for feature engineering

with ohlcv as (
    select * from {{ ref('stg_ohlcv') }}
),

features as (
    select
        symbol,
        price_timestamp,
        close_price,

        -- Rolling returns
        (close_price - lag(close_price, 1) over w) / lag(close_price, 1) over w
            as return_1d,
        (close_price - lag(close_price, 7) over w) / lag(close_price, 7) over w
            as return_7d,

        -- Volatility proxy
        stddev(close_price) over (
            partition by symbol
            order by price_timestamp
            rows between 29 preceding and current row
        ) as volatility_30d,

        -- Volume trend
        avg(volume) over (
            partition by symbol
            order by price_timestamp
            rows between 6 preceding and current row
        ) as avg_volume_7d

    from ohlcv
    window w as (partition by symbol order by price_timestamp)
)

select * from features
where return_1d is not null
```

**`tests/assert_no_negative_price.sql`**（自訂資料品質測試）：

```sql
-- Custom dbt test: No negative prices allowed in staging
-- Returns rows that FAIL the test (dbt convention)

select id, symbol, close_price, price_timestamp
from {{ ref('stg_ohlcv') }}
where close_price < 0
```

**`dbt/README.md`**：

````markdown
# AlphaPulse dbt — Medallion Architecture

## Architecture

| Layer  | Storage               | Description                                    |
| ------ | --------------------- | ---------------------------------------------- |
| Bronze | MinIO / Raw PG tables | Raw ingested data — append only, no transforms |
| Silver | PostgreSQL (stg\_\*)  | Cleaned, typed, anomaly-filtered via dbt       |
| Gold   | PostgreSQL (fct\_\*)  | Feature marts for ML training & reporting      |

## Running dbt

```bash
# Install
pip install dbt-postgres

# Configure connection
cp profiles.yml.example ~/.dbt/profiles.yml

# Run all models
dbt run

# Run tests (Data Quality)
dbt test

# Generate lineage docs
dbt docs generate && dbt docs serve
```
````

## Data Quality Tests

- `not_null` / `unique` on all primary keys
- `close_price > 0` — no negative prices
- `high_price >= low_price` — OHLCV integrity
- Custom SQL tests in `tests/`

````

---

### Task 4：更新 Airflow DAG — 加入 dbt 觸發步驟

**目標**：在現有 Airflow ETL DAG 的最後加入 `dbt run` 觸發步驟

**在現有 DAG 的最後一個 task 之後，加入**：

```python
from airflow.operators.bash import BashOperator

# 在 DAG 定義中加入
dbt_run = BashOperator(
    task_id='dbt_transform_silver_to_gold',
    bash_command=(
        'cd /opt/airflow/dbt && '
        'dbt run --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt'
    ),
    dag=dag,
)

dbt_test = BashOperator(
    task_id='dbt_data_quality_tests',
    bash_command=(
        'cd /opt/airflow/dbt && '
        'dbt test --profiles-dir /opt/airflow/dbt --project-dir /opt/airflow/dbt'
    ),
    dag=dag,
)

# 串接到現有最後一個 task
# 範例：existing_last_task >> dbt_run >> dbt_test
````

**DAG 完成後應有以下流程**：

```
[Ingest API Data] → [Validate with Pydantic] → [Load to Postgres (Bronze)]
    → [dbt run: Bronze→Silver→Gold] → [dbt test: Data Quality Gate]
    → [Trigger ML Training]
```

---

### Task 5：新增 README — Data Engineering 專屬章節

**目標檔案**：`README.md`

在 Tech Stack 表格之後，新增以下章節：

````markdown
## 🏛️ Data Architecture — Medallion Design

\```
┌─────────────────────────────────────────────────────────────┐
│ BRONZE (Raw) SILVER (Staged) GOLD (Mart) │
│ │
│ MinIO / PG raw ──► dbt stg_ohlcv ──► fct_features │
│ (Airflow ETL) (Cleaned+Typed) (ML-Ready) │
│ │
│ Pydantic v2 dbt tests dbt tests │
│ (ingestion gate) (schema & quality) (business rules) │
└─────────────────────────────────────────────────────────────┘
\```

**Data Flow:**

1. **Airflow** ingests raw OHLCV & signal data → MinIO (Bronze)
2. **Pydantic v2** validates schema at ingestion boundary (Data Contract)
3. **dbt staging models** clean, type-cast, and filter anomalies (Silver)
4. **dbt mart models** compute rolling features for ML consumption (Gold)
5. **dbt tests** act as automated Data Quality gates at each layer
6. **ML Trainer** consumes only from Gold layer — never touches raw data

**Idempotency Strategy:**
All Airflow tasks use UPSERT (INSERT ... ON CONFLICT DO UPDATE) to ensure
safe retries without data duplication.
````

---

### Task 6：更新 README — 🎯 Role-Specific Navigation 表格

**目標檔案**：`README.md`

將現有的 Role 表格替換為：

```markdown
## 🎯 Role-Specific Navigation

| If you are a...       | Start here                                                                                           |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| **Hiring Manager**    | [FinOps Journey](#finops) · [Architecture Overview](#arch)                                           |
| **Data Engineer**     | [Medallion Architecture](#medallion) · [dbt Models](./dbt/) · [Airflow DAGs](./airflow/)             |
| **Data Analyst**      | [Gold Layer Feature Mart](./dbt/models/marts/) · [Dashboard](https://alphapulse.luichu.dev/)         |
| **Platform / DevOps** | [Terraform IaC](./infra/terraform/) · [K3s Setup](./infra/k3s/) · [CI/CD](./.github/workflows/)      |
| **ML Engineer**       | [Iterative Trainer](./training/) · [MLflow Registry](./docs/) · [Feature Store](./dbt/models/marts/) |
```

---

### Task 7：新增 docs/DATA_ENGINEERING.md

**目標**：新建一份給 Data Engineering 面試官看的深度文檔

````markdown
# Data Engineering Deep Dive

## Architecture Decisions

### Why Medallion Architecture?

Financial data pipelines require strict separation between:

- **Immutable raw data** (audit trail, regulatory compliance)
- **Validated staging data** (downstream safety)
- **Business-logic marts** (stable contracts for ML/Analytics)

This mirrors production patterns at WealthTech companies where
raw transaction logs must be preserved for regulatory audits,
while downstream teams consume only validated, typed data.

### Why dbt for Transformation?

- **Version-controlled SQL** — all transformations are auditable via Git
- **Built-in testing** — data quality is enforced, not assumed
- **Lineage documentation** — `dbt docs` generates auto-updated DAG lineage
- **Idiomatic for modern data stacks** — standard at Wealthsimple, Questrade, etc.

### Why Pydantic v2 as Data Contract?

At the pipeline ingestion boundary, before any data touches the database,
Pydantic models enforce:

- Field types (str, Decimal, datetime)
- Value ranges (price > 0, volume >= 0)
- Required vs optional fields

This acts as a lightweight **Data Contract** — downstream consumers
can trust that Silver layer data conforms to a known schema.

---

## Scalability Considerations

### Current State

- Single-node PostgreSQL, suitable for research & MVP
- Handles 8+ years of OHLCV data for ~50 symbols

### Production Scale Path (TB-level)

If daily transaction volumes reach TB scale (e.g., full Wealthsimple user base):

1. **Columnar Storage**: Migrate Gold layer to Snowflake or BigQuery
   - Terraform abstraction layer already supports this — change one variable
   - dbt models require zero changes (standard SQL)

2. **Partitioning Strategy**: Partition by `(symbol, year)` for time-series query optimization

3. **Streaming Layer**: Add Kafka → Spark Structured Streaming for real-time PnL
   - Batch Airflow DAG remains for daily feature recomputation
   - Streaming path handles low-latency user-facing metrics

### Idempotency & Fault Tolerance

All Airflow tasks implement UPSERT strategy:

```sql
INSERT INTO prices (...) VALUES (...)
ON CONFLICT (symbol, timestamp) DO UPDATE SET ...
```
````

DAG retries are safe — no duplicate data, no partial writes.

---

## Data Quality Framework

| Layer  | Tool            | What's Validated                      |
| ------ | --------------- | ------------------------------------- |
| Bronze | Pydantic v2     | Schema, types, required fields        |
| Silver | dbt tests       | not_null, unique, value ranges        |
| Gold   | dbt tests       | Business rules, referential integrity |
| Model  | Walk-Forward CV | No look-ahead bias in training data   |

---

## Financial Data Precision

IEEE 754 floating-point arithmetic is unsuitable for financial calculations:

```python
# Problematic
0.1 + 0.2 == 0.3  # False in floating-point

# AlphaPulse approach
from decimal import Decimal
Decimal('0.1') + Decimal('0.2') == Decimal('0.3')  # True
```

All monetary values (prices, PnL, portfolio weights) use Python `Decimal`
and PostgreSQL `NUMERIC(20, 8)` — matching industry standards for
financial data systems.

```

---

## ✅ 完成標準 (Definition of Done)

Agent 完成所有任務後，請確認：

- [ ] `README.md` 標題與 description 已更新（無 "crypto trading" / "MLOps Platform" 作為主標籤）
- [ ] `README.md` Highlights 排序：Data Pipeline 第一，ML 最後
- [ ] `dbt/` 目錄已建立，含完整 Bronze/Silver/Gold 模型
- [ ] `dbt/tests/` 含至少一個自訂 Data Quality 測試
- [ ] Airflow DAG 末端已加入 `dbt run` + `dbt test` steps
- [ ] `README.md` 新增 Medallion Architecture 圖示章節
- [ ] `docs/DATA_ENGINEERING.md` 已建立
- [ ] 所有 SQL 使用 `NUMERIC(20, 8)` 而非 `FLOAT` 儲存金融數值

---

## 🚫 禁止事項

- **不要刪除任何現有功能**——只新增與重組，不破壞
- **不要改變 Terraform / K3s 配置**——基礎設施不動
- **不要移除 ML 相關代碼**——只是降低其在 README 的敘事優先級
- **不要更改現有 Airflow DAG 的核心邏輯**——只在末端 append dbt tasks

---

## 📌 關鍵詞植入清單（SEO for ATS 系統）

確保以下關鍵詞自然出現在 README 與文檔中：

```

ELT Pipeline, Data Modeling, Medallion Architecture, dbt, Data Lineage,
Data Contract, Data Quality, Idempotency, Financial Precision, Decimal,
NUMERIC, Airflow DAG, Feature Engineering, Walk-Forward Validation,
Terraform, Cloud-Agnostic, FinOps, Cost Optimization, Pydantic v2,
Schema Validation, Data Governance, Batch Processing

```

---

*文檔版本：v1.0 — 針對加拿大 WealthTech Data Engineer 職缺定位*
*策略目標：Wealthsimple · Questrade · Neo Financial · CI Direct Investing*

---

---

# Part 2：Hero Demo — Zero-Cost Dynamic Mock Mode

> **給 AI Agent 的補充指令**
> 目標：在不花任何錢的前提下，讓 alphapulse.luichu.dev 看起來是一個「活著的」系統。
> 後端服務（Airflow、Postgres、MLflow、FastAPI）全部關閉以節省 OCI 資源。
> 前端繼續部署在 OCI Free K3s，透過 Cloudflare 對外提供服務。

---

## 🎯 架構目標

```

現況（付費資源壓力）：
OCI K3s → [React] + [FastAPI] + [Postgres] + [Airflow] + [MLflow] + [Ollama]

目標（Hero Demo Mode）：
OCI K3s → [React Only]
↓
所有數據由前端 Mock Engine 產生
看起來動態，實際上零後端依賴

````

**核心原則：**
- React 前端繼續部署在 OCI K3s（不換平台，不花錢）
- 後端 Pod 全部 scale to 0 或移除 K3s manifests
- 前端內建 `MockDataEngine`，用 `setInterval` 模擬即時數據流
- GitHub Actions 負責 build & push image，自動部署到 K3s

---

## 📋 任務清單

---

### Task 8：建立 MockDataEngine

**目標檔案**：`frontend/src/mock/MockDataEngine.ts`

**要求**：建立一個中央 Mock 數據引擎，所有頁面共用。

```typescript
// frontend/src/mock/MockDataEngine.ts

export interface OHLCVPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingSignal {
  id: string;
  symbol: string;
  direction: 'LONG' | 'SHORT' | 'HOLD';
  confidence: number;        // 0-1
  price: number;
  timestamp: number;
  model: string;
  pnl_pct: number;
}

export interface PipelineRun {
  dag_id: string;
  run_id: string;
  state: 'running' | 'success' | 'failed' | 'queued';
  start_time: number;
  duration_sec: number;
  tasks_done: number;
  tasks_total: number;
}

export interface ModelMetric {
  name: string;
  version: string;
  accuracy: number;
  sharpe: number;
  max_drawdown: number;
  status: 'production' | 'staging' | 'archived';
}

// ─── Price simulation (Geometric Brownian Motion) ───────────────────────────

function gbmStep(price: number, mu = 0.0001, sigma = 0.012): number {
  const dt = 1;
  const z = gaussianRandom();
  return price * Math.exp((mu - 0.5 * sigma ** 2) * dt + sigma * Math.sqrt(dt) * z);
}

function gaussianRandom(): number {
  // Box-Muller transform
  const u = 1 - Math.random();
  const v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// ─── Seed data ───────────────────────────────────────────────────────────────

const SYMBOLS = ['BTC-USD', 'ETH-USD', 'SPY', 'QQQ'];

const SEED_PRICES: Record<string, number> = {
  'BTC-USD': 67420,
  'ETH-USD': 3540,
  'SPY': 528,
  'QQQ': 452,
};

// ─── MockDataEngine class ────────────────────────────────────────────────────

class MockDataEngine {
  private prices: Record<string, number> = { ...SEED_PRICES };
  private history: Record<string, OHLCVPoint[]> = {};
  private listeners: Set<() => void> = new Set();
  private intervalId: ReturnType<typeof setInterval> | null = null;

  // Pipeline state machine
  private pipelineStates: PipelineRun[] = this.generateInitialPipelines();
  private pipelineTick = 0;

  constructor() {
    // Pre-generate 120 historical candles
    for (const sym of SYMBOLS) {
      this.history[sym] = this.generateHistory(sym, 120);
    }
  }

  // ── Subscribe / Unsubscribe ────────────────────────────────────────────────

  subscribe(cb: () => void): () => void {
    this.listeners.add(cb);
    if (!this.intervalId) this.start();
    return () => {
      this.listeners.delete(cb);
      if (this.listeners.size === 0) this.stop();
    };
  }

  private notify() {
    this.listeners.forEach(cb => cb());
  }

  private start() {
    this.intervalId = setInterval(() => {
      this.tick();
      this.notify();
    }, 2000); // Update every 2 seconds
  }

  private stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  // ── Tick: advance simulation ───────────────────────────────────────────────

  private tick() {
    this.pipelineTick++;

    // Advance prices
    for (const sym of SYMBOLS) {
      const newPrice = gbmStep(this.prices[sym]);
      this.prices[sym] = newPrice;

      const prev = this.history[sym].at(-1)!;
      const wiggle = newPrice * 0.003;
      const candle: OHLCVPoint = {
        timestamp: Date.now(),
        open: prev.close,
        high: newPrice + Math.abs(gaussianRandom() * wiggle),
        low: newPrice - Math.abs(gaussianRandom() * wiggle),
        close: newPrice,
        volume: 800000 + Math.random() * 400000,
      };
      this.history[sym].push(candle);
      if (this.history[sym].length > 200) this.history[sym].shift();
    }

    // Advance pipeline state machine
    this.advancePipelines();
  }

  // ── Public data getters ────────────────────────────────────────────────────

  getPrice(symbol: string): number {
    return this.prices[symbol] ?? 0;
  }

  getHistory(symbol: string, limit = 60): OHLCVPoint[] {
    return (this.history[symbol] ?? []).slice(-limit);
  }

  getSignals(): TradingSignal[] {
    return SYMBOLS.map((sym, i) => {
      const price = this.prices[sym];
      const directions: TradingSignal['direction'][] = ['LONG', 'SHORT', 'HOLD'];
      return {
        id: `sig-${sym}-${Math.floor(Date.now() / 10000)}`,
        symbol: sym,
        direction: directions[Math.floor((Math.sin(this.pipelineTick * 0.3 + i) + 1) * 1.4)],
        confidence: 0.55 + Math.abs(Math.sin(this.pipelineTick * 0.2 + i)) * 0.4,
        price,
        timestamp: Date.now(),
        model: ['CatBoost-v3', 'XGBoost-v2', 'LightGBM-v4', 'Ensemble-v1'][i],
        pnl_pct: (Math.sin(this.pipelineTick * 0.15 + i * 1.2) * 4.5),
      };
    });
  }

  getPipelines(): PipelineRun[] {
    return this.pipelineStates;
  }

  getModelMetrics(): ModelMetric[] {
    const base = 0.71 + Math.sin(this.pipelineTick * 0.05) * 0.03;
    return [
      { name: 'CatBoost', version: 'v3.2', accuracy: base + 0.04, sharpe: 1.82, max_drawdown: -0.087, status: 'production' },
      { name: 'XGBoost',  version: 'v2.1', accuracy: base + 0.01, sharpe: 1.61, max_drawdown: -0.112, status: 'staging' },
      { name: 'LightGBM', version: 'v4.0', accuracy: base - 0.01, sharpe: 1.74, max_drawdown: -0.094, status: 'staging' },
      { name: 'Ensemble', version: 'v1.0', accuracy: base + 0.06, sharpe: 1.95, max_drawdown: -0.071, status: 'production' },
    ];
  }

  getPortfolioValue(): number {
    // Simulated portfolio drifting around $125k
    return 125000 + Math.sin(this.pipelineTick * 0.08) * 3200 + gaussianRandom() * 800;
  }

  // ── Pipeline state machine ─────────────────────────────────────────────────

  private generateInitialPipelines(): PipelineRun[] {
    return [
      { dag_id: 'market_data_ingestion',  run_id: 'run_001', state: 'success', start_time: Date.now() - 3600000, duration_sec: 142, tasks_done: 5, tasks_total: 5 },
      { dag_id: 'dbt_silver_gold',        run_id: 'run_002', state: 'running', start_time: Date.now() - 180000,  duration_sec: 0,   tasks_done: 2, tasks_total: 4 },
      { dag_id: 'feature_engineering',    run_id: 'run_003', state: 'queued',  start_time: 0,                    duration_sec: 0,   tasks_done: 0, tasks_total: 6 },
      { dag_id: 'model_retraining',       run_id: 'run_004', state: 'success', start_time: Date.now() - 7200000, duration_sec: 892, tasks_done: 8, tasks_total: 8 },
    ];
  }

  private advancePipelines() {
    // Every ~10 ticks, cycle pipeline states to look alive
    if (this.pipelineTick % 10 === 0) {
      this.pipelineStates = this.pipelineStates.map(p => {
        if (p.state === 'running') {
          const done = p.tasks_done + 1;
          if (done >= p.tasks_total) {
            return { ...p, state: 'success', tasks_done: p.tasks_total, duration_sec: Math.floor(Math.random() * 300 + 100) };
          }
          return { ...p, tasks_done: done };
        }
        if (p.state === 'success' && Math.random() < 0.15) {
          return { ...p, state: 'queued', tasks_done: 0, run_id: `run_${Date.now()}` };
        }
        if (p.state === 'queued' && Math.random() < 0.4) {
          return { ...p, state: 'running', start_time: Date.now() };
        }
        return p;
      });
    }
  }

  // ── Historical generation ──────────────────────────────────────────────────

  private generateHistory(symbol: string, count: number): OHLCVPoint[] {
    const points: OHLCVPoint[] = [];
    let price = SEED_PRICES[symbol];
    const now = Date.now();
    for (let i = count; i >= 0; i--) {
      price = gbmStep(price);
      const wiggle = price * 0.008;
      points.push({
        timestamp: now - i * 60000,
        open: price * (1 + gaussianRandom() * 0.002),
        high: price + Math.abs(gaussianRandom() * wiggle),
        low: price - Math.abs(gaussianRandom() * wiggle),
        close: price,
        volume: 500000 + Math.random() * 600000,
      });
    }
    return points;
  }
}

// Singleton export
export const mockEngine = new MockDataEngine();
````

---

### Task 9：建立 useMockData Hook

**目標檔案**：`frontend/src/mock/useMockData.ts`

```typescript
// frontend/src/mock/useMockData.ts
import { useState, useEffect } from "react";
import { mockEngine } from "./MockDataEngine";

// Generic hook — re-renders whenever MockDataEngine ticks
export function useMockData<T>(selector: () => T): T {
  const [data, setData] = useState<T>(selector);

  useEffect(() => {
    const unsubscribe = mockEngine.subscribe(() => {
      setData(selector());
    });
    return unsubscribe;
  }, []);

  return data;
}

// Convenience hooks per data type
export const usePrices = () =>
  useMockData(() => ({
    "BTC-USD": mockEngine.getPrice("BTC-USD"),
    "ETH-USD": mockEngine.getPrice("ETH-USD"),
    SPY: mockEngine.getPrice("SPY"),
    QQQ: mockEngine.getPrice("QQQ"),
  }));

export const useHistory = (symbol: string, limit?: number) =>
  useMockData(() => mockEngine.getHistory(symbol, limit));

export const useSignals = () => useMockData(() => mockEngine.getSignals());
export const usePipelines = () => useMockData(() => mockEngine.getPipelines());
export const useModels = () => useMockData(() => mockEngine.getModelMetrics());
export const usePortfolio = () =>
  useMockData(() => mockEngine.getPortfolioValue());
```

---

### Task 10：改造前端四個頁面接入 Mock Engine

**原則**：找到每個頁面原本 call API 的地方，替換為對應的 useMock hook。

#### Dashboard.tsx

替換 API call 為：

```typescript
import {
  usePrices,
  useHistory,
  useSignals,
  usePortfolio,
} from "../mock/useMockData";

// 在 component 內
const prices = usePrices();
const btcHistory = useHistory("BTC-USD", 60);
const signals = useSignals();
const portfolio = usePortfolio();
```

新增 **「LIVE」閃爍徽章** 在頁面右上角：

```tsx
<span
  style={{
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    background: "#ff4444",
    color: "white",
    padding: "3px 10px",
    borderRadius: 12,
    fontSize: 12,
    fontWeight: 700,
  }}
>
  <span style={{ animation: "pulse 1.2s infinite" }}>●</span> LIVE
</span>
```

CSS animation（加在 global CSS）：

```css
@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.2;
  }
}
```

#### Trading Signal 頁面

```typescript
import { useSignals } from "../mock/useMockData";
const signals = useSignals();
```

每個 Signal Card 需展示：

- Direction badge（LONG = 綠色、SHORT = 紅色、HOLD = 灰色）
- Confidence bar（animated progress bar）
- PnL %（正數綠色，負數紅色）
- Model name
- 時間戳（"just now" / "2s ago"）

#### MLOps Console 頁面

```typescript
import { usePipelines, useModels } from "../mock/useMockData";
const pipelines = usePipelines();
const models = useModels();
```

Pipeline 列表需展示：

- State badge（running = 藍色旋轉 spinner、success = 綠色、queued = 黃色、failed = 紅色）
- Progress bar（tasks_done / tasks_total）
- DAG name 與 run_id

Model Registry 表格需展示：

- Accuracy / Sharpe / Max Drawdown
- Status badge（production = 綠色、staging = 藍色）

#### Strategy Playground 頁面

使用 `useHistory` 顯示即時更新的 candlestick 或 line chart。
加入以下互動元素（純前端，不需後端）：

- Symbol 切換下拉（BTC-USD / ETH-USD / SPY / QQQ）
- 時間區間切換（15m / 1h / 4h）— 改變 `limit` 參數
- Buy/Sell 按鈕（點擊後彈出 toast "Order simulated — no real trades executed"）

---

### Task 11：Demo Mode Banner

**目標**：在所有頁面頂端加入一條 Banner，告訴訪客這是 Demo Mode。

```tsx
// frontend/src/components/DemoModeBanner.tsx — 更新內容

export function DemoModeBanner() {
  return (
    <div
      style={{
        background: "linear-gradient(90deg, #1a1a2e, #16213e)",
        borderBottom: "1px solid #0f3460",
        padding: "8px 20px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        fontSize: 13,
        color: "#8892b0",
      }}
    >
      <span>
        <span style={{ color: "#64ffda", fontWeight: 700 }}>● DEMO MODE</span> —
        Simulated market data updated every 2s via Geometric Brownian Motion. No
        real trades. No backend.
      </span>
      <a
        href="https://github.com/ChuLiYu/alphapulse-mlops-platform"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: "#64ffda", textDecoration: "none" }}
      >
        View Source →
      </a>
    </div>
  );
}
```

---

### Task 12：關閉後端 K3s Deployments

**目標目錄**：`infra/k3s/base/`

**要求**：找到以下 Deployment manifests，將 `replicas` 改為 `0`：

```yaml
# 對以下所有 deployment 執行相同操作
# airflow-webserver, airflow-scheduler, airflow-worker
# fastapi
# mlflow
# trainer
# ollama
# postgres（可保留或關閉，視 demo 需求）
# minio（可保留或關閉）

spec:
  replicas: 0 # 從原本的 1 改為 0
```

**保留運行的 Pod（replicas: 1）：**

- `frontend`（React）
- `traefik`（Ingress）
- `grafana`（可選，若有靜態看板）

**新增 `infra/k3s/overlays/demo/`** 目錄，建立 Kustomize overlay：

```yaml
# infra/k3s/overlays/demo/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
  - ../../base

patches:
  - path: scale-down-backends.yaml
```

```yaml
# infra/k3s/overlays/demo/scale-down-backends.yaml
# Scale all backend services to 0 for demo mode
- op: replace
  path: /spec/replicas
  value: 0
```

---

### Task 13：更新 GitHub Actions Workflow

**目標檔案**：`.github/workflows/deploy-k3s.yml`

**要求**：新增一個 **`deploy-demo`** job，只 build & deploy 前端：

```yaml
# 在現有 workflows 中新增或修改

name: Deploy Hero Demo

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"
      - "infra/k3s/overlays/demo/**"
  workflow_dispatch:
    inputs:
      mode:
        description: "Deploy mode"
        required: true
        default: "demo"
        type: choice
        options: [demo, full]

jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install & Build
        working-directory: frontend
        run: |
          npm ci
          npm run build
        env:
          VITE_DEMO_MODE: "true"
          VITE_APP_VERSION: ${{ github.sha }}

      - name: Build & Push Docker Image (Frontend only)
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/alphapulse-frontend:demo
            ghcr.io/${{ github.repository_owner }}/alphapulse-frontend:${{ github.sha }}
        # 使用 GitHub Container Registry（免費）

  deploy-demo:
    needs: build-frontend
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to OCI K3s (Frontend only)
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.OCI_HOST }}
          username: ${{ secrets.OCI_USER }}
          key: ${{ secrets.OCI_SSH_KEY }}
          script: |
            # Apply demo overlay — scales backends to 0, keeps frontend
            kubectl apply -k /home/ubuntu/alphapulse/infra/k3s/overlays/demo/

            # Pull and restart frontend only
            kubectl rollout restart deployment/frontend -n application

            # Confirm backends are scaled down
            kubectl scale deployment fastapi airflow-webserver mlflow trainer \
              --replicas=0 -n application

            echo "✅ Demo mode deployed. Only frontend is running."

      - name: Health Check
        run: |
          sleep 30
          curl -f https://alphapulse.luichu.dev/ || exit 1
```

---

### Task 14：新增 Vite 環境變數控制

**目標檔案**：`frontend/.env.demo`

```bash
# frontend/.env.demo
VITE_DEMO_MODE=true
VITE_API_BASE_URL=   # 留空，demo mode 不需要 API
VITE_APP_TITLE=AlphaPulse Demo
```

**目標檔案**：`frontend/src/config.ts`（新建或修改）

```typescript
export const config = {
  isDemoMode: import.meta.env.VITE_DEMO_MODE === "true",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "",
  appVersion: import.meta.env.VITE_APP_VERSION ?? "dev",
} as const;
```

在 `frontend/src/api/client.ts` 加入 Demo Mode guard：

```typescript
import { config } from "../config";

// 在所有 API call 的最頂部加入
if (config.isDemoMode) {
  console.warn("[Demo Mode] API call intercepted — using mock data");
  // Return mock data instead
  return;
}
```

---

## ✅ Part 2 完成標準

- [ ] `MockDataEngine.ts` 建立，GBM 價格模擬正常運作
- [ ] `useMockData` hooks 建立並正確 re-render
- [ ] Dashboard、Signal、MLOps、Strategy 四頁面接入 mock hooks
- [ ] `● LIVE` 閃爍徽章出現在 Dashboard
- [ ] Demo Mode Banner 顯示在所有頁面頂端
- [ ] K3s backend deployments scale to 0（只有 frontend + traefik 在跑）
- [ ] GitHub Actions `deploy-demo` job 只 build/deploy 前端
- [ ] `VITE_DEMO_MODE=true` 時，API client 不發出任何真實 HTTP request
- [ ] `https://alphapulse.luichu.dev/` health check 通過

---

## 🚫 Part 2 禁止事項

- **不要刪除後端代碼**——只是 scale to 0，保留完整代碼供面試官審查
- **不要換平台**——繼續用 OCI Free，不動 Terraform
- **不要用真實 API key**——Mock Engine 完全不需要外部 API
- **不要在 Demo 中顯示假的「真實交易」**——Banner 必須清楚標示 Demo Mode

---

_Part 2 文檔版本：v1.0 — Hero Demo Zero-Cost Dynamic Mock Mode_
_部署目標：OCI Always Free K3s · alphapulse.luichu.dev_
