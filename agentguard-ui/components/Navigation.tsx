'use client';

import { AppBar, Toolbar, Typography, Button, Box, Container, IconButton, Tooltip } from '@mui/material';
import { Visibility, Dashboard, Assessment, Science, LightMode, DarkMode } from '@mui/icons-material';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTheme } from '@mui/material/styles';

interface NavigationProps {
  darkMode?: boolean;
  onToggleDarkMode?: () => void;
}

export default function Navigation({ darkMode = false, onToggleDarkMode }: NavigationProps) {
  const pathname = usePathname();
  const theme = useTheme();

  const navItems = [
    { label: 'Dashboard', href: '/', icon: <Dashboard /> },
    { label: 'Live Monitor', href: '/monitor', icon: <Assessment /> },
    { label: 'Quick Test', href: '/freeform', icon: <Science /> },
    { label: 'Demo', href: '/demo', icon: <Science /> },
    { label: 'Metrics', href: '/metrics', icon: <Assessment /> },
  ];

  return (
    <AppBar position="static" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #1976D2 0%, #1565C0 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: 2,
              boxShadow: '0 3px 10px rgba(25, 118, 210, 0.3)',
            }}
          >
            <Visibility sx={{ color: 'white', fontSize: '20px' }} />
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography
              variant="h6"
              component="div"
              sx={{ fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2 }}
            >
              Watcher-AI
            </Typography>
            <Typography
              variant="caption"
              sx={{ 
                color: 'text.secondary', 
                fontSize: '11px',
                fontWeight: 500,
                letterSpacing: '0.02em'
              }}
            >
              Real-Time Hallucination Defense
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {navItems.map((item) => (
              <Button
                key={item.href}
                component={Link}
                href={item.href}
                startIcon={item.icon}
                color="inherit"
                sx={{
                  fontWeight: pathname === item.href ? 600 : 400,
                  borderBottom: pathname === item.href ? 2 : 0,
                  borderRadius: 0,
                  borderColor: 'primary.main',
                }}
              >
                {item.label}
              </Button>
            ))}
            
            {/* Dark Mode Toggle */}
            <Tooltip title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              <IconButton
                onClick={onToggleDarkMode}
                color="inherit"
                sx={{ ml: 1 }}
              >
                {darkMode ? <LightMode /> : <DarkMode />}
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

