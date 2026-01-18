#!/bin/sh

APP_URL=${APP_URL:-http://localhost}
AIRFLOW_URL=${AIRFLOW_URL:-http://localhost:8080}
MLFLOW_URL=${MLFLOW_URL:-http://localhost:5002}
GRAFANA_URL=${GRAFANA_URL:-http://localhost:3100}
FASTAPI_URL=${FASTAPI_URL:-http://localhost:8000}
API_URL=${API_URL:-http://localhost:8000}

export APP_URL AIRFLOW_URL MLFLOW_URL GRAFANA_URL FASTAPI_URL API_URL

envsubst < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js

echo "Configuration loaded successfully"
