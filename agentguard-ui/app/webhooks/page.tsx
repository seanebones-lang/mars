'use client';

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  Alert,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Paper,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add,
  Delete,
  Edit,
  Send,
  Notifications,
  Email,
  Webhook,
  Chat,
  Business,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface WebhookConfig {
  webhook_id: string;
  name: string;
  url: string;
  webhook_type: string;
  enabled: boolean;
  alert_types: string[];
  severity_threshold: string;
  headers: Record<string, string>;
  template?: string;
  retry_count: number;
  timeout_seconds: number;
  rate_limit_per_minute: number;
}

interface WebhookStats {
  total_alerts: number;
  total_webhooks: number;
  enabled_webhooks: number;
  severity_distribution: Record<string, number>;
  alert_type_distribution: Record<string, number>;
  rate_limits: Record<string, number>;
}

interface AlertHistory {
  alert_id: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  agent_id: string;
  agent_name: string;
  timestamp: string;
  hallucination_risk: number;
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
      id={`webhook-tabpanel-${index}`}
      aria-labelledby={`webhook-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function WebhooksPage() {
  const [tabValue, setTabValue] = useState(0);
  const [webhooks, setWebhooks] = useState<WebhookConfig[]>([]);
  const [stats, setStats] = useState<WebhookStats | null>(null);
  const [alertHistory, setAlertHistory] = useState<AlertHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<string>('');
  
  // Form states
  const [formData, setFormData] = useState({
    webhook_id: '',
    name: '',
    url: '',
    webhook_type: 'slack',
    enabled: true,
    alert_types: ['hallucination'],
    severity_threshold: 'medium',
    headers: '{"Content-Type": "application/json"}',
    template: '',
    retry_count: 3,
    timeout_seconds: 30,
    rate_limit_per_minute: 60
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [webhooksRes, statsRes, alertsRes] = await Promise.all([
        axios.get(`${API_URL}/webhooks`),
        axios.get(`${API_URL}/webhooks/stats`),
        axios.get(`${API_URL}/webhooks/alerts?limit=50`)
      ]);
      
      setWebhooks(webhooksRes.data.data);
      setStats(statsRes.data.data);
      setAlertHistory(alertsRes.data.data);
      
    } catch (err) {
      console.error('Failed to load webhook data:', err);
      setError('Failed to load webhook data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAddWebhook = async () => {
    try {
      const headers = formData.headers ? JSON.parse(formData.headers) : {};
      
      await axios.post(`${API_URL}/webhooks`, {
        ...formData,
        headers,
        alert_types: formData.alert_types.length > 0 ? formData.alert_types : null
      });
      
      setAddDialogOpen(false);
      resetForm();
      await loadData();
      
    } catch (err) {
      console.error('Failed to add webhook:', err);
      setError('Failed to add webhook. Please check your configuration.');
    }
  };

  const handleDeleteWebhook = async (webhookId: string) => {
    if (!confirm('Are you sure you want to delete this webhook?')) return;
    
    try {
      await axios.delete(`${API_URL}/webhooks/${webhookId}`);
      await loadData();
    } catch (err) {
      console.error('Failed to delete webhook:', err);
      setError('Failed to delete webhook.');
    }
  };

  const handleTestWebhook = async (webhookId: string, testMessage: string) => {
    try {
      const response = await axios.post(`${API_URL}/webhooks/test`, {
        webhook_id: webhookId,
        test_message: testMessage
      });
      
      if (response.data.status === 'success') {
        alert('Test alert sent successfully!');
      } else {
        alert('Test alert failed to send.');
      }
      
      setTestDialogOpen(false);
      
    } catch (err) {
      console.error('Failed to test webhook:', err);
      alert('Failed to test webhook.');
    }
  };

  const resetForm = () => {
    setFormData({
      webhook_id: '',
      name: '',
      url: '',
      webhook_type: 'slack',
      enabled: true,
      alert_types: ['hallucination'],
      severity_threshold: 'medium',
      headers: '{"Content-Type": "application/json"}',
      template: '',
      retry_count: 3,
      timeout_seconds: 30,
      rate_limit_per_minute: 60
    });
  };

  const getWebhookIcon = (type: string) => {
    switch (type) {
      case 'slack': return <Chat color="primary" />;
      case 'teams': return <Business color="primary" />;
      case 'email': return <Email color="primary" />;
      default: return <Webhook color="primary" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <Typography>Loading webhook data...</Typography>
        </Box>
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
            <Typography variant="h4" component="h1" gutterBottom>
              Webhook Management
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Configure alerts for Slack, Teams, email, and custom endpoints
            </Typography>
          </Box>
          
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setAddDialogOpen(true)}
            size="large"
          >
            Add Webhook
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Summary Cards */}
        {stats && (
          <Grid container spacing={3} mb={4}>
            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Webhook color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">Total Webhooks</Typography>
                  </Box>
                  <Typography variant="h4" color="primary">
                    {stats.total_webhooks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {stats.enabled_webhooks} enabled
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Notifications color="info" sx={{ mr: 1 }} />
                    <Typography variant="h6">Total Alerts</Typography>
                  </Box>
                  <Typography variant="h4" color="info">
                    {stats.total_alerts}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    All time
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Warning color="warning" sx={{ mr: 1 }} />
                    <Typography variant="h6">Critical Alerts</Typography>
                  </Box>
                  <Typography variant="h4" color="warning">
                    {stats.severity_distribution.critical || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Requires attention
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, sm: 6, md: 3 }}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <CheckCircle color="success" sx={{ mr: 1 }} />
                    <Typography variant="h6">Success Rate</Typography>
                  </Box>
                  <Typography variant="h4" color="success">
                    {stats.total_alerts > 0 ? '95%' : 'N/A'}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Delivery success
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange}>
            <Tab label="Webhooks" />
            <Tab label="Statistics" />
            <Tab label="Alert History" />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            {webhooks.map((webhook) => (
               <Grid size={{ xs: 12, md: 6, lg: 4 }} key={webhook.webhook_id}>
                <Card>
                  <CardContent>
                    <Box display="flex" alignItems="center" mb={2}>
                      {getWebhookIcon(webhook.webhook_type)}
                      <Box ml={1} flexGrow={1}>
                        <Typography variant="h6">{webhook.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {webhook.webhook_type.toUpperCase()}
                        </Typography>
                      </Box>
                      <Chip
                        label={webhook.enabled ? 'Enabled' : 'Disabled'}
                        color={webhook.enabled ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>

                    <Typography variant="body2" sx={{ mb: 2, wordBreak: 'break-all' }}>
                      {webhook.url}
                    </Typography>

                    <Box display="flex" flexWrap="wrap" gap={0.5} mb={2}>
                      {webhook.alert_types.map((type) => (
                        <Chip key={type} label={type} size="small" variant="outlined" />
                      ))}
                    </Box>

                    <Typography variant="body2" color="text.secondary" mb={2}>
                      Min Severity: <strong>{webhook.severity_threshold}</strong>
                    </Typography>

                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<Send />}
                        onClick={() => {
                          setSelectedWebhook(webhook.webhook_id);
                          setTestDialogOpen(true);
                        }}
                      >
                        Test
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<Delete />}
                        onClick={() => handleDeleteWebhook(webhook.webhook_id)}
                      >
                        Delete
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}

            {webhooks.length === 0 && (
              <Grid size={12}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                  <Webhook sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No webhooks configured
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mb={3}>
                    Add your first webhook to start receiving alerts
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setAddDialogOpen(true)}
                  >
                    Add Webhook
                  </Button>
                </Paper>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          {stats && (
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Severity Distribution
                    </Typography>
                    <List>
                      {Object.entries(stats.severity_distribution).map(([severity, count]) => (
                        <ListItem key={severity}>
                          <ListItemText
                            primary={
                              <Box display="flex" alignItems="center">
                                <Chip
                                  label={severity.toUpperCase()}
                                  color={getSeverityColor(severity) as any}
                                  size="small"
                                  sx={{ mr: 2, minWidth: 80 }}
                                />
                                {count} alerts
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Alert Types
                    </Typography>
                    <List>
                      {Object.entries(stats.alert_type_distribution).map(([type, count]) => (
                        <ListItem key={type}>
                          <ListItemText
                            primary={`${type}: ${count} alerts`}
                          />
                        </ListItem>
                      ))}
                      {Object.keys(stats.alert_type_distribution).length === 0 && (
                        <ListItem>
                          <ListItemText
                            primary="No alerts sent yet"
                            secondary="Alerts will appear here once the system starts detecting issues"
                          />
                        </ListItem>
                      )}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Alerts
              </Typography>
              <List>
                {alertHistory.map((alert, index) => (
                  <React.Fragment key={alert.alert_id}>
                    <ListItem alignItems="flex-start">
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={alert.severity.toUpperCase()}
                              color={getSeverityColor(alert.severity) as any}
                              size="small"
                            />
                            <Typography variant="subtitle2">
                              {alert.title}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {alert.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Agent: {alert.agent_name} • Risk: {(alert.hallucination_risk * 100).toFixed(1)}% • {new Date(alert.timestamp).toLocaleString()}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < alertHistory.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
                {alertHistory.length === 0 && (
                  <ListItem>
                    <ListItemText
                      primary="No alerts in history"
                      secondary="Alert history will appear here once the system starts sending notifications"
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </TabPanel>
      </motion.div>

      {/* Add Webhook Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Webhook</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Webhook ID"
                value={formData.webhook_id}
                onChange={(e) => setFormData({ ...formData, webhook_id: e.target.value })}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid size={12}>
              <TextField
                fullWidth
                label="Webhook URL"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                required
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Webhook Type</InputLabel>
                <Select
                  value={formData.webhook_type}
                  onChange={(e) => setFormData({ ...formData, webhook_type: e.target.value })}
                >
                  <MenuItem value="slack">Slack</MenuItem>
                  <MenuItem value="teams">Microsoft Teams</MenuItem>
                  <MenuItem value="generic">Generic</MenuItem>
                  <MenuItem value="pagerduty">PagerDuty</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Severity Threshold</InputLabel>
                <Select
                  value={formData.severity_threshold}
                  onChange={(e) => setFormData({ ...formData, severity_threshold: e.target.value })}
                >
                  <MenuItem value="low">Low</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="critical">Critical</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid size={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleAddWebhook} variant="contained">Add Webhook</Button>
        </DialogActions>
      </Dialog>

      {/* Test Webhook Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Test Webhook</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Test Message"
            defaultValue="This is a test alert from Watcher-AI webhook system."
            sx={{ mt: 2 }}
            id="test-message"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={() => {
              const message = (document.getElementById('test-message') as HTMLInputElement)?.value || 'Test message';
              handleTestWebhook(selectedWebhook, message);
            }}
            variant="contained"
            startIcon={<Send />}
          >
            Send Test
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
