'use client';

import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Divider,
  Stack,
  Paper,
} from '@mui/material';
import { TestResult } from '@/lib/store';

interface ResultModalProps {
  open: boolean;
  result: TestResult;
  onClose: () => void;
}

export default function ResultModal({ open, result, onClose }: ResultModalProps) {
  const riskColor = result.hallucination_risk > 0.7 ? 'error' : 
                    result.hallucination_risk > 0.4 ? 'warning' : 'success';

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Test Result Details
        <Typography variant="caption" display="block" color="text.secondary">
          {new Date(result.timestamp).toLocaleString()}
        </Typography>
      </DialogTitle>
      
      <DialogContent dividers>
        {/* Summary Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Summary</Typography>
          <Stack spacing={2}>
            <Box>
              <Typography variant="body2" color="text.secondary">Hallucination Risk</Typography>
              <Chip
                label={`${(result.hallucination_risk * 100).toFixed(1)}%`}
                color={riskColor}
                sx={{ mt: 0.5 }}
              />
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">Uncertainty</Typography>
              <Typography variant="body1">{(result.uncertainty * 100).toFixed(1)}%</Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">Confidence Interval</Typography>
              <Typography variant="body1">
                [{result.confidence_interval[0].toFixed(3)}, {result.confidence_interval[1].toFixed(3)}]
              </Typography>
            </Box>
            
            <Box>
              <Typography variant="body2" color="text.secondary">Needs Human Review</Typography>
              <Chip
                label={result.details.needs_review ? 'Yes' : 'No'}
                color={result.details.needs_review ? 'warning' : 'default'}
                size="small"
                sx={{ mt: 0.5 }}
              />
            </Box>
            
            {result.latency_seconds && (
              <Box>
                <Typography variant="body2" color="text.secondary">Latency</Typography>
                <Typography variant="body1">{result.latency_seconds.toFixed(3)}s</Typography>
              </Box>
            )}
          </Stack>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        {/* Claude Judge Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Claude Judge Analysis</Typography>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Score: {(result.details.claude_score * 100).toFixed(1)}%
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {result.details.claude_explanation}
            </Typography>
            
            {result.details.hallucinated_segments.length > 0 && (
              <Box>
                <Typography variant="body2" color="error" gutterBottom>
                  Hallucinated Segments:
                </Typography>
                <Stack spacing={0.5}>
                  {result.details.hallucinated_segments.map((segment, i) => (
                    <Chip
                      key={i}
                      label={segment}
                      color="error"
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </Paper>
        </Box>
        
        <Divider sx={{ my: 2 }} />
        
        {/* Statistical Analysis Section */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>Statistical Analysis</Typography>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography variant="body2" color="text.secondary">
              Statistical Score: {(result.details.statistical_score * 100).toFixed(1)}%
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
              Token-level entropy and confidence analysis
            </Typography>
          </Paper>
        </Box>
        
        {/* Ensemble Weights */}
        {result.details.ensemble_weights && (
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Ensemble Weights
            </Typography>
            <Typography variant="caption">
              Claude: {(result.details.ensemble_weights.claude * 100).toFixed(0)}% | 
              Statistical: {(result.details.ensemble_weights.statistical * 100).toFixed(0)}%
            </Typography>
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

