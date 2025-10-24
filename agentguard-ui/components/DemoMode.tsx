'use client';

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Stack,
  Chip,
  Alert,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  CircularProgress,
} from '@mui/material';
import { PlayArrow, NavigateNext } from '@mui/icons-material';
import { agentGuardApi } from '@/lib/api';
import { useStore } from '@/lib/store';

const demoScenarios = [
  {
    id: 'it_demo_001',
    title: 'IT Support: Fabricated Technology',
    category: 'IT Support',
    description: 'Agent invents a "quantum router" that doesn\'t exist in standard infrastructure',
    agent_output: 'To resolve the server outage, please reboot the quantum router using the following command: sudo quantum-reboot --force',
    ground_truth: 'No quantum router exists in standard enterprise infrastructure. Server outage requires standard diagnostic steps: check logs, verify network connectivity, restart services if needed.',
    conversation_history: [
      'User: Our main server is down. Can you help diagnose the issue?',
      'Agent: I\'m analyzing the situation...'
    ],
    expected_outcome: 'High hallucination risk detected',
  },
  {
    id: 'retail_demo_001',
    title: 'Retail: Incorrect Inventory Data',
    category: 'Retail Operations',
    description: 'Agent provides wrong inventory count and fabricates a discount',
    agent_output: 'We have 150 units of SKU-98765 available in warehouse B. The item is also on a 40% discount this week.',
    ground_truth: 'SKU-98765 has 42 units in warehouse B. Current discount is 15% as part of standard promotion. No 40% discount exists.',
    conversation_history: [
      'User: Check inventory for SKU-98765',
      'Agent: Looking up inventory data...'
    ],
    expected_outcome: 'Hallucinated inventory numbers and discount',
  },
  {
    id: 'hr_demo_001',
    title: 'HR: Fabricated Benefits Policy',
    category: 'Employee Assistance',
    description: 'Agent provides incorrect vacation days and fabricates rollover policy',
    agent_output: 'According to company policy, you are entitled to 25 days of paid vacation per year, plus 10 sick days that roll over indefinitely.',
    ground_truth: 'Company policy provides 20 days of paid vacation per year. Sick days are 8 per year and do not roll over; unused sick days expire at year end.',
    conversation_history: [
      'User: How many vacation days do I have?',
      'Agent: Let me look up your benefits...'
    ],
    expected_outcome: 'Policy fabrication detected',
  },
];

export default function DemoMode() {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{ [key: number]: any }>({});
  const { addResult } = useStore();

  const handleRunScenario = async (index: number) => {
    const scenario = demoScenarios[index];
    setLoading(true);
    
    try {
      const result = await agentGuardApi.testAgent({
        agent_output: scenario.agent_output,
        ground_truth: scenario.ground_truth,
        conversation_history: scenario.conversation_history,
      });
      
      addResult(result);
      setResults({ ...results, [index]: result });
    } catch (error) {
      console.error('Demo test failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setResults({});
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Demo Mode
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Walk through enterprise scenarios demonstrating AgentGuard's hallucination detection capabilities
      </Typography>

      <Stepper activeStep={activeStep} orientation="vertical">
        {demoScenarios.map((scenario, index) => (
          <Step key={scenario.id}>
            <StepLabel>
              <Box>
                <Typography variant="subtitle1">{scenario.title}</Typography>
                <Chip label={scenario.category} size="small" sx={{ mt: 0.5 }} />
              </Box>
            </StepLabel>
            <StepContent>
              <Typography variant="body2" paragraph>
                {scenario.description}
              </Typography>

              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2" fontWeight="bold">Expected Outcome:</Typography>
                <Typography variant="body2">{scenario.expected_outcome}</Typography>
              </Alert>

              <Box sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  Agent Output:
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 2 }}>
                  "{scenario.agent_output}"
                </Typography>

                <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                  Ground Truth:
                </Typography>
                <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                  "{scenario.ground_truth}"
                </Typography>
              </Box>

              {results[index] && (
                <Alert severity={results[index].hallucination_risk > 0.5 ? 'error' : 'success'} sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    <strong>Hallucination Risk:</strong> {(results[index].hallucination_risk * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    <strong>Uncertainty:</strong> {(results[index].uncertainty * 100).toFixed(1)}%
                  </Typography>
                  {results[index].details.hallucinated_segments.length > 0 && (
                    <Typography variant="body2">
                      <strong>Flagged Segments:</strong> {results[index].details.hallucinated_segments.join(', ')}
                    </Typography>
                  )}
                </Alert>
              )}

              <Stack direction="row" spacing={2} sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={() => handleRunScenario(index)}
                  disabled={loading || !!results[index]}
                  startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
                >
                  {results[index] ? 'Completed' : 'Run Test'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={handleNext}
                  disabled={!results[index]}
                  endIcon={<NavigateNext />}
                >
                  {index === demoScenarios.length - 1 ? 'Finish' : 'Next'}
                </Button>
              </Stack>
            </StepContent>
          </Step>
        ))}
      </Stepper>

      {activeStep === demoScenarios.length && (
        <Paper sx={{ p: 3, mt: 3, bgcolor: 'success.main', color: 'success.contrastText' }}>
          <Typography variant="h6" gutterBottom>
            Demo Complete!
          </Typography>
          <Typography variant="body2" paragraph>
            All scenarios have been tested. Check the Results tab to see detailed analysis.
          </Typography>
          <Button onClick={handleReset} variant="contained" color="inherit">
            Reset Demo
          </Button>
        </Paper>
      )}
    </Paper>
  );
}

