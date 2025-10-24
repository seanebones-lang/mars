'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Chip,
  LinearProgress,
  Stack,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  SpeedOutlined as Speed,
  MemoryOutlined as Memory,
  StorageOutlined as Storage,
  NetworkCheckOutlined as NetworkCheck,
  ComputerOutlined as Cpu,
  TimelineOutlined as Timeline,
  TrendingUpOutlined as TrendingUp,
  TrendingDownOutlined as TrendingDown,
  CheckCircleOutlined as CheckCircle,
  WarningOutlined as Warning,
  ErrorOutlined as Error,
  RefreshOutlined as Refresh,
  DownloadOutlined as Download
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { motion } from 'framer-motion';
import CircularMeter from '@/components/CircularMeter';
import { useStore } from '@/lib/store';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`performance-tabpanel-${index}`}
      aria-labelledby={`performance-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface PerformanceMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_latency: number;
  response_time: number;
  throughput: number;
  error_rate: number;
  uptime: number;
}

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  services: {
    api: 'online' | 'offline' | 'degraded';
    database: 'online' | 'offline' | 'degraded';
    websocket: 'online' | 'offline' | 'degraded';
    claude_api: 'online' | 'offline' | 'degraded';
  };
  last_updated: string;
}

export default function PerformancePage() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [historicalData, setHistoricalData] = useState<any[]>([]);
  
  const { apiUrl } = useStore();

  useEffect(() => {
    loadPerformanceData();
    const interval = setInterval(loadPerformanceData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadPerformanceData = async () => {
    try {
      setError(null);
      
      // Mock data for now - in production this would come from the backend
      const mockMetrics: PerformanceMetrics = {
        cpu_usage: 45.2 + Math.random() * 10,
        memory_usage: 62.8 + Math.random() * 15,
        disk_usage: 34.1,
        network_latency: 12 + Math.random() * 8,
        response_time: 850 + Math.random() * 200,
        throughput: 156 + Math.random() * 50,
        error_rate: 0.8 + Math.random() * 1.2,
        uptime: 99.7
      };

      const mockHealth: SystemHealth = {
        status: mockMetrics.error_rate > 2 ? 'critical' : mockMetrics.cpu_usage > 80 ? 'warning' : 'healthy',
        services: {
          api: 'online',
          database: 'online',
          websocket: 'online',
          claude_api: 'online'
        },
        last_updated: new Date().toISOString()
      };

      // Generate historical data
      const now = new Date();
      const historical = Array.from({ length: 24 }, (_, i) => {
        const time = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000);
        return {
          time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cpu: 40 + Math.random() * 30,
          memory: 50 + Math.random() * 30,
          response_time: 800 + Math.random() * 400,
          throughput: 100 + Math.random() * 100,
          error_rate: Math.random() * 3
        };
      });

      setMetrics(mockMetrics);
      setSystemHealth(mockHealth);
      setHistoricalData(historical);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load performance data:', err);
      setError('Failed to load performance data. Please try again.');
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return 'success';
      case 'warning':
      case 'degraded':
        return 'warning';
      case 'critical':
      case 'offline':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle color="success" />;
      case 'warning':
      case 'degraded':
        return <Warning color="warning" />;
      case 'critical':
      case 'offline':
        return <Error color="error" />;
      default:
        return <CheckCircle />;
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!metrics || !systemHealth) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="info">
          No performance data available.
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h3" fontWeight={700} gutterBottom>
              System Performance
            </Typography>
            <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
              Real-Time Health & Metrics
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Monitor system health, resource usage, and performance metrics
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Tooltip title="Refresh Data">
              <IconButton onClick={loadPerformanceData}>
                <Refresh />
              </IconButton>
            </Tooltip>
            <Tooltip title="Export Report">
              <IconButton>
                <Download />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* System Status Alert */}
        <Alert 
          severity={getStatusColor(systemHealth.status) as any}
          sx={{ mb: 3 }}
          icon={getStatusIcon(systemHealth.status)}
        >
          System Status: {systemHealth.status.toUpperCase()} - Last updated: {new Date(systemHealth.last_updated).toLocaleString()}
        </Alert>

        {/* Performance Metrics Grid */}
        <Box sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, 
          gap: 4, 
          mb: 6, 
          justifyItems: 'center'
        }}>
          <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
            <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
              <CircularMeter
                value={metrics.cpu_usage}
                size={100}
                thickness={8}
                label="CPU Usage"
                color={metrics.cpu_usage > 80 ? "error" : metrics.cpu_usage > 60 ? "warning" : "success"}
                showValue={true}
                subtitle="%"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {metrics.cpu_usage > 80 ? 'High Usage' : 'Normal'}
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
            <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
              <CircularMeter
                value={metrics.memory_usage}
                size={100}
                thickness={8}
                label="Memory Usage"
                color={metrics.memory_usage > 85 ? "error" : metrics.memory_usage > 70 ? "warning" : "info"}
                showValue={true}
                subtitle="%"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {metrics.memory_usage > 85 ? 'High Usage' : 'Normal'}
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
            <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
              <CircularMeter
                value={100 - metrics.response_time / 20} // Convert to percentage (lower is better)
                size={100}
                thickness={8}
                label="Response Speed"
                color={metrics.response_time > 2000 ? "error" : metrics.response_time > 1000 ? "warning" : "success"}
                showValue={false}
              />
              <Typography variant="h5" fontWeight={700} color={metrics.response_time > 2000 ? "error.main" : metrics.response_time > 1000 ? "warning.main" : "success.main"} sx={{ mt: 1 }}>
                {metrics.response_time.toFixed(0)}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Average latency
              </Typography>
            </CardContent>
          </Card>

          <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
            <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
              <CircularMeter
                value={metrics.uptime}
                size={100}
                thickness={8}
                label="System Uptime"
                color="primary"
                showValue={true}
                subtitle="%"
              />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {metrics.uptime > 99 ? 'Excellent' : 'Good'}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Service Status */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Service Health Status
                </Typography>
                <Grid container spacing={2}>
                  {Object.entries(systemHealth.services).map(([service, status]) => (
                    <Grid size={{ xs: 12, sm: 6, md: 3 }} key={service}>
                      <Box sx={{ display: 'flex', alignItems: 'center', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                        {getStatusIcon(status)}
                        <Box sx={{ ml: 2, flexGrow: 1 }}>
                          <Typography variant="subtitle2" sx={{ textTransform: 'capitalize' }}>
                            {service.replace('_', ' ')}
                          </Typography>
                          <Chip 
                            label={status.toUpperCase()} 
                            size="small" 
                            color={getStatusColor(status) as any}
                            sx={{ mt: 0.5 }}
                          />
                        </Box>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="performance tabs">
            <Tab label="Resource Usage" />
            <Tab label="Response Times" />
            <Tab label="Throughput" />
            <Tab label="System Details" />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Resource Usage Over Time
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <RechartsTooltip 
                        formatter={(value: any, name: string) => [
                          `${value.toFixed(1)}${name === 'cpu' || name === 'memory' ? '%' : ''}`,
                          name === 'cpu' ? 'CPU Usage' : name === 'memory' ? 'Memory Usage' : name
                        ]}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="cpu" 
                        stroke="#F44336" 
                        strokeWidth={2}
                        name="CPU Usage (%)"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="memory" 
                        stroke="#2196F3" 
                        strokeWidth={2}
                        name="Memory Usage (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Response Time Trends
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <RechartsTooltip formatter={(value: any) => [`${value.toFixed(0)}ms`, 'Response Time']} />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="response_time" 
                        stroke="#4CAF50" 
                        fill="#4CAF50"
                        fillOpacity={0.6}
                        name="Response Time (ms)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Request Throughput
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <RechartsTooltip formatter={(value: any) => [`${value.toFixed(0)}`, 'Requests/min']} />
                      <Bar dataKey="throughput" fill="#FF9800" name="Throughput" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Error Rate
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <RechartsTooltip formatter={(value: any) => [`${value.toFixed(2)}%`, 'Error Rate']} />
                      <Line 
                        type="monotone" 
                        dataKey="error_rate" 
                        stroke="#F44336" 
                        strokeWidth={3}
                        name="Error Rate (%)"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Resources
                  </Typography>
                  <List>
                    <ListItem>
                      <ListItemIcon>
                        <Cpu color="primary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="CPU Usage"
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={metrics.cpu_usage} 
                              color={metrics.cpu_usage > 80 ? "error" : metrics.cpu_usage > 60 ? "warning" : "success"}
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="body2">
                              {metrics.cpu_usage.toFixed(1)}% - {metrics.cpu_usage > 80 ? 'High' : 'Normal'}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    <Divider />
                    
                    <ListItem>
                      <ListItemIcon>
                        <Memory color="info" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Memory Usage"
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={metrics.memory_usage} 
                              color={metrics.memory_usage > 85 ? "error" : metrics.memory_usage > 70 ? "warning" : "info"}
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="body2">
                              {metrics.memory_usage.toFixed(1)}% - {metrics.memory_usage > 85 ? 'High' : 'Normal'}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    <Divider />
                    
                    <ListItem>
                      <ListItemIcon>
                        <Storage color="secondary" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Disk Usage"
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={metrics.disk_usage} 
                              color="secondary"
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="body2">
                              {metrics.disk_usage.toFixed(1)}% - Normal
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    <Divider />
                    
                    <ListItem>
                      <ListItemIcon>
                        <NetworkCheck color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Network Latency"
                        secondary={`${metrics.network_latency.toFixed(1)}ms - ${metrics.network_latency > 50 ? 'High' : 'Good'}`}
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Summary
                  </Typography>
                  <Stack spacing={3}>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Current Throughput
                      </Typography>
                      <Typography variant="h4" color="primary">
                        {metrics.throughput.toFixed(0)} req/min
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Average Response Time
                      </Typography>
                      <Typography variant="h4" color={metrics.response_time > 2000 ? "error" : metrics.response_time > 1000 ? "warning" : "success"}>
                        {metrics.response_time.toFixed(0)}ms
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Error Rate
                      </Typography>
                      <Typography variant="h4" color={metrics.error_rate > 2 ? "error" : metrics.error_rate > 1 ? "warning" : "success"}>
                        {metrics.error_rate.toFixed(2)}%
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        System Uptime
                      </Typography>
                      <Typography variant="h4" color="primary">
                        {metrics.uptime.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </motion.div>
    </Container>
  );
}
