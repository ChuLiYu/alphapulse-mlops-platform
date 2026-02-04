import { useState, useEffect } from "react";
import {
  dashboardApi,
  Signal,
  DriftAnalysis,
  PipelineStatus,
} from "../api/dashboard";
import { SERVICE_URLS } from "../config/links-runtime";

// --- Local Mock Data (Fallback) ---
const getMockPrices = () => [
  { time: "00:00", price: 92000 + Math.random() * 500 },
  { time: "04:00", price: 93500 + Math.random() * 500 },
  { time: "08:00", price: 93000 + Math.random() * 500 },
  { time: "12:00", price: 95000 + Math.random() * 500 },
  { time: "16:00", price: 94800 + Math.random() * 500 },
  { time: "20:00", price: 96200 + Math.random() * 500 },
  { time: "23:59", price: 95800 + Math.random() * 500 },
];

const MOCK_SIGNALS: Signal[] = [
  {
    id: 1,
    symbol: "BTC-USD",
    signal_type: "BUY",
    confidence: 0.89,
    timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
    price_at_signal: 95200,
  },
  {
    id: 2,
    symbol: "BTC-USD",
    signal_type: "HOLD",
    confidence: 0.45,
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    price_at_signal: 95000,
  },
  {
    id: 3,
    symbol: "ETH-USD",
    signal_type: "SELL",
    confidence: 0.72,
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    price_at_signal: 3200,
  },
];

const MOCK_PIPELINE: PipelineStatus = {
  stages: [
    { id: "ingest", label: "Ingestion", status: "success" },
    { id: "validate", label: "Validation", status: "success" },
    { id: "train", label: "Training", status: "running" },
    { id: "eval", label: "Evaluation", status: "pending" },
    { id: "deploy", label: "Deployment", status: "pending" },
  ],
  last_retrained: new Date().toISOString(),
};

const MOCK_DRIFT: DriftAnalysis = {
  overall_score: 0.024,
  features: [
    { feature: "Sentiment_Score", drift: 0.24, alert: true },
    { feature: "RSI_14", drift: 0.08, alert: false },
    { feature: "Vol_24h", drift: 0.05, alert: false },
  ],
};

// --- Hook ---
export const useDashboardData = () => {
  const [prices, setPrices] = useState<any[]>(getMockPrices());
  const [signals, setSignals] = useState<Signal[]>(MOCK_SIGNALS);
  const [pipeline, setPipeline] = useState<PipelineStatus>(MOCK_PIPELINE);
  const [drift, setDrift] = useState<DriftAnalysis>(MOCK_DRIFT);

  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(SERVICE_URLS.IS_DEMO_MODE);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      // If forced demo mode, just skip fetch and use mocks
      if (SERVICE_URLS.IS_DEMO_MODE) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        // Execute all requests in parallel
        const [pricesData, signalsData, pipelineData, driftData] =
          await Promise.allSettled([
            dashboardApi.getPrices("BTC-USD", 24),
            dashboardApi.getLatestSignals(5),
            dashboardApi.getPipelineStatus(),
            dashboardApi.getDriftAnalysis(),
          ]);

        if (!mounted) return;

        // Process Prices
        if (pricesData.status === "fulfilled" && pricesData.value.success && pricesData.value.data.length > 0) {
          // Transform backend price format to Recharts format
          const formattedPrices = pricesData.value.data
            .map((p: any) => ({
              time: new Date(p.timestamp).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
              price: Number(p.price),
            }))
            .reverse(); // Assuming API returns newest first
          setPrices(formattedPrices);
        } else {
          setUsingMock(true);
        }

        // Process Signals
        if (signalsData.status === "fulfilled" && signalsData.value.success && signalsData.value.data.length > 0) {
          setSignals(signalsData.value.data);
        } else {
          setUsingMock(true);
        }

        // Process Pipeline
        if (pipelineData.status === "fulfilled" && pipelineData.value && pipelineData.value.stages) {
          setPipeline(pipelineData.value);
        } else {
          setUsingMock(true);
        }

        // Process Drift
        if (driftData.status === "fulfilled" && driftData.value && driftData.value.features) {
          setDrift(driftData.value);
        } else {
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

    return () => {
      mounted = false;
    };
  }, []);

  return { prices, signals, pipeline, drift, loading, usingMock, isDemo: SERVICE_URLS.IS_DEMO_MODE };
};
