import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, LinearProgress, alpha, useTheme } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import apiClient from '../../../api/client';

const defaultDriftData = [
  { feature: 'BTC_Vol_24h', drift: 0.02 },
  { feature: 'RSI_14', drift: 0.08 },
  { feature: 'Sentiment_Score', drift: 0.24 }, // High drift!
  { feature: 'MACD_Signal', drift: 0.05 },
  { feature: 'Whale_Inflow', drift: 0.12 },
];

const DriftMonitor: React.FC = () => {
  const theme = useTheme();
  const [driftData, setDriftData] = useState(defaultDriftData);
  const [highDriftFeature, setHighDriftFeature] = useState<string | null>('Sentiment_Score');

  useEffect(() => {
    const fetchDrift = async () => {
      try {
        const response = await apiClient.get('/v1/ops/drift-analysis');
        if (response.data && response.data.features) {
          setDriftData(response.data.features);
          const high = response.data.features.find((f: any) => f.alert);
          setHighDriftFeature(high ? high.feature : null);
        }
      } catch (error) {
        console.error('Failed to fetch drift analysis', error);
      }
    };
    fetchDrift();
  }, []);

  return (
    <Box sx={{ p: 3, height: '100%' }}>
      <Typography variant="h6" gutterBottom>Feature Drift Analysis (PSI)</Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>
        Population Stability Index (PSI) compared to training baseline.
      </Typography>

      <Box sx={{ height: 250, width: '100%' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={driftData} layout="vertical" margin={{ left: 20 }}>
            <XAxis type="number" hide domain={[0, 0.3]} />
            <YAxis 
              dataKey="feature" 
              type="category" 
              stroke={theme.palette.text.secondary} 
              fontSize={12} 
              width={100}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip 
              cursor={{ fill: 'transparent' }}
              contentStyle={{ backgroundColor: theme.palette.background.paper, border: 'none', borderRadius: 8 }}
            />
            <Bar dataKey="drift" radius={[0, 4, 4, 0]} barSize={20}>
              {driftData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={entry.drift > 0.2 ? theme.palette.error.main : entry.drift > 0.1 ? theme.palette.warning.main : theme.palette.primary.main} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Box>

      <Box sx={{ mt: 2 }}>
        {highDriftFeature && (
          <Typography variant="caption" color="error.main" fontWeight="bold">
            ⚠️ Alert: High drift detected in '{highDriftFeature}'. Triggering retraining investigation.
          </Typography>
        )}
      </Box>
    </Box>
  );
};

export default DriftMonitor;
