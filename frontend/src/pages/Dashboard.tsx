import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { ArrowUpRight, Activity, ShieldCheck } from 'lucide-react';

const mockPriceData = [
  { time: '00:00', price: 92000 },
  { time: '04:00', price: 93500 },
  { time: '08:00', price: 93000 },
  { time: '12:00', price: 95000 },
  { time: '16:00', price: 94800 },
  { time: '20:00', price: 96200 },
  { time: '23:59', price: 95800 },
];

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 1 }}>Market Overview</Typography>
          <Typography variant="body2" color="text.secondary">Real-time trading insights and model performance.</Typography>
        </Box>
        <Chip 
          icon={<ShieldCheck size={16} />} 
          label="System Healthy" 
          color="success" 
          variant="outlined" 
          sx={{ borderRadius: 1 }}
        />
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>BTC Price</Typography>
              <Typography variant="h5" sx={{ my: 1 }}>$95,800.50</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'success.main' }}>
                <ArrowUpRight size={16} />
                <Typography variant="body2" sx={{ ml: 0.5 }}>+3.25% (24h)</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>Active Signals</Typography>
              <Typography variant="h5" sx={{ my: 1 }}>BUY</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                <Activity size={16} />
                <Typography variant="body2" sx={{ ml: 0.5 }}>Confidence: 89%</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>CPU Load</Typography>
              <Typography variant="h5" sx={{ my: 1 }}>45.2%</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'warning.main' }}>
                <Typography variant="body2">4 OCPUs Active</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>Memory</Typography>
              <Typography variant="h5" sx={{ my: 1 }}>14.2 GB</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                <Typography variant="body2">Total: 24 GB</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent sx={{ height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Price Trend (BTC-USD)</Typography>
              <Box sx={{ height: 300, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mockPriceData}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3f51b5" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3f51b5" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" fontSize={12} />
                    <YAxis domain={['auto', 'auto']} stroke="rgba(255,255,255,0.5)" fontSize={12} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#112240', border: '1px solid rgba(255,255,255,0.1)' }}
                      itemStyle={{ color: '#fff' }}
                    />
                    <Area type="monotone" dataKey="price" stroke="#3f51b5" fillOpacity={1} fill="url(#colorPrice)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>Recent Signals</Typography>
              {[1, 2, 3, 4, 5].map((i) => (
                <Box key={i} sx={{ display: 'flex', justifyContent: 'space-between', py: 1.5, borderBottom: i === 5 ? 'none' : '1px solid rgba(255,255,255,0.05)' }}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>BTC-USD</Typography>
                    <Typography variant="caption" color="text.secondary">2 mins ago</Typography>
                  </Box>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body2" color="success.main" sx={{ fontWeight: 'bold' }}>BUY</Typography>
                    <Typography variant="caption" color="text.secondary">92% conf.</Typography>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;