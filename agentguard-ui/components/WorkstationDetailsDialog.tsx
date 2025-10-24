"use client";

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Avatar,
  LinearProgress,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Badge,
  Tooltip,
  IconButton,
  Stack,
  Tab,
  Tabs,
  CircularProgress,
} from '@mui/material';
import {
  ComputerOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  WarningOutlined,
  InfoOutlined,
  SpeedOutlined,
  MemoryOutlined,
  StorageOutlined,
  NetworkCheckOutlined,
  SecurityOutlined,
  BugReportOutlined,
  UpdateOutlined,
  PlayArrowOutlined,
  StopOutlined,
  RestartAltOutlined,
  SettingsOutlined,
  LocationOnOutlined,
  BusinessOutlined,
  PersonOutlined,
  DevicesOutlined,
  WifiOutlined,
  VpnKeyOutlined,
  ShieldOutlined,
  ExpandMoreOutlined,
  CloseOutlined,
  RefreshOutlined,
  VisibilityOutlined,
  CodeOutlined,
  CloudOutlined,
  TimelineOutlined,
  AssessmentOutlined,
  NotificationsOutlined,
  AutoAwesome,
  Psychology,
  Lightbulb,
  TrendingUp,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { agentGuardApi } from '@/lib/api';

interface Workstation {
  id: string;
  hostname: string;
  status: string;
  location: string;
  department: string;
  ipAddress: string;
  lastSeen: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  agentCount: number;
  alertCount: number;
  platform: string;
  version: string;
  uptime: number;
  networkLatency: number;
  coordinates: {
    lat: number;
    lng: number;
  };
  // Additional backend fields
  macAddress: string;
  user: string;
  cpuCount: number;
  memoryTotalGb: number;
  diskTotalGb: number;
  platformVersion: string;
  pythonVersion: string;
  watcherClientVersion: string;
  manufacturer?: string;
  model?: string;
  serialNumber?: string;
  openPorts: number[];
  services: { [port: number]: string };
  installedSoftware: string[];
  runningProcesses: string[];
  vulnerabilities: Array<{ severity: string; description: string; cve?: string }>;
  securityScore?: number;
  agentInstalled: boolean;
  agentVersion?: string;
  agentStatus?: string;
  discoveryMethod: string;
  tags: string[];
}

interface WorkstationDetailsDialogProps {
  open: boolean;
  workstation: Workstation | null;
  onClose: () => void;
  onAction: (action: string, workstationId: string) => void;
  actionInProgress: string | null;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'online': return 'success';
    case 'monitoring': return 'info';
    case 'offline': return 'default';
    case 'error': return 'error';
    case 'maintenance': return 'warning';
    default: return 'default';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'online': return <CheckCircleOutlined />;
    case 'monitoring': return <SpeedOutlined />;
    case 'offline': return <ComputerOutlined />;
    case 'error': return <ErrorOutlined />;
    case 'maintenance': return <WarningOutlined />;
    default: return <InfoOutlined />;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'high': return 'error';
    case 'medium': return 'warning';
    case 'low': return 'info';
    default: return 'default';
  }
};

const formatUptime = (seconds: number) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) {
    return `${days}d ${hours}h ${minutes}m`;
  }
  return `${hours}h ${minutes}m`;
};

