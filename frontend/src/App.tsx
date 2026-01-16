import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box, Typography, alpha } from '@mui/material';
import theme from './theme';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import MLOpsConsole from './pages/MLOpsConsole';

const PlaceholderPage: React.FC<{ title: string }> = ({ title }) => (
  <Box 
    sx={{ 
      height: '80vh', 
      display: 'flex', 
      flexDirection: 'column',
      justifyContent: 'center', 
      alignItems: 'center',
      border: '1px dashed',
      borderColor: alpha('#00d2ff', 0.2),
      borderRadius: 4,
      bgcolor: alpha('#00d2ff', 0.02)
    }}
  >
    <Typography variant="h4" gutterBottom color="primary">{title}</Typography>
    <Typography variant="body1" color="text.secondary">This feature is currently under development for the MLOps Platform.</Typography>
  </Box>
);

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
          <Sidebar />
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 4,
              width: { sm: `calc(100% - 240px)` },
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/market" element={<PlaceholderPage title="Market Data" />} />
              <Route path="/signals" element={<PlaceholderPage title="Trading Signals" />} />
              <Route path="/status" element={<MLOpsConsole />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;
