"use client";

import React, { useState } from 'react';
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
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Switch,
  FormControlLabel,
  Alert,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
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
  Tooltip,
  Badge,
  Stack
} from '@mui/material';
import {
  NetworkCheckOutlined,
  SearchOutlined,
  AddOutlined,
  DeleteOutlined,
  PlayArrowOutlined,
  StopOutlined,
  SettingsOutlined,
  WifiOutlined,
  RouterOutlined,
  DnsOutlined,
  BusinessOutlined,
  ComputerOutlined,
  SecurityOutlined,
  ExpandMoreOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  WarningOutlined,
  InfoOutlined,
  RefreshOutlined,
  VisibilityOutlined,
  CloseOutlined,
  ScheduleOutlined,
  StorageOutlined
} from '@mui/icons-material';

interface NetworkRange {
  id: string;
  name: string;
  cidr: string;
  description: string;
  enabled: boolean;
  lastScanned?: string;
  devicesFound: number;
}

interface DiscoveryTask {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  method: string;
  targetRanges: string[];
  schedule?: string;
  progress: number;
  devicesFound: number;
  startTime?: string;
  endTime?: string;
  errors?: string[];
}

interface WorkstationDiscoveryDialogProps {
  open: boolean;
  onClose: () => void;
}

const discoveryMethods = [
  { value: 'network_scan', label: 'Network Scan', icon: <NetworkCheckOutlined /> },
  { value: 'dhcp_lease', label: 'DHCP Lease Table', icon: <RouterOutlined /> },
  { value: 'dns_query', label: 'DNS Query', icon: <DnsOutlined /> },
  { value: 'active_directory', label: 'Active Directory', icon: <BusinessOutlined /> },
  { value: 'snmp', label: 'SNMP Discovery', icon: <WifiOutlined /> },
  { value: 'manual', label: 'Manual Entry', icon: <ComputerOutlined /> }
];

const mockNetworkRanges: NetworkRange[] = [
  {
    id: 'range_1',
    name: 'Corporate Network',
    cidr: '192.168.1.0/24',
    description: 'Main corporate office network',
    enabled: true,
    lastScanned: '2024-10-24T10:30:00Z',
    devicesFound: 45
  },
  {
    id: 'range_2',
    name: 'Development Lab',
    cidr: '10.0.1.0/24',
    description: 'Development and testing environment',
    enabled: true,
    lastScanned: '2024-10-24T09:15:00Z',
    devicesFound: 12
  },
  {
    id: 'range_3',
    name: 'Guest Network',
    cidr: '172.16.0.0/24',
    description: 'Guest and visitor access',
    enabled: false,
    devicesFound: 0
  }
];

const mockDiscoveryTasks: DiscoveryTask[] = [
  {
    id: 'task_1',
    name: 'Daily Corporate Scan',
    status: 'completed',
    method: 'network_scan',
    targetRanges: ['192.168.1.0/24'],
    schedule: 'Daily at 2:00 AM',
    progress: 100,
    devicesFound: 45,
    startTime: '2024-10-24T02:00:00Z',
    endTime: '2024-10-24T02:15:00Z'
  },
  {
    id: 'task_2',
    name: 'DHCP Discovery',
    status: 'running',
    method: 'dhcp_lease',
    targetRanges: ['10.0.1.0/24'],
    progress: 65,
    devicesFound: 8,
    startTime: '2024-10-24T11:00:00Z'
  },
  {
    id: 'task_3',
    name: 'AD Computer Sync',
    status: 'failed',
    method: 'active_directory',
    targetRanges: [],
    progress: 0,
    devicesFound: 0,
    errors: ['Authentication failed', 'Domain controller unreachable']
  }
];

