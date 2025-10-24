'use client';

import { Container, Typography, Box } from '@mui/material';
import AgentReliabilityDashboard from '@/components/AgentReliabilityDashboard';

export default function ReliabilityPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          Agent Reliability Center
        </Typography>
        <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
          Enterprise AI Safety Monitoring
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor safety scores, track performance trends, and manage deployment status 
          across your entire AI agent fleet with real-time reliability metrics.
        </Typography>
      </Box>

      <AgentReliabilityDashboard />
    </Container>
  );
}
