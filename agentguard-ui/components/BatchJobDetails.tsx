'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Divider,
  Stack,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  Close,
  Download,
  Assessment,
  Schedule,
  CheckCircle,
  Error,
  Warning,
  Info,
  MoreVert
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { motion } from 'framer-motion';

import { BatchJob, BatchProgressUpdate, batchAPI } from '@/lib/batchApi';

interface BatchJobDetailsProps {
  job: BatchJob | null;
  open: boolean;
  onClose: () => void;
  progressUpdate?: BatchProgressUpdate;
  onExport: (jobId: string, format: 'csv' | 'json' | 'xlsx') => void;
}

export default function BatchJobDetails({ 
  job, 
  open, 
  onClose, 
  progressUpdate,
  onExport 
}: BatchJobDetailsProps) {
  const theme = useTheme();
  const [exportMenuAnchor, setExportMenuAnchor] = useState<null | HTMLElement>(null);

  if (!job) return null;

  const handleExportClick = (event: React.MouseEvent<HTMLElement>) => {
    setExportMenuAnchor(event.currentTarget);
  };

  const handleExportClose = () => {
    setExportMenuAnchor(null);
  };

  const handleExport = (format: 'csv' | 'json' | 'xlsx') => {
    onExport(job.job_id, format);
    handleExportClose();
  };

  const getProgress = () => {
    if (progressUpdate) {
      return progressUpdate.progress_percentage;
    }
    return job.total_rows > 0 ? (job.processed_rows / job.total_rows) * 100 : 0;
  };

  const getStatusDetails = () => {
    switch (job.status) {
      case 'pending':
        return {
          icon: <Schedule color="action" />,
          color: 'default' as const,
          message: 'Job is queued and waiting to be processed'
        };
      case 'processing':
        return {
          icon: <Assessment color="primary" />,
          color: 'primary' as const,
          message: progressUpdate?.estimated_time_remaining 
            ? `Processing... Estimated ${Math.round(progressUpdate.estimated_time_remaining / 60)} minutes remaining`
            : 'Processing your file...'
        };
      case 'completed':
        return {
          icon: <CheckCircle color="success" />,
          color: 'success' as const,
          message: 'Processing completed successfully'
        };
      case 'failed':
        return {
          icon: <Error color="error" />,
          color: 'error' as const,
          message: job.error_message || 'Processing failed'
        };
      case 'cancelled':
        return {
          icon: <Warning color="warning" />,
          color: 'warning' as const,
          message: 'Job was cancelled'
        };
      default:
        return {
          icon: <Info color="info" />,
          color: 'info' as const,
          message: 'Unknown status'
        };
    }
  };

  const statusDetails = getStatusDetails();
  const progress = getProgress();

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startDate: string, endDate?: string) => {
    const start = new Date(startDate);
    const end = endDate ? new Date(endDate) : new Date();
    const diffMs = end.getTime() - start.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMinutes / 60);
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes % 60}m`;
    }
    return `${diffMinutes}m`;
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '600px' }
      }}
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {statusDetails.icon}
            <Box>
              <Typography variant="h6">
                {job.filename}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Job ID: {job.job_id}
              </Typography>
            </Box>
          </Box>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Status Alert */}
          <Alert 
            severity={statusDetails.color === 'default' ? 'info' : statusDetails.color as any} 
            sx={{ mb: 3 }}
            icon={statusDetails.icon}
          >
            {statusDetails.message}
          </Alert>

          {/* Progress Section */}
          {job.status === 'processing' && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Processing Progress
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={progress} 
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {job.processed_rows} / {job.total_rows} rows
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {progress.toFixed(1)}%
                    </Typography>
                  </Box>
                </Box>
                
                {progressUpdate?.current_row_data && (
                  <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" fontWeight={600} gutterBottom>
                      Current Row:
                    </Typography>
                    <Typography variant="body2" sx={{ 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}>
                      {progressUpdate.current_row_data.agent_output}
                    </Typography>
                    <Chip
                      size="small"
                      label={`Risk: ${(progressUpdate.current_row_data.hallucination_risk * 100).toFixed(1)}%`}
                      color={progressUpdate.current_row_data.flagged ? 'error' : 'success'}
                      sx={{ mt: 1 }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          )}

          {/* Job Information */}
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    File Information
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Filename
                      </Typography>
                      <Typography variant="body1">
                        {job.filename}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Format
                      </Typography>
                      <Chip label={job.file_format.toUpperCase()} size="small" />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Total Rows
                      </Typography>
                      <Typography variant="body1">
                        {job.total_rows.toLocaleString()}
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Status
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Status
                      </Typography>
                      <Chip 
                        label={job.status.toUpperCase()} 
                        color={batchAPI.getStatusColor(job.status)}
                        icon={<span>{batchAPI.getStatusIcon(job.status)}</span>}
                      />
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Processed Rows
                      </Typography>
                      <Typography variant="body1">
                        {job.processed_rows.toLocaleString()} / {job.total_rows.toLocaleString()}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                      <Typography variant="body1">
                        {job.processed_rows > 0 
                          ? `${((job.successful_rows / job.processed_rows) * 100).toFixed(1)}%`
                          : 'N/A'
                        }
                      </Typography>
                    </Box>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Timing
                  </Typography>
                  <Stack spacing={2}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Created
                      </Typography>
                      <Typography variant="body1">
                        {formatDateTime(job.created_at)}
                      </Typography>
                    </Box>
                    {job.started_at && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Started
                        </Typography>
                        <Typography variant="body1">
                          {formatDateTime(job.started_at)}
                        </Typography>
                      </Box>
                    )}
                    {job.completed_at && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Completed
                        </Typography>
                        <Typography variant="body1">
                          {formatDateTime(job.completed_at)}
                        </Typography>
                      </Box>
                    )}
                    {job.started_at && (
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Duration
                        </Typography>
                        <Typography variant="body1">
                          {formatDuration(job.started_at, job.completed_at)}
                        </Typography>
                      </Box>
                    )}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            {job.status === 'completed' && (
              <Grid size={{ xs: 12, md: 6 }}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Results Summary
                    </Typography>
                    <Stack spacing={2}>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Average Risk Score
                        </Typography>
                        <Typography variant="body1">
                          {job.average_risk_score !== undefined 
                            ? `${(job.average_risk_score * 100).toFixed(1)}%`
                            : 'N/A'
                          }
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Flagged Responses
                        </Typography>
                        <Typography variant="body1">
                          {job.flagged_percentage !== undefined 
                            ? `${job.flagged_percentage.toFixed(1)}%`
                            : 'N/A'
                          }
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Avg Processing Time
                        </Typography>
                        <Typography variant="body1">
                          {job.average_processing_time !== undefined 
                            ? `${job.average_processing_time.toFixed(0)}ms`
                            : 'N/A'
                          }
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>

          {/* Error Details */}
          {job.status === 'failed' && job.error_message && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom color="error">
                  Error Details
                </Typography>
                <Typography variant="body2" sx={{ 
                  fontFamily: 'monospace',
                  bgcolor: 'grey.100',
                  p: 2,
                  borderRadius: 1,
                  whiteSpace: 'pre-wrap'
                }}>
                  {job.error_message}
                </Typography>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 0 }}>
        <Button onClick={onClose}>
          Close
        </Button>
        
        {job.status === 'completed' && (
          <>
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={handleExportClick}
              endIcon={<MoreVert />}
            >
              Export Results
            </Button>
            
            <Menu
              anchorEl={exportMenuAnchor}
              open={Boolean(exportMenuAnchor)}
              onClose={handleExportClose}
            >
              <MenuItem onClick={() => handleExport('csv')}>
                <ListItemIcon>
                  <Download fontSize="small" />
                </ListItemIcon>
                <ListItemText>Export as CSV</ListItemText>
              </MenuItem>
              <MenuItem onClick={() => handleExport('json')}>
                <ListItemIcon>
                  <Download fontSize="small" />
                </ListItemIcon>
                <ListItemText>Export as JSON</ListItemText>
              </MenuItem>
              <MenuItem onClick={() => handleExport('xlsx')}>
                <ListItemIcon>
                  <Download fontSize="small" />
                </ListItemIcon>
                <ListItemText>Export as Excel</ListItemText>
              </MenuItem>
            </Menu>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
