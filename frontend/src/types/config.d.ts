interface WindowConfig {
  APP_URL: string
  AIRFLOW_URL: string
  MLFLOW_URL: string
  GRAFANA_URL: string
  FASTAPI_URL: string
  API_URL: string
}

declare global {
  interface Window {
    __CONFIG__?: WindowConfig
  }
}

export {};
