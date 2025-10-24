'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  Slider,
  FormControlLabel,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Stack,
  Chip,
  Alert,
  FormGroup,
  Checkbox
} from '@mui/material';
import {
  Notifications,
  Schedule,
  Visibility,
  ClearAll
} from '@mui/icons-material';
import { persistentAlerts, AlertSettings as AlertSettingsType, AlertCategory, AlertSeverity } from '@/lib/persistentAlerts';

export default function AlertSettings() {
  const [settings, setSettings] = useState<AlertSettingsType>(persistentAlerts.getSettings());
  const [stats, setStats] = useState(persistentAlerts.getAlertStats());

  useEffect(() => {
    // Update stats periodically
    const interval = setInterval(() => {
      setStats(persistentAlerts.getAlertStats());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleSettingChange = (key: keyof AlertSettingsType, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    persistentAlerts.updateSettings({ [key]: value });
  };

  const handleCategoryToggle = (category: AlertCategory) => {
    const newCategories = settings.persistentCategories.includes(category)
      ? settings.persistentCategories.filter(c => c !== category)
      : [...settings.persistentCategories, category];
    
    handleSettingChange('persistentCategories', newCategories);
  };

  const handleClearAll = () => {
    persistentAlerts.clearAll();
    setStats(persistentAlerts.getAlertStats());
  };

  const severityLevels: AlertSeverity[] = ['low', 'medium', 'high', 'critical'];
  const categories: { key: AlertCategory; label: string; description: string }[] = [
    { key: 'hallucination', label: 'Hallucination Detection', description: 'AI agent hallucination alerts' },
    { key: 'system', label: 'System Events', description: 'System status and health alerts' },
    { key: 'connection', label: 'Connection Issues', description: 'Network and connectivity alerts' },
    { key: 'performance', label: 'Performance', description: 'Performance and latency alerts' }
  ];

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Notifications color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Persistent Alert Settings
          </Typography>
        </Box>

        {/* Current Stats */}
        {stats.total > 0 && (
          <Alert severity={stats.critical > 0 ? 'error' : stats.unacknowledged > 0 ? 'warning' : 'info'} sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>{stats.unacknowledged} unacknowledged alerts</strong> 
              {stats.critical > 0 && ` (${stats.critical} critical)`}
              {stats.escalated > 0 && ` • ${stats.escalated} escalated`}
            </Typography>
            {stats.unacknowledged > 0 && (
              <Button 
                size="small" 
                color="inherit" 
                onClick={handleClearAll}
                startIcon={<ClearAll />}
                sx={{ mt: 1 }}
              >
                Clear All Alerts
              </Button>
            )}
          </Alert>
        )}

        <Stack spacing={3}>
          {/* Master Enable/Disable */}
          <Box>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enabled}
                  onChange={(e) => handleSettingChange('enabled', e.target.checked)}
                />
              }
              label="Enable Persistent Alerts"
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Show persistent on-screen alerts that require acknowledgment
            </Typography>
          </Box>

          <Divider />

          {/* Alert Categories */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Alert Categories
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              Choose which types of alerts should be persistent
            </Typography>

            <FormGroup>
              {categories.map((category) => (
                <Box key={category.key} sx={{ mb: 1 }}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={settings.persistentCategories.includes(category.key)}
                        onChange={() => handleCategoryToggle(category.key)}
                        disabled={!settings.enabled}
                      />
                    }
                    label={category.label}
                  />
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ ml: 4 }}>
                    {category.description}
                  </Typography>
                </Box>
              ))}
            </FormGroup>
          </Box>

          <Divider />

          {/* Minimum Severity */}
          <Box>
            <FormControl fullWidth disabled={!settings.enabled}>
              <InputLabel>Minimum Severity Level</InputLabel>
              <Select
                value={settings.minimumSeverity}
                label="Minimum Severity Level"
                onChange={(e) => handleSettingChange('minimumSeverity', e.target.value)}
              >
                {severityLevels.map((level) => (
                  <MenuItem key={level} value={level}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        label={level.toUpperCase()}
                        size="small"
                        color={
                          level === 'critical' ? 'error' :
                          level === 'high' ? 'warning' :
                          level === 'medium' ? 'info' : 'success'
                        }
                      />
                      <Typography>
                        {level === 'critical' ? 'Critical and above' :
                         level === 'high' ? 'High and above' :
                         level === 'medium' ? 'Medium and above' : 'All alerts'}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Only alerts at or above this severity will be persistent
            </Typography>
          </Box>

          {/* Max Visible Alerts */}
          <Box>
            <Typography gutterBottom fontWeight={500}>
              Maximum Visible Alerts: {settings.maxVisibleAlerts}
            </Typography>
            <Slider
              value={settings.maxVisibleAlerts}
              onChange={(_, value) => handleSettingChange('maxVisibleAlerts', value as number)}
              disabled={!settings.enabled}
              min={1}
              max={10}
              step={1}
              marks={[
                { value: 1, label: '1' },
                { value: 5, label: '5' },
                { value: 10, label: '10' }
              ]}
            />
            <Typography variant="caption" color="text.secondary">
              Maximum number of alerts to show simultaneously
            </Typography>
          </Box>

          {/* Auto-Escalation Timeout */}
          <Box>
            <Typography gutterBottom fontWeight={500}>
              Auto-Escalation Timeout: {settings.autoEscalateTimeout} minutes
            </Typography>
            <Slider
              value={settings.autoEscalateTimeout}
              onChange={(_, value) => handleSettingChange('autoEscalateTimeout', value as number)}
              disabled={!settings.enabled}
              min={1}
              max={30}
              step={1}
              marks={[
                { value: 1, label: '1m' },
                { value: 5, label: '5m' },
                { value: 15, label: '15m' },
                { value: 30, label: '30m' }
              ]}
            />
            <Typography variant="caption" color="text.secondary">
              Time before unacknowledged alerts are automatically escalated
            </Typography>
          </Box>

          <Divider />

          {/* Display Options */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Display Options
            </Typography>

            <Stack spacing={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showOnAllPages}
                    onChange={(e) => handleSettingChange('showOnAllPages', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Show on All Pages"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.playAudioOnNew}
                    onChange={(e) => handleSettingChange('playAudioOnNew', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Play Audio on New Alerts"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.blinkOnCritical}
                    onChange={(e) => handleSettingChange('blinkOnCritical', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Blink Animation for Critical Alerts"
              />
            </Stack>
          </Box>

          <Divider />

          {/* Test Alert */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Test Persistent Alerts
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {severityLevels.map((severity) => (
                <Button
                  key={severity}
                  variant="outlined"
                  color={
                    severity === 'critical' ? 'error' :
                    severity === 'high' ? 'warning' :
                    severity === 'medium' ? 'info' : 'success'
                  }
                  onClick={() => {
                    persistentAlerts.createAlert({
                      title: `Test ${severity.toUpperCase()} Alert`,
                      message: `This is a test ${severity} severity persistent alert`,
                      severity,
                      category: 'system',
                      metadata: { test: true }
                    });
                  }}
                  disabled={!settings.enabled}
                >
                  {severity.toUpperCase()}
                </Button>
              ))}
            </Box>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
