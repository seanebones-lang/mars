'use client';

import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, Container, IconButton, Tooltip, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import { 
  VisibilityOutlined, 
  DashboardOutlined, 
  AssessmentOutlined, 
  ScienceOutlined, 
  LightModeOutlined, 
  DarkModeOutlined, 
  CloudUploadOutlined, 
  AnalyticsOutlined, 
  WebhookOutlined, 
  RocketLaunchOutlined, 
  ExpandMoreOutlined, 
  CodeOutlined, 
  SettingsOutlined,
  MonitorHeartOutlined,
  TuneOutlined,
  SecurityOutlined,
  SpeedOutlined,
  BugReportOutlined,
  PlayArrowOutlined,
  ComputerOutlined
} from '@mui/icons-material';
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
  const [monitoringAnchor, setMonitoringAnchor] = React.useState<null | HTMLElement>(null);
  const [integrationsAnchor, setIntegrationsAnchor] = React.useState<null | HTMLElement>(null);
  const [testingAnchor, setTestingAnchor] = React.useState<null | HTMLElement>(null);
  const [isHydrated, setIsHydrated] = React.useState(false);

  React.useEffect(() => {
    setIsHydrated(true);
  }, []);

  // Core navigation - just Dashboard
  const coreNavItems = [
    { label: 'Dashboard', href: '/', icon: <DashboardOutlined /> },
  ];

  // Monitoring & Analytics dropdown
  const monitoringItems = [
    { label: 'Live Monitor', href: '/monitor', icon: <MonitorHeartOutlined />, description: 'Real-time agent monitoring' },
    { label: 'Agent Reliability', href: '/reliability', icon: <AssessmentOutlined />, description: 'AI agent safety dashboard' },
    { label: 'Workstations', href: '/workstations', icon: <ComputerOutlined />, description: 'Enterprise workstation dashboard' },
    { label: 'Analytics', href: '/analytics', icon: <AnalyticsOutlined />, description: 'Performance insights & trends' },
    { label: 'Performance', href: '/performance', icon: <SpeedOutlined />, description: 'System health & metrics' },
    { label: 'Custom Rules', href: '/custom-rules', icon: <TuneOutlined />, description: 'Industry-specific detection' },
  ];

  // Deploy & Integrations dropdown
  const integrationItems = [
    { label: 'Webhooks', href: '/webhooks', icon: <WebhookOutlined />, description: 'Slack, Teams, Email alerts' },
    { label: 'Python SDK', href: '/sdk', icon: <CodeOutlined />, description: 'Enterprise integration library' },
    { label: 'Batch Processing', href: '/batch', icon: <CloudUploadOutlined />, description: 'Bulk analysis & exports' },
    { label: 'API Docs', href: '/docs', icon: <SettingsOutlined />, description: 'REST API documentation' },
  ];

  // Testing & Demo dropdown
  const testingItems = [
    { label: 'Agent Validator', href: '/freeform', icon: <ScienceOutlined />, description: 'Instant AI agent validation' },
    { label: 'Industry Scenarios', href: '/scenarios', icon: <PlayArrowOutlined />, description: 'Real-world testing scenarios' },
    { label: 'Batch Testing', href: '/batch-testing', icon: <CloudUploadOutlined />, description: 'Bulk agent validation' },
    { label: 'Demo Mode', href: '/demo', icon: <PlayArrowOutlined />, description: 'Interactive demonstration' },
    { label: 'Debug Tools', href: '/debug', icon: <BugReportOutlined />, description: 'Advanced debugging features' },
  ];

  // Dropdown handlers
  const handleMonitoringClick = (event: React.MouseEvent<HTMLElement>) => {
    setMonitoringAnchor(event.currentTarget);
  };
  const handleMonitoringClose = () => {
    setMonitoringAnchor(null);
  };

  const handleIntegrationsClick = (event: React.MouseEvent<HTMLElement>) => {
    setIntegrationsAnchor(event.currentTarget);
  };
  const handleIntegrationsClose = () => {
    setIntegrationsAnchor(null);
  };

  const handleTestingClick = (event: React.MouseEvent<HTMLElement>) => {
    setTestingAnchor(event.currentTarget);
  };
  const handleTestingClose = () => {
    setTestingAnchor(null);
  };

  // Active state checks
  const isMonitoringActive = monitoringItems.some(item => pathname === item.href);
  const isIntegrationsActive = integrationItems.some(item => pathname === item.href);
  const isTestingActive = testingItems.some(item => pathname === item.href);

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
            <VisibilityOutlined sx={{ color: 'white', fontSize: '20px' }} />
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
            {/* Core Navigation Items */}
            {coreNavItems.map((item) => (
              <Link key={item.href} href={item.href} passHref style={{ textDecoration: 'none' }}>
                <Button
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
              </Link>
            ))}

            {/* Monitoring Dropdown */}
            <Button
              onClick={handleMonitoringClick}
              endIcon={<ExpandMoreOutlined />}
              startIcon={<MonitorHeartOutlined />}
              color="inherit"
              sx={{
                fontWeight: isMonitoringActive ? 600 : 400,
                borderBottom: isMonitoringActive ? 2 : 0,
                borderRadius: 0,
                borderColor: 'primary.main',
              }}
            >
              Monitor
            </Button>

            {/* Testing Dropdown */}
            <Button
              onClick={handleTestingClick}
              endIcon={<ExpandMoreOutlined />}
              startIcon={<ScienceOutlined />}
              color="inherit"
              sx={{
                fontWeight: isTestingActive ? 600 : 400,
                borderBottom: isTestingActive ? 2 : 0,
                borderRadius: 0,
                borderColor: 'primary.main',
              }}
            >
              Test
            </Button>

            {/* Deploy Dropdown */}
            <Button
              onClick={handleIntegrationsClick}
              endIcon={<ExpandMoreOutlined />}
              startIcon={<RocketLaunchOutlined />}
              color="inherit"
              sx={{
                fontWeight: isIntegrationsActive ? 600 : 400,
                borderBottom: isIntegrationsActive ? 2 : 0,
                borderRadius: 0,
                borderColor: 'primary.main',
              }}
            >
              Deploy
            </Button>

            {/* Monitoring Menu */}
            <Menu
              anchorEl={monitoringAnchor}
              open={Boolean(monitoringAnchor)}
              onClose={handleMonitoringClose}
              PaperProps={{
                sx: {
                  mt: 1,
                  minWidth: 280,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                  border: '1px solid',
                  borderColor: 'divider',
                }
              }}
            >
              {monitoringItems.map((item) => (
                <Link key={item.href} href={item.href} passHref style={{ textDecoration: 'none', color: 'inherit' }}>
                  <MenuItem
                    onClick={handleMonitoringClose}
                    sx={{
                      py: 1.5,
                      backgroundColor: pathname === item.href ? 'action.selected' : 'transparent',
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      secondary={item.description}
                      primaryTypographyProps={{
                        fontWeight: pathname === item.href ? 600 : 400,
                      }}
                      secondaryTypographyProps={{
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                      }}
                    />
                  </MenuItem>
                </Link>
              ))}
            </Menu>

            {/* Testing Menu */}
            <Menu
              anchorEl={testingAnchor}
              open={Boolean(testingAnchor)}
              onClose={handleTestingClose}
              PaperProps={{
                sx: {
                  mt: 1,
                  minWidth: 280,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                  border: '1px solid',
                  borderColor: 'divider',
                }
              }}
            >
              {testingItems.map((item) => (
                <Link key={item.href} href={item.href} passHref style={{ textDecoration: 'none', color: 'inherit' }}>
                  <MenuItem
                    onClick={handleTestingClose}
                    sx={{
                      py: 1.5,
                      backgroundColor: pathname === item.href ? 'action.selected' : 'transparent',
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      secondary={item.description}
                      primaryTypographyProps={{
                        fontWeight: pathname === item.href ? 600 : 400,
                      }}
                      secondaryTypographyProps={{
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                      }}
                    />
                  </MenuItem>
                </Link>
              ))}
            </Menu>
            
            {/* Deploy Menu */}
            <Menu
              anchorEl={integrationsAnchor}
              open={Boolean(integrationsAnchor)}
              onClose={handleIntegrationsClose}
              PaperProps={{
                sx: {
                  mt: 1,
                  minWidth: 280,
                  boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
                  border: '1px solid',
                  borderColor: 'divider',
                }
              }}
            >
              {integrationItems.map((item) => (
                <Link key={item.href} href={item.href} passHref style={{ textDecoration: 'none', color: 'inherit' }}>
                  <MenuItem
                    onClick={handleIntegrationsClose}
                    sx={{
                      py: 1.5,
                      backgroundColor: pathname === item.href ? 'action.selected' : 'transparent',
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      secondary={item.description}
                      primaryTypographyProps={{
                        fontWeight: pathname === item.href ? 600 : 400,
                      }}
                      secondaryTypographyProps={{
                        fontSize: '0.75rem',
                        color: 'text.secondary',
                      }}
                    />
                  </MenuItem>
                </Link>
              ))}
            </Menu>
            
            {/* Dark Mode Toggle */}
            <Tooltip title={isHydrated ? (darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode') : 'Theme Toggle'}>
              <IconButton
                onClick={onToggleDarkMode}
                color="inherit"
                sx={{ ml: 1 }}
              >
                {isHydrated ? (darkMode ? <LightModeOutlined /> : <DarkModeOutlined />) : <LightModeOutlined />}
              </IconButton>
            </Tooltip>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

