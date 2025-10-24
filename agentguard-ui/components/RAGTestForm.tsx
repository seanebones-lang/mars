'use client';

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  TextField,
  Button,
  Box,
  Typography,
  Alert,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  FormControlLabel,
  Switch,
  Grid,
  Paper
} from '@mui/material';
import {
  ExpandMore,
  Psychology,
  TrendingUp,
  Lightbulb,
  FindInPage,
  Security,
  Speed,
  CheckCircle,
  Warning,
  Error
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { testAgentWithRAG, findSimilarResponses, RAGTestResponse, SimilarResponse } from '@/lib/analyticsApi';

interface RAGTestFormProps {
  onResult?: (result: RAGTestResponse) => void;
}

export default function RAGTestForm({ onResult }: RAGTestFormProps) {
  const [agentOutput, setAgentOutput] = useState('');
  const [groundTruth, setGroundTruth] = useState('');
  const [agentId, setAgentId] = useState('test-agent');
  const [agentName, setAgentName] = useState('Test Agent');
  const [useRAG, setUseRAG] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RAGTestResponse | null>(null);
  const [similarResponses, setSimilarResponses] = useState<SimilarResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agentOutput.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setSimilarResponses([]);

    try {
      // Test with RAG enhancement
      const testResult = await testAgentWithRAG(
        {
          agent_output: agentOutput,
          ground_truth: groundTruth || undefined,
          conversation_history: []
        },
        agentId,
        agentName,
        useRAG
      );

      setResult(testResult);
      onResult?.(testResult);

      // If RAG is enabled, also find similar responses
      if (useRAG && groundTruth) {
        try {
          const similar = await findSimilarResponses(
            groundTruth,
            agentOutput,
            5,
            0.6
          );
          setSimilarResponses(similar);
        } catch (err) {
          console.warn('Failed to find similar responses:', err);
        }
      }

    } catch (err) {
      console.error('RAG test failed:', err);
      setError('Failed to analyze response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk >= 0.7) return 'error';
    if (risk >= 0.4) return 'warning';
    return 'success';
  };

  const getRiskIcon = (risk: number) => {
    if (risk >= 0.7) return <Error color="error" />;
    if (risk >= 0.4) return <Warning color="warning" />;
    return <CheckCircle color="success" />;
  };

  const formatRisk = (risk: number) => (risk * 100).toFixed(1) + '%';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" mb={3}>
            <Psychology color="primary" sx={{ mr: 2, fontSize: 32 }} />
            <Box>
              <Typography variant="h5" component="h2">
                🧠 RAG-Enhanced Detection
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Test agent outputs with graph database context and pattern matching
              </Typography>
            </Box>
          </Box>

          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Agent Output to Test"
                  value={agentOutput}
                  onChange={(e) => setAgentOutput(e.target.value)}
                  placeholder="Paste the AI agent's response here..."
                  required
                />
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Ground Truth / Context (Optional)"
                  value={groundTruth}
                  onChange={(e) => setGroundTruth(e.target.value)}
                  placeholder="Provide context or expected correct information..."
                />
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  fullWidth
                  label="Agent ID"
                  value={agentId}
                  onChange={(e) => setAgentId(e.target.value)}
                  placeholder="e.g., customer-service-bot"
                />
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  fullWidth
                  label="Agent Name"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  placeholder="e.g., Customer Service Bot"
                />
              </Grid>

              <Grid size={{ xs: 12, md: 4 }}>
                <Box display="flex" alignItems="center" height="100%">
                  <FormControlLabel
                    control={
                      <Switch
                        checked={useRAG}
                        onChange={(e) => setUseRAG(e.target.checked)}
                        color="primary"
                      />
                    }
                    label="Enable RAG Enhancement"
                  />
                </Box>
              </Grid>
            </Grid>

            <Box mt={3}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                disabled={loading || !agentOutput.trim()}
                startIcon={loading ? <CircularProgress size={20} /> : <Security />}
                sx={{ minWidth: 200 }}
              >
                {loading ? 'Analyzing...' : 'Analyze Response'}
              </Button>
            </Box>
          </form>

          {error && (
            <Alert severity="error" sx={{ mt: 3 }}>
              {error}
            </Alert>
          )}

          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Paper elevation={2} sx={{ mt: 4, p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Analysis Results
                </Typography>

                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Box display="flex" alignItems="center" mb={2}>
                      {getRiskIcon(result.hallucination_risk)}
                      <Typography variant="h4" sx={{ ml: 1 }} color={getRiskColor(result.hallucination_risk)}>
                        {formatRisk(result.hallucination_risk)}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Hallucination Risk
                    </Typography>
                  </Grid>

                  <Grid size={{ xs: 12, md: 4 }}>
                    <Box display="flex" alignItems="center" mb={2}>
                      <TrendingUp color="info" />
                      <Typography variant="h4" sx={{ ml: 1 }} color="info">
                        {formatRisk(1 - result.uncertainty)}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Confidence Level
                    </Typography>
                  </Grid>

                  <Grid size={{ xs: 12, md: 4 }}>
                    <Box display="flex" alignItems="center" mb={2}>
                      <Speed color="primary" />
                      <Typography variant="h4" sx={{ ml: 1 }} color="primary">
                        {result.details.rag_similar_cases_count || 0}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      Similar Cases Found
                    </Typography>
                  </Grid>
                </Grid>

                {result.needs_review && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    This response requires human review due to high uncertainty or risk.
                  </Alert>
                )}

                {/* RAG Insights */}
                {useRAG && (result.details.rag_pattern_matches || result.details.rag_contextual_explanation) && (
                  <Accordion sx={{ mt: 3 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box display="flex" alignItems="center">
                        <Lightbulb color="primary" sx={{ mr: 1 }} />
                        <Typography variant="h6">RAG Insights</Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      {result.details.rag_contextual_explanation && (
                        <Alert severity="info" sx={{ mb: 2 }}>
                          {result.details.rag_contextual_explanation}
                        </Alert>
                      )}

                      {result.details.rag_pattern_matches && result.details.rag_pattern_matches.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Known Pattern Matches:
                          </Typography>
                          <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                            {result.details.rag_pattern_matches.map((pattern, index) => (
                              <Chip
                                key={index}
                                label={`${pattern.pattern} (${pattern.frequency}x)`}
                                color={
                                  pattern.severity === 'high' ? 'error' :
                                  pattern.severity === 'medium' ? 'warning' : 'info'
                                }
                                size="small"
                              />
                            ))}
                          </Box>
                        </Box>
                      )}

                      {result.details.rag_suggested_corrections && result.details.rag_suggested_corrections.length > 0 && (
                        <Box>
                          <Typography variant="subtitle2" gutterBottom>
                            Suggested Corrections:
                          </Typography>
                          <List dense>
                            {result.details.rag_suggested_corrections.map((correction, index) => (
                              <ListItem key={index}>
                                <ListItemIcon>
                                  <CheckCircle color="success" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText primary={correction} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Similar Responses */}
                {similarResponses.length > 0 && (
                  <Accordion sx={{ mt: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Box display="flex" alignItems="center">
                        <FindInPage color="secondary" sx={{ mr: 1 }} />
                        <Typography variant="h6">Similar Historical Cases ({similarResponses.length})</Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {similarResponses.map((response, index) => (
                          <React.Fragment key={response.id}>
                            <ListItem alignItems="flex-start">
                              <ListItemText
                                primary={
                                  <Box display="flex" alignItems="center" gap={1}>
                                    <Typography variant="subtitle2">
                                      Similarity: {(response.similarity * 100).toFixed(1)}%
                                    </Typography>
                                    <Chip
                                      label={`Risk: ${formatRisk(response.hallucination_risk)}`}
                                      color={getRiskColor(response.hallucination_risk)}
                                      size="small"
                                    />
                                  </Box>
                                }
                                secondary={
                                  <Box>
                                    <Typography variant="body2" sx={{ mt: 1 }}>
                                      {response.text.length > 200 
                                        ? response.text.substring(0, 200) + '...'
                                        : response.text
                                      }
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      {new Date(response.timestamp).toLocaleDateString()}
                                    </Typography>
                                  </Box>
                                }
                              />
                            </ListItem>
                            {index < similarResponses.length - 1 && <Divider />}
                          </React.Fragment>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Technical Details */}
                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Typography variant="h6">Technical Details</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="subtitle2">Claude Explanation:</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {result.details.claude_explanation || 'No explanation provided'}
                        </Typography>
                      </Grid>
                      <Grid size={{ xs: 12, sm: 6 }}>
                        <Typography variant="subtitle2">Statistical Score:</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {result.details.statistical_score?.toFixed(3) || 'N/A'}
                        </Typography>
                      </Grid>
                      {result.details.rag_confidence_adjustment && (
                        <Grid size={12}>
                          <Typography variant="subtitle2">RAG Confidence Adjustment:</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {result.details.rag_confidence_adjustment > 0 ? '+' : ''}
                            {(result.details.rag_confidence_adjustment * 100).toFixed(1)}%
                          </Typography>
                        </Grid>
                      )}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Paper>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
