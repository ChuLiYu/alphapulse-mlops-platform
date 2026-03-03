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
```
