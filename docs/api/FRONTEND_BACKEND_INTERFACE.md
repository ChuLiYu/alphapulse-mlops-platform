# Frontend-Backend API Interface

**Base URL**: `/api`
**Authentication**: Bearer Token (JWT) in `Authorization` header.

---

## 1. Authentication

### Login
- **Endpoint**: `POST /auth/login`
- **Request**:
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```
- **Response (200)**:
  ```json
  {
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer",
    "expires_in": 1800
  }
  ```

### Get Current User
- **Endpoint**: `GET /auth/me`
- **Response (200)**:
  ```json
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "is_superuser": true
  }
  ```

---

## 2. Market Data (Prices)

### Get Historical Prices
- **Endpoint**: `GET /prices/{symbol}`
- **Parameters**:
  - `days` (int, default=7): History range in days.
  - `limit` (int, optional): Max records.
- **Response (200)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "symbol": "BTC-USD",
        "timestamp": "2026-01-15T12:00:00Z",
        "price": "95000.50",
        "volume": "120.5"
      }
    ],
    "total": 100
  }
  ```

### Get Price Statistics
- **Endpoint**: `GET /prices/{symbol}/stats`
- **Parameters**: `days` (default=30)
- **Response (200)**:
  ```json
  {
    "symbol": "BTC-USD",
    "prices": {
      "latest": "95000.50",
      "minimum": "92000.00",
      "maximum": "98000.00",
      "average": "94500.25"
    },
    "changes": {
      "percentage": "3.25"
    }
  }
  ```

---

## 3. Trading Signals

### Get Latest Signal
- **Endpoint**: `GET /signals/{symbol}/latest`
- **Response (200)**:
  ```json
  {
    "success": true,
    "data": {
      "id": 101,
      "symbol": "BTC-USD",
      "signal_type": "BUY",
      "confidence": "0.8950",
      "price_at_signal": "94800.00",
      "timestamp": "2026-01-15T14:30:00Z"
    }
  }
  ```

### Get Signal Statistics
- **Endpoint**: `GET /signals/{symbol}/stats`
- **Response (200)**:
  ```json
  {
    "total_signals": 50,
    "buy_signals": 30,
    "sell_signals": 15,
    "hold_signals": 5,
    "avg_confidence": "0.7500"
  }
  ```

---

## 4. Technical Indicators

### Get Indicators
- **Endpoint**: `GET /indicators/{symbol}`
- **Parameters**: `days` (default=7)
- **Response (200)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "timestamp": "2026-01-15T12:00:00Z",
        "rsi_14": "65.5",
        "macd": "120.5",
        "bb_upper": "96000.00",
        "bb_lower": "93000.00"
      }
    ]
  }
  ```

---

## 5. System Health

### Metrics
- **Endpoint**: `GET /health/metrics`
- **Response (200)**:
  ```json
  {
    "status": "healthy",
    "metrics": {
      "uptime": { "seconds": 3600 },
      "cpu_usage": { "percent": 45.2 },
      "memory_usage": { "percent": 60.1 }
    }
  }
  ```
