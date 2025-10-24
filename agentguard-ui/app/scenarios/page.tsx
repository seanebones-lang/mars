'use client';

import { Container, Typography, Box } from '@mui/material';
import ScenarioBasedTesting from '@/components/ScenarioBasedTesting';

export default function ScenariosPage() {
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          Industry Testing Scenarios
        </Typography>
        <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
          Real-World AI Agent Validation
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Test AI agents with realistic scenarios from different industries. See how our hallucination detection 
          catches dangerous fabrications that could harm your business.
        </Typography>
      </Box>

      <ScenarioBasedTesting />
    </Container>
  );
}
