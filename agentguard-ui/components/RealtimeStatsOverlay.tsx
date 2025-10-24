'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  IconButton,
  Tooltip,
  Collapse,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  Speed,
  TrendingUp,
  TrendingDown,
  TrendingFlat,
  Computer,
  NetworkCheck,
  Timer,
  Security,
  Visibility,
  VisibilityOff,
  Minimize,
  Maximize,
  Settings,
  DragIndicator
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { realtimeStats, SystemMetrics, StatsSettings } from '@/lib/realtimeStats';
import CircularMeter from './CircularMeter';

interface RealtimeStatsOverlayProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right' | 'floating';
  maxWidth?: number;
}

export default function RealtimeStatsOverlay({ 
  position = 'top-left', 
  maxWidth = 350 
}: RealtimeStatsOverlayProps) {
  const [metrics, setMetrics] = useState<SystemMetrics>(realtimeStats.getMetrics());
  const [settings, setSettings] = useState<StatsSettings>(realtimeStats.getSettings());
  const [isMinimized, setIsMinimized] = useState(true); // Start minimized
  const [isVisible, setIsVisible] = useState(true);
  const [showAgentDetails, setShowAgentDetails] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragPosition, setDragPosition] = useState({ x: 0, y: 0 });
  const dragRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const unsubscribe = realtimeStats.subscribe(setMetrics);
    return unsubscribe;
  }, []);

  // Drag functionality
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!dragRef.current) return;
    
    setIsDragging(true);
    const rect = dragRef.current.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    const handleMouseMove = (e: MouseEvent) => {
      setDragPosition({
        x: e.clientX - offsetX,
        y: e.clientY - offsetY
      });
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const getPositionStyles = () => {
    const baseStyles = {
      position: 'fixed' as const,
      zIndex: 9999,
      maxWidth: 280, // Much smaller
      pointerEvents: 'auto' as const,
      cursor: isDragging ? 'grabbing' : 'grab'
    };

    // If dragging, use drag position
    if (isDragging || (dragPosition.x !== 0 || dragPosition.y !== 0)) {
      return {
        ...baseStyles,
        left: dragPosition.x,
        top: dragPosition.y,
        transform: 'none'
      };
    }

    // Default positions
    switch (position) {
      case 'top-left':
        return { ...baseStyles, top: 80, left: 20 };
      case 'top-right':
        return { ...baseStyles, top: 80, right: 20 };
      case 'bottom-left':
        return { ...baseStyles, bottom: 20, left: 20 };
      case 'bottom-right':
        return { ...baseStyles, bottom: 20, right: 20 };
      case 'floating':
        return { 
          ...baseStyles, 
          top: '20%', 
          left: '50%', 
          transform: 'translateX(-50%)'
        };
      default:
        return { ...baseStyles, top: 80, left: 20 };
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
  };

  const formatNumber = (num: number, decimals = 1) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(decimals)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  const getTrendIcon = (trend: number) => {
    if (Math.abs(trend) < 0.1) return <TrendingFlat color="action" />;
    return trend > 0 ? <TrendingUp color="error" /> : <TrendingDown color="success" />;
  };

  const getHealthColor = (health: number) => {
    if (health >= 80) return 'success';
    if (health >= 60) return 'warning';
    return 'error';
  };

  const chartData = metrics.responseTrend.map((responses, index) => ({
    time: index,
    responses,
    risk: metrics.riskTrend[index] * 100,
    latency: metrics.latencyTrend[index]
  }));

  if (!settings.enabled || !isVisible) {
    return null;
  }

  return (
    <Box sx={getPositionStyles()}>
      <AnimatePresence>
        {!isMinimized && (
          <motion.div
            ref={dragRef}
            initial={{ opacity: 0, scale: 0.9, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <Card
              sx={{
                background: 'rgba(0, 0, 0, 0.8)',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
                color: 'white'
              }}
            >
              {/* Header */}
              <CardContent sx={{ p: 1.5, pb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <DragIndicator 
                      sx={{ fontSize: 14, color: 'rgba(255,255,255,0.5)', cursor: 'grab' }}
                      onMouseDown={handleMouseDown}
                    />
                    <Speed sx={{ fontSize: 16, color: '#42A5F5' }} />
                    <Typography variant="body2" fontWeight={600} sx={{ color: 'white' }}>
                      Live Stats
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Tooltip title="Hide">
                      <IconButton size="small" onClick={() => setIsVisible(false)} sx={{ color: 'white' }}>
                        <VisibilityOff sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Minimize">
                      <IconButton size="small" onClick={() => setIsMinimized(true)} sx={{ color: 'white' }}>
                        <Minimize sx={{ fontSize: 16 }} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>

                {/* Compact Metrics */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} sx={{ color: '#42A5F5', lineHeight: 1 }}>
                      {metrics.responsesPerMinute}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '10px' }}>
                      /min
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} sx={{ 
                      color: metrics.flaggedRate > 0.3 ? '#f44336' : '#4caf50',
                      lineHeight: 1 
                    }}>
                      {(metrics.flaggedRate * 100).toFixed(0)}%
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '10px' }}>
                      flagged
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} sx={{ 
                      color: metrics.averageLatency > 2000 ? '#ff9800' : '#4caf50',
                      lineHeight: 1 
                    }}>
                      {metrics.averageLatency.toFixed(0)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '10px' }}>
                      ms
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="h6" fontWeight={700} sx={{ 
                      color: metrics.systemHealth > 80 ? '#4caf50' : metrics.systemHealth > 60 ? '#ff9800' : '#f44336',
                      lineHeight: 1 
                    }}>
                      {metrics.systemHealth.toFixed(0)}
                    </Typography>
                    <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '10px' }}>
                      health
                    </Typography>
                  </Box>
                </Box>

                {/* Session Info */}
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '10px' }}>
                    Session: {formatDuration(metrics.sessionDuration)} • {metrics.totalResponses} total
                  </Typography>
                </Box>
              </CardContent>

              {/* Agent Details */}
              {settings.showAgentBreakdown && (
                <Collapse in={showAgentDetails}>
                  <Divider />
                  <CardContent sx={{ pt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom fontWeight={600}>
                      Agent Performance
                    </Typography>
                    <Stack spacing={1}>
                      {Object.values(metrics.agentStats).map((agent) => (
                        <Box
                          key={agent.agentId}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            p: 1,
                            borderRadius: 1,
                            bgcolor: agent.isActive ? 'rgba(76, 175, 80, 0.1)' : 'rgba(158, 158, 158, 0.1)'
                          }}
                        >
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Computer 
                              fontSize="small" 
                              color={agent.isActive ? 'success' : 'disabled'} 
                            />
                            <Typography variant="body2" fontWeight={500}>
                              {agent.agentId.replace('_', ' ').toUpperCase()}
                            </Typography>
                            {getTrendIcon(agent.trend === 'improving' ? -1 : agent.trend === 'degrading' ? 1 : 0)}
                          </Box>
                          
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip
                              label={`${agent.responsesPerMinute}/min`}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={`${(agent.flaggedRate * 100).toFixed(0)}%`}
                              size="small"
                              color={agent.flaggedRate > 0.3 ? 'error' : 'success'}
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Stack>
                  </CardContent>
                </Collapse>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimized State */}
      {isMinimized && (
        <motion.div
          ref={dragRef}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
        >
          <Card
            sx={{
              cursor: 'pointer',
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              '&:hover': { transform: 'scale(1.05)' },
              transition: 'transform 0.2s',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}
            onClick={() => setIsMinimized(false)}
          >
            <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <DragIndicator 
                  sx={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', cursor: 'grab' }}
                  onMouseDown={handleMouseDown}
                />
                <Speed sx={{ fontSize: 14, color: '#42A5F5' }} />
                <Typography variant="caption" fontWeight={600} sx={{ color: 'white' }}>
                  {metrics.responsesPerMinute}/min
                </Typography>
                <Typography variant="caption" sx={{ 
                  color: metrics.flaggedRate > 0.3 ? '#f44336' : '#4caf50'
                }}>
                  {(metrics.flaggedRate * 100).toFixed(0)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Show/Hide Toggle (when hidden) */}
      {!isVisible && (
        <Box
          sx={{
            position: 'fixed',
            top: position.includes('top') ? 80 : 'auto',
            bottom: position.includes('bottom') ? 20 : 'auto',
            left: position.includes('left') ? 20 : 'auto',
            right: position.includes('right') ? 20 : 'auto',
            zIndex: 9998
          }}
        >
          <Tooltip title="Show Stats">
            <IconButton
              onClick={() => setIsVisible(true)}
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                boxShadow: 2
              }}
            >
              <Visibility />
            </IconButton>
          </Tooltip>
        </Box>
      )}
    </Box>
  );
}
