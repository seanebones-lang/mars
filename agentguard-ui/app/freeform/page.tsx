'use client';

import { Container, Box, Typography } from '@mui/material';
import FreeformTest from '@/components/FreeformTest';

export default function FreeformPage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
          Quick Hallucination Check
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Paste any AI agent response and we'll analyze it for hallucinations, fabrications, and suspicious claims
        </Typography>
      </Box>

      <FreeformTest />
    </Container>
  );
}

