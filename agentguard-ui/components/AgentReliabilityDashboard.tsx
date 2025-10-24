"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Alert,
  Button,
  IconButton,
  Tooltip,
  LinearProgress,
  Stack,
  Divider,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Warning,
  CheckCircle,
  Error,
  Shield,
  Computer,
  ShoppingCart,
  People,
  Phone,
  LocalHospital,
  AccountBalance,
  Refresh,
  Assessment,
  Timeline,
  Security,
  Speed,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { agentGuardApi } from '@/lib/api';

interface AgentMetrics {
  agentId: string;
  agentName: string;
  industry: string;
  icon: React.ReactNode;
  totalTests: number;
  safetyScore: number;
  riskTrend: 'improving' | 'stable' | 'declining';
  lastTested: string;
  criticalIssues: number;
  avgResponseTime: number;
  deploymentStatus: 'production' | 'testing' | 'suspended';
}

interface TrendData {
  date: string;
  safetyScore: number;
  testsRun: number;
  criticalIssues: number;
}

interface RiskDistribution {
  category: string;
  count: number;
  percentage: number;
  color: string;
}

const mockAgentMetrics: AgentMetrics[] = [
  {
    agentId: 'it-support-001',
    agentName: 'IT Support Assistant',
    industry: 'Technology',
    icon: <Computer />,
    totalTests: 1247,
    safetyScore: 94.2,
    riskTrend: 'improving',
    lastTested: '2 hours ago',
    criticalIssues: 3,
    avgResponseTime: 1.2,
    deploymentStatus: 'production'
  },
  {
    agentId: 'ecommerce-001',
    agentName: 'Product Assistant',
    industry: 'E-commerce',
    icon: <ShoppingCart />,
    totalTests: 2156,
    safetyScore: 87.8,
    riskTrend: 'stable',
    lastTested: '15 minutes ago',
    criticalIssues: 8,
    avgResponseTime: 0.9,
    deploymentStatus: 'production'
  },
  {
    agentId: 'hr-001',
    agentName: 'HR Policy Bot',
    industry: 'Human Resources',
    icon: <People />,
    totalTests: 892,
    safetyScore: 96.1,
    riskTrend: 'improving',
    lastTested: '1 hour ago',
    criticalIssues: 1,
    avgResponseTime: 1.8,
    deploymentStatus: 'production'
  },
  {
    agentId: 'customer-service-001',
    agentName: 'Customer Support',
    industry: 'Customer Service',
    icon: <Phone />,
    totalTests: 3421,
    safetyScore: 82.3,
    riskTrend: 'declining',
    lastTested: '5 minutes ago',
    criticalIssues: 15,
    avgResponseTime: 2.1,
    deploymentStatus: 'testing'
  },
  {
    agentId: 'healthcare-001',
    agentName: 'Health Info Assistant',
    industry: 'Healthcare',
    icon: <LocalHospital />,
    totalTests: 567,
    safetyScore: 98.7,
    riskTrend: 'stable',
    lastTested: '30 minutes ago',
    criticalIssues: 0,
    avgResponseTime: 1.5,
    deploymentStatus: 'production'
  },
  {
    agentId: 'finance-001',
    agentName: 'Financial Advisor',
    industry: 'Finance',
    icon: <AccountBalance />,
    totalTests: 234,
    safetyScore: 76.4,
    riskTrend: 'declining',
    lastTested: '3 hours ago',
    criticalIssues: 12,
    avgResponseTime: 3.2,
    deploymentStatus: 'suspended'
  }
];

const mockTrendData: TrendData[] = [
  { date: '2024-10-17', safetyScore: 89.2, testsRun: 145, criticalIssues: 8 },
  { date: '2024-10-18', safetyScore: 91.1, testsRun: 167, criticalIssues: 6 },
  { date: '2024-10-19', safetyScore: 88.7, testsRun: 189, criticalIssues: 12 },
  { date: '2024-10-20', safetyScore: 92.3, testsRun: 203, criticalIssues: 4 },
  { date: '2024-10-21', safetyScore: 90.8, testsRun: 178, criticalIssues: 7 },
  { date: '2024-10-22', safetyScore: 93.5, testsRun: 234, criticalIssues: 3 },
  { date: '2024-10-23', safetyScore: 91.9, testsRun: 267, criticalIssues: 5 },
  { date: '2024-10-24', safetyScore: 94.2, testsRun: 289, criticalIssues: 2 }
];

const mockRiskDistribution: RiskDistribution[] = [
  { category: 'Safe (0-30%)', count: 7234, percentage: 78.2, color: '#4CAF50' },
  { category: 'Low Risk (30-50%)', count: 1456, percentage: 15.7, color: '#FF9800' },
  { category: 'Medium Risk (50-70%)', count: 423, percentage: 4.6, color: '#FF5722' },
  { category: 'High Risk (70-100%)', count: 142, percentage: 1.5, color: '#F44336' }
];

