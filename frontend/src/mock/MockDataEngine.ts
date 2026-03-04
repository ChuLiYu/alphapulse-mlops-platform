// Box-Muller transform for Gaussian random numbers
function gaussianRandom(): number {
  const u = 1 - Math.random();
  const v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Geometric Brownian Motion - foundation of Black-Scholes pricing
function gbmStep(price: number, mu = 0.0001, sigma = 0.012): number {
  return price * Math.exp(mu - 0.5 * sigma ** 2 + sigma * gaussianRandom());
}

const SYMBOLS = ["BTC-USD", "ETH-USD", "SPY", "QQQ"];

const SEED_PRICES: Record<string, number> = {
  "BTC-USD": 67420,
  "ETH-USD": 3540,
  SPY: 528,
  QQQ: 452,
};

export interface OHLCVPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingSignal {
  id: string;
  symbol: string;
  direction: "LONG" | "SHORT" | "HOLD";
  confidence: number;
  price: number;
  timestamp: number;
  model: string;
  pnl_pct: number;
}

export interface PipelineRun {
  dag_id: string;
  run_id: string;
  state: "running" | "success" | "failed" | "queued";
  start_time: number;
  duration_sec: number;
  tasks_done: number;
  tasks_total: number;
}

export interface ModelMetric {
  name: string;
  version: string;
  accuracy: number;
  sharpe: number;
  max_drawdown: number;
  status: "production" | "staging" | "archived";
}

class MockDataEngine {
  private prices: Record<string, number> = {};
  private history: Record<string, OHLCVPoint[]> = {};
  private listeners: Set<() => void> = new Set();
  private intervalId: ReturnType<typeof setInterval> | null = null;
  private pipelineStates: PipelineRun[] = [];
  private tick = 0;

  constructor() {
    this.initPrices();
    this.initHistory();
    this.initPipelines();
  }

  private initPrices(): void {
    for (const symbol of SYMBOLS) {
      this.prices[symbol] = SEED_PRICES[symbol];
    }
  }

  private initHistory(): void {
    const now = Date.now();
    const intervalMs = 5000; // 5 seconds per candle

    for (const symbol of SYMBOLS) {
      const history: OHLCVPoint[] = [];
      let price = SEED_PRICES[symbol];

      for (let i = 119; i >= 0; i--) {
        const timestamp = now - i * intervalMs;
        
        // Generate OHLCV with GBM
        const open = price;
        const close = gbmStep(price);
        
        // High/low spread based on gaussian
        const spread = Math.abs(close - open) + Math.abs(gaussianRandom() * price * 0.005);
        const high = Math.max(open, close) + spread * Math.random() * 0.5;
        const low = Math.min(open, close) - spread * Math.random() * 0.5;
        
        const volume = Math.floor(1000000 + gaussianRandom() * 500000);
        
        history.push({
          timestamp,
          open,
          high,
          low,
          close,
          volume,
        });
        
        price = close;
      }
      
      this.prices[symbol] = price;
      this.history[symbol] = history;
    }
  }

  private initPipelines(): void {
    const now = Date.now();
    
    this.pipelineStates = [
      {
        dag_id: "market_data_ingestion",
        run_id: `run_${Date.now()}_1`,
        state: "success",
        start_time: now - 120000,
        duration_sec: 45,
        tasks_done: 5,
        tasks_total: 5,
      },
      {
        dag_id: "dbt_silver_gold",
        run_id: `run_${Date.now()}_2`,
        state: "running",
        start_time: now - 60000,
        duration_sec: 0,
        tasks_done: 2,
        tasks_total: 4,
      },
      {
        dag_id: "feature_engineering",
        run_id: `run_${Date.now()}_3`,
        state: "queued",
        start_time: 0,
        duration_sec: 0,
        tasks_done: 0,
        tasks_total: 6,
      },
      {
        dag_id: "model_retraining",
        run_id: `run_${Date.now()}_4`,
        state: "success",
        start_time: now - 300000,
        duration_sec: 180,
        tasks_done: 8,
        tasks_total: 8,
      },
    ];
  }

  subscribe(callback: () => void): () => void {
    this.listeners.add(callback);

    if (!this.intervalId) {
      this.intervalId = setInterval(() => {
        this.advance();
      }, 2000);
    }

    return () => {
      this.listeners.delete(callback);
      if (this.listeners.size === 0 && this.intervalId) {
        clearInterval(this.intervalId);
        this.intervalId = null;
      }
    };
  }

  private advance(): void {
    this.tick++;
    const now = Date.now();
    
    for (const symbol of SYMBOLS) {
      const currentPrice = this.prices[symbol];
      const history = this.history[symbol];
      const lastCandle = history[history.length - 1];
      
      const newPrice = gbmStep(currentPrice);
      
      // Generate OHLCV for the new tick
      const open = lastCandle.close;
      const close = newPrice;
      const spread = Math.abs(close - open) + Math.abs(gaussianRandom() * open * 0.005);
      const high = Math.max(open, close) + spread * Math.random() * 0.5;
      const low = Math.min(open, close) - spread * Math.random() * 0.5;
      const volume = Math.floor(1000000 + gaussianRandom() * 500000);
      
      const newPoint: OHLCVPoint = {
        timestamp: now,
        open,
        high,
        low,
        close,
        volume,
      };
      
      // Maintain max 200 history points
      this.history[symbol] = [...history.slice(-199), newPoint];
      this.prices[symbol] = newPrice;
    }
    
    // Every 10 ticks, advance pipelines
    if (this.tick % 10 === 0) {
      this.advancePipelines();
    }
    
    // Notify listeners
    for (const listener of this.listeners) {
      listener();
    }
  }

  private advancePipelines(): void {
    for (const pipeline of this.pipelineStates) {
      if (pipeline.state === "running") {
        // Increment tasks
        if (pipeline.tasks_done < pipeline.tasks_total) {
          pipeline.tasks_done += 1;
        }
        
        // Update duration
        pipeline.duration_sec += 10;
        
        // Check if completed
        if (pipeline.tasks_done >= pipeline.tasks_total) {
          // Random chance of success or failure (mostly success)
          pipeline.state = Math.random() > 0.1 ? "success" : "failed";
        }
      } else if (pipeline.state === "queued") {
        // Maybe start running
        if (Math.random() > 0.5) {
          pipeline.state = "running";
          pipeline.start_time = Date.now();
        }
      } else if (pipeline.state === "success" || pipeline.state === "failed") {
        // Reset for demo purposes
        if (Math.random() > 0.7) {
          pipeline.state = "queued";
          pipeline.tasks_done = 0;
          pipeline.duration_sec = 0;
          pipeline.start_time = 0;
        }
      }
    }
  }

  getPrice(symbol: string): number {
    return this.prices[symbol] ?? 0;
  }

  getHistory(symbol: string, n = 60): OHLCVPoint[] {
    const history = this.history[symbol] ?? [];
    return history.slice(-n);
  }

  getPortfolio(): Record<string, number> {
    return { ...this.prices };
  }

  getSignals(): TradingSignal[] {
    const signals: TradingSignal[] = [];
    const models = ["AlphaPulse-V2", "Quantum-5", "DeepFlow-X", "TrendMaster-Pro"];
    
    for (let i = 0; i < SYMBOLS.length; i++) {
      const symbol = SYMBOLS[i];
      const price = this.prices[symbol];
      
      // Animate direction based on tick
      const directionIndex = (this.tick + i) % 3;
      const direction: "LONG" | "SHORT" | "HOLD" = 
        directionIndex === 0 ? "LONG" : directionIndex === 1 ? "SHORT" : "HOLD";
      
      const confidence = 0.5 + Math.abs(gaussianRandom()) * 0.45;
      const pnl_pct = (gaussianRandom() * 10 - 2);
      
      signals.push({
        id: `sig_${symbol}_${this.tick}`,
        symbol,
        direction,
        confidence: Math.round(confidence * 100) / 100,
        price,
        timestamp: Date.now(),
        model: models[i % models.length],
        pnl_pct: Math.round(pnl_pct * 100) / 100,
      });
    }
    
    return signals;
  }

  getModels(): ModelMetric[] {
    return [
      {
        name: "AlphaPulse-V2",
        version: "v2.4.1",
        accuracy: 0.873,
        sharpe: 2.34,
        max_drawdown: -0.124,
        status: "production",
      },
      {
        name: "Quantum-5",
        version: "v5.1.0",
        accuracy: 0.891,
        sharpe: 2.67,
        max_drawdown: -0.098,
        status: "production",
      },
      {
        name: "DeepFlow-X",
        version: "v1.2.0",
        accuracy: 0.845,
        sharpe: 1.92,
        max_drawdown: -0.156,
        status: "staging",
      },
      {
        name: "TrendMaster-Pro",
        version: "v3.0.0",
        accuracy: 0.812,
        sharpe: 1.56,
        max_drawdown: -0.203,
        status: "staging",
      },
      {
        name: "Legacy-V1",
        version: "v1.8.5",
        accuracy: 0.756,
        sharpe: 1.12,
        max_drawdown: -0.289,
        status: "archived",
      },
    ];
  }

  getPipelines(): PipelineRun[] {
    return [...this.pipelineStates];
  }
}

export const mockEngine = new MockDataEngine();
