# Frontend-Backend API Interface

**Base URL**: `/api/v1`
**Authentication**: Bearer Token (JWT) in `Authorization` header.

---

## 1. Authentication & Security

### Login
- **Endpoint**: `POST /auth/login`
- **Response**: `{ "access_token": "...", "role": "admin", "model_version": "v2.4.1-prod" }`

---

## 2. Interactive Simulation (Strategy Playground)

### Run Quick Backtest
- **Endpoint**: `POST /simulation/backtest`
- **Request**:
  ```json
  {
    "risk_level": 5,
    "confidence_threshold": 0.75,
    "stop_loss_pct": 0.05
  }
  ```
- **Response**:
  ```json
  {
    "equity_curve": [
      { "day": 0, "value": 10000, "benchmark": 10000 },
      { "day": 1, "value": 10200, "benchmark": 10150 }
    ]
  }
  ```

---

## 3. MLOps & Observability [Implemented Structures]

### Pipeline Health
- **Endpoint**: `GET /ops/pipeline-status`
- **Response**:
  ```json
  {
    "stages": [
      { "id": "ingest", "label": "Data Ingestion", "status": "success" },
      { "id": "train", "label": "Model Training", "status": "running" }
    ],
    "last_retrained": "2026-01-15T10:00:00Z"
  }
  ```

### Data Drift (PSI)
- **Endpoint**: `GET /ops/drift-analysis`
- **Response**:
  ```json
  {
    "overall_score": 0.024,
    "features": [
      { "feature": "Sentiment_Score", "drift": 0.24, "alert": true },
      { "feature": "RSI_14", "drift": 0.08, "alert": false }
    ]
  }
  ```

### Model Registry
- **Endpoint**: `GET /models`
- **Response**:
  ```json
  [
    { "version": "v2.4.1", "stage": "Production", "accuracy": "89.2%", "status": "Active" },
    { "version": "v2.5.0-rc1", "stage": "Staging", "accuracy": "91.5%", "status": "Testing" }
  ]
  ```

---

## 4. Market Data & Signals

### Get Latest Signals
- **Endpoint**: `GET /signals`
- **Response**:
  ```json
  [
    { "id": 1, "symbol": "BTC-USD", "type": "BUY", "confidence": 0.89, "timestamp": "..." }
  ]
  ```
