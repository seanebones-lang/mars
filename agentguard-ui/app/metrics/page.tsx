'use client';

import { Container, Box, Typography } from '@mui/material';
import MetricsCharts from '@/components/MetricsCharts';

export default function MetricsPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
          Metrics & Analytics
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Track hallucination detection accuracy, latency, and performance trends
        </Typography>
      </Box>

      <MetricsCharts />
    </Container>
  );
}

