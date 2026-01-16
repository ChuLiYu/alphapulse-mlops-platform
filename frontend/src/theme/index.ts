import { createTheme, alpha } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00d2ff', // Cyber Blue
      light: '#6fffff',
      dark: '#00a0cc',
    },
    secondary: {
      main: '#00ff9f', // Neon Green / Success
    },
    success: {
      main: '#00ff9f',
    },
    error: {
      main: '#ff2e63', // Neon Red
    },
    warning: {
      main: '#f39c12',
    },
    background: {
      default: '#050a14', // Very deep black/navy
      paper: '#0d1624',
    },
    text: {
      primary: '#e6f1ff',
      secondary: '#8892b0',
    },
  },
  typography: {
    fontFamily: '"Inter", "JetBrains Mono", "Roboto", sans-serif',
    h4: {
      fontWeight: 800,
      letterSpacing: '-0.02em',
    },
    h6: {
      fontWeight: 700,
      letterSpacing: '0.01em',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: alpha('#0d1624', 0.8),
          backdropFilter: 'blur(10px)',
          border: `1px solid ${alpha('#00d2ff', 0.1)}`,
          boxShadow: `0 8px 32px 0 ${alpha('#000', 0.4)}`,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            boxShadow: `0 0 15px ${alpha('#00d2ff', 0.4)}`,
          },
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          color: '#00d2ff',
        },
        thumb: {
          '&:hover, &.Mui-focusVisible': {
            boxShadow: `0 0 0 8px ${alpha('#00d2ff', 0.16)}`,
          },
        },
      },
    },
  },
});

export default theme;
