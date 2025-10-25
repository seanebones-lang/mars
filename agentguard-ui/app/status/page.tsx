'use client';

import React, { useState, useEffect } from 'react';
import {
  Container, Box, Typography, Grid, Card, CardContent, Chip, LinearProgress,
  List, ListItem, ListItemText, Divider, Alert, AlertTitle, Stack
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Build as BuildIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';

// Types
interface Component {
  id: string;
  name: string;
  description: string;
  status: 'operational' | 'degraded_performance' | 'partial_outage' | 'major_outage' | 'under_maintenance';
  uptime_percentage: number;
  last_checked: string;
  response_time_ms?: number;
}

interface IncidentUpdate {
  id: string;
  timestamp: string;
  status: string;
  message: string;
}

interface Incident {
  id: string;
  title: string;
  severity: 'minor' | 'major' | 'critical';
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  affected_components: string[];
  started_at: string;
  resolved_at?: string;
  updates: IncidentUpdate[];
  impact: string;
}

interface MaintenanceWindow {
  id: string;
  title: string;
  description: string;
  scheduled_start: string;
  scheduled_end: string;
  affected_components: string[];
  status: string;
}

interface UptimeMetrics {
  last_24h: number;
  last_7d: number;
  last_30d: number;
  last_90d: number;
}

interface SystemMetrics {
  cpu_usage_percent: number;
  memory_usage_percent: number;
  disk_usage_percent: number;
  active_connections: number;
  requests_per_minute: number;
  average_response_time_ms: number;
  error_rate_percent: number;
}

interface StatusPageData {
  overall_status: string;
  components: Component[];
  active_incidents: Incident[];
  scheduled_maintenance: MaintenanceWindow[];
  uptime_metrics: UptimeMetrics;
  system_metrics: SystemMetrics;
  last_updated: string;
}

export default function StatusPage() {
  const [statusData, setStatusData] = useState<StatusPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatusData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatusData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatusData = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/status`);
      if (!response.ok) throw new Error('Failed to fetch status');
      const data = await response.json();
      setStatusData(data);
      setError(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational': return 'success';
      case 'degraded_performance': return 'warning';
      case 'partial_outage': return 'error';
      case 'major_outage': return 'error';
      case 'under_maintenance': return 'info';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational': return <CheckCircleIcon color="success" />;
      case 'degraded_performance': return <WarningIcon color="warning" />;
      case 'partial_outage': return <ErrorIcon color="error" />;
      case 'major_outage': return <ErrorIcon color="error" />;
      case 'under_maintenance': return <BuildIcon color="info" />;
      default: return <CheckCircleIcon />;
    }
  };

  const getStatusText = (status: string) => {
    return status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'minor': return 'warning';
      case 'major': return 'error';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography>Loading status...</Typography>
        <LinearProgress sx={{ mt: 2 }} />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">
          <AlertTitle>Error Loading Status</AlertTitle>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!statusData) return null;

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          AgentGuard System Status
        </Typography>
        <Stack direction="row" spacing={2} justifyContent="center" alignItems="center" sx={{ mt: 2 }}>
          {getStatusIcon(statusData.overall_status)}
          <Typography variant="h5" color={getStatusColor(statusData.overall_status)}>
            {getStatusText(statusData.overall_status)}
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Last updated: {new Date(statusData.last_updated).toLocaleString()}
        </Typography>
      </Box>

      {/* Active Incidents */}
      {statusData.active_incidents.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Active Incidents
          </Typography>
          {statusData.active_incidents.map((incident) => (
            <Alert 
              key={incident.id} 
              severity={getSeverityColor(incident.severity) as any}
              sx={{ mb: 2 }}
            >
              <AlertTitle>
                <strong>{incident.title}</strong> - {getStatusText(incident.status)}
              </AlertTitle>
              <Typography variant="body2">{incident.impact}</Typography>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Started: {new Date(incident.started_at).toLocaleString()}
              </Typography>
              {incident.updates.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>Updates:</Typography>
                  {incident.updates.slice(-3).reverse().map((update) => (
                    <Box key={update.id} sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(update.timestamp).toLocaleString()}
                      </Typography>
                      <Typography variant="body2">{update.message}</Typography>
                    </Box>
                  ))}
                </Box>
              )}
            </Alert>
          ))}
        </Box>
      )}

      {/* Scheduled Maintenance */}
      {statusData.scheduled_maintenance.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom fontWeight={600}>
            Scheduled Maintenance
          </Typography>
          {statusData.scheduled_maintenance.map((maintenance) => (
            <Alert key={maintenance.id} severity="info" sx={{ mb: 2 }}>
              <AlertTitle><strong>{maintenance.title}</strong></AlertTitle>
              <Typography variant="body2">{maintenance.description}</Typography>
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                {new Date(maintenance.scheduled_start).toLocaleString()} - {new Date(maintenance.scheduled_end).toLocaleString()}
              </Typography>
            </Alert>
          ))}
        </Box>
      )}

      {/* Components */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom fontWeight={600}>
          System Components
        </Typography>
        <Grid container spacing={2}>
          {statusData.components.map((component) => (
            <Grid item xs={12} md={6} key={component.id}>
              <Card>
                <CardContent>
                  <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {component.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {component.description}
                      </Typography>
                      <Chip 
                        label={getStatusText(component.status)}
                        color={getStatusColor(component.status) as any}
                        size="small"
                        sx={{ mt: 1 }}
                      />
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      {getStatusIcon(component.status)}
                      <Typography variant="h6" color="success.main" sx={{ mt: 1 }}>
                        {component.uptime_percentage.toFixed(2)}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        uptime
                      </Typography>
                      {component.response_time_ms && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {component.response_time_ms.toFixed(0)}ms
                        </Typography>
                      )}
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Uptime Metrics */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom fontWeight={600}>
          <TrendingUpIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Uptime Metrics
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {statusData.uptime_metrics.last_24h.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 24 Hours
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {statusData.uptime_metrics.last_7d.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 7 Days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {statusData.uptime_metrics.last_30d.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 30 Days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main" gutterBottom>
                  {statusData.uptime_metrics.last_90d.toFixed(2)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last 90 Days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* System Metrics */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom fontWeight={600}>
          System Performance
        </Typography>
        <Card>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  CPU Usage: {statusData.system_metrics.cpu_usage_percent.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={statusData.system_metrics.cpu_usage_percent} 
                  color={statusData.system_metrics.cpu_usage_percent > 80 ? 'error' : 'primary'}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Memory Usage: {statusData.system_metrics.memory_usage_percent.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={statusData.system_metrics.memory_usage_percent}
                  color={statusData.system_metrics.memory_usage_percent > 80 ? 'error' : 'primary'}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Disk Usage: {statusData.system_metrics.disk_usage_percent.toFixed(1)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={statusData.system_metrics.disk_usage_percent}
                  color={statusData.system_metrics.disk_usage_percent > 80 ? 'error' : 'primary'}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Error Rate: {statusData.system_metrics.error_rate_percent.toFixed(2)}%
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={statusData.system_metrics.error_rate_percent}
                  color={statusData.system_metrics.error_rate_percent > 1 ? 'error' : 'success'}
                />
              </Grid>
            </Grid>
            <Divider sx={{ my: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Active Connections
                </Typography>
                <Typography variant="h6">
                  {statusData.system_metrics.active_connections}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Requests/min
                </Typography>
                <Typography variant="h6">
                  {statusData.system_metrics.requests_per_minute.toFixed(0)}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
                <Typography variant="h6">
                  {statusData.system_metrics.average_response_time_ms.toFixed(0)}ms
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Error Rate
                </Typography>
                <Typography variant="h6">
                  {statusData.system_metrics.error_rate_percent.toFixed(2)}%
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>

      {/* Footer */}
      <Box sx={{ textAlign: 'center', py: 4, borderTop: 1, borderColor: 'divider' }}>
        <Typography variant="body2" color="text.secondary">
          © 2025 AgentGuard | Real-Time AI Safety Platform
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
          For support, contact: support@agentguard.ai
        </Typography>
      </Box>
    </Container>
  );
}

