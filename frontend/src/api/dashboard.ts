import apiClient from './client';

// Types based on the backend schemas and frontend requirements
export interface PriceData {
  time: string;
  price: number;
}

export interface Signal {
  id: number;
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  timestamp: string;
  price_at_signal: number;
}

export interface PipelineStage {
  id: string;
  label: string;
  status: 'success' | 'running' | 'pending' | 'failed';
}

export interface PipelineStatus {
  stages: PipelineStage[];
  last_retrained: string;
}

export interface DriftFeature {
  feature: string;
  drift: number;
  alert: boolean;
}

export interface DriftAnalysis {
  overall_score: number;
  features: DriftFeature[];
}

export const dashboardApi = {
  // Market Data
  getPrices: async (symbol: string = 'BTC-USD', limit: number = 24) => {
    const response = await apiClient.get('/prices', { params: { symbol, limit } });
    return response.data;
  },

  getLatestPrice: async (symbol: string = 'BTC-USD') => {
    const response = await apiClient.get(`/prices/${symbol}/latest`);
    return response.data;
  },

  // Signals
  getLatestSignals: async (limit: number = 5) => {
    const response = await apiClient.get('/signals', { params: { limit } });
    return response.data;
  },

  // MLOps
  getPipelineStatus: async () => {
    const response = await apiClient.get('/ops/pipeline-status');
    return response.data;
  },

  getDriftAnalysis: async () => {
    const response = await apiClient.get('/ops/drift-analysis');
    return response.data;
  }
};
