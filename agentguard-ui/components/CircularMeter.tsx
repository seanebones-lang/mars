'use client';

import React from 'react';
import { Box, Typography, useTheme } from '@mui/material';
import { motion } from 'framer-motion';

interface CircularMeterProps {
  value: number; // 0-100
  size?: number;
  thickness?: number;
  label?: string;
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info';
  animated?: boolean;
  showValue?: boolean;
  subtitle?: string;
}

export default function CircularMeter({
  value,
  size = 120,
  thickness = 8,
  label,
  color = 'primary',
  animated = true,
  showValue = true,
  subtitle
}: CircularMeterProps) {
  const theme = useTheme();
  
  // Clamp value between 0 and 100
  const clampedValue = Math.max(0, Math.min(100, value));
  
  // Calculate circle properties
  const radius = (size - thickness) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (clampedValue / 100) * circumference;
  
  // Get color based on theme and color prop
  const getColor = () => {
    switch (color) {
      case 'success': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'error': return theme.palette.error.main;
      case 'info': return theme.palette.info.main;
      default: return theme.palette.primary.main;
    }
  };
  
  // Get risk level color based on value
  const getRiskColor = () => {
    if (clampedValue >= 70) return theme.palette.error.main;
    if (clampedValue >= 40) return theme.palette.warning.main;
    return theme.palette.success.main;
  };
  
  const strokeColor = color === 'primary' ? getRiskColor() : getColor();
  
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1,
      }}
    >
      {label && (
        <Typography variant="body2" color="text.secondary" fontWeight={600} sx={{ minHeight: '20px', textAlign: 'center' }}>
          {label}
        </Typography>
      )}
      
      <Box sx={{ position: 'relative', display: 'inline-flex' }}>
        <svg width={size} height={size}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={theme.palette.divider}
            strokeWidth={thickness}
            fill="none"
            opacity={0.3}
          />
          
          {/* Progress circle */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={thickness}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={animated ? strokeDashoffset : circumference}
            initial={animated ? { strokeDashoffset: circumference } : {}}
            animate={animated ? { strokeDashoffset } : {}}
            transition={{ duration: 1.5, ease: "easeInOut" }}
            style={{
              transform: 'rotate(-90deg)',
              transformOrigin: '50% 50%',
            }}
          />
          
          {/* Glow effect for high risk */}
          {clampedValue >= 70 && (
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={strokeColor}
              strokeWidth={thickness + 2}
              fill="none"
              strokeLinecap="round"
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              opacity={0.3}
              animate={{
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              style={{
                transform: 'rotate(-90deg)',
                transformOrigin: '50% 50%',
                filter: 'blur(2px)',
              }}
            />
          )}
        </svg>
        
        {/* Center content */}
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {showValue && (
            <motion.div
              initial={animated ? { scale: 0 } : {}}
              animate={animated ? { scale: 1 } : {}}
              transition={{ delay: 0.5, duration: 0.5 }}
            >
              <Typography
                variant="h4"
                fontWeight={700}
                color={strokeColor}
                sx={{ lineHeight: 1 }}
              >
                {Math.round(clampedValue)}
              </Typography>
            </motion.div>
          )}
          
          {subtitle && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: '10px', textAlign: 'center' }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
}
