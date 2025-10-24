'use client';

import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  IconButton,
  Button,
  Stack,
} from '@mui/material';
import { DataGrid, GridColDef, GridRenderCellParams } from '@mui/x-data-grid';
import { Visibility, Download, DeleteOutline } from '@mui/icons-material';
import { useStore, TestResult } from '@/lib/store';
import ResultModal from './ResultModal';

export default function ResultsTable() {
  const { results, clearResults } = useStore();
  const [selectedResult, setSelectedResult] = useState<TestResult | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const handleViewDetails = (result: TestResult) => {
    setSelectedResult(result);
    setModalOpen(true);
  };

  const handleExportJSON = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = `agentguard-results-${new Date().toISOString()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleExportCSV = () => {
    const headers = ['Timestamp', 'Hallucination Risk', 'Uncertainty', 'Needs Review', 'Latency (s)'];
    const rows = results.map(r => [
      r.timestamp,
      r.hallucination_risk.toFixed(3),
      r.uncertainty.toFixed(3),
      r.details.needs_review ? 'Yes' : 'No',
      r.latency_seconds?.toFixed(3) || 'N/A',
    ]);
    
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');
    
    const dataUri = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
    const exportFileDefaultName = `agentguard-results-${new Date().toISOString()}.csv`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const columns: GridColDef[] = [
    {
      field: 'timestamp',
      headerName: 'Timestamp',
      width: 180,
      valueFormatter: (value) => new Date(value).toLocaleString(),
    },
    {
      field: 'hallucination_risk',
      headerName: 'Hallucination Risk',
      width: 150,
      renderCell: (params: GridRenderCellParams<TestResult>) => {
        const risk = params.row.hallucination_risk;
        const color = risk > 0.7 ? 'error' : risk > 0.4 ? 'warning' : 'success';
        return (
          <Chip
            label={`${(risk * 100).toFixed(1)}%`}
            color={color}
            size="small"
          />
        );
      },
    },
    {
      field: 'uncertainty',
      headerName: 'Uncertainty',
      width: 120,
      valueFormatter: (value) => `${(Number(value) * 100).toFixed(1)}%`,
    },
    {
      field: 'needs_review',
      headerName: 'Needs Review',
      width: 120,
      renderCell: (params: GridRenderCellParams<TestResult>) => {
        const needsReview = params.row.details.needs_review;
        return needsReview ? (
          <Chip label="Yes" color="warning" size="small" />
        ) : (
          <Chip label="No" color="default" size="small" variant="outlined" />
        );
      },
    },
    {
      field: 'latency_seconds',
      headerName: 'Latency (s)',
      width: 110,
      valueFormatter: (value) => value ? Number(value).toFixed(3) : 'N/A',
    },
    {
      field: 'hallucinated_segments',
      headerName: 'Flagged Segments',
      width: 200,
      valueGetter: (value, row) => row.details.hallucinated_segments.length,
      renderCell: (params: GridRenderCellParams<TestResult>) => {
        const segments = params.row.details.hallucinated_segments;
        return segments.length > 0 ? (
          <Typography variant="body2" color="error">
            {segments.length} segment{segments.length > 1 ? 's' : ''}
          </Typography>
        ) : (
          <Typography variant="body2" color="text.secondary">
            None
          </Typography>
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 100,
      sortable: false,
      renderCell: (params: GridRenderCellParams<TestResult>) => (
        <IconButton
          size="small"
          onClick={() => handleViewDetails(params.row)}
          color="primary"
        >
          <Visibility />
        </IconButton>
      ),
    },
  ];

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h5">
          Test Results ({results.length})
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            startIcon={<Download />}
            onClick={handleExportJSON}
            disabled={results.length === 0}
            size="small"
          >
            Export JSON
          </Button>
          <Button
            startIcon={<Download />}
            onClick={handleExportCSV}
            disabled={results.length === 0}
            size="small"
          >
            Export CSV
          </Button>
          <Button
            startIcon={<DeleteOutline />}
            onClick={clearResults}
            disabled={results.length === 0}
            color="error"
            size="small"
          >
            Clear
          </Button>
        </Stack>
      </Stack>
      
      {results.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No test results yet. Run a test to see results here.
          </Typography>
        </Box>
      ) : (
        <DataGrid
          rows={results}
          columns={columns}
          initialState={{
            pagination: {
              paginationModel: { pageSize: 10 },
            },
          }}
          pageSizeOptions={[5, 10, 25]}
          autoHeight
          disableRowSelectionOnClick
        />
      )}
      
      {selectedResult && (
        <ResultModal
          open={modalOpen}
          result={selectedResult}
          onClose={() => {
            setModalOpen(false);
            setSelectedResult(null);
          }}
        />
      )}
    </Paper>
  );
}

