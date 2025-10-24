'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Alert,
  Tabs,
  Tab,
  Divider,
  Stack
} from '@mui/material';
import {
  CloudUpload,
  PlayArrow,
  Stop,
  Download,
  Refresh,
  Delete,
  Visibility,
  Settings,
  Assessment,
  FileUpload
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';

import { batchAPI, BatchJob, BatchProgressUpdate, BatchUploadOptions } from '@/lib/batchApi';
import BatchUploadDialog from '@/components/BatchUploadDialog';
import BatchJobDetails from '@/components/BatchJobDetails';
// import BatchProgressTracker from '@/components/BatchProgressTracker'; // Component not implemented yet

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`batch-tabpanel-${index}`}
      aria-labelledby={`batch-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function BatchProcessingPage() {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJob, setSelectedJob] = useState<BatchJob | null>(null);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [progressUpdates, setProgressUpdates] = useState<Map<string, BatchProgressUpdate>>(new Map());
  const [webSockets, setWebSockets] = useState<Map<string, WebSocket>>(new Map());

  // Load jobs on component mount
  useEffect(() => {
    loadJobs();
  }, []);

  // Set up WebSocket connections for active jobs
  useEffect(() => {
    const activeJobs = jobs.filter(job => job.status === 'processing');
    
    // Close existing connections for completed jobs
    webSockets.forEach((ws, jobId) => {
      const job = jobs.find(j => j.job_id === jobId);
      if (!job || job.status !== 'processing') {
        ws.close();
        setWebSockets(prev => {
          const newMap = new Map(prev);
          newMap.delete(jobId);
          return newMap;
        });
      }
    });

    // Create new connections for active jobs
    activeJobs.forEach(job => {
      if (!webSockets.has(job.job_id)) {
        try {
          const ws = batchAPI.createProgressWebSocket(job.job_id);
          
          ws.onmessage = (event) => {
            const update: BatchProgressUpdate = JSON.parse(event.data);
            setProgressUpdates(prev => new Map(prev.set(update.job_id, update)));
            
            // Update job status if changed
            if (update.status !== job.status) {
              setJobs(prev => prev.map(j => 
                j.job_id === update.job_id 
                  ? { ...j, status: update.status as any, processed_rows: update.processed_rows }
                  : j
              ));
            }
          };

          ws.onclose = () => {
            setWebSockets(prev => {
              const newMap = new Map(prev);
              newMap.delete(job.job_id);
              return newMap;
            });
          };

          ws.onerror = (error) => {
            console.error('WebSocket error for job', job.job_id, error);
          };

          setWebSockets(prev => new Map(prev.set(job.job_id, ws)));
        } catch (error) {
          console.error('Failed to create WebSocket for job', job.job_id, error);
        }
      }
    });

    // Cleanup on unmount
    return () => {
      webSockets.forEach(ws => ws.close());
    };
  }, [jobs]);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const response = await batchAPI.listJobs();
      setJobs(response.jobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      toast.error('Failed to load batch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File, options: BatchUploadOptions) => {
    try {
      const response = await batchAPI.uploadFile(file, options);
      toast.success(`File uploaded successfully! Job ID: ${response.job.job_id}`);
      setUploadDialogOpen(false);
      await loadJobs();
    } catch (error: any) {
      console.error('Upload failed:', error);
      toast.error(error.response?.data?.detail || 'Upload failed');
    }
  };

  const handleStartProcessing = async (jobId: string) => {
    try {
      await batchAPI.startProcessing(jobId);
      toast.success('Processing started');
      await loadJobs();
    } catch (error: any) {
      console.error('Failed to start processing:', error);
      toast.error(error.response?.data?.detail || 'Failed to start processing');
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      await batchAPI.cancelJob(jobId);
      toast.success('Job cancelled');
      await loadJobs();
    } catch (error: any) {
      console.error('Failed to cancel job:', error);
      toast.error(error.response?.data?.detail || 'Failed to cancel job');
    }
  };

  const handleExportResults = async (jobId: string, format: 'csv' | 'json' | 'xlsx' = 'csv') => {
    try {
      const job = jobs.find(j => j.job_id === jobId);
      if (!job) return;

      const blob = await batchAPI.exportResults(jobId, {
        format,
        include_metadata: true,
        include_explanations: true,
        filter_flagged_only: false
      });

      batchAPI.downloadFile(blob, `${job.filename}_results.${format}`);
      toast.success('Results exported successfully');
    } catch (error: any) {
      console.error('Export failed:', error);
      toast.error(error.response?.data?.detail || 'Export failed');
    }
  };

  const handleViewDetails = (job: BatchJob) => {
    setSelectedJob(job);
    setDetailsDialogOpen(true);
  };

  const getJobProgress = (job: BatchJob): number => {
    const update = progressUpdates.get(job.job_id);
    if (update) {
      return update.progress_percentage;
    }
    return job.total_rows > 0 ? (job.processed_rows / job.total_rows) * 100 : 0;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getJobSummary = () => {
    const total = jobs.length;
    const pending = jobs.filter(j => j.status === 'pending').length;
    const processing = jobs.filter(j => j.status === 'processing').length;
    const completed = jobs.filter(j => j.status === 'completed').length;
    const failed = jobs.filter(j => j.status === 'failed').length;

    return { total, pending, processing, completed, failed };
  };

  const summary = getJobSummary();

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" fontWeight={700} gutterBottom>
            Batch Processing
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Upload CSV, JSON, or JSONL files for bulk hallucination detection analysis
          </Typography>

          {/* Summary Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight={700} color="primary.main">
                    {summary.total}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Jobs
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight={700} color="warning.main">
                    {summary.pending}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Pending
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight={700} color="info.main">
                    {summary.processing}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Processing
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight={700} color="success.main">
                    {summary.completed}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" fontWeight={700} color="error.main">
                    {summary.failed}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Failed
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              startIcon={<CloudUpload />}
              onClick={() => setUploadDialogOpen(true)}
              size="large"
            >
              Upload File
            </Button>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadJobs}
              disabled={loading}
            >
              Refresh
            </Button>
          </Stack>
        </Box>

        {/* Main Content */}
        <Card>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="All Jobs" />
            <Tab label="Active Jobs" />
            <Tab label="Completed Jobs" />
          </Tabs>

          <TabPanel value={activeTab} index={0}>
            {/* All Jobs */}
            <JobsTable
              jobs={jobs}
              loading={loading}
              progressUpdates={progressUpdates}
              onStartProcessing={handleStartProcessing}
              onCancelJob={handleCancelJob}
              onExportResults={handleExportResults}
              onViewDetails={handleViewDetails}
              getJobProgress={getJobProgress}
              formatDateTime={formatDateTime}
            />
          </TabPanel>

          <TabPanel value={activeTab} index={1}>
            {/* Active Jobs */}
            <JobsTable
              jobs={jobs.filter(job => ['pending', 'processing'].includes(job.status))}
              loading={loading}
              progressUpdates={progressUpdates}
              onStartProcessing={handleStartProcessing}
              onCancelJob={handleCancelJob}
              onExportResults={handleExportResults}
              onViewDetails={handleViewDetails}
              getJobProgress={getJobProgress}
              formatDateTime={formatDateTime}
            />
          </TabPanel>

          <TabPanel value={activeTab} index={2}>
            {/* Completed Jobs */}
            <JobsTable
              jobs={jobs.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status))}
              loading={loading}
              progressUpdates={progressUpdates}
              onStartProcessing={handleStartProcessing}
              onCancelJob={handleCancelJob}
              onExportResults={handleExportResults}
              onViewDetails={handleViewDetails}
              getJobProgress={getJobProgress}
              formatDateTime={formatDateTime}
            />
          </TabPanel>
        </Card>
      </motion.div>

      {/* Upload Dialog */}
      <BatchUploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUpload={handleFileUpload}
      />

      {/* Job Details Dialog */}
      <BatchJobDetails
        job={selectedJob}
        open={detailsDialogOpen}
        onClose={() => setDetailsDialogOpen(false)}
        progressUpdate={selectedJob ? progressUpdates.get(selectedJob.job_id) : undefined}
        onExport={handleExportResults}
      />
    </Container>
  );
}

interface JobsTableProps {
  jobs: BatchJob[];
  loading: boolean;
  progressUpdates: Map<string, BatchProgressUpdate>;
  onStartProcessing: (jobId: string) => void;
  onCancelJob: (jobId: string) => void;
  onExportResults: (jobId: string, format?: 'csv' | 'json' | 'xlsx') => void;
  onViewDetails: (job: BatchJob) => void;
  getJobProgress: (job: BatchJob) => number;
  formatDateTime: (dateString: string) => string;
}

function JobsTable({
  jobs,
  loading,
  progressUpdates,
  onStartProcessing,
  onCancelJob,
  onExportResults,
  onViewDetails,
  getJobProgress,
  formatDateTime
}: JobsTableProps) {
  if (loading) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <LinearProgress sx={{ mb: 2 }} />
        <Typography>Loading batch jobs...</Typography>
      </Box>
    );
  }

  if (jobs.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <FileUpload sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.secondary" gutterBottom>
          No batch jobs found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Upload a file to get started with batch processing
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>File</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Progress</TableCell>
            <TableCell>Results</TableCell>
            <TableCell>Created</TableCell>
            <TableCell align="right">Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <AnimatePresence>
            {jobs.map((job) => (
              <motion.tr
                key={job.job_id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight={600}>
                      {job.filename}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {job.file_format.toUpperCase()} • {job.total_rows} rows
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    label={job.status.toUpperCase()}
                    color={batchAPI.getStatusColor(job.status)}
                    size="small"
                    icon={<span>{batchAPI.getStatusIcon(job.status)}</span>}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ minWidth: 120 }}>
                    <LinearProgress
                      variant="determinate"
                      value={getJobProgress(job)}
                      sx={{ mb: 1 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {job.processed_rows}/{job.total_rows} ({getJobProgress(job).toFixed(1)}%)
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  {job.status === 'completed' && (
                    <Box>
                      <Typography variant="body2">
                        {job.successful_rows} successful
                      </Typography>
                      {job.flagged_percentage !== undefined && (
                        <Typography variant="caption" color="text.secondary">
                          {job.flagged_percentage.toFixed(1)}% flagged
                        </Typography>
                      )}
                    </Box>
                  )}
                  {job.status === 'failed' && (
                    <Typography variant="body2" color="error">
                      {job.error_message || 'Processing failed'}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDateTime(job.created_at)}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1}>
                    {job.status === 'pending' && (
                      <Tooltip title="Start Processing">
                        <IconButton
                          size="small"
                          onClick={() => onStartProcessing(job.job_id)}
                        >
                          <PlayArrow />
                        </IconButton>
                      </Tooltip>
                    )}
                    {job.status === 'processing' && (
                      <Tooltip title="Cancel Job">
                        <IconButton
                          size="small"
                          onClick={() => onCancelJob(job.job_id)}
                        >
                          <Stop />
                        </IconButton>
                      </Tooltip>
                    )}
                    {job.status === 'completed' && (
                      <Tooltip title="Export Results">
                        <IconButton
                          size="small"
                          onClick={() => onExportResults(job.job_id)}
                        >
                          <Download />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => onViewDetails(job)}
                      >
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                  </Stack>
                </TableCell>
              </motion.tr>
            ))}
          </AnimatePresence>
        </TableBody>
      </Table>
    </TableContainer>
  );
}
