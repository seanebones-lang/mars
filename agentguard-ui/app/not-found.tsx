'use client';

import { Container, Typography, Button, Box } from '@mui/material';
import Link from 'next/link';

export default function NotFound() {
  return (
    <Container sx={{ py: 8, textAlign: 'center' }}>
      <Typography variant="h2" gutterBottom>
        404
      </Typography>
      <Typography variant="h5" color="text.secondary" gutterBottom>
        Page Not Found
      </Typography>
      <Box sx={{ mt: 4 }}>
        <Link href="/" passHref>
          <Button variant="contained">
            Return to Dashboard
          </Button>
        </Link>
      </Box>
    </Container>
  );
}

