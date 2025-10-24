'use client';

import { AppBar, Toolbar, Typography, Button, Box, Container } from '@mui/material';
import { Security, Dashboard, Assessment, Science } from '@mui/icons-material';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Dashboard', href: '/', icon: <Dashboard /> },
    { label: 'Quick Test', href: '/freeform', icon: <Science /> },
    { label: 'Demo', href: '/demo', icon: <Science /> },
    { label: 'Metrics', href: '/metrics', icon: <Assessment /> },
  ];

  return (
    <AppBar position="static" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Security sx={{ mr: 1.5, fontSize: 30 }} />
          <Typography
            variant="h6"
            component="div"
            sx={{ flexGrow: 1, fontWeight: 600, letterSpacing: -0.5 }}
          >
            AgentGuard
          </Typography>

          <Box sx={{ display: 'flex', gap: 1 }}>
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
                  borderColor: 'white',
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

