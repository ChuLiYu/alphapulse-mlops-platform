import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Stack,
  Divider,
  alpha,
  CircularProgress,
} from '@mui/material';
import { motion } from 'framer-motion';
import AutoGraphIcon from '@mui/icons-material/AutoGraph';
import StrategyChart from './StrategyChart';
import StrategyControlPanel from './StrategyControlPanel';
import apiClient from '../../../api/client';

const StrategyPlayground: React.FC = () => {
  const [riskLevel, setRiskLevel] = useState(5);
  const [confidence, setConfidence] = useState(0.75);
  const [stopLoss, setStopLoss] = useState(0.05);
  const [simulationData, setSimulationData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  
  const runSimulation = async () => {
    setLoading(true);
    try {
      const riskMap: Record<number, string> = { 1: 'low', 2: 'low', 3: 'low', 4: 'medium', 5: 'medium', 6: 'medium', 7: 'high', 8: 'high', 9: 'high', 10: 'high' };
      const response = await apiClient.post('/v1/simulation/backtest', {
        risk_level: riskMap[riskLevel] || 'medium',
        confidence_threshold: confidence,
        stop_loss_pct: stopLoss,
        initial_capital: 10000
      });
      setSimulationData(response.data.equity_curve);
      setMetrics(response.data.metrics);
    } catch (error) {
      console.error('Simulation failed', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runSimulation();
  }, [riskLevel, confidence, stopLoss]);

  const latestValue = simulationData.length > 0 ? simulationData[simulationData.length - 1].value : 10000;
  const initialValue = 10000;
  const returnPct = metrics ? metrics.total_return : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card sx={{ mt: 4, overflow: 'hidden' }}>
        <Box sx={{ p: 3, borderBottom: '1px solid', borderColor: 'divider', bgcolor: alpha('#00d2ff', 0.03) }}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <AutoGraphIcon color="primary" />
            <Typography variant="h6">Strategy Playground (Hero Demo)</Typography>
          </Stack>
          <Typography variant="body2" color="text.secondary">
            Simulate how AlphaPulse ML models perform with different risk configurations.
          </Typography>
        </Box>

        <CardContent sx={{ p: 0 }}>
          <Grid container>
            <Grid item xs={12} md={4} sx={{ borderRight: { md: '1px solid' }, borderColor: 'divider' }}>
              <StrategyControlPanel
                riskLevel={riskLevel}
                setRiskLevel={setRiskLevel}
                confidence={confidence}
                setConfidence={setConfidence}
                stopLoss={stopLoss}
                setStopLoss={setStopLoss}
              />
              <Divider />
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="overline" color="text.secondary">
                  Projected 30D Return
                </Typography>
                {loading ? (
                  <Box sx={{ py: 1 }}><CircularProgress size={24} /></Box>
                ) : (
                  <Typography 
                    variant="h4" 
                    color={returnPct >= 0 ? 'secondary.main' : 'error.main'}
                    sx={{ fontStyle: 'italic', fontWeight: 'bold' }}
                  >
                    {returnPct >= 0 ? '+' : ''}{returnPct.toFixed(2)}%
                  </Typography>
                )}
                <Button 
                  variant="contained" 
                  fullWidth 
                  sx={{ mt: 2 }}
                  onClick={runSimulation}
                  disabled={loading}
                >
                  {loading ? 'Simulating...' : 'Rerun Simulation'}
                </Button>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={8} sx={{ bgcolor: alpha('#000', 0.2), p: 2, position: 'relative' }}>
              {loading && (
                <Box sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: alpha('#000', 0.3), zIndex: 1 }}>
                  <CircularProgress />
                </Box>
              )}
              <Stack direction="row" spacing={3} sx={{ mb: 2, px: 2 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Current Balance</Typography>
                  <Typography variant="h6">${latestValue.toLocaleString()}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Initial Capital</Typography>
                  <Typography variant="h6">$10,000</Typography>
                </Box>
              </Stack>
              <StrategyChart data={simulationData.length > 0 ? simulationData : []} />
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default StrategyPlayground;
