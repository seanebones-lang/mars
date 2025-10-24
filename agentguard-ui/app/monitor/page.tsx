'use client';

import { useState, useEffect } from 'react';
import {
  Container, Grid, Card, CardContent, Typography, Box, Switch,
  FormControlLabel, Button, Alert, Chip, List, ListItem, Paper,
  Stack, IconButton, Tooltip, Collapse, TextField, Slider,
  Divider, FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import RiskGauge from '@/components/RiskGauge';
import CircularMeter from '@/components/CircularMeter';
import AudioSettings from '@/components/AudioSettings';
import AlertSettings from '@/components/AlertSettings';
import StatsSettings from '@/components/StatsSettings';
import { 
  PlayArrow, Stop, Refresh, Download, Settings, 
  Computer, Store, People, Warning, CheckCircle 
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useRealtimeMonitoring } from '@/hooks/useRealtimeMonitoring';
import { useStore } from '@/lib/store';
import toast from 'react-hot-toast';

const AGENT_CONFIG = {
  it_bot: { 
    name: 'IT Support Bot', 
    color: '#2196F3', 
    icon: <Computer />,
    description: 'Handles IT support tickets and troubleshooting'
  },
  retail_assistant: { 
    name: 'Retail Assistant', 
    color: '#4CAF50', 
    icon: <Store />,
    description: 'Assists customers with product inquiries and orders'
  },
  hr_helper: { 
    name: 'HR Helper', 
    color: '#FF9800', 
    icon: <People />,
    description: 'Provides employee support and policy information'
  }
};

export default function MonitorPage() {
  const [autoMode, setAutoMode] = useState(true);
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [responseInterval, setResponseInterval] = useState(3.0);
  const [showSettings, setShowSettings] = useState(false);
  const [jitterAmount, setJitterAmount] = useState(1.0);
  const [alertThreshold, setAlertThreshold] = useState(0.5);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  
  const { connect, disconnect, isConnected, connectionState, error, reconnectAttempts } = useRealtimeMonitoring();
  const { realtimeResults, clearRealtimeResults, apiUrl } = useStore();

  // Auto-connect WebSocket when page loads
  useEffect(() => {
    console.log('MonitorPage mounted, attempting WebSocket connection...');
    connect();
    
    // Check if monitoring is already active on backend
    const checkBackendStatus = async () => {
      try {
        const response = await fetch(`${apiUrl}/monitor/status`);
        if (response.ok) {
          const data = await response.json();
          if (data.is_active) {
            setMonitoringActive(true);
            console.log('Backend monitoring already active');
          }
        }
      } catch (error) {
        console.error('Failed to check backend status:', error);
      }
    };
    
    checkBackendStatus();
  }, [connect, apiUrl]);

  const startMonitoring = async () => {
    try {
      // Connect WebSocket first
      connect();
      
      // Start backend monitoring
      const response = await fetch(`${apiUrl}/monitor/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          response_interval: responseInterval,
          jitter: jitterAmount
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.status === 'started' || data.status === 'already_running') {
        setMonitoringActive(true);
        toast.success('Live monitoring started');
      } else {
        throw new Error(data.message || 'Failed to start monitoring');
      }
    } catch (error: any) {
      console.error('Failed to start monitoring:', error);
      toast.error(`Failed to start monitoring: ${error.message}`);
    }
  };

  const stopMonitoring = async () => {
    try {
      const response = await fetch(`${apiUrl}/monitor/stop`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Monitoring stopped:', data);
      }
      
      disconnect();
      setMonitoringActive(false);
      toast.success('Monitoring stopped');
    } catch (error: any) {
      console.error('Failed to stop monitoring:', error);
      toast.error(`Failed to stop monitoring: ${error.message}`);
      // Still disconnect WebSocket even if API call fails
      disconnect();
      setMonitoringActive(false);
    }
  };

  const getAgentStatus = (agentId: string) => {
    const recentResults = realtimeResults
      .filter(r => r.agent_id === agentId)
      .slice(-3);
    
    if (recentResults.length === 0) return 'idle';
    
    const hasHighRisk = recentResults.some(r => r.hallucination_risk > 0.7);
    const hasMediumRisk = recentResults.some(r => r.hallucination_risk > 0.4);
    
    if (hasHighRisk) return 'danger';
    if (hasMediumRisk) return 'warning';
    return 'healthy';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'danger': return '#f44336';
      case 'warning': return '#ff9800';
      case 'healthy': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'danger': return <Warning />;
      case 'healthy': return <CheckCircle />;
      default: return <Warning />;
    }
  };

  // Calculate metrics for charts
  const chartData = realtimeResults.slice(-20).map((result, index) => ({
    time: index,
    risk: result.hallucination_risk * 100,
    agent: result.agent_id,
    timestamp: new Date(result.timestamp).toLocaleTimeString()
  }));

  const agentMetrics = Object.keys(AGENT_CONFIG).map(agentId => {
    const agentResults = realtimeResults.filter(r => r.agent_id === agentId);
    const flaggedCount = agentResults.filter(r => r.flagged).length;
    
    return {
      agent: AGENT_CONFIG[agentId as keyof typeof AGENT_CONFIG].name,
      total: agentResults.length,
      flagged: flaggedCount,
      rate: agentResults.length > 0 ? (flaggedCount / agentResults.length) * 100 : 0
    };
  });

  const totalChecks = realtimeResults.length;
  const flaggedCount = realtimeResults.filter(r => r.flagged).length;
  const flaggedRate = totalChecks > 0 ? (flaggedCount / totalChecks) * 100 : 0;
  const avgProcessingTime = realtimeResults.length > 0 
    ? realtimeResults.reduce((sum, r) => sum + r.processing_time_ms, 0) / realtimeResults.length / 1000
    : 0;

  const exportAuditTrail = () => {
    const headers = ['Timestamp', 'Agent', 'Query', 'Response', 'Risk %', 'Flagged', 'Processing Time (ms)', 'Segments'];
    const rows = realtimeResults.map(result => [
      result.timestamp,
      AGENT_CONFIG[result.agent_id as keyof typeof AGENT_CONFIG]?.name || result.agent_id,
      result.query,
      result.output,
      (result.hallucination_risk * 100).toFixed(1),
      result.flagged ? 'Yes' : 'No',
      result.processing_time_ms.toString(),
      result.flagged_segments.join('; ')
    ]);
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(field => `"${field}"`).join(','))
      .join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agentguard-audit-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast.success('Audit trail exported');
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3" fontWeight={700} gutterBottom>
            Live Agent Monitoring
          </Typography>
          <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
            Real-Time Hallucination Defense
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor multiple AI agents and catch hallucinations before they impact your business
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControlLabel
            control={<Switch checked={autoMode} onChange={(e) => setAutoMode(e.target.checked)} />}
            label="Auto Mode"
          />
          
          {/* Compact Audio Controls */}
          <AudioSettings compact={true} />
          
          <Tooltip title="Settings">
            <IconButton onClick={() => setShowSettings(!showSettings)}>
              <Settings />
            </IconButton>
          </Tooltip>
          <Button
            variant={monitoringActive ? "outlined" : "contained"}
            color={monitoringActive ? "error" : "primary"}
            onClick={monitoringActive ? stopMonitoring : startMonitoring}
            size="large"
            startIcon={monitoringActive ? <Stop /> : <PlayArrow />}
            disabled={connectionState === 'connecting'}
          >
            {monitoringActive ? 'Stop Monitoring' : 'Start Monitoring'}
          </Button>
        </Box>
      </Box>

      {/* Connection Status */}
      <Alert 
        severity={
          connectionState === 'connected' ? "success" : 
          connectionState === 'connecting' ? "info" :
          connectionState === 'error' ? "error" : "warning"
        } 
        sx={{ mb: 3 }}
        action={
          error && (
            <Button color="inherit" size="small" onClick={() => window.location.reload()}>
              Reload
            </Button>
          )
        }
      >
        {connectionState === 'connected' && (
          <>
            <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
            Connected to live monitoring
          </>
        )}
        {connectionState === 'connecting' && (
          <>
            <Warning sx={{ mr: 1, color: 'warning.main' }} />
            Connecting to monitoring service...
          </>
        )}
        {connectionState === 'disconnected' && (
          <>
            <Warning sx={{ mr: 1, color: 'error.main' }} />
            Not connected to monitoring service
          </>
        )}
        {connectionState === 'error' && (
          <>
            <Warning sx={{ mr: 1, color: 'error.main' }} />
            Connection error: {error}
          </>
        )}
        {reconnectAttempts > 0 && ` (Reconnect attempt ${reconnectAttempts}/5)`}
      </Alert>

      {/* Settings Panel */}
      <Collapse in={showSettings}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Monitoring Settings
          </Typography>
          
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>Response Interval (seconds)</Typography>
                  <Slider
                    value={responseInterval}
                    onChange={(_, value) => setResponseInterval(value as number)}
                    min={1}
                    max={10}
                    step={0.5}
                    marks={[
                      { value: 1, label: '1s' },
                      { value: 3, label: '3s' },
                      { value: 5, label: '5s' },
                      { value: 10, label: '10s' }
                    ]}
                    valueLabelDisplay="on"
                    disabled={monitoringActive}
                  />
                  <Typography variant="caption" color="text.secondary">
                    How often agents generate responses
                  </Typography>
                </Box>

                <Box>
                  <Typography gutterBottom>Response Jitter (seconds)</Typography>
                  <Slider
                    value={jitterAmount}
                    onChange={(_, value) => setJitterAmount(value as number)}
                    min={0}
                    max={3}
                    step={0.1}
                    marks={[
                      { value: 0, label: '0s' },
                      { value: 1, label: '1s' },
                      { value: 2, label: '2s' },
                      { value: 3, label: '3s' }
                    ]}
                    valueLabelDisplay="on"
                    disabled={monitoringActive}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Random variation in response timing
                  </Typography>
                </Box>
              </Stack>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Stack spacing={3}>
                <Box>
                  <Typography gutterBottom>Alert Threshold</Typography>
                  <Slider
                    value={alertThreshold}
                    onChange={(_, value) => setAlertThreshold(value as number)}
                    min={0.1}
                    max={1.0}
                    step={0.1}
                    marks={[
                      { value: 0.3, label: '30%' },
                      { value: 0.5, label: '50%' },
                      { value: 0.7, label: '70%' },
                      { value: 0.9, label: '90%' }
                    ]}
                    valueLabelDisplay="on"
                    valueLabelFormat={(value) => `${(value * 100).toFixed(0)}%`}
                  />
                  <Typography variant="caption" color="text.secondary">
                    Minimum risk level to trigger alerts
                  </Typography>
                </Box>

                <Divider />

                <Stack spacing={2}>
                  <FormControlLabel
                    control={
                      <Switch 
                        checked={notificationsEnabled} 
                        onChange={(e) => setNotificationsEnabled(e.target.checked)} 
                      />
                    }
                    label="Desktop Notifications"
                  />
                </Stack>
                
                <Divider />
                
                {/* Audio Settings */}
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Audio Alert System
                  </Typography>
                  <AudioSettings compact={false} />
                </Box>
                
                <Divider />
                
                {/* Persistent Alert Settings */}
                <Box>
                  <AlertSettings />
                </Box>
                
                <Divider />
                
                {/* Real-time Stats Settings */}
                <Box>
                  <StatsSettings />
                </Box>
              </Stack>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
            <Button 
              variant="outlined" 
              onClick={() => {
                setResponseInterval(3.0);
                setJitterAmount(1.0);
                setAlertThreshold(0.5);
                setNotificationsEnabled(true);
                setSoundEnabled(true);
              }}
            >
              Reset to Defaults
            </Button>
            <Button 
              variant="contained" 
              onClick={() => setShowSettings(false)}
            >
              Close Settings
            </Button>
          </Box>
        </Paper>
      </Collapse>

      {/* Metrics Summary with Circular Meters - Horizontal Layout */}
      <Box sx={{ 
        display: 'grid', 
        gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', lg: 'repeat(4, 1fr)' }, 
        gap: 4, 
        mb: 6, 
        mt: 2,
        justifyItems: 'center'
      }}>
        <RiskGauge
          riskLevel={flaggedRate}
          title="Hallucination Rate"
          subtitle={`${flaggedCount} of ${totalChecks} flagged`}
          size="small"
          showTrend={true}
          trendValue={2.1}
        />
        
        <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
          <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
            <CircularMeter
              value={Math.min(100, (totalChecks / 50) * 100)} // Scale to 50 max
              size={100}
              thickness={8}
              label="Total Responses"
              color="info"
              showValue={false}
            />
            <Typography variant="h5" fontWeight={700} color="info.main" sx={{ mt: 1 }}>
              {totalChecks}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Processed in session
            </Typography>
          </CardContent>
        </Card>
        
        <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
          <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
            <CircularMeter
              value={100 - (avgProcessingTime / 20 * 100)} // Invert: lower time = higher score
              size={100}
              thickness={8}
              label="Response Speed"
              color={avgProcessingTime > 10 ? "warning" : "success"}
              showValue={false}
            />
            <Typography variant="h5" fontWeight={700} color={avgProcessingTime > 10 ? "warning.main" : "success.main"} sx={{ mt: 1 }}>
              {avgProcessingTime.toFixed(1)}s
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Average latency
            </Typography>
          </CardContent>
        </Card>
        
        <Card sx={{ height: 'auto', display: 'flex', alignItems: 'center', justifyContent: 'center', width: '200px', minHeight: '240px' }}>
          <CardContent sx={{ textAlign: 'center', p: 3, pt: 4 }}>
            <CircularMeter
              value={92.3} // Mock accuracy
              size={100}
              thickness={8}
              label="Detection Accuracy"
              color="primary"
              showValue={true}
              subtitle="%"
            />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              System accuracy
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Agent Status Grid */}
      <Grid container spacing={3} sx={{ mb: 4, justifyContent: 'center' }}>
        {Object.entries(AGENT_CONFIG).map(([agentId, config]) => {
          const status = getAgentStatus(agentId);
          const statusColor = getStatusColor(status);
          const agentResults = realtimeResults.filter(r => r.agent_id === agentId);
          const lastResponse = agentResults.slice(-1)[0];
          
          return (
            <Grid size={{ xs: 12, md: 4 }} key={agentId} sx={{ display: 'flex', justifyContent: 'center' }}>
              <motion.div
                animate={{ 
                  scale: status === 'danger' ? [1, 1.02, 1] : 1,
                }}
                transition={{ repeat: status === 'danger' ? Infinity : 0, duration: 2 }}
              >
                <Card sx={{ 
                  borderLeft: `4px solid ${statusColor}`,
                  bgcolor: status === 'danger' ? 'rgba(244, 67, 54, 0.05)' : 'background.paper',
                  height: '100%'
                }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Box sx={{ color: config.color }}>
                        {config.icon}
                      </Box>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6">{config.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {config.description}
                        </Typography>
                      </Box>
                      <Box sx={{ color: statusColor }}>
                        {getStatusIcon(status)}
                      </Box>
                    </Box>
                    
                    <Stack spacing={1}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Status:</Typography>
                        <Typography variant="body2" fontWeight="bold" sx={{ color: statusColor }}>
                          {status.toUpperCase()}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Responses:</Typography>
                        <Typography variant="body2">{agentResults.length}</Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Last Active:</Typography>
                        <Typography variant="body2">
                          {lastResponse 
                            ? new Date(lastResponse.timestamp).toLocaleTimeString()
                            : 'Never'
                          }
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          );
        })}
      </Grid>

      {/* Live Activity Stream & Charts */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper sx={{ p: 3, height: 500 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Live Activity Stream
              </Typography>
              <Box>
                <IconButton onClick={() => clearRealtimeResults()} disabled={realtimeResults.length === 0}>
                  <Refresh />
                </IconButton>
                <IconButton onClick={exportAuditTrail} disabled={realtimeResults.length === 0}>
                  <Download />
                </IconButton>
              </Box>
            </Box>
            
            <Box sx={{ height: 400, overflow: 'auto' }}>
              <List>
                <AnimatePresence>
                  {realtimeResults.slice(-10).reverse().map((result, index) => (
                    <motion.div
                      key={`${result.agent_id}-${result.timestamp}-${index}`}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ duration: 0.3 }}
                    >
                      <ListItem sx={{ 
                        border: result.flagged ? '2px solid #f44336' : '1px solid #e0e0e0',
                        borderRadius: 2,
                        mb: 1,
                        bgcolor: result.flagged ? 'rgba(244, 67, 54, 0.05)' : 'background.paper',
                        flexDirection: 'column',
                        alignItems: 'stretch'
                      }}>
                        <Box sx={{ width: '100%' }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box sx={{ color: AGENT_CONFIG[result.agent_id as keyof typeof AGENT_CONFIG]?.color }}>
                                {AGENT_CONFIG[result.agent_id as keyof typeof AGENT_CONFIG]?.icon}
                              </Box>
                              <Typography variant="subtitle2">
                                {AGENT_CONFIG[result.agent_id as keyof typeof AGENT_CONFIG]?.name}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                              <Chip 
                                label={`${(result.hallucination_risk * 100).toFixed(1)}%`}
                                size="small"
                                color={result.flagged ? "error" : "success"}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {result.processing_time_ms}ms
                              </Typography>
                            </Box>
                          </Box>
                          
                          <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                            Q: {result.query}
                          </Typography>
                          
                          <Typography variant="body2" sx={{ mb: 1 }}>
                            A: {result.output}
                          </Typography>
                          
                          {result.flagged && result.flagged_segments.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="error" sx={{ fontWeight: 'bold' }}>
                                Flagged Content: 
                              </Typography>
                              <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} flexWrap="wrap">
                                {result.flagged_segments.map((segment: string, i: number) => (
                                  <Chip
                                    key={i}
                                    label={segment}
                                    size="small"
                                    color="error"
                                    variant="outlined"
                                  />
                                ))}
                              </Stack>
                            </Box>
                          )}
                          
                          {result.mitigation && (
                            <Box sx={{ mt: 1, p: 1, bgcolor: 'primary.light', borderRadius: 1 }}>
                              <Typography variant="caption" color="primary.dark" sx={{ fontWeight: 'bold' }}>
                                Suggested Fix: 
                              </Typography>
                              <Typography variant="body2" color="primary.dark">
                                {result.mitigation}
                              </Typography>
                            </Box>
                          )}
                        </Box>
                      </ListItem>
                    </motion.div>
                  ))}
                </AnimatePresence>
                
                {realtimeResults.length === 0 && (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No activity yet. Start monitoring to see live agent responses.
                    </Typography>
                  </Box>
                )}
              </List>
            </Box>
          </Paper>
        </Grid>
        
        <Grid size={{ xs: 12, lg: 4 }}>
          <Stack spacing={3}>
            {/* Risk Trend Chart */}
            <Paper sx={{ p: 3, height: 240 }}>
              <Typography variant="h6" gutterBottom>
                Hallucination Risk Trend
              </Typography>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <RechartsTooltip 
                    formatter={(value: any) => [`${value}%`, 'Risk']}
                    labelFormatter={(label) => `Response ${label}`}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="risk" 
                    stroke="#f44336" 
                    strokeWidth={2}
                    dot={{ fill: '#f44336', strokeWidth: 2, r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Paper>

            {/* Agent Performance */}
            <Paper sx={{ p: 3, height: 240 }}>
              <Typography variant="h6" gutterBottom>
                Agent Performance
              </Typography>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={agentMetrics}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="agent" />
                  <YAxis />
                  <RechartsTooltip 
                    formatter={(value: any, name: string) => [
                      name === 'rate' ? `${value.toFixed(1)}%` : value,
                      name === 'rate' ? 'Hallucination Rate' : 'Total Responses'
                    ]}
                  />
                  <Bar dataKey="total" fill="#2196F3" name="total" />
                  <Bar dataKey="rate" fill="#f44336" name="rate" />
                </BarChart>
              </ResponsiveContainer>
            </Paper>
          </Stack>
        </Grid>
      </Grid>
    </Container>
  );
}
