'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Button,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider,
  LinearProgress,
  CircularProgress,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stack,
  Badge,
  Avatar
} from '@mui/material';
import {
  BugReportOutlined,
  PlayArrowOutlined,
  StopOutlined,
  RefreshOutlined,
  DownloadOutlined,
  UploadOutlined,
  SettingsOutlined,
  VisibilityOutlined,
  CodeOutlined,
  TimelineOutlined,
  NetworkCheckOutlined,
  SpeedOutlined,
  MemoryOutlined,
  StorageOutlined,
  SecurityOutlined,
  ExpandMoreOutlined,
  ContentCopyOutlined,
  DeleteOutlined,
  FilterListOutlined,
  SearchOutlined,
  TuneOutlined,
  AnalyticsOutlined,
  ErrorOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoOutlined
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';

interface DebugSession {
  id: string;
  timestamp: string;
  agentOutput: string;
  groundTruth?: string;
  detectionResult: {
    flagged: boolean;
    confidence: number;
    reasoning: string;
    categories: string[];
    processingTime: number;
  };
  metadata: {
    model: string;
    temperature: number;
    tokens: number;
    latency: number;
  };
  status: 'running' | 'completed' | 'failed' | 'queued';
}

interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
  activeConnections: number;
  queueSize: number;
  errorRate: number;
  avgResponseTime: number;
}

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
      id={`debug-tabpanel-${index}`}
      aria-labelledby={`debug-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function DebugPage() {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [debugSessions, setDebugSessions] = useState<DebugSession[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [realTimeMode, setRealTimeMode] = useState(false);
  const [selectedSession, setSelectedSession] = useState<DebugSession | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [groundTruthInput, setGroundTruthInput] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu: 45,
    memory: 62,
    disk: 78,
    network: 23,
    activeConnections: 156,
    queueSize: 8,
    errorRate: 2.1,
    avgResponseTime: 245
  });

  const wsRef = useRef<WebSocket | null>(null);

  // Generate mock debug sessions
  useEffect(() => {
    const generateMockSessions = () => {
      const sessions: DebugSession[] = [];
      const statuses: ('running' | 'completed' | 'failed' | 'queued')[] = ['completed', 'failed', 'running', 'queued'];
      const models = ['Claude-3.5-Sonnet', 'GPT-4-Turbo', 'Gemini-Pro', 'Claude-3-Haiku'];
      const categories = ['factual_error', 'logical_inconsistency', 'fabrication', 'bias', 'hallucination'];

      for (let i = 0; i < 25; i++) {
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        const flagged = Math.random() > 0.7;
        
        sessions.push({
          id: `debug_${i.toString().padStart(3, '0')}`,
          timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
          agentOutput: `Sample agent response ${i + 1}: This is a test output that may contain various types of potential issues for debugging purposes.`,
          groundTruth: Math.random() > 0.5 ? `Expected ground truth for test case ${i + 1}` : undefined,
          detectionResult: {
            flagged,
            confidence: flagged ? 0.6 + Math.random() * 0.4 : Math.random() * 0.5,
            reasoning: flagged 
              ? `Detected potential ${categories[Math.floor(Math.random() * categories.length)]} with high confidence`
              : 'No significant issues detected in the response',
            categories: flagged ? [categories[Math.floor(Math.random() * categories.length)]] : [],
            processingTime: 150 + Math.random() * 300
          },
          metadata: {
            model: models[Math.floor(Math.random() * models.length)],
            temperature: Math.round((Math.random() * 1.5 + 0.1) * 100) / 100,
            tokens: Math.floor(Math.random() * 2000 + 100),
            latency: Math.floor(Math.random() * 500 + 50)
          },
          status
        });
      }
      
      return sessions.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    };

    setDebugSessions(generateMockSessions());
  }, []);

  // Real-time metrics simulation
  useEffect(() => {
    if (!realTimeMode) return;

    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        cpu: Math.max(0, Math.min(100, prev.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, prev.memory + (Math.random() - 0.5) * 5)),
        disk: Math.max(0, Math.min(100, prev.disk + (Math.random() - 0.5) * 2)),
        network: Math.max(0, Math.min(100, prev.network + (Math.random() - 0.5) * 15)),
        activeConnections: Math.max(0, prev.activeConnections + Math.floor((Math.random() - 0.5) * 20)),
        queueSize: Math.max(0, prev.queueSize + Math.floor((Math.random() - 0.5) * 5)),
        errorRate: Math.max(0, prev.errorRate + (Math.random() - 0.5) * 1),
        avgResponseTime: Math.max(50, prev.avgResponseTime + (Math.random() - 0.5) * 50)
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [realTimeMode]);

  // Filter sessions
  const filteredSessions = debugSessions.filter(session => {
    const matchesStatus = filterStatus === 'all' || session.status === filterStatus;
    const matchesSearch = session.agentOutput.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         session.metadata.model.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleRunTest = async () => {
    if (!testInput.trim()) return;

    setIsRunning(true);
    
    // Simulate API call
    const newSession: DebugSession = {
      id: `debug_${Date.now()}`,
      timestamp: new Date().toISOString(),
      agentOutput: testInput,
      groundTruth: groundTruthInput || undefined,
      detectionResult: {
        flagged: Math.random() > 0.6,
        confidence: Math.random(),
        reasoning: 'Analysis in progress...',
        categories: [],
        processingTime: 0
      },
      metadata: {
        model: 'Claude-3.5-Sonnet',
        temperature: 0.7,
        tokens: testInput.split(' ').length * 1.3,
        latency: 0
      },
      status: 'running'
    };

    setDebugSessions(prev => [newSession, ...prev]);

    // Simulate processing
    setTimeout(() => {
      const flagged = Math.random() > 0.6;
      const updatedSession = {
        ...newSession,
        detectionResult: {
          flagged,
          confidence: flagged ? 0.7 + Math.random() * 0.3 : Math.random() * 0.5,
          reasoning: flagged 
            ? 'Potential hallucination detected based on factual inconsistencies'
            : 'No significant issues detected in the response',
          categories: flagged ? ['factual_error', 'hallucination'] : [],
          processingTime: 180 + Math.random() * 120
        },
        metadata: {
          ...newSession.metadata,
          latency: 150 + Math.random() * 200
        },
        status: 'completed' as const
      };

      setDebugSessions(prev => prev.map(s => s.id === newSession.id ? updatedSession : s));
      setIsRunning(false);
    }, 3000);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'running': return 'info';
      case 'queued': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined />;
      case 'failed': return <ErrorOutlined />;
      case 'running': return <CircularProgress size={16} />;
      case 'queued': return <WarningOutlined />;
      default: return <InfoOutlined />;
    }
  };

  const exportSessions = () => {
    const dataStr = JSON.stringify(filteredSessions, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `debug-sessions-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
            Debug Tools
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced debugging and analysis tools for AI agent hallucination detection
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={realTimeMode}
                onChange={(e) => setRealTimeMode(e.target.checked)}
              />
            }
            label="Real-time Monitoring"
          />
          
          <Button
            variant="outlined"
            startIcon={<DownloadOutlined />}
            onClick={exportSessions}
          >
            Export Data
          </Button>
        </Box>
      </Box>

      {/* System Metrics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SpeedOutlined />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h6">{systemMetrics.cpu.toFixed(1)}%</Typography>
                  <Typography variant="body2" color="text.secondary">CPU Usage</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemMetrics.cpu} 
                    color={systemMetrics.cpu > 80 ? 'error' : systemMetrics.cpu > 60 ? 'warning' : 'primary'}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <MemoryOutlined />
                </Avatar>
                <Box flex={1}>
                  <Typography variant="h6">{systemMetrics.memory.toFixed(1)}%</Typography>
                  <Typography variant="body2" color="text.secondary">Memory Usage</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={systemMetrics.memory} 
                    color={systemMetrics.memory > 80 ? 'error' : systemMetrics.memory > 60 ? 'warning' : 'info'}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <NetworkCheckOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h6">{systemMetrics.activeConnections}</Typography>
                  <Typography variant="body2" color="text.secondary">Active Connections</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Queue: {systemMetrics.queueSize}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: systemMetrics.errorRate > 5 ? 'error.main' : 'warning.main' }}>
                  <AnalyticsOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h6">{systemMetrics.avgResponseTime.toFixed(0)}ms</Typography>
                  <Typography variant="body2" color="text.secondary">Avg Response Time</Typography>
                  <Typography variant="caption" color={systemMetrics.errorRate > 5 ? 'error.main' : 'text.secondary'}>
                    Error Rate: {systemMetrics.errorRate.toFixed(1)}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content Tabs */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
            <Tab label="Live Testing" icon={<PlayArrowOutlined />} />
            <Tab label="Session History" icon={<TimelineOutlined />} />
            <Tab label="System Analysis" icon={<AnalyticsOutlined />} />
            <Tab label="Configuration" icon={<SettingsOutlined />} />
          </Tabs>
        </Box>

        {/* Live Testing Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Test Input" />
                <CardContent>
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    placeholder="Enter agent output to test for hallucinations..."
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    placeholder="Ground truth (optional)"
                    value={groundTruthInput}
                    onChange={(e) => setGroundTruthInput(e.target.value)}
                    sx={{ mb: 2 }}
                  />
                  
                  <Box display="flex" gap={2}>
                    <Button
                      variant="contained"
                      startIcon={isRunning ? <CircularProgress size={16} /> : <PlayArrowOutlined />}
                      onClick={handleRunTest}
                      disabled={isRunning || !testInput.trim()}
                      fullWidth
                    >
                      {isRunning ? 'Analyzing...' : 'Run Debug Test'}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Real-time Results" />
                <CardContent>
                  {debugSessions.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <Box display="flex" alignItems="center" gap={2} mb={2}>
                        <Chip
                          icon={getStatusIcon(debugSessions[0].status)}
                          label={debugSessions[0].status}
                          color={getStatusColor(debugSessions[0].status) as any}
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary">
                          {new Date(debugSessions[0].timestamp).toLocaleTimeString()}
                        </Typography>
                      </Box>
                      
                      <Alert 
                        severity={debugSessions[0].detectionResult.flagged ? 'warning' : 'success'}
                        sx={{ mb: 2 }}
                      >
                        <Typography variant="body2">
                          <strong>Confidence:</strong> {(debugSessions[0].detectionResult.confidence * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2">
                          {debugSessions[0].detectionResult.reasoning}
                        </Typography>
                      </Alert>
                      
                      {debugSessions[0].detectionResult.categories.length > 0 && (
                        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
                          {debugSessions[0].detectionResult.categories.map((category, index) => (
                            <Chip key={index} label={category} size="small" variant="outlined" />
                          ))}
                        </Box>
                      )}
                      
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Typography variant="caption" color="text.secondary">
                          Processing: {debugSessions[0].detectionResult.processingTime.toFixed(0)}ms
                        </Typography>
                        <Button
                          size="small"
                          onClick={() => {
                            setSelectedSession(debugSessions[0]);
                            setDetailsOpen(true);
                          }}
                        >
                          View Details
                        </Button>
                      </Box>
                    </motion.div>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Session History Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box display="flex" gap={2} mb={3} alignItems="center">
            <TextField
              placeholder="Search sessions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchOutlined sx={{ mr: 1, color: 'text.secondary' }} />
              }}
              size="small"
              sx={{ minWidth: 300 }}
            />
            
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Status Filter</InputLabel>
              <Select
                value={filterStatus}
                label="Status Filter"
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="queued">Queued</MenuItem>
              </Select>
            </FormControl>
            
            <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
              {filteredSessions.length} sessions
            </Typography>
          </Box>
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Session ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Model</TableCell>
                  <TableCell>Flagged</TableCell>
                  <TableCell>Confidence</TableCell>
                  <TableCell>Processing Time</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <AnimatePresence>
                  {filteredSessions.slice(0, 10).map((session) => (
                    <TableRow
                      key={session.id}
                      hover
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {session.id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          icon={getStatusIcon(session.status)}
                          label={session.status}
                          color={getStatusColor(session.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {session.metadata.model}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={session.detectionResult.flagged ? 'Yes' : 'No'}
                          color={session.detectionResult.flagged ? 'error' : 'success'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {(session.detectionResult.confidence * 100).toFixed(1)}%
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {session.detectionResult.processingTime.toFixed(0)}ms
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(session.timestamp).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedSession(session);
                                setDetailsOpen(true);
                              }}
                            >
                              <VisibilityOutlined />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Copy ID">
                            <IconButton
                              size="small"
                              onClick={() => navigator.clipboard.writeText(session.id)}
                            >
                              <ContentCopyOutlined />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </AnimatePresence>
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* System Analysis Tab */}
        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Performance Trends" />
                <CardContent>
                  <Box height={300} display="flex" alignItems="center" justifyContent="center">
                    <Typography variant="body2" color="text.secondary">
                      Performance charts would be rendered here using Chart.js or Recharts
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Error Analysis" />
                <CardContent>
                  <Box height={300} display="flex" alignItems="center" justifyContent="center">
                    <Typography variant="body2" color="text.secondary">
                      Error distribution charts would be rendered here
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Configuration Tab */}
        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Debug Settings" />
                <CardContent>
                  <Stack spacing={3}>
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Enable verbose logging"
                    />
                    <FormControlLabel
                      control={<Switch defaultChecked />}
                      label="Auto-save debug sessions"
                    />
                    <FormControlLabel
                      control={<Switch />}
                      label="Enable performance profiling"
                    />
                    <FormControlLabel
                      control={<Switch />}
                      label="Real-time WebSocket monitoring"
                    />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card variant="outlined">
                <CardHeader title="Export Settings" />
                <CardContent>
                  <Stack spacing={2}>
                    <Button variant="outlined" startIcon={<DownloadOutlined />}>
                      Export All Sessions
                    </Button>
                    <Button variant="outlined" startIcon={<DownloadOutlined />}>
                      Export System Logs
                    </Button>
                    <Button variant="outlined" startIcon={<DownloadOutlined />}>
                      Export Performance Metrics
                    </Button>
                    <Divider />
                    <Button variant="outlined" startIcon={<UploadOutlined />}>
                      Import Debug Sessions
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Card>

      {/* Session Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Debug Session Details
        </DialogTitle>
        <DialogContent>
          {selectedSession && (
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" gutterBottom>Session Information</Typography>
                <Grid container spacing={2}>
                  <Grid size={6}>
                    <Typography variant="body2"><strong>ID:</strong> {selectedSession.id}</Typography>
                  </Grid>
                  <Grid size={6}>
                    <Typography variant="body2"><strong>Status:</strong> {selectedSession.status}</Typography>
                  </Grid>
                  <Grid size={6}>
                    <Typography variant="body2"><strong>Model:</strong> {selectedSession.metadata.model}</Typography>
                  </Grid>
                  <Grid size={6}>
                    <Typography variant="body2"><strong>Temperature:</strong> {selectedSession.metadata.temperature}</Typography>
                  </Grid>
                </Grid>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" gutterBottom>Agent Output</Typography>
                <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                    {selectedSession.agentOutput}
                  </Typography>
                </Paper>
              </Box>
              
              {selectedSession.groundTruth && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>Ground Truth</Typography>
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {selectedSession.groundTruth}
                    </Typography>
                  </Paper>
                </Box>
              )}
              
              <Box>
                <Typography variant="subtitle2" gutterBottom>Detection Results</Typography>
                <Alert severity={selectedSession.detectionResult.flagged ? 'warning' : 'success'}>
                  <Typography variant="body2">
                    <strong>Flagged:</strong> {selectedSession.detectionResult.flagged ? 'Yes' : 'No'}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Confidence:</strong> {(selectedSession.detectionResult.confidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    <strong>Reasoning:</strong> {selectedSession.detectionResult.reasoning}
                  </Typography>
                </Alert>
                
                {selectedSession.detectionResult.categories.length > 0 && (
                  <Box mt={2}>
                    <Typography variant="body2" gutterBottom><strong>Categories:</strong></Typography>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {selectedSession.detectionResult.categories.map((category, index) => (
                        <Chip key={index} label={category} size="small" />
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
          <Button variant="contained">Export Session</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
