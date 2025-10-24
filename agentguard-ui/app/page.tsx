'use client';

import { Container, Box, Typography } from '@mui/material';
import DashboardSummary from '@/components/DashboardSummary';
import TestAgentForm from '@/components/TestAgentForm';
import ResultsTable from '@/components/ResultsTable';

export default function Home() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
          AgentGuard Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          AI Agent Hallucination Detection Platform - Enterprise-Grade Reliability Testing
        </Typography>
      </Box>

      <DashboardSummary />
      
      <Box sx={{ mb: 4 }}>
        <TestAgentForm />
      </Box>

      <ResultsTable />
    </Container>
  );
}
