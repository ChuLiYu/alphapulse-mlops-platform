import React from 'react';
import { Box, Typography, Grid, Card, CardContent, alpha, useTheme } from '@mui/material';
import { motion } from 'framer-motion';
import SettingsInputComponentIcon from '@mui/icons-material/SettingsInputComponent';
import PipelineFlow from '../features/mlops/components/PipelineFlow';
import DriftMonitor from '../features/mlops/components/DriftMonitor';
import ModelRegistry from '../features/mlops/components/ModelRegistry';

const MLOpsConsole: React.FC = () => {
  const theme = useTheme();

  return (
    <Box>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <SettingsInputComponentIcon color="primary" sx={{ fontSize: 32 }} />
          MLOps Command Center
        </Typography>
        <Typography variant="body2" color="text.secondary">
          End-to-end lifecycle management: from automated pipelines to production monitoring.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Full Width: Pipeline Flow */}
        <Grid item xs={12}>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
            <Card>
              <PipelineFlow />
            </Card>
          </motion.div>
        </Grid>

        {/* Half Width: Drift Monitoring */}
        <Grid item xs={12} md={6}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
            <Card sx={{ height: '100%' }}>
              <DriftMonitor />
            </Card>
          </motion.div>
        </Grid>

        {/* Half Width: Model Registry */}
        <Grid item xs={12} md={6}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.3 }}>
            <Card sx={{ height: '100%' }}>
              <ModelRegistry />
            </Card>
          </motion.div>
        </Grid>

        {/* System Logs / Stats */}
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.05) }}>
            <CardContent>
              <Typography variant="overline" color="secondary.main" fontWeight="bold">Training Efficiency</Typography>
              <Typography variant="h4">98.2%</Typography>
              <Typography variant="caption" color="text.secondary">GPU Utilization (A100 Cluster)</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
            <CardContent>
              <Typography variant="overline" color="primary.main" fontWeight="bold">Average Latency</Typography>
              <Typography variant="h4">112ms</Typography>
              <Typography variant="caption" color="text.secondary">Inference P99 (FastAPI)</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card sx={{ bgcolor: alpha(theme.palette.error.main, 0.05) }}>
            <CardContent>
              <Typography variant="overline" color="error.main" fontWeight="bold">Retraining Cycle</Typography>
              <Typography variant="h4">24h</Typography>
              <Typography variant="caption" color="text.secondary">Automated Daily Refresh</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MLOpsConsole;
