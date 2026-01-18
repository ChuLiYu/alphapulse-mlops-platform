  const config = window.__CONFIG__ || {
    APP_URL: 'http://localhost',
    AIRFLOW_URL: 'http://localhost:8080',
    MLFLOW_URL: 'http://localhost:5002',
    GRAFANA_URL: 'http://localhost:3100',
    FASTAPI_URL: 'http://localhost:8000',
    API_URL: 'http://localhost:8000'
  };

export const SERVICE_URLS = {
    AIRFLOW: config.AIRFLOW_URL,
    MLFLOW: config.MLFLOW_URL,
    GRAFANA: config.GRAFANA_URL,
    FASTAPI_DOCS: `${config.FASTAPI_URL}/api/docs`,
    EVIDENTLY: `${config.FASTAPI_URL}/api/monitoring`,
    API_BASE: config.API_URL,
    HEALTH_CHECK: `${config.API_URL}/api/v1/health`
  };

export default SERVICE_URLS;
