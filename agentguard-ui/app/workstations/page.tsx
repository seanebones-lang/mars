"use client";

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  Fab,
  Badge,
  Switch,
  FormControlLabel,
  Divider,
  Avatar,
  ListItemText,
  Menu,
  ListItemIcon,
  Stack
} from '@mui/material';
import {
  SearchOutlined,
  FilterListOutlined,
  RefreshOutlined,
  SettingsOutlined,
  ComputerOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  InfoOutlined,
  LocationOnOutlined,
  SpeedOutlined,
  MemoryOutlined,
  StorageOutlined,
  NetworkCheckOutlined,
  PlayArrowOutlined,
  StopOutlined,
  RestartAltOutlined,
  DeleteOutlined,
  MoreVertOutlined,
  ViewListOutlined,
  ViewModuleOutlined,
  MapOutlined,
  TrendingUpOutlined,
  NotificationsOutlined,
  GroupOutlined,
  BusinessOutlined
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '@mui/material/styles';
import InteractiveWorldMap from '@/components/InteractiveWorldMap';
import WorkstationDetailsDialog from '@/components/WorkstationDetailsDialog';
import WorkstationDiscoveryDialog from '@/components/WorkstationDiscoveryDialog';

// Mock data for workstations
const generateMockWorkstations = (count: number) => {
  const statuses = ['online', 'offline', 'monitoring', 'error', 'maintenance'];
  const locationData = [
    { name: 'New York', lat: 40.7128, lng: -74.0060 },
    { name: 'London', lat: 51.5074, lng: -0.1278 },
    { name: 'Tokyo', lat: 35.6762, lng: 139.6503 },
    { name: 'Sydney', lat: -33.8688, lng: 151.2093 },
    { name: 'Frankfurt', lat: 50.1109, lng: 8.6821 },
    { name: 'Singapore', lat: 1.3521, lng: 103.8198 },
    { name: 'Toronto', lat: 43.6532, lng: -79.3832 },
    { name: 'Mumbai', lat: 19.0760, lng: 72.8777 }
  ];
  const departments = ['IT', 'Finance', 'HR', 'Sales', 'Marketing', 'Operations', 'R&D', 'Support'];
  const manufacturers = ['Dell', 'HP', 'Lenovo', 'Apple', 'ASUS', 'Acer', 'Microsoft'];
  const models = ['OptiPlex 7090', 'EliteDesk 800', 'ThinkCentre M90q', 'iMac Pro', 'VivoBook', 'Aspire', 'Surface Studio'];
  const platforms = ['Windows 11', 'macOS Sonoma', 'Ubuntu 22.04', 'Windows 10', 'macOS Ventura', 'CentOS 8'];
  const users = ['john.doe', 'jane.smith', 'mike.johnson', 'sarah.wilson', 'david.brown', 'lisa.davis'];
  const discoveryMethods = ['network_scan', 'dhcp_lease', 'dns_query', 'active_directory', 'manual'];
  const commonPorts = [22, 80, 443, 3389, 5900, 8080, 9090];
  const commonServices = ['SSH', 'HTTP', 'HTTPS', 'RDP', 'VNC', 'HTTP-Alt', 'Prometheus'];
  const softwareList = ['Chrome', 'Firefox', 'VS Code', 'Office 365', 'Slack', 'Zoom', 'Docker', 'Python', 'Node.js'];
  const processList = ['chrome.exe', 'firefox.exe', 'code.exe', 'outlook.exe', 'slack.exe', 'zoom.exe', 'docker.exe'];
  const vulnerabilities = [
    { severity: 'low', description: 'Outdated browser version', cve: 'CVE-2024-1234' },
    { severity: 'medium', description: 'Unpatched OS vulnerability', cve: 'CVE-2024-5678' },
    { severity: 'high', description: 'Critical security update missing', cve: 'CVE-2024-9012' }
  ];
  
  return Array.from({ length: count }, (_, i) => {
    const locationInfo = locationData[Math.floor(Math.random() * locationData.length)];
    const latOffset = (Math.random() - 0.5) * 0.5;
    const lngOffset = (Math.random() - 0.5) * 0.5;
    const platform = platforms[Math.floor(Math.random() * platforms.length)];
    const manufacturer = manufacturers[Math.floor(Math.random() * manufacturers.length)];
    const openPortsCount = Math.floor(Math.random() * 5) + 1;
    const selectedPorts = commonPorts.slice(0, openPortsCount);
    const services: { [port: number]: string } = {};
    selectedPorts.forEach((port, idx) => {
      services[port] = commonServices[idx] || 'Unknown';
    });
    
    const vulnCount = Math.floor(Math.random() * 3);
    const deviceVulns = vulnerabilities.slice(0, vulnCount);
    const securityScore = Math.max(0, 100 - (vulnCount * 25) - Math.floor(Math.random() * 20));
    
    return {
      id: `ws_${i.toString().padStart(4, '0')}`,
      hostname: `workstation-${i + 1}`,
      status: statuses[Math.floor(Math.random() * statuses.length)],
      location: locationInfo.name,
      department: departments[Math.floor(Math.random() * departments.length)],
      ipAddress: `192.168.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`,
      lastSeen: new Date(Date.now() - Math.random() * 86400000).toISOString(),
      cpuUsage: Math.floor(Math.random() * 100),
      memoryUsage: Math.floor(Math.random() * 100),
      diskUsage: Math.floor(Math.random() * 100),
      agentCount: Math.floor(Math.random() * 5),
      alertCount: Math.floor(Math.random() * 10),
      platform: platform.split(' ')[0], // Keep backward compatibility
      version: '1.0.0',
      uptime: Math.floor(Math.random() * 86400),
      networkLatency: Math.floor(Math.random() * 100),
      coordinates: {
        lat: locationInfo.lat + latOffset,
        lng: locationInfo.lng + lngOffset
      },
      // Additional backend fields
      macAddress: Array.from({length: 6}, () => Math.floor(Math.random() * 256).toString(16).padStart(2, '0')).join(':'),
      user: users[Math.floor(Math.random() * users.length)],
      cpuCount: [4, 6, 8, 12, 16][Math.floor(Math.random() * 5)],
      memoryTotalGb: [8, 16, 32, 64, 128][Math.floor(Math.random() * 5)],
      diskTotalGb: [256, 512, 1024, 2048][Math.floor(Math.random() * 4)],
      platformVersion: platform,
      pythonVersion: ['3.9.0', '3.10.0', '3.11.0', '3.12.0'][Math.floor(Math.random() * 4)],
      watcherClientVersion: '1.2.0',
      manufacturer,
      model: models[Math.floor(Math.random() * models.length)],
      serialNumber: `SN${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
      openPorts: selectedPorts,
      services,
      installedSoftware: softwareList.slice(0, Math.floor(Math.random() * 6) + 3),
      runningProcesses: processList.slice(0, Math.floor(Math.random() * 4) + 2),
      vulnerabilities: deviceVulns,
      securityScore,
      agentInstalled: Math.random() > 0.3,
      agentVersion: Math.random() > 0.5 ? '1.2.0' : '1.1.0',
      agentStatus: ['active', 'idle', 'error'][Math.floor(Math.random() * 3)],
      discoveryMethod: discoveryMethods[Math.floor(Math.random() * discoveryMethods.length)],
      tags: ['production', 'monitored', 'critical'].slice(0, Math.floor(Math.random() * 3))
    };
  });
};

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

const formatUptime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
};

const WorkstationCard: React.FC<{ 
  workstation: Workstation; 
  onSelect: (id: string) => void; 
  selected: boolean;
  onManage: (workstation: Workstation) => void;
}> = ({
  workstation,
  onSelect,
  selected,
  onManage
}) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        sx={{
          cursor: 'pointer',
          border: selected ? `2px solid ${theme.palette.primary.main}` : '1px solid',
          borderColor: selected ? 'primary.main' : 'divider',
          '&:hover': {
            boxShadow: theme.shadows[4],
            borderColor: 'primary.main'
          }
        }}
        onClick={() => onSelect(workstation.id)}
      >
        <CardHeader
          avatar={
            <Avatar sx={{ bgcolor: getStatusColor(workstation.status) === 'success' ? 'success.main' : 
                                getStatusColor(workstation.status) === 'error' ? 'error.main' :
                                getStatusColor(workstation.status) === 'warning' ? 'warning.main' :
                                getStatusColor(workstation.status) === 'info' ? 'info.main' : 'grey.500' }}>
              {getStatusIcon(workstation.status)}
            </Avatar>
          }
          action={
            <IconButton onClick={handleMenuClick}>
              <MoreVertOutlined />
            </IconButton>
          }
          title={
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="h6" noWrap>
                {workstation.hostname}
              </Typography>
              <Chip
                label={workstation.status}
                color={getStatusColor(workstation.status) as any}
                size="small"
              />
            </Box>
          }
          subheader={
            <Box>
              <Typography variant="body2" color="text.secondary">
                {workstation.location} • {workstation.department}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {workstation.ipAddress} • {workstation.platform}
              </Typography>
            </Box>
          }
        />
        
        <CardContent sx={{ pt: 0 }}>
          <Grid container spacing={2}>
            <Grid size={6}>
              <Box display="flex" alignItems="center" gap={1}>
                <SpeedOutlined fontSize="small" color="action" />
                <Box flex={1}>
                  <Typography variant="caption" color="text.secondary">
                    CPU: {workstation.cpuUsage}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={workstation.cpuUsage}
                    color={workstation.cpuUsage > 80 ? 'error' : workstation.cpuUsage > 60 ? 'warning' : 'primary'}
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>
              </Box>
            </Grid>
            
            <Grid size={6}>
              <Box display="flex" alignItems="center" gap={1}>
                <MemoryOutlined fontSize="small" color="action" />
                <Box flex={1}>
                  <Typography variant="caption" color="text.secondary">
                    Memory: {workstation.memoryUsage}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={workstation.memoryUsage}
                    color={workstation.memoryUsage > 80 ? 'error' : workstation.memoryUsage > 60 ? 'warning' : 'primary'}
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>
              </Box>
            </Grid>
            
            <Grid size={12}>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box display="flex" alignItems="center" gap={1}>
                  <ComputerOutlined fontSize="small" color="action" />
                  <Typography variant="body2">
                    {workstation.agentCount} agents
                  </Typography>
                </Box>
                
                <Box display="flex" alignItems="center" gap={1}>
                  {workstation.alertCount > 0 && (
                    <Badge badgeContent={workstation.alertCount} color="error">
                      <NotificationsOutlined fontSize="small" />
                    </Badge>
                  )}
                  <Typography variant="caption" color="text.secondary">
                    {formatUptime(workstation.uptime)}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <PlayArrowOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText>Start Monitoring</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <StopOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText>Stop Monitoring</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose}>
            <ListItemIcon>
              <RestartAltOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText>Restart Agent</ListItemText>
          </MenuItem>
          <Divider />
          <MenuItem onClick={() => {
            handleMenuClose();
            onManage(workstation);
          }}>
            <ListItemIcon>
              <SettingsOutlined fontSize="small" />
            </ListItemIcon>
            <ListItemText>Manage Workstation</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleMenuClose} sx={{ color: 'error.main' }}>
            <ListItemIcon>
              <DeleteOutlined fontSize="small" color="error" />
            </ListItemIcon>
            <ListItemText>Remove</ListItemText>
          </MenuItem>
        </Menu>
      </Card>
    </motion.div>
  );
};

const WorkstationRow: React.FC<{ workstation: Workstation; onSelect: (id: string) => void; selected: boolean }> = ({
  workstation,
  onSelect,
  selected
}) => {
  const theme = useTheme();

  return (
    <TableRow
      hover
      selected={selected}
      onClick={() => onSelect(workstation.id)}
      sx={{ cursor: 'pointer' }}
    >
      <TableCell>
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar sx={{ 
            bgcolor: getStatusColor(workstation.status) === 'success' ? 'success.main' : 
                     getStatusColor(workstation.status) === 'error' ? 'error.main' :
                     getStatusColor(workstation.status) === 'warning' ? 'warning.main' :
                     getStatusColor(workstation.status) === 'info' ? 'info.main' : 'grey.500',
            width: 32,
            height: 32
          }}>
            {getStatusIcon(workstation.status)}
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight={500}>
              {workstation.hostname}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {workstation.ipAddress}
            </Typography>
          </Box>
        </Box>
      </TableCell>
      
      <TableCell>
        <Chip
          label={workstation.status}
          color={getStatusColor(workstation.status) as any}
          size="small"
        />
      </TableCell>
      
      <TableCell>
        <Typography variant="body2">{workstation.location}</Typography>
        <Typography variant="caption" color="text.secondary">
          {workstation.department}
        </Typography>
      </TableCell>
      
      <TableCell>
        <Box display="flex" alignItems="center" gap={1}>
          <LinearProgress
            variant="determinate"
            value={workstation.cpuUsage}
            color={workstation.cpuUsage > 80 ? 'error' : workstation.cpuUsage > 60 ? 'warning' : 'primary'}
            sx={{ width: 60, height: 6, borderRadius: 3 }}
          />
          <Typography variant="caption">
            {workstation.cpuUsage}%
          </Typography>
        </Box>
      </TableCell>
      
      <TableCell>
        <Box display="flex" alignItems="center" gap={1}>
          <LinearProgress
            variant="determinate"
            value={workstation.memoryUsage}
            color={workstation.memoryUsage > 80 ? 'error' : workstation.memoryUsage > 60 ? 'warning' : 'primary'}
            sx={{ width: 60, height: 6, borderRadius: 3 }}
          />
          <Typography variant="caption">
            {workstation.memoryUsage}%
          </Typography>
        </Box>
      </TableCell>
      
      <TableCell>
        <Typography variant="body2">{workstation.agentCount}</Typography>
      </TableCell>
      
      <TableCell>
        {workstation.alertCount > 0 ? (
          <Badge badgeContent={workstation.alertCount} color="error">
            <NotificationsOutlined />
          </Badge>
        ) : (
          <Typography variant="body2" color="text.secondary">-</Typography>
        )}
      </TableCell>
      
      <TableCell>
        <Typography variant="caption" color="text.secondary">
          {formatUptime(workstation.uptime)}
        </Typography>
      </TableCell>
    </TableRow>
  );
};

export default function WorkstationsPage() {
  const theme = useTheme();
  const [workstations, setWorkstations] = useState<Workstation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [locationFilter, setLocationFilter] = useState('all');
  const [departmentFilter, setDepartmentFilter] = useState('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list' | 'map'>('grid');
  const [selectedWorkstations, setSelectedWorkstations] = useState<Set<string>>(new Set());
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedWorkstation, setSelectedWorkstation] = useState<Workstation | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [manageDialogOpen, setManageDialogOpen] = useState(false);
  const [discoveryDialogOpen, setDiscoveryDialogOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  // Load mock data
  useEffect(() => {
    const loadWorkstations = async () => {
      setLoading(true);
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setWorkstations(generateMockWorkstations(150));
      setLoading(false);
    };

    loadWorkstations();
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate real-time updates
      setWorkstations(prev => prev.map(ws => ({
        ...ws,
        cpuUsage: Math.max(0, Math.min(100, ws.cpuUsage + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(0, Math.min(100, ws.memoryUsage + (Math.random() - 0.5) * 5)),
        lastSeen: new Date().toISOString()
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Filter workstations
  const filteredWorkstations = useMemo(() => {
    return workstations.filter(ws => {
      const matchesSearch = ws.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           ws.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           ws.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           ws.ipAddress.includes(searchTerm);
      
      const matchesStatus = statusFilter === 'all' || ws.status === statusFilter;
      const matchesLocation = locationFilter === 'all' || ws.location === locationFilter;
      const matchesDepartment = departmentFilter === 'all' || ws.department === departmentFilter;
      
      return matchesSearch && matchesStatus && matchesLocation && matchesDepartment;
    });
  }, [workstations, searchTerm, statusFilter, locationFilter, departmentFilter]);

  // Get unique values for filters
  const uniqueLocations = [...new Set(workstations.map(ws => ws.location))].sort();
  const uniqueDepartments = [...new Set(workstations.map(ws => ws.department))].sort();

  // Statistics
  const stats = useMemo(() => {
    const total = workstations.length;
    const online = workstations.filter(ws => ws.status === 'online').length;
    const monitoring = workstations.filter(ws => ws.status === 'monitoring').length;
    const offline = workstations.filter(ws => ws.status === 'offline').length;
    const errors = workstations.filter(ws => ws.status === 'error').length;
    const totalAlerts = workstations.reduce((sum, ws) => sum + ws.alertCount, 0);
    const avgCpu = Math.round(workstations.reduce((sum, ws) => sum + ws.cpuUsage, 0) / total);
    const avgMemory = Math.round(workstations.reduce((sum, ws) => sum + ws.memoryUsage, 0) / total);

    return { total, online, monitoring, offline, errors, totalAlerts, avgCpu, avgMemory };
  }, [workstations]);

  const handleWorkstationSelect = (id: string) => {
    const workstation = workstations.find(ws => ws.id === id);
    if (workstation) {
      setSelectedWorkstation(workstation);
      setDetailsOpen(true);
    }
  };

  const handleBulkSelect = (id: string) => {
    const newSelected = new Set(selectedWorkstations);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedWorkstations(newSelected);
  };

  const handleRefresh = () => {
    setWorkstations(generateMockWorkstations(150));
  };

  // Workstation Management Functions
  const handleManageWorkstation = (workstation: Workstation) => {
    setSelectedWorkstation(workstation);
    setManageDialogOpen(true);
  };

  const executeWorkstationAction = async (action: string, workstationId: string) => {
    setActionInProgress(action);
    try {
      // Simulate API call to backend
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update workstation status based on action
      setWorkstations(prev => prev.map(ws => {
        if (ws.id === workstationId) {
          switch (action) {
            case 'start_monitoring':
              return { ...ws, status: 'monitoring' };
            case 'stop_monitoring':
              return { ...ws, status: 'offline' };
            case 'restart_agent':
              return { ...ws, status: 'online', uptime: 0 };
            case 'update_software':
              return { ...ws, version: '1.1.0' };
            case 'run_diagnostics':
              return { ...ws, alertCount: 0 };
            default:
              return ws;
          }
        }
        return ws;
      }));
      
      // Show success notification
      console.log(`Action ${action} completed successfully for workstation ${workstationId}`);
    } catch (error) {
      console.error(`Failed to execute ${action}:`, error);
    } finally {
      setActionInProgress(null);
    }
  };

  const executeBulkAction = async (action: string, workstationIds: string[]) => {
    setActionInProgress(action);
    try {
      // Simulate bulk API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      // Update multiple workstations
      setWorkstations(prev => prev.map(ws => {
        if (workstationIds.includes(ws.id)) {
          switch (action) {
            case 'bulk_update':
              return { ...ws, version: '1.1.0' };
            case 'bulk_restart':
              return { ...ws, status: 'online', uptime: 0 };
            case 'bulk_scan':
              return { ...ws, alertCount: 0 };
            default:
              return ws;
          }
        }
        return ws;
      }));
      
      console.log(`Bulk action ${action} completed for ${workstationIds.length} workstations`);
    } catch (error) {
      console.error(`Failed to execute bulk ${action}:`, error);
    } finally {
      setActionInProgress(null);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Workstation Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Monitor and manage {stats.total} workstations across your enterprise
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
            }
            label="Auto-refresh"
          />
          
          <Button
            variant="outlined"
            startIcon={<RefreshOutlined />}
            onClick={handleRefresh}
          >
            Refresh
          </Button>
          
          <Button
            variant="contained"
            startIcon={<SearchOutlined />}
            onClick={() => setDiscoveryDialogOpen(true)}
          >
            Discovery
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <ComputerOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h4">{stats.total}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Workstations
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
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircleOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h4">{stats.online}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Online ({Math.round((stats.online / stats.total) * 100)}%)
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
                <Avatar sx={{ bgcolor: 'error.main' }}>
                  <ErrorOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h4">{stats.errors}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Errors & Alerts
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
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <TrendingUpOutlined />
                </Avatar>
                <Box>
                  <Typography variant="h4">{stats.avgCpu}%</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg CPU Usage
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters and Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                placeholder="Search workstations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchOutlined />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="online">Online</MenuItem>
                  <MenuItem value="monitoring">Monitoring</MenuItem>
                  <MenuItem value="offline">Offline</MenuItem>
                  <MenuItem value="error">Error</MenuItem>
                  <MenuItem value="maintenance">Maintenance</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Location</InputLabel>
                <Select
                  value={locationFilter}
                  label="Location"
                  onChange={(e) => setLocationFilter(e.target.value)}
                >
                  <MenuItem value="all">All Locations</MenuItem>
                  {uniqueLocations.map(location => (
                    <MenuItem key={location} value={location}>{location}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 2 }}>
              <FormControl fullWidth>
                <InputLabel>Department</InputLabel>
                <Select
                  value={departmentFilter}
                  label="Department"
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                >
                  <MenuItem value="all">All Departments</MenuItem>
                  {uniqueDepartments.map(dept => (
                    <MenuItem key={dept} value={dept}>{dept}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid size={{ xs: 12, md: 2 }}>
              <Box display="flex" gap={1}>
                <Tooltip title="Grid View">
                  <IconButton
                    color={viewMode === 'grid' ? 'primary' : 'default'}
                    onClick={() => setViewMode('grid')}
                  >
                    <ViewModuleOutlined />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="List View">
                  <IconButton
                    color={viewMode === 'list' ? 'primary' : 'default'}
                    onClick={() => setViewMode('list')}
                  >
                    <ViewListOutlined />
                  </IconButton>
                </Tooltip>
                
                <Tooltip title="Map View">
                  <IconButton
                    color={viewMode === 'map' ? 'primary' : 'default'}
                    onClick={() => setViewMode('map')}
                  >
                    <MapOutlined />
                  </IconButton>
                </Tooltip>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Results Summary */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="body1">
          Showing {filteredWorkstations.length} of {workstations.length} workstations
        </Typography>
        
        {selectedWorkstations.size > 0 && (
          <Box display="flex" gap={2} alignItems="center">
            <Typography variant="body2">
              {selectedWorkstations.size} selected
            </Typography>
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => executeBulkAction('bulk_update', Array.from(selectedWorkstations))}
              disabled={actionInProgress !== null}
            >
              Bulk Actions
            </Button>
          </Box>
        )}
      </Box>

      {/* Content */}
      {loading ? (
        <Box display="flex" justifyContent="center" py={8}>
          <LinearProgress sx={{ width: 300 }} />
        </Box>
      ) : (
        <>
          {/* Grid View */}
          {viewMode === 'grid' && (
            <Grid container spacing={3}>
              <AnimatePresence>
                {filteredWorkstations.map((workstation) => (
                   <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={workstation.id}>
                    <WorkstationCard
                      workstation={workstation}
                      onSelect={handleWorkstationSelect}
                      selected={selectedWorkstations.has(workstation.id)}
                      onManage={handleManageWorkstation}
                    />
                  </Grid>
                ))}
              </AnimatePresence>
            </Grid>
          )}

          {/* List View */}
          {viewMode === 'list' && (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Workstation</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Location</TableCell>
                    <TableCell>CPU</TableCell>
                    <TableCell>Memory</TableCell>
                    <TableCell>Agents</TableCell>
                    <TableCell>Alerts</TableCell>
                    <TableCell>Uptime</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredWorkstations.map((workstation) => (
                    <WorkstationRow
                      key={workstation.id}
                      workstation={workstation}
                      onSelect={handleWorkstationSelect}
                      selected={selectedWorkstations.has(workstation.id)}
                    />
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Map View */}
          {viewMode === 'map' && (
            <InteractiveWorldMap
              workstations={filteredWorkstations}
              onWorkstationSelect={(workstation) => handleWorkstationSelect(workstation.id)}
            />
          )}
        </>
      )}

      {/* Comprehensive Workstation Details Dialog */}
      <WorkstationDetailsDialog
        open={detailsOpen}
        workstation={selectedWorkstation}
        onClose={() => setDetailsOpen(false)}
        onAction={executeWorkstationAction}
        actionInProgress={actionInProgress}
      />

      {/* Comprehensive Workstation Management Dialog */}
      <Dialog
        open={manageDialogOpen}
        onClose={() => setManageDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={2}>
            <ComputerOutlined color="primary" />
            <Box>
              <Typography variant="h5" fontWeight={600}>
                Manage Workstation: {selectedWorkstation?.hostname}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Enterprise Workstation Management Console
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedWorkstation && (
            <Grid container spacing={4}>
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
                          onClick={() => executeWorkstationAction('start_monitoring', selectedWorkstation.id)}
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
                          onClick={() => executeWorkstationAction('stop_monitoring', selectedWorkstation.id)}
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
                          onClick={() => executeWorkstationAction('restart_agent', selectedWorkstation.id)}
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
                          onClick={() => executeWorkstationAction('run_diagnostics', selectedWorkstation.id)}
                          disabled={actionInProgress !== null}
                        >
                          Run Diagnostics
                        </Button>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* System Management */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="System Management" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<SettingsOutlined />}
                        onClick={() => executeWorkstationAction('update_software', selectedWorkstation.id)}
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

              {/* Security & Compliance */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardHeader title="Security & Compliance" />
                  <CardContent>
                    <Stack spacing={2}>
                      <Button
                        fullWidth
                        variant="contained"
                        color="warning"
                        startIcon={<WarningOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Security Scan
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<CheckCircleOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Compliance Check
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<InfoOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Audit Trail
                      </Button>
                      <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<BusinessOutlined />}
                        disabled={actionInProgress !== null}
                      >
                        Policy Enforcement
                      </Button>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>

              {/* Real-time Metrics */}
              <Grid size={12}>
                <Card>
                  <CardHeader title="Real-time Performance Metrics" />
                  <CardContent>
                    <Grid container spacing={3}>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="primary.main" fontWeight={700}>
                            {selectedWorkstation.cpuUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            CPU Usage
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={selectedWorkstation.cpuUsage}
                            color={selectedWorkstation.cpuUsage > 80 ? 'error' : 'primary'}
                            sx={{ mt: 1, height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="info.main" fontWeight={700}>
                            {selectedWorkstation.memoryUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Memory Usage
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={selectedWorkstation.memoryUsage}
                            color={selectedWorkstation.memoryUsage > 80 ? 'error' : 'info'}
                            sx={{ mt: 1, height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                      <Grid size={{ xs: 12, md: 4 }}>
                        <Box textAlign="center">
                          <Typography variant="h4" color="success.main" fontWeight={700}>
                            {selectedWorkstation.diskUsage}%
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Disk Usage
                          </Typography>
                          <LinearProgress
                            variant="determinate"
                            value={selectedWorkstation.diskUsage}
                            color={selectedWorkstation.diskUsage > 80 ? 'error' : 'success'}
                            sx={{ mt: 1, height: 8, borderRadius: 4 }}
                          />
                        </Box>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* AI-Powered Insights */}
              <Grid size={12}>
                <Card>
                  <CardHeader title="AI-Powered Insights & Recommendations" />
                  <CardContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                      <Typography variant="body2" fontWeight={500}>
                        AI Analysis Complete
                      </Typography>
                      <Typography variant="body2">
                        Based on performance patterns, this workstation shows optimal performance. 
                        Recommended actions: Schedule maintenance during low-usage hours (2-4 AM).
                      </Typography>
                    </Alert>
                    
                    <Box display="flex" gap={2} flexWrap="wrap">
                      <Chip 
                        label="Performance: Excellent" 
                        color="success" 
                        icon={<TrendingUpOutlined />} 
                      />
                      <Chip 
                        label="Security: Compliant" 
                        color="success" 
                        icon={<CheckCircleOutlined />} 
                      />
                      <Chip 
                        label="Uptime: 99.8%" 
                        color="primary" 
                        icon={<SpeedOutlined />} 
                      />
                      <Chip 
                        label="Next Maintenance: 3 days" 
                        color="warning" 
                        icon={<WarningOutlined />} 
                      />
                    </Box>
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
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setManageDialogOpen(false)}>
            Close
          </Button>
          <Button 
            variant="outlined" 
            startIcon={<GroupOutlined />}
            onClick={() => {
              setManageDialogOpen(false);
              // Open bulk management for similar workstations
            }}
          >
            Manage Similar
          </Button>
          <Button 
            variant="contained" 
            startIcon={<RefreshOutlined />}
            onClick={() => handleRefresh()}
          >
            Refresh Data
          </Button>
        </DialogActions>
      </Dialog>

      {/* Workstation Discovery Dialog */}
      <WorkstationDiscoveryDialog
        open={discoveryDialogOpen}
        onClose={() => setDiscoveryDialogOpen(false)}
      />

    </Container>
  );
}
