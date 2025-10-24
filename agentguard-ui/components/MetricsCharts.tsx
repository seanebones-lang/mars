'use client';

import { Paper, Typography, Box, Stack } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import { useStore } from '@/lib/store';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default function MetricsCharts() {
  const { results } = useStore();

  // Get last 10 results for charts
  const recentResults = results.slice(0, Math.min(10, results.length));
  
  // Hallucination Risk Bar Chart
  const hallucinationRiskData = {
    labels: recentResults.map((_, i) => `Test ${results.length - i}`),
    datasets: [
      {
        label: 'Hallucination Risk',
        data: recentResults.map(r => Number(r.hallucination_risk)),
        backgroundColor: recentResults.map(r => 
          r.hallucination_risk > 0.7 ? '#FF5252' : 
          r.hallucination_risk > 0.4 ? '#FF9800' : '#4CAF50'
        ),
        borderColor: recentResults.map(r => 
          r.hallucination_risk > 0.7 ? '#D32F2F' : 
          r.hallucination_risk > 0.4 ? '#F57C00' : '#388E3C'
        ),
        borderWidth: 1,
      },
    ],
  };

  // Latency Line Chart
  const latencyData = {
    labels: recentResults.map((_, i) => `Test ${results.length - i}`),
    datasets: [
      {
        label: 'Latency (seconds)',
        data: recentResults.map(r => Number(r.latency_seconds) || 0),
        borderColor: '#2196F3',
        backgroundColor: 'rgba(33, 150, 243, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'Target (0.5s)',
        data: Array(recentResults.length).fill(0.5),
        borderColor: '#FF5252',
        borderDash: [5, 5],
        pointRadius: 0,
      },
    ],
  };

  // Risk Distribution Doughnut
  const lowRisk = results.filter(r => r.hallucination_risk < 0.3).length;
  const mediumRisk = results.filter(r => r.hallucination_risk >= 0.3 && r.hallucination_risk < 0.7).length;
  const highRisk = results.filter(r => r.hallucination_risk >= 0.7).length;

  const riskDistributionData = {
    labels: ['Low Risk (<30%)', 'Medium Risk (30-70%)', 'High Risk (>70%)'],
    datasets: [
      {
        data: [lowRisk, mediumRisk, highRisk],
        backgroundColor: ['#4CAF50', '#FF9800', '#FF5252'],
        borderColor: ['#388E3C', '#F57C00', '#D32F2F'],
        borderWidth: 1,
      },
    ],
  };

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  };

  const barOptions: any = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 1,
        title: {
          display: true,
          text: 'Hallucination Risk',
        },
      },
    },
  };

  const lineOptions: any = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Latency (seconds)',
        },
      },
    },
  };

  if (results.length === 0) {
    return (
      <Paper elevation={3} sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No data available. Run some tests to see metrics visualizations.
        </Typography>
      </Paper>
    );
  }

  return (
    <Stack spacing={3}>
      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 3 }}>
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Hallucination Risk by Test
          </Typography>
          <Box sx={{ height: 300 }}>
            <Bar data={hallucinationRiskData} options={barOptions} />
          </Box>
        </Paper>

        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Risk Distribution
          </Typography>
          <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Doughnut data={riskDistributionData} options={chartOptions} />
          </Box>
        </Paper>
      </Box>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Latency Over Time
        </Typography>
        <Box sx={{ height: 300 }}>
          <Line data={latencyData} options={lineOptions} />
        </Box>
      </Paper>
    </Stack>
  );
}

