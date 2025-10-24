'use client';

import { Container, Typography, Box } from '@mui/material';
import BatchAgentTesting from '@/components/BatchAgentTesting';

export default function BatchTestingPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          Batch Agent Testing
        </Typography>
        <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
          Bulk AI Agent Validation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Test multiple AI agent outputs simultaneously for comprehensive safety validation. 
          Upload text responses in bulk and get detailed risk assessments for each one.
        </Typography>
      </Box>

      <BatchAgentTesting />
    </Container>
  );
}
