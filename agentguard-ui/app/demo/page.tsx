'use client';

import { Container, Box, Typography } from '@mui/material';
import DemoMode from '@/components/DemoMode';

export default function DemoPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
          Demo Mode
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Experience AgentGuard's capabilities with pre-configured enterprise scenarios
        </Typography>
      </Box>

      <DemoMode />
    </Container>
  );
}

