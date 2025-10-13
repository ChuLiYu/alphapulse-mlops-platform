# Airflow Migration Verification Guide

Since the automated checks could not be completed, please follow these steps to verify the system manually once your Docker environment is responsive.

## 1. Start Services
Run the following command to rebuild and start the new Airflow-based stack:
```bash
make rebuild
```
*Expected Output*: `airflow-webserver`, `airflow-scheduler`, `postgres`, `minio`, `fastapi`, `mlflow`, and `ollama` services should all confirm "Started".

## 2. Check Service Health
Verify all containers are running:
```bash
make health
```
*Expected Output*: All health checks (Postgres, Airflow, MLflow, MinIO, FastAPI) should pass with a `✓`.

## 3. Access Airflow UI
1. Open [http://localhost:8080](http://localhost:8080)
2. Login:
   - **User**: `airflow`
   - **Password**: `airflow`
3. You should see the following DAGs:
   - `btc_price_ingestion`
   - `news_ingestion`
   - `news_sentiment_analysis`
   - `feature_integration`
   - `model_training`

## 4. Test Run
Trigger the **`news_ingestion`** DAG first to ensure database connectivity and internet access.
1. Click the "Play" button (▶️) on the `news_ingestion` row.
2. Click "Trigger DAG".
3. Click on the DAG name to view the "Grid" or "Graph" view.
4. Verify that tasks turn **Dark Green** (Success).

## 5. View Logs (Debugging)
If a task fails (Red):
1. Click on the failed task box.
2. Click "Logs" in the top tab.
3. Look for error messages.

## Common Issues & Fixes
- **Docker I/O Error**: Restart Docker Desktop or Reboot your Mac.
- **Port Conflicts**: Ensure port 8080 is not used by another app.
- **Database Connection**: Run `make db-migrate` if you see table missing errors.
