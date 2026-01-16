import { useState, useEffect } from 'react';
import { dashboardApi, Signal, DriftAnalysis, PipelineStatus } from '../api/dashboard';

// --- Local Hero Mock Data (Fallback) ---
const MOCK_PRICES_HERO = [
  { time: '00:00', price: 92000 },
  { time: '04:00', price: 93500 },
  { time: '08:00', price: 93000 },
  { time: '12:00', price: 95000 },
  { time: '16:00', price: 94800 },
  { time: '20:00', price: 96200 },
  { time: '23:59', price: 95800 },
];

const MOCK_SIGNALS_HERO: Signal[] = [
  { id: 1, symbol: 'BTC-USD', signal_type: 'BUY', confidence: 0.89, timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(), price_at_signal: 95200 },
  { id: 2, symbol: 'BTC-USD', signal_type: 'HOLD', confidence: 0.45, timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), price_at_signal: 95000 },
  { id: 3, symbol: 'ETH-USD', signal_type: 'SELL', confidence: 0.72, timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), price_at_signal: 3200 },
];

const MOCK_PIPELINE_HERO: PipelineStatus = {
  stages: [
    { id: 'ingest', label: 'Ingestion', status: 'success' },
    { id: 'validate', label: 'Validation', status: 'success' },
    { id: 'train', label: 'Training', status: 'running' },
    { id: 'eval', label: 'Evaluation', status: 'pending' },
    { id: 'deploy', label: 'Deployment', status: 'pending' },
  ],
  last_retrained: new Date().toISOString()
};

const MOCK_DRIFT_HERO: DriftAnalysis = {
  overall_score: 0.024,
  features: [
    { feature: 'Sentiment_Score', drift: 0.24, alert: true },
    { feature: 'RSI_14', drift: 0.08, alert: false },
    { feature: 'Vol_24h', drift: 0.05, alert: false }
  ]
};

// --- Hook ---
export const useDashboardData = () => {
  const [prices, setPrices] = useState<any[]>(MOCK_PRICES_HERO);
  const [signals, setSignals] = useState<Signal[]>(MOCK_SIGNALS_HERO);
  const [pipeline, setPipeline] = useState<PipelineStatus>(MOCK_PIPELINE_HERO);
  const [drift, setDrift] = useState<DriftAnalysis>(MOCK_DRIFT_HERO);
  
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        // Execute all requests in parallel
        const [pricesData, signalsData, pipelineData, driftData] = await Promise.allSettled([
          dashboardApi.getPrices('BTC-USD', 24),
          dashboardApi.getLatestSignals(5),
          dashboardApi.getPipelineStatus(),
          dashboardApi.getDriftAnalysis()
        ]);

        if (!mounted) return;

        // Process Prices
        if (pricesData.status === 'fulfilled' && pricesData.value.success) {
           // Transform backend price format to Recharts format
           const formattedPrices = pricesData.value.data.map((p: any) => ({
             time: new Date(p.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
             price: Number(p.price)
           })).reverse(); // Assuming API returns newest first
           setPrices(formattedPrices.length > 0 ? formattedPrices : MOCK_PRICES_HERO);
        } else {
           console.warn('Using fallback prices');
           setUsingMock(true);
        }

        // Process Signals
        if (signalsData.status === 'fulfilled' && signalsData.value.success) {
          setSignals(signalsData.value.data);
        } else {
          setUsingMock(true);
        }

        // Process Pipeline (If backend endpoint exists, otherwise use mock)
        if (pipelineData.status === 'fulfilled') {
            setPipeline(pipelineData.value);
        } else {
            // Expected failure if endpoint not implemented yet
            setUsingMock(true);
        }

        // Process Drift (If backend endpoint exists, otherwise use mock)
        if (driftData.status === 'fulfilled') {
            setDrift(driftData.value);
        } else {
             // Expected failure if endpoint not implemented yet
            setUsingMock(true);
        }

      } catch (error) {
        console.error("Dashboard data fetch failed, using fallbacks:", error);
        setUsingMock(true);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchData();

    return () => { mounted = false; };
  }, []);

  return { prices, signals, pipeline, drift, loading, usingMock };
};
