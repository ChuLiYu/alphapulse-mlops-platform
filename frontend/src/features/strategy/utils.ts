export interface SimulationData {
  day: number;
  value: number;
  benchmark: number;
}

export const generateSimulationData = (
  riskLevel: number, // 1 - 10
  confidenceThreshold: number, // 0.5 - 0.99
  stopLossPct: number // 0.01 - 0.1
): SimulationData[] => {
  const days = 30;
  const data: SimulationData[] = [];
  let currentBalance = 10000;
  let currentBenchmark = 10000;

  // Base daily volatility
  const volatility = 0.02 * (riskLevel / 5);

  for (let i = 0; i <= days; i++) {
    if (i === 0) {
      data.push({ day: i, value: currentBalance, benchmark: currentBenchmark });
      continue;
    }

    // Benchmark (e.g., Buy & Hold BTC) - random walk
    const benchChange = 1 + (Math.random() * 0.04 - 0.018); // Slightly positive bias
    currentBenchmark *= benchChange;

    // Strategy Logic (Mocked)
    // Higher confidence and lower risk level leads to smoother, better returns in this mock
    const winProbability = 0.5 + (confidenceThreshold - 0.5) * 0.5;
    const isWin = Math.random() < winProbability;
    
    let change: number;
    if (isWin) {
      // Win: proportional to risk level
      change = 1 + (Math.random() * volatility);
    } else {
      // Loss: limited by stop loss
      const rawLoss = Math.random() * volatility;
      const actualLoss = Math.min(rawLoss, stopLossPct);
      change = 1 - actualLoss;
    }

    currentBalance *= change;

    data.push({
      day: i,
      value: Math.round(currentBalance),
      benchmark: Math.round(currentBenchmark),
    });
  }

  return data;
};
