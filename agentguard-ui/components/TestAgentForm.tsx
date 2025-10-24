'use client';

import { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  Chip,
  Stack,
  Alert,
  CircularProgress,
} from '@mui/material';
import { PlayArrow, Upload } from '@mui/icons-material';
import { agentGuardApi } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function TestAgentForm() {
  const [agentOutput, setAgentOutput] = useState('');
  const [groundTruth, setGroundTruth] = useState('');
  const [historyInput, setHistoryInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  const { addResult, loading, setLoading } = useStore();
  
  const conversationHistory = historyInput
    .split('\n')
    .filter(line => line.trim())
    .map(line => line.trim());

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    
    if (!agentOutput || !groundTruth) {
      setError('Agent output and ground truth are required');
      return;
    }
    
    setLoading(true);
    const startTime = Date.now();
    
    try {
      const result = await agentGuardApi.testAgent({
        agent_output: agentOutput,
        ground_truth: groundTruth,
        conversation_history: conversationHistory.length > 0 ? conversationHistory : undefined,
      });
      
      const latency = (Date.now() - startTime) / 1000;
      addResult({ ...result, latency_seconds: latency });
      setSuccess(true);
      
      // Clear form after successful submission
      setTimeout(() => {
        setAgentOutput('');
        setGroundTruth('');
        setHistoryInput('');
        setSuccess(false);
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Test failed');
    } finally {
      setLoading(false);
    }
  };
  
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const scenarios = Array.isArray(data) ? data : [data];
      
      const results = await agentGuardApi.batchTest(scenarios);
      results.forEach(result => addResult(result));
      setSuccess(true);
    } catch (err: any) {
      setError('File upload failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Test AI Agent
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Test completed successfully!
        </Alert>
      )}
      
      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Agent Output"
          multiline
          rows={4}
          fullWidth
          value={agentOutput}
          onChange={(e) => setAgentOutput(e.target.value)}
          placeholder="Enter the AI agent's response to test..."
          sx={{ mb: 2 }}
          required
        />
        
        <TextField
          label="Ground Truth / Reference"
          multiline
          rows={3}
          fullWidth
          value={groundTruth}
          onChange={(e) => setGroundTruth(e.target.value)}
          placeholder="Enter the expected correct response..."
          sx={{ mb: 2 }}
          required
        />
        
        <TextField
          label="Conversation History (optional)"
          multiline
          rows={3}
          fullWidth
          value={historyInput}
          onChange={(e) => setHistoryInput(e.target.value)}
          placeholder="Enter conversation history (one message per line)..."
          helperText="Multi-turn conversation support. Enter previous exchanges, one per line."
          sx={{ mb: 2 }}
        />
        
        {conversationHistory.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Conversation turns: {conversationHistory.length}
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              {conversationHistory.map((msg, i) => (
                <Chip
                  key={i}
                  label={msg.substring(0, 30) + (msg.length > 30 ? '...' : '')}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>
        )}
        
        <Stack direction="row" spacing={2} alignItems="center">
          <Button
            type="submit"
            variant="contained"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Run Test'}
          </Button>
          
          <Button
            variant="outlined"
            component="label"
            startIcon={<Upload />}
            disabled={loading}
          >
            Upload JSON
            <input
              type="file"
              hidden
              accept=".json"
              onChange={handleFileUpload}
            />
          </Button>
        </Stack>
      </Box>
    </Paper>
  );
}

