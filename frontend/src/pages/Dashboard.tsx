import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip, Button, Skeleton, LinearProgress, Stack, Tooltip as MuiTooltip } from '@mui/material';
import { ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip } from 'recharts';
import { ArrowUpRight, Activity, ShieldCheck, Lock, Unlock, Server, Zap, GitBranch, AlertTriangle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardData } from '../hooks/useDashboardData';
import { alpha, useTheme } from '@mui/material/styles';

const MetricCard: React.FC<{ 
  title: string; 
  value: string; 
  subValue?: string; 
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  color?: string;
}> = ({ title, value, subValue, icon, color = 'primary.main' }) => (
  <Card sx={{ 
    height: '100%', 
    background: (theme) => `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.9)} 0%, ${alpha(theme.palette.background.paper, 0.6)} 100%)`,
    backdropFilter: 'blur(10px)',
    border: '1px solid',
    borderColor: (theme) => alpha(color, 0.2),
    boxShadow: (theme) => `0 4px 20px ${alpha(color, 0.1)}`
  }}>
    <CardContent>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
        <Typography variant="caption" sx={{ fontWeight: 600, textTransform: 'uppercase', color: 'text.secondary', letterSpacing: 1 }}>
          {title}
        </Typography>
        <Box sx={{ p: 0.5, borderRadius: 1, bgcolor: (theme) => alpha(color, 0.1), color: color }}>
          {icon}
        </Box>
      </Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>{value}</Typography>
      {subValue && (
        <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          {subValue}
        </Typography>
      )}
    </CardContent>
  </Card>
);

const PipelineNode: React.FC<{ label: string; status: 'success' | 'running' | 'pending' | 'failed' }> = ({ label, status }) => {
  const theme = useTheme();
  const colors = {
    success: theme.palette.success.main,
    running: theme.palette.info.main,
    pending: theme.palette.text.disabled,
    failed: theme.palette.error.main
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
      <Box sx={{ 
        position: 'relative',
        width: 16, 
        height: 16, 
        borderRadius: '50%', 
        bgcolor: colors[status],
        boxShadow: status === 'running' ? `0 0 10px ${colors[status]}` : 'none'
      }}>
        {status === 'running' && (
          <Box sx={{
            position: 'absolute', top: -4, left: -4, right: -4, bottom: -4,
            border: `2px solid ${alpha(colors[status], 0.3)}`,
            borderRadius: '50%',
            animation: 'pulse 2s infinite'
          }} />
        )}
      </Box>
      <Typography variant="caption" sx={{ color: status === 'pending' ? 'text.disabled' : 'text.primary' }}>
        {label}
      </Typography>
    </Box>
  );
};

