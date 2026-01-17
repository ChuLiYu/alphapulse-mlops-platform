import { SystemLog } from '../types';

export type PredefinedLog = Omit<SystemLog, 'id' | 'timestamp'>;

export const PREDEFINED_LOGS: PredefinedLog[] = [
  // --- BOOT SEQUENCE: Oracle Cloud ARM64 Infrastructure ---
  { level: 'SYSTEM', message: 'kernel: [    0.000000] Booting Linux on physical CPU 0x0000000000 [0x411fd070]' },
  { level: 'SYSTEM', message: 'kernel: [    0.000000] Machine model: Oracle Cloud Ampere A1 (aarch64)' },
  { level: 'INFO', message: 'cloud-init[452]: [OCI] Fetching metadata from http://169.254.169.254/opc/v1/instance/' },
  { level: 'INFO', message: 'cloud-init[452]: [OCI] Instance Shape: VM.Standard.A1.Flex (4 OCPU, 24GB RAM)' },
  { level: 'SYSTEM', message: 'systemd[1]: Started Kubernetes K3s Agent.' },
  { level: 'INFO', message: 'k3s-agent: Connecting to server wss://10.0.0.5:6443/v1-k3s/connect' },
  { level: 'DEBUG', message: 'k3s-agent: Node label `kubernetes.io/arch=arm64` applied.' },

  // --- SERVICE STARTUP: Python/FastAPI & Go ---
  { level: 'INFO', message: 'infra-manager: Terraform State Lock acquired (DynamoDB: alphapulse-lock).' },
  { level: 'INFO', message: 'uvicorn.error: Started server process [78]' },
  { level: 'INFO', message: 'uvicorn.error: Waiting for application startup.' },
  { level: 'DEBUG', message: 'fastapi: Loading configuration from `/app/config/prod/config.yaml`' },
  { level: 'INFO', message: 'sqlalchemy.engine: Engine(postgresql+asyncpg://admin:***@10.43.2.14:5432/alphapulse_db)' },
  { level: 'INFO', message: 'uvicorn.error: Application startup complete.' },
  { level: 'INFO', message: 'uvicorn.error: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)' },
  { level: 'SYSTEM', message: 'ingestion-svc-go: GOMAXPROCS=4. Initializing WebSocket Hub.' },

  // --- WORKFLOW: Real-time Data Ingestion (Go) ---
  { level: 'INFO', message: 'ingestion-svc-go: [Binance] Connecting to wss://stream.binance.com:9443/ws/btcusdt@trade' },
  { level: 'INFO', message: 'ingestion-svc-go: [Kraken] Connecting to wss://ws.kraken.com' },
  { level: 'INFO', message: 'ingestion-svc-go: [Coinbase] Connecting to wss://ws-feed.pro.coinbase.com' },
  { level: 'DEBUG', message: 'ingestion-svc-go: WebSocket Pool Ready. Active Connections: 3.' },
  { level: 'INFO', message: 'kafka-producer: [Topic: raw-market-data] Partition leader found: broker-0 (id: 1001)' },
  { level: 'DEBUG', message: 'kafka-producer: Flushing batch (size: 145KB, msgs: 500) to broker.' },

  // --- WORKFLOW: Airflow DAG Execution (News Sentiment) ---
  { level: 'INFO', message: 'airflow-scheduler: DagFileProcessorManager: Processing file /opt/airflow/dags/news_sentiment_dag.py' },
  { level: 'INFO', message: 'airflow-scheduler: Creating DagRun for DAG: news_sentiment_dag [execution_date=2025-10-16T14:00:00]' },
  { level: 'INFO', message: 'airflow-worker: Executing command: airflow tasks run news_sentiment_dag fetch_news_api ...' },
  { level: 'INFO', message: 'news_ingestion: Fetching from NewsAPI (q="Bitcoin OR Ethereum"). Page 1/5.' },
  { level: 'WARN', message: 'news_ingestion: Rate limit warning (X-RateLimit-Remaining: 15). Backing off 2s.' },
  { level: 'INFO', message: 'airflow-worker: Task `fetch_news_api` success. XCom pushed: `s3://raw/news/batch_402.json`' },
  { level: 'INFO', message: 'airflow-worker: Executing command: airflow tasks run news_sentiment_dag compute_finbert_sentiment ...' },
  { level: 'DEBUG', message: 'sentiment-engine: Loading model `ProsusAI/finbert` from HuggingFace Cache.' },
  { level: 'INFO', message: 'sentiment-engine: Inference Start. Batch Size: 32. Device: CPU (NEON optimized).' },
  { level: 'SUCCESS', message: 'airflow-worker: Task `compute_finbert_sentiment` success. 1450 articles processed.' },

  // --- WORKFLOW: Model Training (MLflow + Optuna) ---
  { level: 'INFO', message: 'airflow-scheduler: Triggering DAG `training_dag` (Dataset Trigger: `s3://features/sentiment_v2`).' },
  { level: 'INFO', message: 'mlflow-tracking: Experiment `AlphaPulse_XGB_v2` (ID: 4) active.' },
  { level: 'INFO', message: 'optuna-worker: Trial 14 started. Params: { learning_rate: 0.05, max_depth: 6 }.' },
  { level: 'WARN', message: 'training-job: Data sparsity detected in feature `social_volume_24h`. Imputing with median.' },
  { level: 'INFO', message: 'xgboost: [14:05:00] src/tree/updater_prune.cc:101: tree pruning end, 124 roots...' },
  { level: 'DEBUG', message: 'mlflow-logger: Metric `val_rmse` = 0.4215.' },
  { level: 'INFO', message: 'optuna-worker: Trial 14 finished. Objective: 0.4215.' },
  { level: 'SUCCESS', message: 'mlflow-registry: Registered model `AlphaPulse_Predictor` version 12.' },
  
  // --- SCENARIO: Anomaly Detection (Evidently) ---
  { level: 'INFO', message: 'evidently-service: Scheduled job `data_drift_check` started.' },
  { level: 'INFO', message: 'evidently-service: Loading reference dataset (ref_v11) and current batch (cur_v12).' },
  { level: 'WARN', message: 'drift-monitor: Column `btc_dominance`: Wasserstein distance 0.15 > threshold 0.1.' },
  { level: 'ERROR', message: 'drift-monitor: Test failed: `Share of Drifted Features` (Value: 0.35, Condition: < 0.2).' },
  { level: 'INFO', message: 'alert-manager: Firing alert `DataDriftCritical` to Slack channel #mlops-alerts.' },
  { level: 'INFO', message: 'airflow-api: Triggering DAG `retrain_on_drift` via API.' },

  // --- SCENARIO: Runtime Error & Recovery ---
  { level: 'INFO', message: 'inference-svc: POST /v1/predict (Client: HedgeFund_A)' },
  { level: 'DEBUG', message: 'feature-store: Reading vector `BTC-USD:latest` from Redis Cluster.' },
  { level: 'ERROR', message: 'inference-svc: TimeoutError: Redis sentinel `redis-node-2` unreachable.' },
  { level: 'WARN', message: 'circuit-breaker: Circuit `redis-feature-store` OPEN.' },
  { level: 'INFO', message: 'inference-svc: Serving fallback prediction (Safe Mode).' },
  { level: 'INFO', message: 'k8s-controller: Liveness probe failed for pod `redis-node-2-x7z`. Restarting.' },
  { level: 'SYSTEM', message: 'k8s-event: Container `redis` created.' },
  { level: 'SYSTEM', message: 'k8s-event: Container `redis` started.' },
  { level: 'INFO', message: 'circuit-breaker: Circuit `redis-feature-store` HALF-OPEN. Testing connection...' },
  { level: 'SUCCESS', message: 'circuit-breaker: Circuit `redis-feature-store` CLOSED. System recovered.' },

  // --- SCENARIO: Auto-Scaling & Financial Precision ---
  { level: 'INFO', message: 'prometheus-adapter: Metric `http_requests_per_second` crossed threshold (1200 > 1000).' },
  { level: 'INFO', message: 'k8s-hpa: Scaling deployment `inference-api` from 3 to 5 replicas.' },
  { level: 'INFO', message: 'k8s-scheduler: Successfully assigned `inference-api-xx8` to node `pool-arm64-2`.' },
  { level: 'INFO', message: 'compliance-engine: Auditing Transaction #992102.' },
  { level: 'DEBUG', message: 'compliance-engine: Decimal Precision Check: Input `42000.12345678` -> Stored `42000.12345678` (Scale: 8).' },
  { level: 'SUCCESS', message: 'compliance-engine: ACID Transaction committed to Ledger.' },

  // --- ROUTINE MAINTENANCE ---
  { level: 'INFO', message: 'log-rotator: Compressing /var/log/alphapulse/access.log.1.gz' },
  { level: 'INFO', message: 's3-sync: Uploading logs to bucket `alpha-pulse-logs-archive`.' },
  { level: 'SYSTEM', message: 'go-runtime: GC forced. Heap cleared.' },
  { level: 'INFO', message: 'heartbeat: System Status: GREEN. Active Nodes: 2. API Latency: 12ms.' }
];
