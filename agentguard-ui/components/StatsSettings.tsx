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
  Alert,
  Chip
} from '@mui/material';
import {
  Speed,
  Refresh,
  Visibility,
  TrendingUp
} from '@mui/icons-material';
import { realtimeStats, StatsSettings as StatsSettingsType } from '@/lib/realtimeStats';

export default function StatsSettings() {
  const [settings, setSettings] = useState<StatsSettingsType>(realtimeStats.getSettings());
  const [metrics, setMetrics] = useState(realtimeStats.getMetrics());

  useEffect(() => {
    const unsubscribe = realtimeStats.subscribe(setMetrics);
    return unsubscribe;
  }, []);

  const handleSettingChange = (key: keyof StatsSettingsType, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    realtimeStats.updateSettings({ [key]: value });
  };

  const handleReset = () => {
    realtimeStats.reset();
  };

  const positions = [
    { value: 'top-left', label: 'Top Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'bottom-right', label: 'Bottom Right' },
    { value: 'floating', label: 'Floating Center' }
  ];

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Speed color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Real-time Stats Settings
          </Typography>
        </Box>

        {/* Current Session Stats */}
        {metrics.totalResponses > 0 && (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Session Active:</strong> {metrics.totalResponses} responses processed • 
              {metrics.responsesPerMinute}/min current rate • 
              {(metrics.flaggedRate * 100).toFixed(1)}% flagged
            </Typography>
            <Button 
              size="small" 
              color="inherit" 
              onClick={handleReset}
              startIcon={<Refresh />}
              sx={{ mt: 1 }}
            >
              Reset Session Data
            </Button>
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
              label="Enable Real-time Stats Overlay"
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Show live performance metrics overlay on all pages
            </Typography>
          </Box>

          <Divider />

          {/* Display Settings */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Display Options
            </Typography>

            <Stack spacing={2}>
              <FormControl fullWidth disabled={!settings.enabled}>
                <InputLabel>Overlay Position</InputLabel>
                <Select
                  value={settings.position}
                  label="Overlay Position"
                  onChange={(e) => handleSettingChange('position', e.target.value)}
                >
                  {positions.map((pos) => (
                    <MenuItem key={pos.value} value={pos.value}>
                      {pos.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.compact}
                    onChange={(e) => handleSettingChange('compact', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Compact Mode"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showTrends}
                    onChange={(e) => handleSettingChange('showTrends', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Show Trend Charts"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showAgentBreakdown}
                    onChange={(e) => handleSettingChange('showAgentBreakdown', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Show Agent Breakdown"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoHide}
                    onChange={(e) => handleSettingChange('autoHide', e.target.checked)}
                    disabled={!settings.enabled}
                  />
                }
                label="Auto-hide When Inactive"
              />
            </Stack>
          </Box>

          <Divider />

          {/* Performance Settings */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Performance Settings
            </Typography>

            <Stack spacing={3}>
              <Box>
                <Typography gutterBottom fontWeight={500}>
                  Update Interval: {settings.updateInterval / 1000}s
                </Typography>
                <Slider
                  value={settings.updateInterval}
                  onChange={(_, value) => handleSettingChange('updateInterval', value as number)}
                  disabled={!settings.enabled}
                  min={500}
                  max={5000}
                  step={500}
                  marks={[
                    { value: 500, label: '0.5s' },
                    { value: 1000, label: '1s' },
                    { value: 2000, label: '2s' },
                    { value: 5000, label: '5s' }
                  ]}
                />
                <Typography variant="caption" color="text.secondary">
                  How often to update the statistics display
                </Typography>
              </Box>

              <Box>
                <Typography gutterBottom fontWeight={500}>
                  Trend Window: {settings.trendWindow} minutes
                </Typography>
                <Slider
                  value={settings.trendWindow}
                  onChange={(_, value) => handleSettingChange('trendWindow', value as number)}
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
                  Time window for trend calculations and charts
                </Typography>
              </Box>

              <Box>
                <Typography gutterBottom fontWeight={500}>
                  Transparency: {Math.round(settings.transparency * 100)}%
                </Typography>
                <Slider
                  value={settings.transparency * 100}
                  onChange={(_, value) => handleSettingChange('transparency', (value as number) / 100)}
                  disabled={!settings.enabled}
                  min={10}
                  max={100}
                  step={10}
                  marks={[
                    { value: 30, label: '30%' },
                    { value: 60, label: '60%' },
                    { value: 90, label: '90%' },
                    { value: 100, label: '100%' }
                  ]}
                />
                <Typography variant="caption" color="text.secondary">
                  Overlay background transparency (lower = more see-through)
                </Typography>
              </Box>
            </Stack>
          </Box>

          <Divider />

          {/* Current Metrics Preview */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Current Metrics
            </Typography>
            
            <Stack direction="row" spacing={1} flexWrap="wrap" sx={{ gap: 1 }}>
              <Chip
                icon={<Speed />}
                label={`${metrics.responsesPerMinute}/min`}
                color="primary"
                variant="outlined"
              />
              <Chip
                label={`${(metrics.flaggedRate * 100).toFixed(1)}% flagged`}
                color={metrics.flaggedRate > 0.3 ? 'error' : 'success'}
                variant="outlined"
              />
              <Chip
                label={`${metrics.averageLatency.toFixed(0)}ms avg`}
                color={metrics.averageLatency > 2000 ? 'warning' : 'success'}
                variant="outlined"
              />
              <Chip
                label={`${metrics.activeAgents} agents`}
                color="info"
                variant="outlined"
              />
              <Chip
                label={`${metrics.systemHealth.toFixed(0)}% health`}
                color={metrics.systemHealth > 80 ? 'success' : metrics.systemHealth > 60 ? 'warning' : 'error'}
                variant="outlined"
              />
            </Stack>

            {metrics.totalResponses === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Start monitoring to see live statistics
              </Typography>
            )}
          </Box>

          <Divider />

          {/* Reset and Test */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Data Management
            </Typography>
            
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={handleReset}
                disabled={!settings.enabled || metrics.totalResponses === 0}
              >
                Reset Session Data
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<TrendingUp />}
                onClick={() => {
                  // Simulate some test data
                  for (let i = 0; i < 10; i++) {
                    setTimeout(() => {
                      realtimeStats.addResponse({
                        agentId: ['it_bot', 'retail_assistant', 'hr_helper'][i % 3],
                        riskScore: Math.random(),
                        latency: 500 + Math.random() * 1000,
                        flagged: Math.random() > 0.7
                      });
                    }, i * 100);
                  }
                }}
                disabled={!settings.enabled}
              >
                Generate Test Data
              </Button>
            </Stack>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
