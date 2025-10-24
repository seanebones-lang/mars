'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Button,
  IconButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CardHeader,
  Avatar,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Analytics,
  Timeline,
  Pattern,
  Speed,
  Security,
  Warning,
  CheckCircle,
  Error,
  Info,
  AutoAwesome,
  Psychology,
  Lightbulb,
  Assessment,
  Refresh
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
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { motion } from 'framer-motion';
import { getAnalyticsOverview, getTimeSeriesData, getHallucinationPatterns, AnalyticsOverview } from '@/lib/analyticsApi';
import { agentGuardApi } from '@/lib/api';

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
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const COLORS = ['#1976D2', '#00BCD4', '#4CAF50', '#FF9800', '#F44336', '#9C27B0', '#607D8B'];

const RISK_COLORS = {
  low: '#4CAF50',
  medium: '#FF9800',
  high: '#F44336'
};

export default function AnalyticsPage() {
  const [tabValue, setTabValue] = useState(0);
  const [timeRange, setTimeRange] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsOverview | null>(null);
  const [claudeInsights, setClaudeInsights] = useState<any>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [showInsights, setShowInsights] = useState(false);

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await getAnalyticsOverview(timeRange);
      setAnalyticsData(data);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setError('Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Claude Insights Functions
  const getClaudeInsights = async () => {
    if (!analyticsData) return;
    
    setInsightsLoading(true);
    try {
      const insights = await agentGuardApi.getAnalyticsInsights({
        totalTests: analyticsData.agent_metrics?.total_responses || 0,
        avgRiskScore: analyticsData.agent_metrics?.avg_hallucination_risk || 0,
        accuracy: ((analyticsData.agent_metrics?.total_responses - analyticsData.agent_metrics?.flagged_responses) / analyticsData.agent_metrics?.total_responses * 100) || 0,
        processingVolume: analyticsData.agent_metrics?.total_responses || 0,
        falsePositiveRate: 3.2, // Mock false positive rate
        avgLatency: analyticsData.agent_metrics?.avg_processing_time || 0,
        highRiskDetections: analyticsData.agent_metrics?.flagged_responses || 0,
        costPerDetection: 0.05, // Mock cost data
        userSatisfaction: 87, // Mock satisfaction data
        uptime: 99.8 // Mock uptime data
      });
      setClaudeInsights(insights);
      setShowInsights(true);
    } catch (err) {
      console.error('Failed to get Claude insights:', err);
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleRefreshInsights = async () => {
    setClaudeInsights(null);
    await getClaudeInsights();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatRisk = (risk: number) => (risk * 100).toFixed(1) + '%';
  const formatTime = (time: number) => time.toFixed(0) + 'ms';

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      </Container>
    );
  }

  if (!analyticsData) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Alert severity="info">
          No analytics data available. Start monitoring agents to see insights.
        </Alert>
      </Container>
    );
  }

  const { agent_metrics, hallucination_patterns, time_series, summary } = analyticsData;

  // Prepare chart data
  const timeSeriesChartData = time_series.map(item => ({
    ...item,
    risk_percentage: item.avg_hallucination_risk * 100,
    flagged_rate: (item.flagged_responses / item.total_responses) * 100
  }));

  const patternChartData = hallucination_patterns.map((pattern, index) => ({
    ...pattern,
    color: COLORS[index % COLORS.length]
  }));

  const riskDistribution = [
    { name: 'Low Risk (0-30%)', value: time_series.filter(d => d.avg_hallucination_risk <= 0.3).length, color: RISK_COLORS.low },
    { name: 'Medium Risk (30-70%)', value: time_series.filter(d => d.avg_hallucination_risk > 0.3 && d.avg_hallucination_risk <= 0.7).length, color: RISK_COLORS.medium },
    { name: 'High Risk (70%+)', value: time_series.filter(d => d.avg_hallucination_risk > 0.7).length, color: RISK_COLORS.high }
  ];

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
          <Box>
            <Typography variant="h4" component="h1" gutterBottom>
              Analytics Dashboard
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Claude-Powered Business Intelligence & Insights
            </Typography>
          </Box>
          
          <Box display="flex" gap={2} alignItems="center">
            <Button
              variant="outlined"
              startIcon={<AutoAwesome />}
              onClick={getClaudeInsights}
              disabled={insightsLoading || !analyticsData}
              sx={{ 
                borderColor: 'primary.main',
                color: 'primary.main',
                '&:hover': {
                  borderColor: 'primary.dark',
                  backgroundColor: 'primary.light'
                }
              }}
            >
              {insightsLoading ? 'Analyzing...' : 'Claude Insights'}
            </Button>
            
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
          </Box>
        </Box>

        {/* Summary Cards */}
        <Grid container spacing={3} mb={4}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Analytics color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Responses</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {agent_metrics.total_responses.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Across {summary.total_agents || 'multiple'} agents
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Security color="error" sx={{ mr: 1 }} />
                  <Typography variant="h6">Avg Risk</Typography>
                </Box>
                <Typography variant="h4" color="error">
                  {formatRisk(agent_metrics.avg_hallucination_risk)}
                </Typography>
                <Box display="flex" alignItems="center" mt={1}>
                  {agent_metrics.trend === 'improving' ? (
                    <TrendingDown color="success" fontSize="small" />
                  ) : (
                    <TrendingUp color="error" fontSize="small" />
                  )}
                  <Typography variant="body2" color="text.secondary" ml={0.5}>
                    {agent_metrics.trend}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Warning color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Flagged</Typography>
                </Box>
                <Typography variant="h4" color="warning">
                  {agent_metrics.flagged_responses}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {((agent_metrics.flagged_responses / agent_metrics.total_responses) * 100).toFixed(1)}% of total
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Speed color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Avg Speed</Typography>
                </Box>
                <Typography variant="h4" color="info">
                  {formatTime(agent_metrics.avg_processing_time)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Processing time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper sx={{ mb: 3 }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="analytics tabs">
            <Tab label="Trends" />
            <Tab label="Patterns" />
            <Tab label="Distribution" />
            <Tab label="Performance" />
          </Tabs>
        </Paper>

        {/* Tab Panels */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Hallucination Risk Trends
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={timeSeriesChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip 
                        formatter={(value: any, name: string) => [
                          name === 'risk_percentage' ? `${value.toFixed(1)}%` : value,
                          name === 'risk_percentage' ? 'Risk Level' : name
                        ]}
                      />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="risk_percentage" 
                        stroke="#F44336" 
                        strokeWidth={3}
                        name="Risk Level (%)"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="total_responses" 
                        stroke="#1976D2" 
                        strokeWidth={2}
                        name="Total Responses"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Response Volume & Flagged Rate
                  </Typography>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={timeSeriesChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="total_responses" 
                        stackId="1"
                        stroke="#1976D2" 
                        fill="#1976D2"
                        fillOpacity={0.6}
                        name="Total Responses"
                      />
                      <Area 
                        type="monotone" 
                        dataKey="flagged_responses" 
                        stackId="2"
                        stroke="#F44336" 
                        fill="#F44336"
                        fillOpacity={0.8}
                        name="Flagged Responses"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 8 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Top Hallucination Patterns
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={patternChartData} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="pattern" type="category" width={150} />
                      <Tooltip />
                      <Bar dataKey="frequency" fill="#1976D2">
                        {patternChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Pattern Details
                  </Typography>
                  <List>
                    {hallucination_patterns.slice(0, 10).map((pattern, index) => (
                      <React.Fragment key={pattern.pattern}>
                        <ListItem>
                          <ListItemIcon>
                            {pattern.severity === 'high' ? (
                              <Error color="error" />
                            ) : pattern.severity === 'medium' ? (
                              <Warning color="warning" />
                            ) : (
                              <Info color="info" />
                            )}
                          </ListItemIcon>
                          <ListItemText
                            primary={pattern.pattern}
                            secondary={
                              <Box>
                                <Typography variant="body2">
                                  Frequency: {pattern.frequency}
                                </Typography>
                                <Chip 
                                  label={pattern.severity} 
                                  size="small" 
                                  color={
                                    pattern.severity === 'high' ? 'error' :
                                    pattern.severity === 'medium' ? 'warning' : 'info'
                                  }
                                  sx={{ mt: 0.5 }}
                                />
                              </Box>
                            }
                          />
                        </ListItem>
                        {index < hallucination_patterns.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Risk Level Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <PieChart>
                      <Pie
                        data={riskDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, value, percent }: any) => `${name}: ${value} (${((percent as number) * 100).toFixed(0)}%)`}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {riskDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Time Distribution
                  </Typography>
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={timeSeriesChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`${value}ms`, 'Processing Time']} />
                      <Bar dataKey="avg_processing_time" fill="#00BCD4" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid size={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System Performance Metrics
                  </Typography>
                  <Grid container spacing={3}>
                    <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                      <Box textAlign="center" p={2}>
                        <CheckCircle color="success" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="h4" color="success">
                          {((agent_metrics.total_responses - agent_metrics.flagged_responses) / agent_metrics.total_responses * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2">
                          Accuracy Rate
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                      <Box textAlign="center" p={2}>
                        <Speed color="primary" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="h4" color="primary">
                          {(agent_metrics.total_responses / timeRange).toFixed(1)}
                        </Typography>
                        <Typography variant="body2">
                          Responses/Day
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                      <Box textAlign="center" p={2}>
                        <Timeline color="info" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="h4" color="info">
                          {formatTime(agent_metrics.avg_processing_time)}
                        </Typography>
                        <Typography variant="body2">
                          Avg Response Time
                        </Typography>
                      </Box>
                    </Grid>
                    
                    <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                      <Box textAlign="center" p={2}>
                        <Pattern color="secondary" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="h4" color="secondary">
                          {summary.total_patterns}
                        </Typography>
                        <Typography variant="body2">
                          Known Patterns
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Claude Insights Section */}
        {showInsights && (
          <Box mt={4}>
            <Card elevation={3}>
              <CardHeader
                title={
                  <Box display="flex" alignItems="center" gap={2}>
                    <AutoAwesome color="primary" />
                    <Typography variant="h6">
                      Claude Business Intelligence
                    </Typography>
                    <Chip label="AI Powered" color="primary" size="small" />
                  </Box>
                }
                action={
                  <IconButton 
                    onClick={handleRefreshInsights} 
                    disabled={insightsLoading}
                    title="Refresh Insights"
                  >
                    <Refresh />
                  </IconButton>
                }
              />
              <CardContent>
                {insightsLoading && (
                  <Box sx={{ mb: 3, textAlign: 'center' }}>
                    <LinearProgress />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Claude is analyzing your analytics data for business insights...
                    </Typography>
                  </Box>
                )}

                {claudeInsights && (
                  <Grid container spacing={3}>
                    {/* Business Impact */}
                    <Grid size={12}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Business Impact Analysis" 
                          avatar={<Assessment color="primary" />}
                        />
                        <CardContent>
                          <Typography variant="body2" gutterBottom>
                            {claudeInsights.businessImpact}
                          </Typography>
                          <Box sx={{ mt: 2 }}>
                            <Chip 
                              label={claudeInsights.riskAssessment} 
                              color={claudeInsights.riskAssessment.includes('Low') ? 'success' : 
                                     claudeInsights.riskAssessment.includes('Medium') ? 'warning' : 'error'}
                              size="small"
                            />
                          </Box>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Trend Analysis */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Trend Analysis" 
                          avatar={<Psychology color="primary" />}
                        />
                        <CardContent>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {claudeInsights.trendAnalysis}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Performance Insights */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Performance Insights" 
                          avatar={<TrendingUp color="success" />}
                        />
                        <CardContent>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {claudeInsights.performanceInsights}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Key Findings */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Key Findings" 
                          avatar={<Lightbulb color="warning" />}
                        />
                        <CardContent>
                          <List dense>
                            {claudeInsights.keyFindings.map((finding: string, index: number) => (
                              <ListItem key={index}>
                                <ListItemIcon>
                                  <Info color="primary" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText primary={finding} />
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Recommendations */}
                    <Grid size={{ xs: 12, md: 6 }}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Strategic Recommendations" 
                          avatar={<CheckCircle color="success" />}
                        />
                        <CardContent>
                          <List dense>
                            {claudeInsights.recommendations.map((rec: string, index: number) => (
                              <ListItem key={index}>
                                <ListItemIcon>
                                  <Lightbulb color="primary" fontSize="small" />
                                </ListItemIcon>
                                <ListItemText primary={rec} />
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>

                    {/* Optimization Opportunities */}
                    <Grid size={12}>
                      <Accordion>
                        <AccordionSummary expandIcon={<TrendingUp />}>
                          <Box display="flex" alignItems="center" gap={2}>
                            <AutoAwesome color="secondary" />
                            <Typography variant="subtitle1" fontWeight={600}>
                              Optimization Opportunities & Action Items
                            </Typography>
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Grid container spacing={2}>
                            <Grid size={{ xs: 12, md: 6 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Optimization Opportunities:
                              </Typography>
                              <List dense>
                                {claudeInsights.optimizationOpportunities.map((opp: string, index: number) => (
                                  <ListItem key={index}>
                                    <ListItemIcon>
                                      <TrendingUp color="success" fontSize="small" />
                                    </ListItemIcon>
                                    <ListItemText primary={opp} />
                                  </ListItem>
                                ))}
                              </List>
                            </Grid>
                            <Grid size={{ xs: 12, md: 6 }}>
                              <Typography variant="subtitle2" gutterBottom>
                                Immediate Action Items:
                              </Typography>
                              <List dense>
                                {claudeInsights.actionItems.map((action: string, index: number) => (
                                  <ListItem key={index}>
                                    <ListItemIcon>
                                      <CheckCircle color="primary" fontSize="small" />
                                    </ListItemIcon>
                                    <ListItemText primary={action} />
                                  </ListItem>
                                ))}
                              </List>
                            </Grid>
                          </Grid>
                        </AccordionDetails>
                      </Accordion>
                    </Grid>

                    {/* Forecast Insights */}
                    <Grid size={12}>
                      <Card variant="outlined">
                        <CardHeader 
                          title="Forecast & Predictive Analysis" 
                          avatar={<Timeline color="info" />}
                        />
                        <CardContent>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {claudeInsights.forecastInsights}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Box>
        )}

        {!showInsights && !insightsLoading && analyticsData && (
          <Box mt={4} textAlign="center">
            <Card elevation={1} sx={{ py: 4 }}>
              <CardContent>
                <AutoAwesome sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Claude Business Intelligence
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Get AI-powered insights, trend analysis, and strategic recommendations for your analytics data
                </Typography>
                <Button 
                  variant="contained" 
                  size="large"
                  startIcon={<Psychology />}
                  onClick={getClaudeInsights}
                >
                  Generate Business Insights
                </Button>
              </CardContent>
            </Card>
          </Box>
        )}
      </motion.div>
    </Container>
  );
}
