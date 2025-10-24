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
  Card,
  CardContent,
  CardHeader,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import { 
  PlayArrow, 
  Science, 
  AutoAwesome, 
  Lightbulb, 
  TrendingUp, 
  Warning, 
  CheckCircle, 
  Psychology,
  ExpandMore,
  Refresh,
  ContentCopy,
  Share
} from '@mui/icons-material';
import { agentGuardApi } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function FreeformTest() {
  const [agentOutput, setAgentOutput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [claudeInsights, setClaudeInsights] = useState<any>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showAdvancedAnalysis, setShowAdvancedAnalysis] = useState(false);
  
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
      
      // Get Claude-powered insights after successful analysis
      await getClaudeInsights(resultWithLatency);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const getClaudeInsights = async (testResult: any) => {
    if (!testResult || !agentOutput.trim()) return;
    
    setInsightsLoading(true);
    try {
      const insights = await agentGuardApi.getAnalysisInsights(agentOutput, testResult);
      setClaudeInsights(insights);
      setShowAdvancedAnalysis(true);
    } catch (err) {
      console.error('Failed to get Claude insights:', err);
      // Don't show error for insights - it's supplementary
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleRefreshInsights = async () => {
    if (result) {
      await getClaudeInsights(result);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getRiskColor = (risk: number) => {
    if (risk > 0.7) return 'error';
    if (risk > 0.4) return 'warning';
    return 'success';
  };

  return (
    <Box>
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Science sx={{ mr: 1, fontSize: 30, color: 'primary.main' }} />
          <Box sx={{ flex: 1 }}>
            <Box display="flex" alignItems="center" gap={2}>
              <Typography variant="h5">
                Claude-Powered Hallucination Analysis
              </Typography>
              <Chip label="AI Enhanced" color="primary" size="small" icon={<AutoAwesome />} />
            </Box>
            <Typography variant="body2" color="text.secondary">
              Intelligent analysis powered by Claude 4.5 Sonnet with detailed insights and recommendations
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
          {loading ? 'Analyzing with Claude...' : 'Analyze for Hallucinations'}
        </Button>
      </Paper>

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

      {/* Claude-Powered Insights Section */}
      {result && (
        <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={2}>
              <AutoAwesome color="primary" />
              <Typography variant="h6">
                Claude Intelligence Insights
              </Typography>
              <Chip label="AI Powered" color="primary" size="small" />
            </Box>
            <Box>
              <Tooltip title="Refresh Insights">
                <IconButton onClick={handleRefreshInsights} disabled={insightsLoading}>
                  <Refresh />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>

          {insightsLoading && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Claude is analyzing your content for intelligent insights...
              </Typography>
              <LinearProgress />
            </Box>
          )}

          {claudeInsights && (
            <Accordion expanded={showAdvancedAnalysis} onChange={() => setShowAdvancedAnalysis(!showAdvancedAnalysis)}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box display="flex" alignItems="center" gap={2}>
                  <Lightbulb color="primary" />
                  <Typography variant="subtitle1" fontWeight={600}>
                    Intelligent Analysis & Recommendations
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Stack spacing={3}>
                  {/* Claude's Insights */}
                  <Card variant="outlined">
                    <CardHeader 
                      title="Claude's Insights" 
                      avatar={<Psychology color="primary" />}
                    />
                    <CardContent>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {claudeInsights.insights}
                      </Typography>
                    </CardContent>
                  </Card>

                  {/* Improvement Suggestions */}
                  <Card variant="outlined">
                    <CardHeader 
                      title="Improvement Suggestions" 
                      avatar={<CheckCircle color="success" />}
                    />
                    <CardContent>
                      <List dense>
                        {claudeInsights.suggestions.map((suggestion: string, index: number) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <Lightbulb color="primary" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={suggestion} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>

                  {/* Practical Tips */}
                  <Card variant="outlined">
                    <CardHeader 
                      title="Practical Tips" 
                      avatar={<AutoAwesome color="secondary" />}
                    />
                    <CardContent>
                      <List dense>
                        {claudeInsights.improvementTips.map((tip: string, index: number) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              <CheckCircle color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={tip} />
                          </ListItem>
                        ))}
                      </List>
                    </CardContent>
                  </Card>
                </Stack>
              </AccordionDetails>
            </Accordion>
          )}

          {!claudeInsights && !insightsLoading && result && (
            <Box textAlign="center" py={3}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Get intelligent insights and recommendations from Claude
              </Typography>
              <Button 
                variant="outlined" 
                startIcon={<AutoAwesome />}
                onClick={() => getClaudeInsights(result)}
              >
                Generate Claude Insights
              </Button>
            </Box>
          )}
        </Paper>
      )}
    </Box>
  );
}

