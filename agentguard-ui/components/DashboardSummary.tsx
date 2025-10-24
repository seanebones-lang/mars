'use client';

import { useEffect } from 'react';
import { Paper, Typography, Box, Chip, Stack } from '@mui/material';
import {
  Assessment,
  Warning,
  CheckCircle,
  Speed,
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { useStore } from '@/lib/store';

export default function DashboardSummary() {
  const theme = useTheme();
  const { results, metrics, updateMetrics } = useStore();

  useEffect(() => {
    if (results.length === 0) return;

    const highRiskCount = results.filter(r => r.hallucination_risk > 0.7).length;
    const needsReviewCount = results.filter(r => r.details.needs_review).length;
    const avgLatency = results.reduce((sum, r) => sum + (r.latency_seconds || 0), 0) / results.length;
    
    // Calculate accuracy (inverse of average hallucination risk)
    const avgAccuracy = 1 - (results.reduce((sum, r) => sum + r.hallucination_risk, 0) / results.length);

    updateMetrics({
      total_tests: results.length,
      avg_accuracy: avgAccuracy,
      avg_latency: avgLatency,
      high_risk_count: highRiskCount,
      needs_review_count: needsReviewCount,
    });
  }, [results, updateMetrics]);

  const cards = [
    {
      title: 'Total Tests',
      value: metrics.total_tests,
      icon: <Assessment sx={{ fontSize: 40 }} />,
      color: theme.palette.primary.main,
    },
    {
      title: 'Average Accuracy',
      value: `${(metrics.avg_accuracy * 100).toFixed(1)}%`,
      subtitle: 'Target: 92%',
      icon: <CheckCircle sx={{ fontSize: 40 }} />,
      color: metrics.avg_accuracy >= 0.92 ? theme.palette.success.main : theme.palette.warning.main,
      status: metrics.avg_accuracy >= 0.92 ? 'success' : 'warning',
    },
    {
      title: 'Avg Latency',
      value: `${metrics.avg_latency.toFixed(3)}s`,
      subtitle: 'Target: <0.5s',
      icon: <Speed sx={{ fontSize: 40 }} />,
      color: metrics.avg_latency < 0.5 ? theme.palette.success.main : theme.palette.warning.main,
      status: metrics.avg_latency < 0.5 ? 'success' : 'warning',
    },
    {
      title: 'Needs Review',
      value: metrics.needs_review_count,
      subtitle: `${metrics.high_risk_count} high risk`,
      icon: <Warning sx={{ fontSize: 40 }} />,
      color: metrics.needs_review_count > 0 ? theme.palette.error.main : theme.palette.text.disabled,
      status: metrics.needs_review_count > 0 ? 'error' : 'default',
    },
  ];

  return (
    <Box sx={{ mb: 4, display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 3 }}>
      {cards.map((card, index) => (
        <Paper
          key={index}
          elevation={3}
          sx={{
            p: 2.5,
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <Box
            sx={{
              position: 'absolute',
              right: -10,
              top: -10,
              opacity: 0.1,
            }}
          >
            {card.icon}
          </Box>
          
          <Typography
            variant="body2"
            color="text.secondary"
            gutterBottom
            sx={{ fontWeight: 500 }}
          >
            {card.title}
          </Typography>
          
          <Typography variant="h4" sx={{ my: 1, fontWeight: 600, color: card.color }}>
            {card.value}
          </Typography>
          
          {card.subtitle && (
            <Box>
              {card.status ? (
                <Chip
                  label={card.subtitle}
                  size="small"
                  color={card.status as any}
                  variant="outlined"
                />
              ) : (
                <Typography variant="caption" color="text.secondary">
                  {card.subtitle}
                </Typography>
              )}
            </Box>
          )}
        </Paper>
      ))}
    </Box>
  );
}

