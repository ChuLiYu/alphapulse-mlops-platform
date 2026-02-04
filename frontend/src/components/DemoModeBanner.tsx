import React from 'react';
import { Box, Typography, alpha, useTheme } from '@mui/material';
import { Sparkles } from 'lucide-react';

const DemoModeBanner: React.FC = () => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        bgcolor: alpha(theme.palette.secondary.main, 0.9),
        color: 'white',
        py: 0.5,
        px: 2,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1.5,
        position: 'sticky',
        top: 0,
        zIndex: 2000,
        backdropFilter: 'blur(10px)',
        borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
        boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
      }}
    >
      <Sparkles size={16} />
      <Typography variant="caption" sx={{ fontWeight: 800, letterSpacing: 1.2, textTransform: 'uppercase' }}>
        Hero Demo Mode Active • Static MLOps Infrastructure Simulation
      </Typography>
      <Sparkles size={16} />
    </Box>
  );
};

export default DemoModeBanner;
