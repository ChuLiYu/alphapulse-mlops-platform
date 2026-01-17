// frontend/src/types/auth.ts
export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// frontend/src/types/market.ts
export interface PriceData {
  symbol: string;
  timestamp: string;
  price: string;
  volume: string;
}

export interface PriceStats {
  symbol: string;
  prices: {
    latest: string;
    minimum: string;
    maximum: string;
    average: string;
  };
  changes: {
    percentage: string;
  };
  timestamp: string;
}

// frontend/src/types/signals.ts
export type SignalType = 'BUY' | 'SELL' | 'HOLD';

export interface TradingSignal {
  id: number;
  symbol: string;
  signal_type: SignalType;
  confidence: string;
  price_at_signal: string;
  timestamp: string;
}

// frontend/src/types/health.ts
export interface SystemHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  metrics: {
    uptime: { seconds: number };
    cpu_usage: { percent: number };
    memory_usage: { percent: number };
  };
}

// frontend/src/types/logs.ts
export interface SystemLog {
  id: number;
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'WARN' | 'SYSTEM' | 'ERROR' | 'DEBUG';
  message: string;
}
