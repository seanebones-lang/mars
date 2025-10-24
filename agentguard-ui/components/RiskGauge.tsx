'use client';

import React from 'react';
import { Box, Typography, useTheme, Card, CardContent } from '@mui/material';
import { motion } from 'framer-motion';
import CircularMeter from './CircularMeter';

interface RiskGaugeProps {
  riskLevel: number; // 0-100
  title: string;
  subtitle?: string;
  size?: 'small' | 'medium' | 'large';
  showTrend?: boolean;
  trendValue?: number; // -100 to 100 (negative = improving, positive = worsening)
}

export default function RiskGauge({
  riskLevel,
  title,
  subtitle,
  size = 'medium',
  showTrend = false,
  trendValue = 0
}: RiskGaugeProps) {
  const theme = useTheme();
  
  const sizeConfig = {
    small: { meter: 80, card: 160 },
    medium: { meter: 120, card: 220 },
    large: { meter: 160, card: 280 }
  };
  
  const config = sizeConfig[size];
  
  const getRiskStatus = () => {
    if (riskLevel >= 70) return { label: 'HIGH RISK', color: 'error' as const };
    if (riskLevel >= 40) return { label: 'MEDIUM RISK', color: 'warning' as const };
    return { label: 'LOW RISK', color: 'success' as const };
  };
  
  const getTrendIcon = () => {
    if (trendValue > 5) return '↗️'; // Worsening
    if (trendValue < -5) return '↘️'; // Improving
    return '→'; // Stable
  };
  
  const getTrendColor = () => {
    if (trendValue > 5) return theme.palette.error.main;
    if (trendValue < -5) return theme.palette.success.main;
    return theme.palette.text.secondary;
  };
  
  const status = getRiskStatus();
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card
        sx={{
          width: config.card,
          height: config.card + 40,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          background: riskLevel >= 70 
            ? `linear-gradient(135deg, ${theme.palette.error.main}08 0%, ${theme.palette.error.main}04 100%)`
            : 'background.paper',
          border: riskLevel >= 70 
            ? `2px solid ${theme.palette.error.main}40`
            : `1px solid ${theme.palette.divider}`,
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: theme.shadows[8],
          },
          transition: 'all 0.3s ease-in-out',
        }}
      >
        <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1, p: 3, pt: 3 }}>
          <Typography variant="h6" fontWeight={600} textAlign="center" sx={{ mb: 2, minHeight: '24px' }}>
            {title}
          </Typography>
          
          <CircularMeter
            value={riskLevel}
            size={config.meter}
            thickness={size === 'large' ? 12 : size === 'medium' ? 10 : 8}
            animated={true}
            showValue={true}
            subtitle="%"
          />
          
          <Box sx={{ textAlign: 'center', mt: 1 }}>
            <Typography
              variant="body2"
              fontWeight={700}
              color={status.color}
              sx={{ mb: 0.5 }}
            >
              {status.label}
            </Typography>
            
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
            
            {showTrend && (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5, mt: 0.5 }}>
                <Typography
                  variant="caption"
                  sx={{ color: getTrendColor(), fontWeight: 600 }}
                >
                  {getTrendIcon()} {Math.abs(trendValue).toFixed(1)}%
                </Typography>
              </Box>
            )}
          </Box>
        </CardContent>
        
        {/* Pulse animation for high risk */}
        {riskLevel >= 70 && (
          <motion.div
            style={{
              position: 'absolute',
              top: -2,
              left: -2,
              right: -2,
              bottom: -2,
              borderRadius: 'inherit',
              border: `2px solid ${theme.palette.error.main}`,
              pointerEvents: 'none',
            }}
            animate={{
              opacity: [0.5, 1, 0.5],
              scale: [1, 1.02, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
        )}
      </Card>
    </motion.div>
  );
}
