import { useState, useEffect } from "react";
import { mockEngine } from "./MockDataEngine";

export function useMockData<T>(selector: () => T): T {
  const [data, setData] = useState<T>(selector);
  useEffect(() => mockEngine.subscribe(() => setData(selector())), []);
  return data;
}

export const usePrices = () =>
  useMockData(() => ({
    "BTC-USD": mockEngine.getPrice("BTC-USD"),
    "ETH-USD": mockEngine.getPrice("ETH-USD"),
    SPY: mockEngine.getPrice("SPY"),
    QQQ: mockEngine.getPrice("QQQ"),
  }));

export const useHistory = (sym: string, n?: number) =>
  useMockData(() => mockEngine.getHistory(sym, n));

export const useSignals = () => useMockData(() => mockEngine.getSignals());

export const usePipelines = () => useMockData(() => mockEngine.getPipelines());

export const useModels = () => useMockData(() => mockEngine.getModels());

export const usePortfolio = () => useMockData(() => mockEngine.getPortfolio());
