# AlphaPulse - Installation & Local Development

## Prerequisites
- Docker & Docker Compose
- Terraform >= 1.6
- AWS CLI (configured)
- Python 3.12 (for local testing)

## Setup Steps
1. **Clone & Config**
   ```bash
   git clone <repo-url>
   cp .env.example .env.local
   ```
2. **Launch Services**
   ```bash
   cd infra
   docker compose up -d
   ```
3. **Verify**
   - Airflow: http://localhost:8080
   - MLflow: http://localhost:5001
   - API: http://localhost:8000

## Data Backfill
To populate the system with 8 years of data:
```bash
docker exec -it trainer python /app/scripts/data/backfill_prices.py
```
