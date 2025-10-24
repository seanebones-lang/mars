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
              AI Agent Reliability Validator
            </Typography>
            <Chip label="Production Ready" color="success" size="small" icon={<CheckCircle />} />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Test your AI agents for hallucinations, fabrications, and reliability issues. Used by enterprises to validate AI before deployment.
          </Typography>
          </Box>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <TextField
          label="AI Agent Output to Validate"
          multiline
          rows={8}
          fullWidth
          value={agentOutput}
          onChange={(e) => setAgentOutput(e.target.value)}
          placeholder="Paste your AI agent's response here to check for hallucinations and reliability issues...

REAL EXAMPLES TO TRY:

🔧 IT Support Agent:
'To resolve the network connectivity issue, please restart your quantum ethernet adapter through the flux capacitor management console. This will recalibrate the photon streams and restore connectivity within 15 seconds.'

🛒 E-commerce Agent:
'This premium leather jacket is made from authentic dragon hide sourced from our exclusive partnership with Skyrim Industries. It features nano-fiber technology that makes it completely bulletproof while remaining lightweight.'

👥 HR Assistant Agent:
'According to our updated policy, all employees now receive 45 vacation days per year, plus unlimited sick leave. You can also bring your pet dragon to work on Fridays as part of our new mythical creature inclusion program.'

📞 Customer Service Agent:
'I've processed your refund of $2,847 for the item you never purchased. The money has been deposited into your account along with a bonus $500 for the inconvenience. Your order has also been upgraded to our premium platinum membership for life.'"
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
          {loading ? 'Validating Agent Response...' : 'Validate AI Agent'}
        </Button>

        {/* Quick Test Examples */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Quick Test Examples - Click to try:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setAgentOutput("To fix your server issue, simply reboot the quantum router using the admin panel. This will clear the flux capacitor cache and restore normal operations within 30 seconds.")}
            >
              🔧 IT Support (Fabricated Tech)
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setAgentOutput("This premium leather jacket is made from authentic dragon hide sourced from our exclusive partnership with Skyrim Industries. It features nano-fiber technology that makes it completely bulletproof while remaining lightweight.")}
            >
              🛒 E-commerce (Fake Products)
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setAgentOutput("According to our updated policy, all employees now receive 45 vacation days per year, plus unlimited sick leave. You can also bring your pet dragon to work on Fridays as part of our new mythical creature inclusion program.")}
            >
              👥 HR Assistant (False Policies)
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setAgentOutput("I've processed your refund of $2,847 for the item you never purchased. The money has been deposited into your account along with a bonus $500 for the inconvenience. Your order has also been upgraded to our premium platinum membership for life.")}
            >
              📞 Customer Service (Fake Actions)
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={() => setAgentOutput("The server is running normally with 99.9% uptime. All services are operational and there are no current issues affecting performance.")}
            >
              ✅ Good Response (No Hallucinations)
            </Button>
          </Stack>
        </Box>
      </Paper>

      {result && (
        <Box sx={{ mt: 4 }}>
          <Divider sx={{ mb: 3 }} />
          
          <Typography variant="h6" gutterBottom>
            AI Agent Reliability Assessment
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
                {result.hallucination_risk > 0.7 ? '🚨 UNSAFE - Do not deploy this agent response' :
                 result.hallucination_risk > 0.4 ? '⚠️ CAUTION - Review before deployment' :
                 '✅ SAFE - Agent response appears reliable'}
              </Typography>
            </Box>

            {/* Claude's Explanation */}
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Detailed Safety Analysis
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
                🚨 Fabricated/Hallucinated Content Detected:
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

          {/* Practical Next Steps */}
          <Alert 
            severity={result.hallucination_risk > 0.7 ? "error" : result.hallucination_risk > 0.4 ? "warning" : "success"} 
            sx={{ mt: 3 }}
          >
            <Typography variant="body2">
              <strong>
                {result.hallucination_risk > 0.7 ? "🚨 IMMEDIATE ACTION REQUIRED:" :
                 result.hallucination_risk > 0.4 ? "⚠️ REVIEW RECOMMENDED:" :
                 "✅ AGENT RESPONSE APPROVED:"}
              </strong>
              {result.hallucination_risk > 0.7 ? 
                " This agent response contains fabricated information and should NOT be deployed. Retrain or adjust your AI agent before use." :
                result.hallucination_risk > 0.4 ?
                " This response has some reliability concerns. Review the flagged content and consider additional training data." :
                " This agent response appears safe and reliable for deployment."}
            </Typography>
          </Alert>

          {/* Enterprise Integration CTA */}
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>For Production Use:</strong> Integrate Watcher AI into your deployment pipeline via our REST API or Python SDK. 
              Test all agent responses before they reach customers. <strong>Prevent AI hallucinations in production.</strong>
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

