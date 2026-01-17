import { SystemLog } from '../types';

export type PredefinedLog = Omit<SystemLog, 'id' | 'timestamp'>;

export const PREDEFINED_LOGS: PredefinedLog[] = [
  { level: 'SYSTEM', message: 'OCI_ARM64: Hypervisor check passed. Kernel: Linux 5.15.0-1031-oracle (aarch64)' },
  { level: 'INFO', message: 'infra-manager: Terraform state lock acquired. Verifying compartment resources...' },
  { level: 'INFO', message: 'ingestion-svc-go: WebSocket pool initialized. [Binance: OK, Coinbase: OK]' },
  { level: 'INFO', message: 'inference-engine: Loading model v2.4.1 (ONNX/FP16) for ARM64 NEON optimization' },
  { level: 'WARN', message: 'data-cleaner: Missing OHLCV sequence for ETH-USD. Interpolating via linear method.' },
  { level: 'SYSTEM', message: 'go-runtime: GC cycle completed. Reclaimed 45MB. Pause time: 1.2ms' },
  { level: 'INFO', message: 'inference-engine: Batch #4902 complete. Throughput: 1400 req/s. Latency p99: 12ms' },
  { level: 'DEBUG', message: 'feature-store: Flushing to Redis. Keys updated: 15,200. Memory usage: 14.2GB' },
  { level: 'WARN', message: 'drift-monitor: Covariate shift in sentiment_score. PSI: 0.12 (Threshold: 0.10)' },
  { level: 'SUCCESS', message: 'pipeline-orchestrator: Daily-alpha-update triggered via Airflow DAG.' },
  { level: 'INFO', message: 'risk-engine: Recalibrated. Volatility regime: HIGH. Leverage cap: 2.5x' },
  { level: 'INFO', message: 'compliance: Audit log sync success. Decimal precision strictly enforced.' },
  { level: 'ERROR', message: 'feed-handler: WS disconnection (Kraken). Exponential backoff (Attempt 1/5)' },
  { level: 'INFO', message: 'feed-handler: Reconnection successful. Resuming stream consumption.' },
];