export default function WorkstationDiscoveryDialog({
  open,
  onClose
}: WorkstationDiscoveryDialogProps) {
  const [activeStep, setActiveStep] = useState(0);
  const [networkRanges, setNetworkRanges] = useState<NetworkRange[]>(mockNetworkRanges);
  const [discoveryTasks, setDiscoveryTasks] = useState<DiscoveryTask[]>(mockDiscoveryTasks);
  const [newRange, setNewRange] = useState({ name: '', cidr: '', description: '' });
  const [selectedMethod, setSelectedMethod] = useState('network_scan');
  const [taskName, setTaskName] = useState('');
  const [selectedRanges, setSelectedRanges] = useState<string[]>([]);

  const steps = [
    'Network Ranges',
    'Discovery Methods',
    'Task Configuration',
    'Execution & Results'
  ];

  const handleAddRange = () => {
    if (newRange.name && newRange.cidr) {
      const range: NetworkRange = {
        id: `range_${Date.now()}`,
        name: newRange.name,
        cidr: newRange.cidr,
        description: newRange.description,
        enabled: true,
        devicesFound: 0
      };
      setNetworkRanges([...networkRanges, range]);
      setNewRange({ name: '', cidr: '', description: '' });
    }
  };

  const handleToggleRange = (id: string) => {
    setNetworkRanges(ranges =>
      ranges.map(range =>
        range.id === id ? { ...range, enabled: !range.enabled } : range
      )
    );
  };

  const handleDeleteRange = (id: string) => {
    setNetworkRanges(ranges => ranges.filter(range => range.id !== id));
  };

  const handleStartDiscovery = () => {
    if (taskName && selectedRanges.length > 0) {
      const newTask: DiscoveryTask = {
        id: `task_${Date.now()}`,
        name: taskName,
        status: 'running',
        method: selectedMethod,
        targetRanges: selectedRanges,
        progress: 0,
        devicesFound: 0,
        startTime: new Date().toISOString()
      };
      setDiscoveryTasks([newTask, ...discoveryTasks]);
      setActiveStep(3);
      
      // Simulate progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          setDiscoveryTasks(tasks =>
            tasks.map(task =>
              task.id === newTask.id
                ? {
                    ...task,
                    status: 'completed',
                    progress: 100,
                    devicesFound: Math.floor(Math.random() * 20) + 5,
                    endTime: new Date().toISOString()
                  }
                : task
            )
          );
        } else {
          setDiscoveryTasks(tasks =>
            tasks.map(task =>
              task.id === newTask.id
                ? {
                    ...task,
                    progress: Math.floor(progress),
                    devicesFound: Math.floor((progress / 100) * (Math.random() * 20 + 5))
                  }
                : task
            )
          );
        }
      }, 1000);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'info';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined />;
      case 'running': return <RefreshOutlined />;
      case 'failed': return <ErrorOutlined />;
      case 'pending': return <ScheduleOutlined />;
      default: return <InfoOutlined />;
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { height: '90vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            <SearchOutlined color="primary" sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Workstation Discovery System
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Automated network discovery and device management
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onClose}>
            <CloseOutlined />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ p: 3 }}>
          <Stepper activeStep={activeStep} orientation="horizontal" sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {/* Step 1: Network Ranges */}
          {activeStep === 0 && (
            <Grid container spacing={3}>
              <Grid size={12}>
                <Card>
                  <CardHeader 
                    title="Network Range Management"
                    subheader="Define IP ranges for workstation discovery"
                  />
                  <CardContent>
                    <Grid container spacing={2} sx={{ mb: 3 }}>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <TextField
                          fullWidth
                          label="Range Name"
                          value={newRange.name}
                          onChange={(e) => setNewRange({ ...newRange, name: e.target.value })}
                          placeholder="e.g., Corporate Network"
                        />
                      </Grid>
                      <Grid size={{ xs: 12, md: 3 }}>
                        <TextField
                          fullWidth
                          label="CIDR Range"
                          value={newRange.cidr}
                          onChange={(e) => setNewRange({ ...newRange, cidr: e.target.value })}
                          placeholder="e.g., 192.168.1.0/24"
                        />
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <TextField
                          fullWidth
                          label="Description"
                          value={newRange.description}
                          onChange={(e) => setNewRange({ ...newRange, description: e.target.value })}
                          placeholder="Optional description"
                        />
                      </Grid>
                      <Grid size={{ xs: 12, md: 2 }}>
                        <Button
                          fullWidth
                          variant="contained"
                          startIcon={<AddOutlined />}
                          onClick={handleAddRange}
                          disabled={!newRange.name || !newRange.cidr}
                        >
                          Add Range
                        </Button>
                      </Grid>
                    </Grid>

                    <List>
                      {networkRanges.map((range) => (
                        <ListItem key={range.id} divider>
                          <ListItemIcon>
                            <NetworkCheckOutlined color={range.enabled ? 'primary' : 'disabled'} />
                          </ListItemIcon>
                          <ListItemText
                            primary={
                              <Box display="flex" alignItems="center" gap={2}>
                                <Typography variant="body1" fontWeight={500}>
                                  {range.name}
                                </Typography>
                                <Chip
                                  label={range.cidr}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontFamily: 'monospace' }}
                                />
                                {range.devicesFound > 0 && (
                                  <Badge badgeContent={range.devicesFound} color="primary">
                                    <ComputerOutlined fontSize="small" />
                                  </Badge>
                                )}
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  {range.description}
                                </Typography>
                                {range.lastScanned && (
                                  <Typography variant="caption" color="text.secondary">
                                    Last scanned: {new Date(range.lastScanned).toLocaleString()}
                                  </Typography>
                                )}
                              </Box>
                            }
                          />
                          <ListItemSecondaryAction>
                            <Box display="flex" alignItems="center" gap={1}>
                              <Switch
                                checked={range.enabled}
                                onChange={() => handleToggleRange(range.id)}
                                size="small"
                              />
                              <IconButton
                                size="small"
                                onClick={() => handleDeleteRange(range.id)}
                                color="error"
                              >
                                <DeleteOutlined />
                              </IconButton>
                            </Box>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Step 2: Discovery Methods */}
          {activeStep === 1 && (
            <Grid container spacing={3}>
              <Grid size={12}>
                <Card>
                  <CardHeader 
                    title="Discovery Methods"
                    subheader="Choose how to discover workstations on your network"
                  />
                  <CardContent>
                    <Grid container spacing={2}>
                      {discoveryMethods.map((method) => (
                        <Grid size={{ xs: 12, md: 6 }} key={method.value}>
                          <Card
                            variant="outlined"
                            sx={{
                              cursor: 'pointer',
                              border: selectedMethod === method.value ? 2 : 1,
                              borderColor: selectedMethod === method.value ? 'primary.main' : 'divider',
                              '&:hover': {
                                borderColor: 'primary.main'
                              }
                            }}
                            onClick={() => setSelectedMethod(method.value)}
                          >
                            <CardContent>
                              <Box display="flex" alignItems="center" gap={2}>
                                {method.icon}
                                <Box>
                                  <Typography variant="h6">
                                    {method.label}
                                  </Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {method.value === 'network_scan' && 'Scan IP ranges for active devices'}
                                    {method.value === 'dhcp_lease' && 'Query DHCP server for lease information'}
                                    {method.value === 'dns_query' && 'Discover devices through DNS records'}
                                    {method.value === 'active_directory' && 'Import computer objects from AD'}
                                    {method.value === 'snmp' && 'Use SNMP to discover network devices'}
                                    {method.value === 'manual' && 'Manually add workstation information'}
                                  </Typography>
                                </Box>
                              </Box>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Step 3: Task Configuration */}
          {activeStep === 2 && (
            <Grid container spacing={3}>
              <Grid size={12}>
                <Card>
                  <CardHeader 
                    title="Discovery Task Configuration"
                    subheader="Configure your discovery task parameters"
                  />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <TextField
                          fullWidth
                          label="Task Name"
                          value={taskName}
                          onChange={(e) => setTaskName(e.target.value)}
                          placeholder="e.g., Evening Network Scan"
                        />
                      </Grid>
                      <Grid size={{ xs: 12, md: 6 }}>
                        <FormControl fullWidth>
                          <InputLabel>Discovery Method</InputLabel>
                          <Select
                            value={selectedMethod}
                            label="Discovery Method"
                            onChange={(e) => setSelectedMethod(e.target.value)}
                          >
                            {discoveryMethods.map((method) => (
                              <MenuItem key={method.value} value={method.value}>
                                <Box display="flex" alignItems="center" gap={1}>
                                  {method.icon}
                                  {method.label}
                                </Box>
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid size={12}>
                        <Typography variant="subtitle2" gutterBottom>
                          Target Network Ranges
                        </Typography>
                        <Box display="flex" gap={1} flexWrap="wrap">
                          {networkRanges
                            .filter(range => range.enabled)
                            .map((range) => (
                              <Chip
                                key={range.id}
                                label={`${range.name} (${range.cidr})`}
                                clickable
                                color={selectedRanges.includes(range.cidr) ? 'primary' : 'default'}
                                onClick={() => {
                                  if (selectedRanges.includes(range.cidr)) {
                                    setSelectedRanges(ranges => ranges.filter(r => r !== range.cidr));
                                  } else {
                                    setSelectedRanges(ranges => [...ranges, range.cidr]);
                                  }
                                }}
                              />
                            ))}
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Step 4: Execution & Results */}
          {activeStep === 3 && (
            <Grid container spacing={3}>
              <Grid size={12}>
                <Card>
                  <CardHeader 
                    title="Discovery Tasks"
                    subheader="Monitor and manage discovery task execution"
                  />
                  <CardContent>
                    <TableContainer component={Paper} variant="outlined">
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Task</TableCell>
                            <TableCell>Method</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Progress</TableCell>
                            <TableCell>Devices Found</TableCell>
                            <TableCell>Actions</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {discoveryTasks.map((task) => (
                            <TableRow key={task.id}>
                              <TableCell>
                                <Box>
                                  <Typography variant="body2" fontWeight={500}>
                                    {task.name}
                                  </Typography>
                                  {task.schedule && (
                                    <Typography variant="caption" color="text.secondary">
                                      {task.schedule}
                                    </Typography>
                                  )}
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={discoveryMethods.find(m => m.value === task.method)?.label}
                                  size="small"
                                  variant="outlined"
                                />
                              </TableCell>
                              <TableCell>
                                <Box display="flex" alignItems="center" gap={1}>
                                  {getStatusIcon(task.status)}
                                  <Chip
                                    label={task.status}
                                    color={getStatusColor(task.status) as any}
                                    size="small"
                                  />
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Box sx={{ width: 100 }}>
                                  <LinearProgress
                                    variant="determinate"
                                    value={task.progress}
                                    color={getStatusColor(task.status) as any}
                                  />
                                  <Typography variant="caption" color="text.secondary">
                                    {task.progress}%
                                  </Typography>
                                </Box>
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" fontWeight={500}>
                                  {task.devicesFound}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Box display="flex" gap={1}>
                                  <Tooltip title="View Details">
                                    <IconButton size="small">
                                      <VisibilityOutlined />
                                    </IconButton>
                                  </Tooltip>
                                  {task.status === 'running' ? (
                                    <Tooltip title="Stop Task">
                                      <IconButton size="small" color="error">
                                        <StopOutlined />
                                      </IconButton>
                                    </Tooltip>
                                  ) : (
                                    <Tooltip title="Restart Task">
                                      <IconButton size="small" color="primary">
                                        <PlayArrowOutlined />
                                      </IconButton>
                                    </Tooltip>
                                  )}
                                </Box>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </CardContent>
                </Card>
              </Grid>

              {discoveryTasks.some(task => task.errors) && (
                <Grid size={12}>
                  <Card>
                    <CardHeader title="Task Errors" />
                    <CardContent>
                      {discoveryTasks
                        .filter(task => task.errors)
                        .map((task) => (
                          <Alert key={task.id} severity="error" sx={{ mb: 2 }}>
                            <Typography variant="body2" fontWeight={500}>
                              {task.name} failed:
                            </Typography>
                            <ul style={{ margin: 0, paddingLeft: 20 }}>
                              {task.errors?.map((error, index) => (
                                <li key={index}>
                                  <Typography variant="body2">{error}</Typography>
                                </li>
                              ))}
                            </ul>
                          </Alert>
                        ))}
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>
          Close
        </Button>
        
        {activeStep > 0 && (
          <Button onClick={() => setActiveStep(activeStep - 1)}>
            Back
          </Button>
        )}
        
        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={() => setActiveStep(activeStep + 1)}
            disabled={
              (activeStep === 0 && networkRanges.filter(r => r.enabled).length === 0) ||
              (activeStep === 2 && (!taskName || selectedRanges.length === 0))
            }
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            startIcon={<PlayArrowOutlined />}
            onClick={handleStartDiscovery}
            disabled={!taskName || selectedRanges.length === 0}
          >
            Start Discovery
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
