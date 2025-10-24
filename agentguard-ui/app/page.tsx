'use client';

import { Container, Box, Typography } from '@mui/material';
import DashboardSummary from '@/components/DashboardSummary';
import TestAgentForm from '@/components/TestAgentForm';
import ResultsTable from '@/components/ResultsTable';

export default function Home() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          Watcher-AI Dashboard
        </Typography>
        <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
          Real-Time Hallucination Defense
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Enterprise-grade monitoring that catches AI hallucinations before they impact your business
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
