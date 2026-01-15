import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip, Button, Skeleton } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { ArrowUpRight, Activity, ShieldCheck, Lock, Unlock } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

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
  const { isAdmin, loading } = useAuth();

  if (loading) {
    return <Box sx={{ p: 4 }}><Skeleton variant="rectangular" height={400} /></Box>;
  }

  return (
    <Box>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 1 }}>AlphaPulse Dashboard</Typography>
          <Typography variant="body2" color="text.secondary">
            {isAdmin ? "Administrator Management Console" : "Live Strategy Performance (Public View)"}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {isAdmin && (
            <Chip 
              icon={<Unlock size={16} />} 
              label="Admin Privileges Active" 
              color="primary" 
              variant="filled"
            />
          )}
          <Chip 
            icon={<ShieldCheck size={16} />} 
            label="System Healthy" 
            color="success" 
            variant="outlined" 
          />
        </Box>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Public Metric: Price */}
        <Grid item xs={12} md={isAdmin ? 3 : 6}>
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

        {/* Public Metric: Signals */}
        <Grid item xs={12} md={isAdmin ? 3 : 6}>
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

        {/* Admin-only Metrics (Only visible to verified admins via JWT) */}
        {isAdmin && (
          <>
            <Grid item xs={12} md={3}>
              <Card sx={{ bgcolor: 'rgba(63, 81, 181, 0.1)', border: '1px solid rgba(63, 81, 181, 0.3)' }}>
                <CardContent>
                  <Typography color="primary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>CPU Load (Internal)</Typography>
                  <Typography variant="h5" sx={{ my: 1 }}>45.2%</Typography>
                  <Typography variant="body2" color="text.secondary">Oracle ARM 4-Core</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={3}>
              <Card sx={{ bgcolor: 'rgba(63, 81, 181, 0.1)', border: '1px solid rgba(63, 81, 181, 0.3)' }}>
                <CardContent>
                  <Typography color="primary" variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase' }}>Memory (Internal)</Typography>
                  <Typography variant="h5" sx={{ my: 1 }}>14.2 GB</Typography>
                  <Typography variant="body2" color="text.secondary">Total: 24 GB</Typography>
                </CardContent>
              </Card>
            </Grid>
          </>
        )}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent sx={{ height: '100%' }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Market Trend</Typography>
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
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Recent Signals</Typography>
                {isAdmin && <Button size="small">Export CSV</Button>}
              </Box>
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
              {!isAdmin && (
                <Box sx={{ mt: 3, p: 2, bgcolor: 'background.default', borderRadius: 2, textAlign: 'center' }}>
                  <Lock size={20} style={{ opacity: 0.5 }} />
                  <Typography variant="caption" display="block" color="text.secondary">
                    Model weights and deep logs are restricted to platform owners.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;