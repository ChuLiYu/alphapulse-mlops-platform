import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { useTheme, alpha, Box, Typography } from '@mui/material';
import { SimulationData } from '../utils';

interface StrategyChartProps {
  data: SimulationData[];
}

const StrategyChart: React.FC<StrategyChartProps> = ({ data }) => {
  const theme = useTheme();

  return (
    <Box sx={{ width: '100%', height: 350, mt: 2 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3} />
              <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorBench" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.palette.text.secondary} stopOpacity={0.1} />
              <stop offset="95%" stopColor={theme.palette.text.secondary} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={alpha(theme.palette.divider, 0.1)} vertical={false} />
          <XAxis 
            dataKey="day" 
            stroke={theme.palette.text.secondary} 
            fontSize={12}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            stroke={theme.palette.text.secondary} 
            fontSize={12}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value}`}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: theme.palette.background.paper,
              border: `1px solid ${theme.palette.primary.main}`,
              borderRadius: '8px',
            }}
            itemStyle={{ fontSize: '12px' }}
          />
          <Area
            type="monotone"
            dataKey="value"
            name="AlphaPulse Strategy"
            stroke={theme.palette.primary.main}
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#colorValue)"
          />
          <Area
            type="monotone"
            dataKey="benchmark"
            name="Buy & Hold (BTC)"
            stroke={theme.palette.text.secondary}
            strokeDasharray="5 5"
            strokeWidth={1}
            fillOpacity={1}
            fill="url(#colorBench)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default StrategyChart;
