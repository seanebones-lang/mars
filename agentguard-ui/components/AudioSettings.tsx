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
  IconButton,
  Tooltip,
  Alert
} from '@mui/material';
import {
  VolumeUp,
  VolumeOff,
  PlayArrow,
  Settings as SettingsIcon,
  Tune
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { audioAlerts, AudioSettings as AudioSettingsType, AlertLevel } from '@/lib/audioAlerts';

interface AudioSettingsProps {
  compact?: boolean;
}

export default function AudioSettings({ compact = false }: AudioSettingsProps) {
  const [settings, setSettings] = useState<AudioSettingsType>(audioAlerts.getSettings());
  const [isPlaying, setIsPlaying] = useState<AlertLevel | null>(null);
  const [audioPermission, setAudioPermission] = useState<'granted' | 'denied' | 'prompt'>('prompt');
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    // Mark as hydrated and load client-side settings
    setIsHydrated(true);
    
    // Check audio permission status
    if (typeof navigator !== 'undefined' && 'permissions' in navigator) {
      navigator.permissions.query({ name: 'microphone' as PermissionName }).then(result => {
        setAudioPermission(result.state as any);
      }).catch(() => {
        setAudioPermission('prompt');
      });
    }

    // Load settings from localStorage (client-side only)
    const savedSettings = audioAlerts.getSettings();
    setSettings(savedSettings);
  }, []);

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
    // Reload settings after hydration
    const savedSettings = audioAlerts.getSettings();
    setSettings(savedSettings);
  }, []);

  const handleSettingChange = (key: keyof AudioSettingsType, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    audioAlerts.updateSettings({ [key]: value });
  };

  const handleThresholdChange = (level: keyof AudioSettingsType['riskThresholds'], value: number) => {
    const newThresholds = { ...settings.riskThresholds, [level]: value };
    const newSettings = { ...settings, riskThresholds: newThresholds };
    setSettings(newSettings);
    audioAlerts.updateSettings({ riskThresholds: newThresholds });
  };

  const testAlert = async (level: AlertLevel) => {
    if (isPlaying) return;
    
    setIsPlaying(level);
    try {
      await audioAlerts.enableAudio(); // Ensure audio is enabled
      await audioAlerts.testAlert(level);
    } catch (error) {
      console.error('Failed to play test alert:', error);
    } finally {
      setTimeout(() => setIsPlaying(null), 2000);
    }
  };

  const enableAudio = async () => {
    try {
      await audioAlerts.enableAudio();
      handleSettingChange('enabled', true);
      setAudioPermission('granted');
    } catch (error) {
      console.error('Failed to enable audio:', error);
      setAudioPermission('denied');
    }
  };

  if (compact) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Tooltip title={settings.enabled ? 'Audio alerts enabled' : 'Audio alerts disabled'}>
          <IconButton
            onClick={() => handleSettingChange('enabled', !settings.enabled)}
            color={settings.enabled ? 'primary' : 'default'}
          >
            {settings.enabled ? <VolumeUp /> : <VolumeOff />}
          </IconButton>
        </Tooltip>
        
        <Box sx={{ width: 100 }}>
          <Slider
            value={settings.volume * 100}
            onChange={(_, value) => handleSettingChange('volume', (value as number) / 100)}
            size="small"
            disabled={!settings.enabled}
          />
        </Box>
        
        <Tooltip title="Test alert">
          <IconButton
            onClick={() => testAlert('medium')}
            disabled={!settings.enabled || isPlaying !== null}
            size="small"
          >
            <PlayArrow />
          </IconButton>
        </Tooltip>
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <SettingsIcon color="primary" />
          <Typography variant="h6" fontWeight={600}>
            Audio Alert Settings
          </Typography>
        </Box>

        {!settings.enabled && audioPermission !== 'granted' && (
          <Alert severity="info" sx={{ mb: 3 }} action={
            <Button color="inherit" size="small" onClick={enableAudio}>
              Enable Audio
            </Button>
          }>
            Audio alerts are disabled. Click "Enable Audio" to activate sound notifications.
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
              label="Enable Audio Alerts"
            />
            <Typography variant="caption" color="text.secondary" display="block">
              Play sounds when hallucinations are detected
            </Typography>
          </Box>

          <Divider />

          {/* Volume Control */}
          <Box>
            <Typography gutterBottom fontWeight={500}>
              Volume: {isHydrated ? Math.round(settings.volume * 100) : 30}%
            </Typography>
            <Slider
              value={isHydrated ? settings.volume * 100 : 30}
              onChange={(_, value) => handleSettingChange('volume', (value as number) / 100)}
              disabled={!settings.enabled}
              marks={[
                { value: 0, label: '0%' },
                { value: 25, label: '25%' },
                { value: 50, label: '50%' },
                { value: 75, label: '75%' },
                { value: 100, label: '100%' }
              ]}
            />
          </Box>

          {/* Sound Profile */}
          <Box>
            <FormControl fullWidth disabled={!settings.enabled}>
              <InputLabel>Sound Profile</InputLabel>
              <Select
                value={settings.soundProfile}
                label="Sound Profile"
                onChange={(e) => handleSettingChange('soundProfile', e.target.value)}
              >
                <MenuItem value="professional">Professional - Balanced tones for office environments</MenuItem>
                <MenuItem value="subtle">Subtle - Quiet, non-intrusive alerts</MenuItem>
                <MenuItem value="urgent">Urgent - High-intensity alerts for critical environments</MenuItem>
              </Select>
            </FormControl>
          </Box>

          {/* Alert Cooldown */}
          <Box>
            <Typography gutterBottom fontWeight={500}>
              Alert Cooldown: {settings.alertCooldown}s
            </Typography>
            <Slider
              value={settings.alertCooldown}
              onChange={(_, value) => handleSettingChange('alertCooldown', value as number)}
              disabled={!settings.enabled}
              min={1}
              max={10}
              step={0.5}
              marks={[
                { value: 1, label: '1s' },
                { value: 5, label: '5s' },
                { value: 10, label: '10s' }
              ]}
            />
            <Typography variant="caption" color="text.secondary">
              Minimum time between similar alerts to prevent spam
            </Typography>
          </Box>

          <Divider />

          {/* Risk Thresholds */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Risk Level Thresholds
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
              Configure when different alert levels trigger
            </Typography>

            <Stack spacing={2}>
              {Object.entries(settings.riskThresholds).map(([level, threshold]) => (
                <Box key={level}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                    <Chip
                      label={level.toUpperCase()}
                      size="small"
                      color={
                        level === 'critical' ? 'error' :
                        level === 'high' ? 'warning' :
                        level === 'medium' ? 'info' : 'success'
                      }
                      sx={{ minWidth: 80 }}
                    />
                    <Typography variant="body2" sx={{ minWidth: 60 }}>
                      {Math.round(threshold * 100)}%+
                    </Typography>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={isPlaying === level ? <VolumeUp /> : <PlayArrow />}
                      onClick={() => testAlert(level as AlertLevel)}
                      disabled={!settings.enabled || isPlaying !== null}
                      sx={{ minWidth: 100 }}
                    >
                      {isPlaying === level ? 'Playing...' : 'Test'}
                    </Button>
                  </Box>
                  <Slider
                    value={threshold * 100}
                    onChange={(_, value) => handleThresholdChange(level as keyof AudioSettingsType['riskThresholds'], (value as number) / 100)}
                    disabled={!settings.enabled}
                    min={0}
                    max={100}
                    step={5}
                    size="small"
                  />
                </Box>
              ))}
            </Stack>
          </Box>

          <Divider />

          {/* Test All Alerts */}
          <Box>
            <Typography variant="h6" gutterBottom fontWeight={500}>
              Test Audio System
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {(['low', 'medium', 'high', 'critical'] as AlertLevel[]).map((level) => (
                <motion.div
                  key={level}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    variant={isPlaying === level ? 'contained' : 'outlined'}
                    color={
                      level === 'critical' ? 'error' :
                      level === 'high' ? 'warning' :
                      level === 'medium' ? 'info' : 'success'
                    }
                    startIcon={isPlaying === level ? <VolumeUp /> : <PlayArrow />}
                    onClick={() => testAlert(level)}
                    disabled={!settings.enabled || isPlaying !== null}
                  >
                    {isPlaying === level ? 'Playing...' : level.toUpperCase()}
                  </Button>
                </motion.div>
              ))}
            </Box>
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