const Dashboard: React.FC = () => {
  const { isAdmin, loading: authLoading } = useAuth();
  const { prices, signals, pipeline, drift, loading: dataLoading, usingMock } = useDashboardData();
  const theme = useTheme();

  if (authLoading || dataLoading) {
    return <Box sx={{ p: 4 }}><Skeleton variant="rectangular" height={400} sx={{ borderRadius: 2 }} /></Box>;
  }

  const latestPrice = prices.length > 0 ? prices[prices.length - 1].price : 0;
  const priceChange = prices.length > 1 
    ? ((prices[prices.length - 1].price - prices[0].price) / prices[0].price * 100).toFixed(2) 
    : '0.00';

  return (
    <Box sx={{ animation: 'fadeIn 0.5s ease-out' }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 800, mb: 1, background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`, backgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AlphaPulse Command Center
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {isAdmin ? "Administrator Privileges Active" : "Public View • Read-Only Mode"}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {usingMock && (
             <MuiTooltip title="Backend unreachable. Showing Hero Demo data.">
                <Chip icon={<AlertTriangle size={16} />} label="Demo Mode" color="warning" variant="outlined" size="small" />
             </MuiTooltip>
          )}
          {isAdmin && (
            <Chip 
              icon={<Unlock size={16} />} 
              label="Admin" 
              color="primary" 
              variant="filled"
              size="small"
            />
          )}
          <Chip 
            icon={<ShieldCheck size={16} />} 
            label="System Online" 
            color="success" 
            variant="outlined" 
            size="small"
          />
        </Box>
      </Box>

      {/* MLOps Top Row Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="BTC Price" 
            value={`$${latestPrice.toLocaleString()}`} 
            subValue={`${Number(priceChange) >= 0 ? '+' : ''}${priceChange}% (24h)`}
            icon={<Activity size={20} />}
            color={theme.palette.primary.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Inference Latency" 
            value="112ms" 
            subValue="P99 (Oracle ARM)"
            icon={<Zap size={20} />}
            color={theme.palette.warning.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Data Drift (PSI)" 
            value={drift.overall_score.toFixed(3)} 
            subValue={drift.overall_score > 0.1 ? "Drift Detected" : "Stable"}
            icon={<GitBranch size={20} />}
            color={drift.overall_score > 0.1 ? theme.palette.error.main : theme.palette.success.main}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard 
            title="Active Model" 
            value="v2.4.1" 
            subValue="Prod (XGBoost)"
            icon={<Server size={20} />}
            color={theme.palette.info.main}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Main Chart: Strategy Playground / Market Trend */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ 
            height: 450, 
            backdropFilter: 'blur(10px)',
            background: `linear-gradient(180deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.default, 0.4)} 100%)`,
            border: '1px solid',
            borderColor: 'divider'
          }}>
            <CardContent sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight={700}>Market Trend & Strategy Performance</Typography>
                <Stack direction="row" spacing={2} alignItems="center">
                   {/* Placeholder for future sliders */}
                   <Typography variant="caption" color="text.secondary">Strategy Risk: Medium</Typography>
                </Stack>
              </Box>
              
              <Box sx={{ flexGrow: 1, minHeight: 0 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={prices}>
                    <defs>
                      <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={alpha(theme.palette.text.secondary, 0.1)} />
                    <XAxis 
                      dataKey="time" 
                      stroke={alpha(theme.palette.text.secondary, 0.5)} 
                      fontSize={12} 
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      domain={['auto', 'auto']} 
                      stroke={alpha(theme.palette.text.secondary, 0.5)} 
                      fontSize={12} 
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(val) => `$${val.toLocaleString()}`}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: theme.palette.background.paper, 
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 8,
                        boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                      }}
                      itemStyle={{ color: theme.palette.text.primary }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="price" 
                      stroke={theme.palette.primary.main} 
                      fillOpacity={1} 
                      fill="url(#colorPrice)" 
                      strokeWidth={2} 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Column: Pipeline & Signals */}
        <Grid item xs={12} lg={4}>
          <Stack spacing={3}>
            {/* Pipeline Pulse */}
            <Card sx={{ bgcolor: alpha(theme.palette.background.paper, 0.5), border: '1px solid', borderColor: 'divider' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>
                  MLOps Pipeline Pulse
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'relative' }}>
                  {/* Connecting Line */}
                  <Box sx={{ 
                    position: 'absolute', top: 8, left: 20, right: 20, height: 2, 
                    bgcolor: alpha(theme.palette.text.disabled, 0.2), zIndex: 0 
                  }} />
                  {pipeline.stages.map((stage) => (
                    <Box key={stage.id} sx={{ zIndex: 1, bgcolor: theme.palette.background.paper }}>
                      <PipelineNode label={stage.label} status={stage.status} />
                    </Box>
                  ))}
                </Box>
                <Typography variant="caption" display="block" textAlign="right" sx={{ mt: 2, color: 'text.secondary' }}>
                  Last training: {new Date(pipeline.last_retrained).toLocaleTimeString()}
                </Typography>
              </CardContent>
            </Card>

            {/* Signal Stream */}
            <Card sx={{ flexGrow: 1, bgcolor: alpha(theme.palette.background.paper, 0.5), border: '1px solid', borderColor: 'divider' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Live Signal Stream
                  </Typography>
                  {isAdmin && <Button size="small" variant="text">View Log</Button>}
                </Box>
                
                <Stack spacing={2}>
                  {signals.map((signal) => (
                    <Box key={signal.id} sx={{ 
                      p: 1.5, 
                      borderRadius: 2, 
                      bgcolor: alpha(theme.palette.background.default, 0.5),
                      border: '1px solid',
                      borderColor: alpha(theme.palette.divider, 0.5),
                      display: 'flex', 
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      transition: 'transform 0.2s',
                      '&:hover': { transform: 'translateX(4px)', borderColor: theme.palette.primary.main }
                    }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{signal.symbol}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {new Date(signal.timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right' }}>
                        <Chip 
                          label={signal.signal_type} 
                          color={signal.signal_type === 'BUY' ? 'success' : signal.signal_type === 'SELL' ? 'error' : 'default'}
                          size="small"
                          sx={{ mb: 0.5, fontWeight: 700, height: 20 }}
                        />
                        <Typography variant="caption" display="block" color="text.secondary">
                          {(signal.confidence * 100).toFixed(0)}% Conf.
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Stack>
                
                {!isAdmin && (
                  <Box sx={{ mt: 2, p: 1.5, bgcolor: alpha(theme.palette.warning.main, 0.1), borderRadius: 2, display: 'flex', gap: 1.5, alignItems: 'center' }}>
                    <Lock size={16} color={theme.palette.warning.main} />
                    <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.2 }}>
                      Deep logs & XAI weights restricted to admin.
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>
      
      <style>{`
        @keyframes pulse {
          0% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0.4); }
          70% { box-shadow: 0 0 0 6px rgba(0, 210, 255, 0); }
          100% { box-shadow: 0 0 0 0 rgba(0, 210, 255, 0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </Box>
  );
};

export default Dashboard;