export default function AgentReliabilityDashboard() {
  const [timeRange, setTimeRange] = useState(7);
  const [selectedAgent, setSelectedAgent] = useState<string>('all');
  const [loading, setLoading] = useState(false);
  const [insights, setInsights] = useState<any>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'production': return 'success';
      case 'testing': return 'warning';
      case 'suspended': return 'error';
      default: return 'default';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return <TrendingUp color="success" />;
      case 'declining': return <TrendingDown color="error" />;
      default: return <Timeline color="info" />;
    }
  };

  const getSafetyScoreColor = (score: number) => {
    if (score >= 95) return 'success';
    if (score >= 85) return 'warning';
    return 'error';
  };

  const getFleetInsights = async () => {
    setLoading(true);
    try {
      const insights = await agentGuardApi.getFleetInsights(mockAgentMetrics);
      setInsights(insights);
    } catch (err) {
      console.error('Failed to get fleet insights:', err);
    } finally {
      setLoading(false);
    }
  };

  const overallMetrics = {
    totalAgents: mockAgentMetrics.length,
    avgSafetyScore: mockAgentMetrics.reduce((sum, agent) => sum + agent.safetyScore, 0) / mockAgentMetrics.length,
    totalTests: mockAgentMetrics.reduce((sum, agent) => sum + agent.totalTests, 0),
    criticalIssues: mockAgentMetrics.reduce((sum, agent) => sum + agent.criticalIssues, 0),
    productionAgents: mockAgentMetrics.filter(agent => agent.deploymentStatus === 'production').length,
    suspendedAgents: mockAgentMetrics.filter(agent => agent.deploymentStatus === 'suspended').length
  };

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Agent Reliability Dashboard
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Monitor AI agent safety scores, trends, and deployment status across your enterprise
          </Typography>
        </Box>
        
        <Box display="flex" gap={2} alignItems="center">
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value as number)}
            >
              <MenuItem value={7}>Last 7 days</MenuItem>
              <MenuItem value={30}>Last 30 days</MenuItem>
              <MenuItem value={90}>Last 90 days</MenuItem>
            </Select>
          </FormControl>
          
          <Button
            variant="outlined"
            startIcon={loading ? <LinearProgress /> : <Assessment />}
            onClick={getFleetInsights}
            disabled={loading}
          >
            {loading ? 'Analyzing...' : 'Fleet Analysis'}
          </Button>
        </Box>
      </Box>

      {/* Overall Metrics Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <Shield />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.totalAgents}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Agents
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: getSafetyScoreColor(overallMetrics.avgSafetyScore) === 'success' ? 'success.main' : 'warning.main' }}>
                  <Security />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.avgSafetyScore.toFixed(1)}%</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Safety Score
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <Assessment />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.totalTests.toLocaleString()}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Tests
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: overallMetrics.criticalIssues > 10 ? 'error.main' : 'warning.main' }}>
                  <Warning />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.criticalIssues}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Critical Issues
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircle />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.productionAgents}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    In Production
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={2}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar sx={{ bgcolor: 'error.main' }}>
                  <Error />
                </Avatar>
                <Box>
                  <Typography variant="h4">{overallMetrics.suspendedAgents}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Suspended
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} mb={4}>
        {/* Safety Score Trend */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Safety Score Trends" />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={[70, 100]} />
                  <RechartsTooltip />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="safetyScore" 
                    stroke="#4CAF50" 
                    strokeWidth={3}
                    name="Safety Score (%)"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Risk Distribution */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Risk Distribution" />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={mockRiskDistribution}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="count"
                    label={({ percentage }) => `${percentage}%`}
                  >
                    {mockRiskDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box mt={2}>
                {mockRiskDistribution.map((item, index) => (
                  <Box key={index} display="flex" alignItems="center" gap={1} mb={1}>
                    <Box 
                      width={12} 
                      height={12} 
                      bgcolor={item.color} 
                      borderRadius="50%" 
                    />
                    <Typography variant="caption">
                      {item.category}: {item.count}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Agent Details Table */}
      <Card>
        <CardHeader 
          title="Agent Performance Details"
          action={
            <IconButton onClick={() => window.location.reload()}>
              <Refresh />
            </IconButton>
          }
        />
        <CardContent>
          <Grid container spacing={2}>
            {mockAgentMetrics.map((agent) => (
              <Grid item xs={12} md={6} lg={4} key={agent.agentId}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        {agent.icon}
                      </Avatar>
                      <Box flex={1}>
                        <Typography variant="subtitle1" fontWeight={600}>
                          {agent.agentName}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {agent.industry}
                        </Typography>
                      </Box>
                      <Chip 
                        label={agent.deploymentStatus}
                        color={getStatusColor(agent.deploymentStatus)}
                        size="small"
                      />
                    </Box>

                    <Stack spacing={2}>
                      {/* Safety Score */}
                      <Box>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                          <Typography variant="body2">Safety Score</Typography>
                          <Box display="flex" alignItems="center" gap={1}>
                            {getTrendIcon(agent.riskTrend)}
                            <Typography variant="h6" color={getSafetyScoreColor(agent.safetyScore)}>
                              {agent.safetyScore}%
                            </Typography>
                          </Box>
                        </Box>
                        <LinearProgress 
                          variant="determinate" 
                          value={agent.safetyScore} 
                          color={getSafetyScoreColor(agent.safetyScore)}
                        />
                      </Box>

                      {/* Metrics */}
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Tests: {agent.totalTests.toLocaleString()} • 
                          Issues: {agent.criticalIssues} • 
                          Response: {agent.avgResponseTime}s
                        </Typography>
                      </Box>

                      {/* Last Tested */}
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          Last tested: {agent.lastTested}
                        </Typography>
                      </Box>

                      {/* Critical Issues Alert */}
                      {agent.criticalIssues > 5 && (
                        <Alert severity="warning" size="small">
                          <Typography variant="caption">
                            {agent.criticalIssues} critical issues require attention
                          </Typography>
                        </Alert>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Fleet Insights */}
      {insights && (
        <Card sx={{ mt: 3 }}>
          <CardHeader 
            title="Fleet Intelligence Analysis"
            avatar={<Assessment color="primary" />}
          />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Fleet Overview:
                </Typography>
                <Typography variant="body2" paragraph>
                  {insights.fleetOverview}
                </Typography>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Critical Issues:
                </Typography>
                <List dense>
                  {insights.criticalIssues.map((issue: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <Warning color="error" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={issue} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
