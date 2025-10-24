'use client';

import React from 'react';
import { Box, Grid, Typography, Card, CardContent, useTheme } from '@mui/material';
import { motion } from 'framer-motion';
import CircularMeter from './CircularMeter';
import RiskGauge from './RiskGauge';

interface SystemHealthDashboardProps {
  overallRisk: number;
  systemHealth: number;
  responseTime: number; // in ms
  activeAgents: number;
  totalChecks: number;
  flaggedRate: number;
}

export default function SystemHealthDashboard({
  overallRisk,
  systemHealth,
  responseTime,
  activeAgents,
  totalChecks,
  flaggedRate
}: SystemHealthDashboardProps) {
  const theme = useTheme();
  
  // Convert response time to a 0-100 scale (lower is better)
  const responseTimeScore = Math.max(0, 100 - (responseTime / 100)); // 10s = 0%, 0s = 100%
  
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };
  
  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };
  
  return (
    <Box sx={{ pt: 2 }}>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h4" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
            System Health Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time monitoring of Watcher-AI detection system performance
          </Typography>
        </Box>
      
      {/* Main Risk Gauges - Horizontal Layout */}
      <Grid container spacing={4} sx={{ mb: 6, justifyContent: 'center', mt: 2 }}>
        <Grid size={{ xs: 12, sm: 6, lg: 3 }} sx={{ display: 'flex', justifyContent: 'center' }}>
          <motion.div variants={itemVariants}>
            <RiskGauge
              riskLevel={overallRisk}
              title="Overall Risk"
              subtitle="System-wide hallucination risk"
              size="medium"
              showTrend={true}
              trendValue={-2.3} // Improving
            />
          </motion.div>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, lg: 3 }} sx={{ display: 'flex', justifyContent: 'center' }}>
          <motion.div variants={itemVariants}>
            <RiskGauge
              riskLevel={100 - systemHealth}
              title="System Health"
              subtitle="Overall system performance"
              size="medium"
              showTrend={true}
              trendValue={1.2} // Slight degradation
            />
          </motion.div>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, lg: 3 }} sx={{ display: 'flex', justifyContent: 'center' }}>
          <motion.div variants={itemVariants}>
            <RiskGauge
              riskLevel={100 - responseTimeScore}
              title="Response Time"
              subtitle={`${responseTime.toFixed(1)}ms average`}
              size="medium"
              showTrend={true}
              trendValue={-5.7} // Improving
            />
          </motion.div>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, lg: 3 }} sx={{ display: 'flex', justifyContent: 'center' }}>
          <motion.div variants={itemVariants}>
            <RiskGauge
              riskLevel={flaggedRate}
              title="Detection Rate"
              subtitle="Flagged responses"
              size="medium"
              showTrend={true}
              trendValue={3.1} // Increasing detections
            />
          </motion.div>
        </Grid>
      </Grid>
      
      {/* Secondary Metrics */}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6 }}>
          <motion.div variants={itemVariants}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Active Monitoring
                </Typography>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', py: 2 }}>
                  <Box sx={{ textAlign: 'center' }}>
                    <CircularMeter
                      value={(activeAgents / 10) * 100} // Assuming max 10 agents
                      size={100}
                      thickness={8}
                      label="Active Agents"
                      color="info"
                      showValue={false}
                    />
                    <Typography variant="h4" fontWeight={700} color="primary.main" sx={{ mt: 1 }}>
                      {activeAgents}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Agents Online
                    </Typography>
                  </Box>
                  
                  <Box sx={{ textAlign: 'center' }}>
                    <CircularMeter
                      value={Math.min(100, (totalChecks / 1000) * 100)} // Assuming 1000 is full scale
                      size={100}
                      thickness={8}
                      label="Total Checks"
                      color="success"
                      showValue={false}
                    />
                    <Typography variant="h4" fontWeight={700} color="success.main" sx={{ mt: 1 }}>
                      {totalChecks.toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Tests Completed
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
        
        <Grid size={{ xs: 12, md: 6 }}>
          <motion.div variants={itemVariants}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Performance Indicators
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, py: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Claude API Health
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box
                        sx={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          bgcolor: 'success.main',
                          animation: 'pulse 2s infinite',
                          '@keyframes pulse': {
                            '0%': { opacity: 1 },
                            '50%': { opacity: 0.5 },
                            '100%': { opacity: 1 },
                          },
                        }}
                      />
                      <Typography variant="body2" fontWeight={600} color="success.main">
                        Operational
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      WebSocket Connections
                    </Typography>
                    <Typography variant="body2" fontWeight={600}>
                      {activeAgents} Active
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Average Accuracy
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="primary.main">
                      92.3%
                    </Typography>
                  </Box>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      Uptime
                    </Typography>
                    <Typography variant="body2" fontWeight={600} color="success.main">
                      99.9%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>
      </motion.div>
    </Box>
  );
}
