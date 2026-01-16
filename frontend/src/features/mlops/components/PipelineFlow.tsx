import React, { useEffect, useState } from 'react';
import { Box, Typography, Stack, alpha, useTheme } from '@mui/material';
import { motion } from 'framer-motion';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PlayCircleFilledIcon from '@mui/icons-material/PlayCircleFilled';
import AccessTimeFilledIcon from '@mui/icons-material/AccessTimeFilled';
import apiClient from '../../../api/client';

const defaultStages = [
  { id: 'ingest', label: 'Data Ingestion', status: 'success' },
  { id: 'validate', label: 'Data Validation', status: 'success' },
  { id: 'train', label: 'Model Training', status: 'running' },
  { id: 'eval', label: 'Evaluation', status: 'pending' },
  { id: 'deploy', label: 'Deployment', status: 'pending' },
];

const PipelineFlow: React.FC = () => {
  const theme = useTheme();
  const [stages, setStages] = useState(defaultStages);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await apiClient.get('/v1/ops/pipeline-status');
        if (response.data && response.data.stages) {
          // Map backend stages to UI stages if needed, 
          // but here we just use backend data if available
          const mapped = response.data.stages.map((s: any) => ({
            id: s.name.toLowerCase(),
            label: s.name,
            status: s.status === 'active' ? 'running' : s.status === 'healthy' || s.status === 'idle' ? 'success' : 'pending'
          }));
          // Merge or replace depending on how many stages backend returns
          if (mapped.length > 0) setStages(mapped);
        }
      } catch (error) {
        console.error('Failed to fetch pipeline status', error);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ p: 3, bgcolor: alpha(theme.palette.background.paper, 0.5), borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 4 }}>Live Pipeline Execution</Typography>
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems="center" justifyContent="center">
        {stages.map((stage, index) => (
          <React.Fragment key={stage.id}>
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
            >
              <Box sx={{ 
                p: 2, 
                borderRadius: 2, 
                border: '1px solid',
                borderColor: stage.status === 'running' ? 'primary.main' : alpha(theme.palette.divider, 0.1),
                bgcolor: stage.status === 'running' ? alpha(theme.palette.primary.main, 0.05) : 'transparent',
                textAlign: 'center',
                minWidth: 140,
                position: 'relative'
              }}>
                {stage.status === 'success' && <CheckCircleIcon color="secondary" sx={{ fontSize: 20, mb: 1 }} />}
                {stage.status === 'running' && (
                  <motion.div animate={{ rotate: 360 }} transition={{ duration: 2, repeat: Infinity, ease: "linear" }}>
                    <PlayCircleFilledIcon color="primary" sx={{ fontSize: 20, mb: 1 }} />
                  </motion.div>
                )}
                {stage.status === 'pending' && <AccessTimeFilledIcon sx={{ fontSize: 20, mb: 1, color: 'text.disabled' }} />}
                
                <Typography variant="body2" fontWeight="bold" color={stage.status === 'pending' ? 'text.disabled' : 'text.primary'}>
                  {stage.label}
                </Typography>
                
                {stage.status === 'running' && (
                  <Typography variant="caption" color="primary" sx={{ display: 'block', mt: 0.5 }}>
                    Processing...
                  </Typography>
                )}
              </Box>
            </motion.div>
            
            {index < stages.length - 1 && (
              <Box sx={{ 
                width: { xs: 2, md: 40 }, 
                height: { xs: 20, md: 2 }, 
                bgcolor: stage.status === 'success' ? 'secondary.main' : alpha(theme.palette.divider, 0.2),
                transition: 'all 0.5s ease'
              }} />
            )}
          </React.Fragment>
        ))}
      </Stack>
    </Box>
  );
};

export default PipelineFlow;
