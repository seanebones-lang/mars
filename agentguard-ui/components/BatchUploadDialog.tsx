'use client';

import React, { useState, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Paper,
  Stack,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import { useTheme } from '@mui/material/styles';
import { CloudUpload, Description, CheckCircle } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';

import { BatchUploadOptions } from '@/lib/batchApi';

interface BatchUploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File, options: BatchUploadOptions) => Promise<void>;
}

export default function BatchUploadDialog({ open, onClose, onUpload }: BatchUploadDialogProps) {
  const theme = useTheme();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [options, setOptions] = useState<BatchUploadOptions>({
    has_headers: true,
    agent_output_column: 'agent_output',
    ground_truth_column: '',
    query_column: '',
    agent_id_column: ''
  });
  const [step, setStep] = useState<'upload' | 'configure' | 'preview'>('upload');
  const [previewData, setPreviewData] = useState<any[]>([]);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
      setStep('configure');
      
      // Preview file content
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          const text = e.target?.result as string;
          const lines = text.split('\n').slice(0, 5); // First 5 lines
          const preview = lines.map(line => line.split(','));
          setPreviewData(preview);
        };
        reader.readAsText(file);
      } else if (file.type === 'application/json' || file.name.endsWith('.json')) {
        const reader = new FileReader();
        reader.onload = (e) => {
          try {
            const json = JSON.parse(e.target?.result as string);
            const preview = Array.isArray(json) ? json.slice(0, 5) : [json];
            setPreviewData(preview);
          } catch (error) {
            console.error('Error parsing JSON:', error);
          }
        };
        reader.readAsText(file);
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/json': ['.json'],
      'application/x-ndjson': ['.jsonl']
    },
    multiple: false,
    maxSize: 100 * 1024 * 1024 // 100MB
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setUploading(true);
      await onUpload(selectedFile, options);
      handleClose();
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setStep('upload');
    setPreviewData([]);
    setOptions({
      has_headers: true,
      agent_output_column: 'agent_output',
      ground_truth_column: '',
      query_column: '',
      agent_id_column: ''
    });
    onClose();
  };

  const getFileIcon = (file: File) => {
    if (file.name.endsWith('.csv')) return 'CSV';
    if (file.name.endsWith('.json')) return 'JSON';
    if (file.name.endsWith('.jsonl')) return 'JSONL';
    return 'FILE';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '500px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CloudUpload color="primary" />
          <Box>
            <Typography variant="h6">Upload Batch File</Typography>
            <Typography variant="body2" color="text.secondary">
              Step {step === 'upload' ? '1' : step === 'configure' ? '2' : '3'} of 3
            </Typography>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        <AnimatePresence mode="wait">
          {step === 'upload' && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              <Box sx={{ mb: 3 }}>
                <Typography variant="body1" gutterBottom>
                  Upload a CSV, JSON, or JSONL file for batch hallucination detection
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Supported formats: CSV (with headers), JSON (array of objects), JSONL (line-delimited JSON)
                </Typography>
              </Box>

              <Paper
                {...getRootProps()}
                sx={{
                  p: 4,
                  textAlign: 'center',
                  border: '2px dashed',
                  borderColor: isDragActive ? 'primary.main' : (theme.palette.mode === 'dark' ? 'grey.700' : 'grey.300'),
                  backgroundColor: isDragActive ? 'primary.50' : (theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50'),
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    borderColor: 'primary.main',
                    backgroundColor: 'primary.50'
                  }
                }}
              >
                <input {...getInputProps()} />
                <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Drop your file here' : 'Drag & drop a file here'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  or click to browse files
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Maximum file size: 100MB
                </Typography>
              </Paper>

              {/* Format Examples */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Expected File Formats:
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card variant="outlined">
                      <CardContent sx={{ p: 2 }}>
                        <Typography variant="body2" fontWeight={600}>CSV</Typography>
                        <Typography variant="caption" color="text.secondary">
                          agent_output,ground_truth,query
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card variant="outlined">
                      <CardContent sx={{ p: 2 }}>
                        <Typography variant="body2" fontWeight={600}>JSON</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {`[{"agent_output": "...", "ground_truth": "..."}]`}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card variant="outlined">
                      <CardContent sx={{ p: 2 }}>
                        <Typography variant="body2" fontWeight={600}>JSONL</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {`{"agent_output": "..."}`}<br/>{`{"agent_output": "..."}`}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            </motion.div>
          )}

          {step === 'configure' && selectedFile && (
            <motion.div
              key="configure"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.3 }}
            >
              {/* File Info */}
              <Alert severity="success" sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <span style={{ fontSize: '24px' }}>{getFileIcon(selectedFile)}</span>
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Unknown type'}
                    </Typography>
                  </Box>
                </Box>
              </Alert>

              <Typography variant="h6" gutterBottom>
                Configure Column Mapping
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Map your file columns to the expected fields for processing
              </Typography>

              {/* CSV Configuration */}
              {selectedFile.name.endsWith('.csv') && (
                <Box sx={{ mb: 3 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={options.has_headers || false}
                        onChange={(e) => setOptions(prev => ({ ...prev, has_headers: e.target.checked }))}
                      />
                    }
                    label="File has header row"
                  />
                </Box>
              )}

              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Agent Output Column"
                    value={options.agent_output_column || ''}
                    onChange={(e) => setOptions(prev => ({ ...prev, agent_output_column: e.target.value }))}
                    helperText="Required: Column containing AI agent responses"
                    required
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Ground Truth Column"
                    value={options.ground_truth_column || ''}
                    onChange={(e) => setOptions(prev => ({ ...prev, ground_truth_column: e.target.value }))}
                    helperText="Optional: Expected correct responses"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Query Column"
                    value={options.query_column || ''}
                    onChange={(e) => setOptions(prev => ({ ...prev, query_column: e.target.value }))}
                    helperText="Optional: Original user queries"
                  />
                </Grid>
                <Grid size={{ xs: 12, sm: 6 }}>
                  <TextField
                    fullWidth
                    label="Agent ID Column"
                    value={options.agent_id_column || ''}
                    onChange={(e) => setOptions(prev => ({ ...prev, agent_id_column: e.target.value }))}
                    helperText="Optional: Agent identifiers"
                  />
                </Grid>
              </Grid>

              {/* File Preview */}
              {previewData.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    File Preview (First 5 rows):
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                    <pre style={{ margin: 0, fontSize: '12px', fontFamily: 'monospace' }}>
                      {selectedFile.name.endsWith('.csv') 
                        ? previewData.map(row => row.join(', ')).join('\n')
                        : JSON.stringify(previewData, null, 2)
                      }
                    </pre>
                  </Paper>
                </Box>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 0 }}>
        <Button onClick={handleClose} disabled={uploading}>
          Cancel
        </Button>
        
        {step === 'configure' && (
          <Button
            onClick={() => setStep('upload')}
            disabled={uploading}
          >
            Back
          </Button>
        )}
        
        {step === 'upload' && selectedFile && (
          <Button
            onClick={() => setStep('configure')}
            variant="contained"
          >
            Next
          </Button>
        )}
        
        {step === 'configure' && (
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={uploading || !options.agent_output_column}
            startIcon={uploading ? undefined : <CloudUpload />}
          >
            {uploading ? 'Uploading...' : 'Upload & Create Job'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
