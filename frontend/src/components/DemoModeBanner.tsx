import React from 'react';
import { Box, Typography, alpha, useTheme } from '@mui/material';

const DemoModeBanner: React.FC = () => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        background: 'linear-gradient(90deg, #1a1a2e, #16213e)',
        borderBottom: '1px solid #0f3460',
        padding: '8px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: 13,
        color: '#8892b0',
      }}
    >
      <span>
        <span style={{ color: '#64ffda', fontWeight: 700 }}>● DEMO MODE</span> —
        Prices simulated via Geometric Brownian Motion. No real trades. No
        backend.
      </span>
      <a
        href="https://github.com/ChuLiYu/alphapulse-mlops-platform"
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: '#64ffda', textDecoration: 'none' }}
      >
        View Source →
      </a>
    </Box>
  );
};

export default DemoModeBanner;
