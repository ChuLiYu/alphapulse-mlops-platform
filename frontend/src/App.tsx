import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import theme from './theme';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';

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
              <Route path="/market" element={<Box><Typography variant="h4">Market Data (Coming Soon)</Typography></Box>} />
              <Route path="/signals" element={<Box><Typography variant="h4">Trading Signals (Coming Soon)</Typography></Box>} />
              <Route path="/status" element={<Box><Typography variant="h4">System Status (Coming Soon)</Typography></Box>} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

import { Typography } from '@mui/material';

export default App;
