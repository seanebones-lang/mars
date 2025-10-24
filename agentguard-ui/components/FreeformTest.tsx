'use client';

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  Divider,
} from '@mui/material';
import { PlayArrow, Science } from '@mui/icons-material';
import { agentGuardApi } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function FreeformTest() {
  const [agentOutput, setAgentOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  const { addResult } = useStore();

  const handleTest = async () => {
    if (!agentOutput.trim()) {
      setError('Please enter some agent output to test');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    
    const startTime = Date.now();
    
    try {
      // Use Claude to judge without ground truth - it will use its own knowledge
      const response = await agentGuardApi.testAgent({
        agent_output: agentOutput,
        ground_truth: "Evaluate this statement for factual accuracy, fabrications, and hallucinations based on your knowledge. Flag any suspicious claims, made-up technology, incorrect facts, or unrealistic statements.",
        conversation_history: [],
      });
      
      const latency = (Date.now() - startTime) / 1000;
      const resultWithLatency = { ...response, latency_seconds: latency };
      
      addResult(resultWithLatency);
      setResult(resultWithLatency);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk > 0.7) return 'error';
    if (risk > 0.4) return 'warning';
    return 'success';
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Science sx={{ mr: 1, fontSize: 30, color: 'primary.main' }} />
        <Box>
          <Typography variant="h5">
            Free-form Hallucination Test
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Just paste what an agent said - we'll check it for hallucinations, fabrications, and suspicious claims
          </Typography>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TextField
        label="Agent Output to Test"
        multiline
        rows={6}
        fullWidth
        value={agentOutput}
        onChange={(e) => setAgentOutput(e.target.value)}
        placeholder="Paste what the AI agent said here... For example:
        
'To fix your server issue, simply reboot the quantum router using the admin panel. This will clear the flux capacitor cache and restore normal operations within 30 seconds.'"
        sx={{ mb: 3 }}
      />

      <Button
        variant="contained"
        size="large"
        startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
        onClick={handleTest}
        disabled={loading || !agentOutput.trim()}
        fullWidth
      >
        {loading ? 'Analyzing...' : 'Test for Hallucinations'}
      </Button>

      {result && (
        <Box sx={{ mt: 4 }}>
          <Divider sx={{ mb: 3 }} />
          
          <Typography variant="h6" gutterBottom>
            Analysis Results
          </Typography>

          <Stack spacing={3}>
            {/* Hallucination Risk Score */}
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Hallucination Risk
              </Typography>
              <Chip
                label={`${(result.hallucination_risk * 100).toFixed(1)}%`}
                color={getRiskColor(result.hallucination_risk)}
                sx={{ fontSize: '1.2rem', py: 2, px: 1 }}
              />
              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                {result.hallucination_risk > 0.7 ? 'High risk - Likely contains fabrications' :
                 result.hallucination_risk > 0.4 ? 'Medium risk - Some concerns detected' :
                 'Low risk - Appears factually sound'}
              </Typography>
            </Box>

            {/* Claude's Explanation */}
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                AI Judge Analysis
              </Typography>
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="body1">
                  {result.details.claude_explanation}
                </Typography>
              </Paper>
            </Box>

            {/* Flagged Segments */}
            {result.details.hallucinated_segments && result.details.hallucinated_segments.length > 0 && (
              <Box>
                <Typography variant="body2" color="error" gutterBottom>
                  Suspicious/Fabricated Content Detected:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {result.details.hallucinated_segments.map((segment: string, i: number) => (
                    <Chip
                      key={i}
                      label={segment}
                      color="error"
                      variant="outlined"
                      sx={{ mb: 1 }}
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {/* Uncertainty & Review Flag */}
            <Box>
              <Stack direction="row" spacing={2} alignItems="center">
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Uncertainty Level
                  </Typography>
                  <Typography variant="body1">
                    {(result.uncertainty * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Analysis Time
                  </Typography>
                  <Typography variant="body1">
                    {result.latency_seconds?.toFixed(2)}s
                  </Typography>
                </Box>
                {result.details.needs_review && (
                  <Chip
                    label="Human Review Recommended"
                    color="warning"
                    variant="outlined"
                  />
                )}
              </Stack>
            </Box>

            {/* Confidence Scores */}
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Detection Method Scores
              </Typography>
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Claude LLM Judge:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(result.details.claude_score * 100).toFixed(1)}% confidence
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">Statistical Analysis:</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(result.details.statistical_score * 100).toFixed(1)}% confidence
                  </Typography>
                </Box>
              </Stack>
            </Box>
          </Stack>

          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>Note:</strong> This analysis is based on Claude AI's knowledge and statistical patterns. 
              Always verify critical information independently.
            </Typography>
          </Alert>
        </Box>
      )}
    </Paper>
  );
}

