'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Button,
  Chip,
  Stack,
  Collapse,
  Alert,
  AlertTitle,
  Tooltip,
  Badge,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  Close,
  CheckCircle,
  Warning,
  Error,
  Info,
  ExpandMore,
  ExpandLess,
  ClearAll,
  Schedule,
  Person,
  Computer
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { persistentAlerts, PersistentAlert, AlertSeverity } from '@/lib/persistentAlerts';

interface PersistentAlertsProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'center';
  maxWidth?: number;
  showOnAllPages?: boolean;
}

export default function PersistentAlerts({ 
  position = 'top-right', 
  maxWidth = 400,
  showOnAllPages = true 
}: PersistentAlertsProps) {
  const [alerts, setAlerts] = useState<PersistentAlert[]>([]);
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());
  const [isMinimized, setIsMinimized] = useState(false);

  useEffect(() => {
    const unsubscribe = persistentAlerts.subscribe(setAlerts);
    return unsubscribe;
  }, []);

  const getPositionStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 10000,
      maxWidth,
      maxHeight: '80vh',
      overflow: 'auto'
    };

    switch (position) {
      case 'top-right':
        return { ...baseStyles, top: 20, right: 20 };
      case 'top-left':
        return { ...baseStyles, top: 20, left: 20 };
      case 'bottom-right':
        return { ...baseStyles, bottom: 20, right: 20 };
      case 'bottom-left':
        return { ...baseStyles, bottom: 20, left: 20 };
      case 'center':
        return { 
          ...baseStyles, 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)',
          maxHeight: '60vh'
        };
      default:
        return { ...baseStyles, top: 20, right: 20 };
    }
  };

  const getSeverityIcon = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical': return <Error color="error" />;
      case 'high': return <Warning color="warning" />;
      case 'medium': return <Info color="info" />;
      case 'low': return <Info color="success" />;
    }
  };

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
    }
  };

  const formatTimeAgo = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const getEscalationProgress = (alert: PersistentAlert) => {
    if (!alert.autoEscalateAt || alert.acknowledged || alert.escalated) return null;
    
    const now = new Date();
    const created = alert.timestamp;
    const escalateAt = alert.autoEscalateAt;
    
    const totalTime = escalateAt.getTime() - created.getTime();
    const elapsed = now.getTime() - created.getTime();
    const progress = Math.min(100, (elapsed / totalTime) * 100);
    
    return {
      progress,
      timeLeft: Math.max(0, Math.ceil((escalateAt.getTime() - now.getTime()) / 60000))
    };
  };

  const handleAcknowledge = (alertId: string) => {
    persistentAlerts.acknowledgeAlert(alertId, 'user');
  };

  const handleDismiss = (alertId: string) => {
    persistentAlerts.dismissAlert(alertId);
  };

  const handleAcknowledgeAll = () => {
    persistentAlerts.acknowledgeAll('user');
  };

  const toggleExpanded = (alertId: string) => {
    const newExpanded = new Set(expandedAlerts);
    if (newExpanded.has(alertId)) {
      newExpanded.delete(alertId);
    } else {
      newExpanded.add(alertId);
    }
    setExpandedAlerts(newExpanded);
  };

  if (alerts.length === 0) {
    return null;
  }

  const criticalCount = alerts.filter(a => a.severity === 'critical').length;
  const hasEscalated = alerts.some(a => a.escalated);

  return (
    <Box sx={getPositionStyles()}>
      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Card
              sx={{
                background: criticalCount > 0 ? 
                  'linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%)' :
                  'background.paper',
                border: criticalCount > 0 ? '2px solid rgba(244, 67, 54, 0.3)' : '1px solid',
                borderColor: criticalCount > 0 ? 'error.main' : 'divider',
                boxShadow: criticalCount > 0 ? '0 8px 32px rgba(244, 67, 54, 0.2)' : 4,
                animation: criticalCount > 0 ? 'pulse 2s infinite' : 'none',
                '@keyframes pulse': {
                  '0%, 100%': { transform: 'scale(1)' },
                  '50%': { transform: 'scale(1.02)' }
                }
              }}
            >
              {/* Header */}
              <CardContent sx={{ pb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Badge badgeContent={alerts.length} color="error">
                      <Warning color={criticalCount > 0 ? 'error' : 'warning'} />
                    </Badge>
                    <Typography variant="h6" fontWeight={600}>
                      Active Alerts
                    </Typography>
                    {hasEscalated && (
                      <Chip 
                        label="ESCALATED" 
                        color="error" 
                        size="small" 
                        sx={{ fontWeight: 700 }}
                      />
                    )}
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Tooltip title="Acknowledge All">
                      <IconButton size="small" onClick={handleAcknowledgeAll}>
                        <CheckCircle />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Minimize">
                      <IconButton size="small" onClick={() => setIsMinimized(true)}>
                        <ExpandLess />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                {/* Quick Stats */}
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <Chip 
                    label={`${criticalCount} Critical`} 
                    color="error" 
                    size="small" 
                    variant={criticalCount > 0 ? 'filled' : 'outlined'}
                  />
                  <Chip 
                    label={`${alerts.filter(a => a.severity === 'high').length} High`} 
                    color="warning" 
                    size="small" 
                    variant="outlined"
                  />
                  <Chip 
                    label={`${alerts.length} Total`} 
                    color="info" 
                    size="small" 
                    variant="outlined"
                  />
                </Box>
              </CardContent>

              <Divider />

              {/* Alert List */}
              <Box sx={{ maxHeight: '60vh', overflow: 'auto' }}>
                <Stack spacing={1} sx={{ p: 2 }}>
                  <AnimatePresence>
                    {alerts.map((alert, index) => {
                      const isExpanded = expandedAlerts.has(alert.id);
                      const escalation = getEscalationProgress(alert);
                      
                      return (
                        <motion.div
                          key={alert.id}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -20 }}
                          transition={{ delay: index * 0.1 }}
                        >
                          <Alert
                            severity={getSeverityColor(alert.severity) as any}
                            sx={{
                              '& .MuiAlert-message': { width: '100%' },
                              animation: alert.severity === 'critical' ? 'blink 1s infinite' : 'none',
                              '@keyframes blink': {
                                '0%, 50%': { opacity: 1 },
                                '51%, 100%': { opacity: 0.7 }
                              }
                            }}
                            action={
                              <Box sx={{ display: 'flex', gap: 0.5 }}>
                                <Tooltip title={isExpanded ? 'Collapse' : 'Expand'}>
                                  <IconButton size="small" onClick={() => toggleExpanded(alert.id)}>
                                    {isExpanded ? <ExpandLess /> : <ExpandMore />}
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="Acknowledge">
                                  <IconButton size="small" onClick={() => handleAcknowledge(alert.id)}>
                                    <CheckCircle />
                                  </IconButton>
                                </Tooltip>
                                <Tooltip title="Dismiss">
                                  <IconButton size="small" onClick={() => handleDismiss(alert.id)}>
                                    <Close />
                                  </IconButton>
                                </Tooltip>
                              </Box>
                            }
                          >
                            <AlertTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {alert.title}
                              {alert.escalated && (
                                <Chip label="ESCALATED" color="error" size="small" />
                              )}
                            </AlertTitle>
                            
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              {alert.message}
                            </Typography>

                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <Chip 
                                icon={<Schedule />} 
                                label={formatTimeAgo(alert.timestamp)} 
                                size="small" 
                                variant="outlined"
                              />
                              {alert.agentId && (
                                <Chip 
                                  icon={<Computer />} 
                                  label={alert.agentId} 
                                  size="small" 
                                  variant="outlined"
                                />
                              )}
                              {alert.riskScore && (
                                <Chip 
                                  label={`${(alert.riskScore * 100).toFixed(1)}% Risk`} 
                                  size="small" 
                                  color={alert.riskScore > 0.7 ? 'error' : 'warning'}
                                  variant="outlined"
                                />
                              )}
                            </Box>

                            {/* Escalation Progress */}
                            {escalation && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="caption" color="warning.main">
                                  Auto-escalates in {escalation.timeLeft}m
                                </Typography>
                                <LinearProgress 
                                  variant="determinate" 
                                  value={escalation.progress} 
                                  color="warning"
                                  sx={{ mt: 0.5, height: 4, borderRadius: 2 }}
                                />
                              </Box>
                            )}

                            {/* Expanded Details */}
                            <Collapse in={isExpanded}>
                              <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
                                {alert.flaggedSegments && alert.flaggedSegments.length > 0 && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="caption" fontWeight={600} color="error">
                                      Flagged Content:
                                    </Typography>
                                    <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} flexWrap="wrap">
                                      {alert.flaggedSegments.map((segment, i) => (
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

                                {alert.mitigation && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="caption" fontWeight={600} color="primary">
                                      Suggested Mitigation:
                                    </Typography>
                                    <Typography variant="body2" sx={{ mt: 0.5, p: 1, bgcolor: 'primary.light', borderRadius: 1 }}>
                                      {alert.mitigation}
                                    </Typography>
                                  </Box>
                                )}

                                <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                                  <Button
                                    size="small"
                                    variant="contained"
                                    color="success"
                                    startIcon={<CheckCircle />}
                                    onClick={() => handleAcknowledge(alert.id)}
                                  >
                                    Acknowledge
                                  </Button>
                                  <Button
                                    size="small"
                                    variant="outlined"
                                    color="error"
                                    startIcon={<Close />}
                                    onClick={() => handleDismiss(alert.id)}
                                  >
                                    Dismiss
                                  </Button>
                                </Box>
                              </Box>
                            </Collapse>
                          </Alert>
                        </motion.div>
                      );
                    })}
                  </AnimatePresence>
                </Stack>
              </Box>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimized State */}
      {isMinimized && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          <Card
            sx={{
              cursor: 'pointer',
              background: criticalCount > 0 ? 'error.main' : 'warning.main',
              color: 'white',
              '&:hover': { transform: 'scale(1.05)' },
              transition: 'transform 0.2s',
              animation: criticalCount > 0 ? 'pulse 2s infinite' : 'none'
            }}
            onClick={() => setIsMinimized(false)}
          >
            <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Badge badgeContent={alerts.length} color="error">
                  <Warning />
                </Badge>
                <Typography variant="body2" fontWeight={600}>
                  {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
                </Typography>
                {criticalCount > 0 && (
                  <Chip 
                    label={`${criticalCount} CRITICAL`} 
                    size="small" 
                    sx={{ 
                      bgcolor: 'rgba(255,255,255,0.2)', 
                      color: 'white',
                      fontWeight: 700
                    }}
                  />
                )}
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </Box>
  );
}