const formatBytes = (bytes: number) => {
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  if (bytes === 0) return '0 B';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
};

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({
  children,
  value,
  index,
  ...other
}) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`workstation-tabpanel-${index}`}
      aria-labelledby={`workstation-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

export default function WorkstationDetailsDialog({
  open,
  workstation,
  onClose,
  onAction,
  actionInProgress
}: WorkstationDetailsDialogProps) {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [claudeInsights, setClaudeInsights] = useState<any>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);

  if (!workstation) return null;

  // Get Claude insights when dialog opens
  useEffect(() => {
    if (open && workstation && !claudeInsights) {
      getClaudeInsights();
    }
  }, [open, workstation]);

  const getClaudeInsights = async () => {
    if (!workstation) return;
    
    setInsightsLoading(true);
    try {
      const insights = await agentGuardApi.getWorkstationInsights(workstation);
      setClaudeInsights(insights);
      setShowInsights(true);
    } catch (err) {
      console.error('Failed to get Claude insights:', err);
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleRefreshInsights = async () => {
    setClaudeInsights(null);
    await getClaudeInsights();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getSecurityScoreColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="xl"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <Avatar sx={{ 
              bgcolor: getStatusColor(workstation.status) === 'success' ? 'success.main' : 
                       getStatusColor(workstation.status) === 'error' ? 'error.main' :
                       getStatusColor(workstation.status) === 'warning' ? 'warning.main' :
                       getStatusColor(workstation.status) === 'info' ? 'info.main' : 'grey.500',
              width: 48,
              height: 48
            }}>
              {getStatusIcon(workstation.status)}
            </Avatar>
            <Box>
              <Typography variant="h5" fontWeight={600}>
                {workstation.hostname}
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mt={0.5}>
                <Typography variant="body2" color="text.secondary">
                  {workstation.ipAddress} • {workstation.location}
                </Typography>
                <Chip
                  label={workstation.status}
                  color={getStatusColor(workstation.status) as any}
                  size="small"
                />
              </Box>
            </Box>
          </Box>
          <IconButton onClick={onClose}>
            <CloseOutlined />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
            <Tab label="Overview" icon={<AssessmentOutlined />} />
            <Tab label="Hardware" icon={<DevicesOutlined />} />
            <Tab label="Network" icon={<WifiOutlined />} />
            <Tab label="Security" icon={<ShieldOutlined />} />
            <Tab label="Software" icon={<CodeOutlined />} />
            <Tab label="Performance" icon={<TimelineOutlined />} />
            <Tab label="Management" icon={<SettingsOutlined />} />
            <Tab 
              label="Claude Insights" 
              icon={<AutoAwesome />} 
              sx={{ 
                '& .MuiTab-wrapper': { 
                  color: theme.palette.primary.main 
                } 
              }} 
            />
          </Tabs>
        </Box>

        <Box sx={{ px: 3 }}>
          {/* Overview Tab */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              {/* System Status */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="System Status" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Status:</Typography>
                        <Chip
                          label={workstation.status}
                          color={getStatusColor(workstation.status) as any}
                          size="small"
                        />
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Uptime:</Typography>
                        <Typography variant="body2">{formatUptime(workstation.uptime)}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Last Seen:</Typography>
                        <Typography variant="body2">
                          {new Date(workstation.lastSeen).toLocaleString()}
                        </Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Network Latency:</Typography>
                        <Typography variant="body2">{workstation.networkLatency}ms</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Discovery Method:</Typography>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {workstation.discoveryMethod.replace('_', ' ')}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Location & User Info */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Location & User" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LocationOnOutlined fontSize="small" color="action" />
                        <Typography variant="body2">{workstation.location}</Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <BusinessOutlined fontSize="small" color="action" />
                        <Typography variant="body2">{workstation.department}</Typography>
                      </Box>
                      <Box display="flex" alignItems="center" gap={1}>
                        <PersonOutlined fontSize="small" color="action" />
                        <Typography variant="body2">{workstation.user}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Coordinates:</Typography>
                        <Typography variant="body2">
                          {workstation.coordinates.lat.toFixed(4)}, {workstation.coordinates.lng.toFixed(4)}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Performance Overview */}
              <Grid size={12}>
                <Card>
                  <CardHeader title="Performance Overview" />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="primary.main" fontWeight={700}>
                            {workstation.cpuUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            CPU Usage
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.cpuUsage}
                            color={workstation.cpuUsage > 80 ? 'error' : workstation.cpuUsage > 60 ? 'warning' : 'primary'}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="info.main" fontWeight={700}>
                            {workstation.memoryUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Memory Usage ({workstation.memoryTotalGb}GB Total)
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.memoryUsage}
                            color={workstation.memoryUsage > 80 ? 'error' : 'info'}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="success.main" fontWeight={700}>
                            {workstation.diskUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Disk Usage ({workstation.diskTotalGb}GB Total)
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.diskUsage}
                            color={workstation.diskUsage > 80 ? 'error' : 'success'}
                            sx={{ height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Agent Status */}
              <Grid size={12}>
                <Card>
                  <CardHeader title="Agent Status & Alerts" />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: workstation.agentInstalled ? 'success.main' : 'error.main' }}>
                            <ComputerOutlined />
                          </Avatar>
                          <Box>
                            <Typography variant="h6">{workstation.agentCount}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Active Agents
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: workstation.alertCount > 0 ? 'error.main' : 'success.main' }}>
                            <NotificationsOutlined />
                          </Avatar>
                          <Box>
                            <Typography variant="h6">{workstation.alertCount}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Active Alerts
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: 'info.main' }}>
                            <UpdateOutlined />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              {workstation.agentVersion || 'N/A'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Agent Version
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ 
                            bgcolor: workstation.agentStatus === 'active' ? 'success.main' : 
                                     workstation.agentStatus === 'error' ? 'error.main' : 'warning.main'
                          }}>
                            <SpeedOutlined />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight={500} sx={{ textTransform: 'capitalize' }}>
                              {workstation.agentStatus || 'Unknown'}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              Agent Status
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Hardware Tab */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Hardware Information" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Manufacturer:</Typography>
                        <Typography variant="body2">{workstation.manufacturer || 'Unknown'}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Model:</Typography>
                        <Typography variant="body2">{workstation.model || 'Unknown'}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Serial Number:</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {workstation.serialNumber || 'Unknown'}
                        </Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">MAC Address:</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {workstation.macAddress}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="System Specifications" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">CPU Cores:</Typography>
                        <Typography variant="body2">{workstation.cpuCount}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Total Memory:</Typography>
                        <Typography variant="body2">{workstation.memoryTotalGb} GB</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Total Disk:</Typography>
                        <Typography variant="body2">{workstation.diskTotalGb} GB</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Platform:</Typography>
                        <Typography variant="body2">{workstation.platformVersion}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Network Tab */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Network Configuration" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">IP Address:</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {workstation.ipAddress}
                        </Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">MAC Address:</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                          {workstation.macAddress}
                        </Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Network Latency:</Typography>
                        <Typography variant="body2">{workstation.networkLatency}ms</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Open Ports:</Typography>
                        <Typography variant="body2">{workstation.openPorts.length}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Network Services" />
                  <CardContent>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Port</TableCell>
                            <TableCell>Service</TableCell>
                            <TableCell>Status</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {workstation.openPorts.slice(0, 5).map((port) => (
                            <TableRow key={port}>
                              <TableCell sx={{ fontFamily: 'monospace' }}>{port}</TableCell>
                              <TableCell>{workstation.services[port] || 'Unknown'}</TableCell>
                              <TableCell>
                                <Chip label="Open" color="success" size="small" />
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    {workstation.openPorts.length > 5 && (
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                        +{workstation.openPorts.length - 5} more ports
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Security Tab */}
          <TabPanel value={tabValue} index={3}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card>
                  <CardHeader title="Security Score" />
                  <CardContent>
                    <Box textAlign="center">
                      <Typography variant="h2" color={`${getSecurityScoreColor(workstation.securityScore)}.main`} fontWeight={700}>
                        {workstation.securityScore || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Security Score (0-100)
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={workstation.securityScore || 0}
                        color={getSecurityScoreColor(workstation.securityScore) as any}
                        sx={{ mt: 2, height: 8, borderRadius: 4 }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 8 }}>
                <Card>
                  <CardHeader 
                    title="Vulnerabilities" 
                    action={
                      <Badge badgeContent={workstation.vulnerabilities.length} color="error">
                        <BugReportOutlined />
                      </Badge>
                    }
                  />
                  <CardContent>
                    {workstation.vulnerabilities.length === 0 ? (
                      <Alert severity="success">
                        No known vulnerabilities detected
                      </Alert>
                    ) : (
                      <Stack spacing={2}>
                        {workstation.vulnerabilities.map((vuln, index) => (
                          <Alert 
                            key={index} 
                            severity={getSeverityColor(vuln.severity) as any}
                            action={
                              vuln.cve && (
                                <Button size="small" color="inherit">
                                  View CVE
                                </Button>
                              )
                            }
                          >
                            <Typography variant="body2" fontWeight={500}>
                              {vuln.severity.toUpperCase()}: {vuln.description}
                            </Typography>
                            {vuln.cve && (
                              <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                                {vuln.cve}
                              </Typography>
                            )}
                          </Alert>
                        ))}
                      </Stack>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={12}>
                <Card>
                  <CardHeader title="Security Tags" />
                  <CardContent>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {workstation.tags.map((tag) => (
                        <Chip
                          key={tag}
                          label={tag}
                          color="primary"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                      {workstation.tags.length === 0 && (
                        <Typography variant="body2" color="text.secondary">
                          No security tags assigned
                        </Typography>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Software Tab */}
          <TabPanel value={tabValue} index={4}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="System Software" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Platform:</Typography>
                        <Typography variant="body2">{workstation.platformVersion}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Python Version:</Typography>
                        <Typography variant="body2">{workstation.pythonVersion}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Watcher Client:</Typography>
                        <Typography variant="body2">{workstation.watcherClientVersion}</Typography>
                      </Box>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="body2">Agent Version:</Typography>
                        <Typography variant="body2">{workstation.agentVersion || 'Not Installed'}</Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Running Processes" />
                  <CardContent>
                    <List dense>
                      {workstation.runningProcesses.map((process, index) => (
                        <ListItem key={index}>
                          <ListItemIcon>
                            <CodeOutlined fontSize="small" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={process}
                            primaryTypographyProps={{ sx: { fontFamily: 'monospace', fontSize: '0.875rem' } }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={12}>
                <Card>
                  <CardHeader title="Installed Software" />
                  <CardContent>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {workstation.installedSoftware.map((software) => (
                        <Chip
                          key={software}
                          label={software}
                          color="default"
                          variant="outlined"
                          size="small"
                          icon={<CodeOutlined />}
                        />
                      ))}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Performance Tab */}
          <TabPanel value={tabValue} index={5}>
            <Grid container spacing={3}>
              <Grid size={12}>
                <Card>
                  <CardHeader title="Real-time Performance Metrics" />
                  <CardContent>
                    <Grid container spacing={4}>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <SpeedOutlined sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                          <Typography variant="h3" color="primary.main" fontWeight={700}>
                            {workstation.cpuUsage}%
                          </Typography>
                          <Typography variant="body1" color="text.secondary" gutterBottom>
                            CPU Usage ({workstation.cpuCount} cores)
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.cpuUsage}
                            color={workstation.cpuUsage > 80 ? 'error' : workstation.cpuUsage > 60 ? 'warning' : 'primary'}
                            sx={{ height: 12, borderRadius: 6 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <MemoryOutlined sx={{ fontSize: 48, color: 'info.main', mb: 2 }} />
                          <Typography variant="h3" color="info.main" fontWeight={700}>
                            {workstation.memoryUsage}%
                          </Typography>
                          <Typography variant="body1" color="text.secondary" gutterBottom>
                            Memory Usage ({workstation.memoryTotalGb}GB)
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.memoryUsage}
                            color={workstation.memoryUsage > 80 ? 'error' : 'info'}
                            sx={{ height: 12, borderRadius: 6 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <StorageOutlined sx={{ fontSize: 48, color: 'success.main', mb: 2 }} />
                          <Typography variant="h3" color="success.main" fontWeight={700}>
                            {workstation.diskUsage}%
                          </Typography>
                          <Typography variant="body1" color="text.secondary" gutterBottom>
                            Disk Usage ({workstation.diskTotalGb}GB)
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={workstation.diskUsage}
                            color={workstation.diskUsage > 80 ? 'error' : 'success'}
                            sx={{ height: 12, borderRadius: 6 }}
                          />
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={12}>
                <Alert severity="info">
                  <Typography variant="body2" fontWeight={500}>
                    Performance Analysis
                  </Typography>
                  <Typography variant="body2">
                    System performance is {workstation.cpuUsage < 60 && workstation.memoryUsage < 60 ? 'optimal' : 
                    workstation.cpuUsage > 80 || workstation.memoryUsage > 80 ? 'under stress' : 'moderate'}. 
                    Network latency: {workstation.networkLatency}ms. 
                    Uptime: {formatUptime(workstation.uptime)}.
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Management Tab */}
          <TabPanel value={tabValue} index={6}>
            <Grid container spacing={3}>
              {/* Quick Actions */}
              <Grid size={12}>
                <Card>
                  <CardHeader title="Quick Actions" />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<PlayArrowOutlined />}
                          onClick={() => onAction('start_monitoring', workstation.id)}
                          disabled={actionInProgress !== null}
                        >
                          Start Monitoring
                        </Button>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<StopOutlined />}
                          onClick={() => onAction('stop_monitoring', workstation.id)}
                          disabled={actionInProgress !== null}
                        >
                          Stop Monitoring
                        </Button>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<RestartAltOutlined />}
                          onClick={() => onAction('restart_agent', workstation.id)}
                          disabled={actionInProgress !== null}
                        >
                          Restart Agent
                        </Button>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<RefreshOutlined />}
                          onClick={() => onAction('run_diagnostics', workstation.id)}
                          disabled={actionInProgress !== null}
                        >
                          Run Diagnostics
                        </Button>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Advanced Management */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="System Management" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<UpdateOutlined />}
                        onClick={() => onAction('update_software', workstation.id)}
                        disabled={actionInProgress !== null}
                      >
                        Update Software
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<StorageOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Backup Configuration
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<NetworkCheckOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Network Diagnostics
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<MemoryOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Performance Optimization
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Security & Compliance" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Button
                        fullWidth
                        variant="contained"
                        color="warning"
                        startIcon={<SecurityOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Security Scan
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<ShieldOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Compliance Check
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<VisibilityOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Audit Trail
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<VpnKeyOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Policy Enforcement
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Action Progress */}
              {actionInProgress && (
                <Grid size={12}>
                  <Alert severity="info">
                    <Box display="flex" alignItems="center" gap={2}>
                      <LinearProgress sx={{ flexGrow: 1 }} />
                      <Typography variant="body2">
                        Executing: {actionInProgress.replace('_', ' ').toUpperCase()}
                      </Typography>
                    </Box>
                  </Alert>
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* Claude Insights Tab */}
          <TabPanel value={tabValue} index={7}>
            <Box sx={{ py: 2 }}>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
                <Box display="flex" alignItems="center" gap={2}>
                  <AutoAwesome color="primary" />
                  <Typography variant="h6">
                    Claude Intelligence Analysis
                  </Typography>
                  <Chip label="AI Powered" color="primary" size="small" />
                </Box>
                <Tooltip title="Refresh Insights">
                  <IconButton onClick={handleRefreshInsights} disabled={insightsLoading}>
                    <RefreshOutlined />
                  </IconButton>
                </Tooltip>
              </Box>

              {insightsLoading && (
                <Box sx={{ mb: 3, textAlign: 'center' }}>
                  <CircularProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Claude is analyzing workstation data for intelligent insights...
                  </Typography>
                </Box>
              )}

              {claudeInsights && (
                <Grid container spacing={3}>
                  {/* System Health Assessment */}
                  <Grid size={12}>
                    <Card>
                      <CardHeader 
                        title="System Health Assessment" 
                        avatar={<Psychology color="primary" />}
                      />
                      <CardContent>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {claudeInsights.systemHealth}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Risk Factors */}
                  {claudeInsights.riskFactors && claudeInsights.riskFactors.length > 0 && (
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Card>
                        <CardHeader 
                          title="Risk Factors" 
                          avatar={<WarningOutlined color="warning" />}
                        />
                        <CardContent>
                          <List dense>
                            {claudeInsights.riskFactors.map((risk: string, index: number) => (
                              <ListItem key={index}>
                                <ListItemIcon>
                                  <WarningOutlined color="warning" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText primary={risk} />
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  )}

                  {/* Performance Recommendations */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardHeader 
                        title="Performance Recommendations" 
                        avatar={<TrendingUp color="success" />}
                      />
                      <CardContent>
                        <List dense>
                          {claudeInsights.performanceRecommendations.map((rec: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Lightbulb color="primary" fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary={rec} />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Security Assessment */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardHeader 
                        title="Security Assessment" 
                        avatar={<ShieldOutlined color="info" />}
                      />
                      <CardContent>
                        <Typography variant="body2" gutterBottom>
                          {claudeInsights.securityAssessment}
                        </Typography>
                        <Box sx={{ mt: 2 }}>
                          <Chip 
                            label={claudeInsights.complianceStatus} 
                            color={claudeInsights.complianceStatus === 'Compliant' ? 'success' : 'warning'}
                            size="small"
                          />
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Optimization Tips */}
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card>
                      <CardHeader 
                        title="Optimization Tips" 
                        avatar={<AutoAwesome color="secondary" />}
                      />
                      <CardContent>
                        <List dense>
                          {claudeInsights.optimizationTips.map((tip: string, index: number) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <CheckCircleOutlined color="success" fontSize="small" />
                              </ListItemIcon>
                              <ListItemText primary={tip} />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Maintenance Schedule */}
                  <Grid size={12}>
                    <Card>
                      <CardHeader 
                        title="Recommended Maintenance Schedule" 
                        avatar={<UpdateOutlined color="info" />}
                      />
                      <CardContent>
                        <Grid container spacing={2}>
                          {claudeInsights.maintenanceSchedule.map((task: string, index: number) => (
                            <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
                              <Alert severity="info" variant="outlined">
                                <Typography variant="body2">{task}</Typography>
                              </Alert>
                            </Grid>
                          ))}
                        </Grid>
                      </CardContent>
                    </Card>
                  </Grid>

                  {/* Anomaly Detection */}
                  <Grid size={12}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreOutlined />}>
                        <Box display="flex" alignItems="center" gap={2}>
                          <BugReportOutlined color="primary" />
                          <Typography variant="subtitle1" fontWeight={600}>
                            Anomaly Detection Analysis
                          </Typography>
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {claudeInsights.anomalyDetection}
                        </Typography>
                      </AccordionDetails>
                    </Accordion>
                  </Grid>
                </Grid>
              )}

              {!claudeInsights && !insightsLoading && (
                <Box textAlign="center" py={6}>
                  <AutoAwesome sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    Claude Intelligence Insights
                  </Typography>
                  <Typography variant="body2" color="text.secondary" paragraph>
                    Get AI-powered analysis and recommendations for this workstation
                  </Typography>
                  <Button 
                    variant="contained" 
                    startIcon={<Psychology />}
                    onClick={getClaudeInsights}
                  >
                    Generate Insights
                  </Button>
                </Box>
              )}
            </Box>
          </TabPanel>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>
          Close
        </Button>
        <Button 
          variant="outlined" 
          startIcon={<RefreshOutlined />}
        >
          Refresh Data
        </Button>
        <Button 
          variant="contained" 
          startIcon={<SettingsOutlined />}
        >
          Advanced Settings
        </Button>
      </DialogActions>
    </Dialog>
  );
}
