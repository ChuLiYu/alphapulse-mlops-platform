import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3f51b5', // Deep Blue
    },
    secondary: {
      main: '#f50057', // Pink/Red
    },
    success: {
      main: '#00C853', // Trading Green
    },
    error: {
      main: '#D50000', // Trading Red
    },
    background: {
      default: '#0a192f', // Navy background
      paper: '#112240',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 700,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          borderRadius: 12,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

export default theme;
