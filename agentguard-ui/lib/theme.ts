import { createTheme, ThemeOptions } from '@mui/material/styles';

// Create theme factory function for light/dark modes
export const createWatcherTheme = (mode: 'light' | 'dark') => {
  const isLight = mode === 'light';
  
  const themeOptions: ThemeOptions = {
    palette: {
      mode,
      primary: {
        main: '#1976D2', // MUI standard tech-blue for trust
        light: '#42A5F5',
        dark: '#1565C0',
      },
      secondary: {
        main: '#00BCD4', // Cyan for high-tech accent
        light: '#4DD0E1',
        dark: '#0097A7',
      },
      error: {
        main: '#F44336',
        light: '#EF5350',
        dark: '#D32F2F',
      },
      warning: {
        main: '#FF9800',
        light: '#FFB74D',
        dark: '#F57C00',
      },
      success: {
        main: '#4CAF50',
        light: '#66BB6A',
        dark: '#388E3C',
      },
      background: {
        default: isLight ? '#F5F7FA' : '#0A0E1A', // Dark navy for high-tech feel
        paper: isLight ? '#FFFFFF' : '#1A1F2E', // Dark cards
      },
      text: {
        primary: isLight ? '#1A202C' : '#E2E8F0',
        secondary: isLight ? '#4A5568' : '#94A3B8',
      },
      divider: isLight ? '#E2E8F0' : '#334155',
      // Custom Watcher-AI colors
      info: {
        main: '#1976D2', // Consistent with primary
        light: '#42A5F5',
        dark: '#1565C0',
      },
    },
    typography: {
      fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif',
      h1: {
        fontWeight: 700,
        letterSpacing: '-0.025em',
        color: isLight ? '#1A202C' : '#F7FAFC',
      },
      h2: {
        fontWeight: 700,
        letterSpacing: '-0.025em',
        color: isLight ? '#1A202C' : '#F7FAFC',
      },
      h3: {
        fontWeight: 700,
        letterSpacing: '-0.025em',
        color: isLight ? '#1A202C' : '#F7FAFC',
      },
      h4: {
        fontWeight: 600,
        letterSpacing: '-0.02em',
        color: isLight ? '#2D3748' : '#E2E8F0',
      },
      h5: {
        fontWeight: 600,
        letterSpacing: '-0.015em',
        color: isLight ? '#2D3748' : '#E2E8F0',
      },
      h6: {
        fontWeight: 600,
        letterSpacing: '-0.01em',
        color: isLight ? '#2D3748' : '#E2E8F0',
      },
      body1: {
        letterSpacing: '-0.01em',
        color: isLight ? '#4A5568' : '#CBD5E0',
      },
      button: {
        fontWeight: 600,
        letterSpacing: '0.025em',
        textTransform: 'none' as const,
      },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 10,
            padding: '10px 24px',
            boxShadow: 'none',
            '&:hover': {
              boxShadow: isLight 
                ? '0 4px 12px rgba(25, 118, 210, 0.15)' 
                : '0 4px 12px rgba(25, 118, 210, 0.25)',
              transform: 'translateY(-1px)',
              transition: 'all 0.2s ease-in-out',
            },
          },
          contained: {
            background: isLight 
              ? 'linear-gradient(135deg, #1976D2 0%, #1565C0 100%)'
              : 'linear-gradient(135deg, #42A5F5 0%, #1976D2 100%)',
            '&:hover': {
              background: isLight
                ? 'linear-gradient(135deg, #1565C0 0%, #0D47A1 100%)'
                : 'linear-gradient(135deg, #1976D2 0%, #1565C0 100%)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            boxShadow: isLight 
              ? '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)'
              : '0 4px 6px rgba(0, 0, 0, 0.3), 0 2px 4px rgba(0, 0, 0, 0.2)',
            border: isLight 
              ? '1px solid rgba(226, 232, 240, 0.8)' 
              : '1px solid rgba(51, 65, 85, 0.8)',
            backgroundColor: isLight ? '#FFFFFF' : '#1A1F2E',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            boxShadow: isLight 
              ? '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)'
              : '0 4px 6px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)',
            border: isLight 
              ? '1px solid rgba(226, 232, 240, 0.6)' 
              : '1px solid rgba(51, 65, 85, 0.6)',
            backgroundColor: isLight ? '#FFFFFF' : '#1A1F2E',
            '&:hover': {
              boxShadow: isLight 
                ? '0 4px 6px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.1)'
                : '0 8px 12px rgba(0, 0, 0, 0.4), 0 4px 8px rgba(0, 0, 0, 0.3)',
              transform: 'translateY(-1px)',
              transition: 'all 0.2s ease-in-out',
            },
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            fontWeight: 500,
          },
          standardSuccess: {
            background: isLight 
              ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(56, 142, 60, 0.05) 100%)'
              : 'linear-gradient(135deg, rgba(76, 175, 80, 0.2) 0%, rgba(56, 142, 60, 0.1) 100%)',
            border: `1px solid rgba(76, 175, 80, ${isLight ? '0.2' : '0.3'})`,
          },
          standardError: {
            background: isLight 
              ? 'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(211, 47, 47, 0.05) 100%)'
              : 'linear-gradient(135deg, rgba(244, 67, 54, 0.2) 0%, rgba(211, 47, 47, 0.1) 100%)',
            border: `1px solid rgba(244, 67, 54, ${isLight ? '0.2' : '0.3'})`,
          },
          standardWarning: {
            background: isLight 
              ? 'linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(245, 124, 0, 0.05) 100%)'
              : 'linear-gradient(135deg, rgba(255, 152, 0, 0.2) 0%, rgba(245, 124, 0, 0.1) 100%)',
            border: `1px solid rgba(255, 152, 0, ${isLight ? '0.2' : '0.3'})`,
          },
          standardInfo: {
            background: isLight 
              ? 'linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(21, 101, 192, 0.05) 100%)'
              : 'linear-gradient(135deg, rgba(25, 118, 210, 0.2) 0%, rgba(21, 101, 192, 0.1) 100%)',
            border: `1px solid rgba(25, 118, 210, ${isLight ? '0.2' : '0.3'})`,
          },
        },
      },
    },
  };

  return createTheme(themeOptions);
};

// Default light theme
const theme = createWatcherTheme('light');
export default theme;

