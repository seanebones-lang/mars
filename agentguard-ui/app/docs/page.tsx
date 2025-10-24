'use client';

import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardHeader,
  TextField,
  Button,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Divider,
  Tabs,
  Tab,
  Stack,
  Badge,
  Avatar,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Breadcrumbs,
  Link as MuiLink,
  Drawer,
  ListItemButton,
  Collapse
} from '@mui/material';
import {
  ApiOutlined,
  CodeOutlined,
  PlayArrowOutlined,
  ContentCopyOutlined,
  ExpandMoreOutlined,
  ExpandLessOutlined,
  SecurityOutlined,
  SpeedOutlined,
  IntegrationInstructionsOutlined,
  WebhookOutlined,
  KeyOutlined,
  HttpOutlined,
  DataObjectOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  WarningOutlined,
  InfoOutlined,
  MenuBookOutlined,
  LaunchOutlined,
  DownloadOutlined,
  SearchOutlined,
  FilterListOutlined,
  BookmarkOutlined,
  NavigateNextOutlined
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';

interface APIEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  path: string;
  summary: string;
  description: string;
  parameters?: Parameter[];
  requestBody?: RequestBody;
  responses: Response[];
  tags: string[];
  authentication?: boolean;
  rateLimit?: string;
}

interface Parameter {
  name: string;
  in: 'query' | 'path' | 'header' | 'body';
  type: string;
  required: boolean;
  description: string;
  example?: any;
}

interface RequestBody {
  contentType: string;
  schema: any;
  example: any;
}

interface Response {
  status: number;
  description: string;
  schema?: any;
  example?: any;
}

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
      id={`docs-tabpanel-${index}`}
      aria-labelledby={`docs-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

export default function DocsPage() {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [selectedEndpoint, setSelectedEndpoint] = useState<APIEndpoint | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState('all');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedSections, setExpandedSections] = useState<string[]>(['core']);

  // Mock API endpoints data
  const apiEndpoints: APIEndpoint[] = [
    {
      method: 'POST',
      path: '/api/v1/test-agent',
      summary: 'Test Agent Output',
      description: 'Analyze agent output for hallucinations and reliability issues',
      tags: ['core', 'testing'],
      authentication: true,
      rateLimit: '100 requests/minute',
      parameters: [
        {
          name: 'X-API-Key',
          in: 'header',
          type: 'string',
          required: true,
          description: 'Your API authentication key',
          example: 'watcher_api_key_...'
        }
      ],
      requestBody: {
        contentType: 'application/json',
        schema: {
          type: 'object',
          properties: {
            agent_output: { type: 'string', description: 'The agent response to analyze' },
            ground_truth: { type: 'string', description: 'Expected correct response (optional)' },
            context: { type: 'string', description: 'Additional context for analysis' }
          },
          required: ['agent_output']
        },
        example: {
          agent_output: "The capital of France is Paris, which has a population of 12 million people.",
          ground_truth: "The capital of France is Paris.",
          context: "Geography question about European capitals"
        }
      },
      responses: [
        {
          status: 200,
          description: 'Analysis completed successfully',
          example: {
            flagged: true,
            confidence: 0.85,
            reasoning: "Population figure appears inflated - Paris metropolitan area is ~12M but city proper is ~2.1M",
            categories: ["factual_error"],
            processing_time_ms: 245
          }
        },
        {
          status: 400,
          description: 'Invalid request parameters',
          example: { error: "agent_output is required" }
        },
        {
          status: 429,
          description: 'Rate limit exceeded',
          example: { error: "Rate limit exceeded. Try again in 60 seconds." }
        }
      ]
    },
    {
      method: 'GET',
      path: '/api/v1/batch/{batch_id}',
      summary: 'Get Batch Job Status',
      description: 'Retrieve the status and results of a batch processing job',
      tags: ['batch', 'monitoring'],
      authentication: true,
      rateLimit: '1000 requests/minute',
      parameters: [
        {
          name: 'batch_id',
          in: 'path',
          type: 'string',
          required: true,
          description: 'Unique identifier for the batch job',
          example: 'batch_abc123'
        }
      ],
      responses: [
        {
          status: 200,
          description: 'Batch job information retrieved successfully',
          example: {
            batch_id: "batch_abc123",
            status: "completed",
            total_items: 1000,
            processed_items: 1000,
            flagged_items: 127,
            created_at: "2025-10-24T10:30:00Z",
            completed_at: "2025-10-24T10:45:30Z"
          }
        }
      ]
    },
    {
      method: 'POST',
      path: '/api/v1/webhooks',
      summary: 'Create Webhook',
      description: 'Register a webhook endpoint for real-time notifications',
      tags: ['webhooks', 'integrations'],
      authentication: true,
      rateLimit: '10 requests/minute',
      requestBody: {
        contentType: 'application/json',
        schema: {
          type: 'object',
          properties: {
            url: { type: 'string', description: 'Webhook endpoint URL' },
            events: { type: 'array', items: { type: 'string' }, description: 'Events to subscribe to' },
            secret: { type: 'string', description: 'Secret for webhook signature verification' }
          },
          required: ['url', 'events']
        },
        example: {
          url: "https://your-app.com/webhooks/watcher",
          events: ["detection.completed", "batch.finished"],
          secret: "your-webhook-secret"
        }
      },
      responses: [
        {
          status: 201,
          description: 'Webhook created successfully',
          example: {
            webhook_id: "webhook_xyz789",
            url: "https://your-app.com/webhooks/watcher",
            events: ["detection.completed", "batch.finished"],
            created_at: "2025-10-24T10:30:00Z"
          }
        }
      ]
    },
    {
      method: 'GET',
      path: '/api/v1/analytics/overview',
      summary: 'Get Analytics Overview',
      description: 'Retrieve comprehensive analytics and performance metrics',
      tags: ['analytics', 'monitoring'],
      authentication: true,
      rateLimit: '100 requests/minute',
      parameters: [
        {
          name: 'start_date',
          in: 'query',
          type: 'string',
          required: false,
          description: 'Start date for analytics period (ISO 8601)',
          example: '2025-10-01T00:00:00Z'
        },
        {
          name: 'end_date',
          in: 'query',
          type: 'string',
          required: false,
          description: 'End date for analytics period (ISO 8601)',
          example: '2025-10-24T23:59:59Z'
        }
      ],
      responses: [
        {
          status: 200,
          description: 'Analytics data retrieved successfully',
          example: {
            total_requests: 15420,
            flagged_requests: 2184,
            avg_confidence: 0.73,
            avg_processing_time_ms: 187,
            top_categories: ["factual_error", "hallucination", "bias"]
          }
        }
      ]
    }
  ];

  // Get unique tags
  const allTags = ['all', ...Array.from(new Set(apiEndpoints.flatMap(endpoint => endpoint.tags)))];

  // Filter endpoints
  const filteredEndpoints = apiEndpoints.filter(endpoint => {
    const matchesSearch = endpoint.path.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         endpoint.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         endpoint.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTag = selectedTag === 'all' || endpoint.tags.includes(selectedTag);
    return matchesSearch && matchesTag;
  });

  const getMethodColor = (method: string) => {
    switch (method) {
      case 'GET': return 'success';
      case 'POST': return 'primary';
      case 'PUT': return 'warning';
      case 'DELETE': return 'error';
      case 'PATCH': return 'info';
      default: return 'default';
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => 
      prev.includes(section) 
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const sidebarContent = (
    <Box sx={{ width: 280, p: 2 }}>
      <Typography variant="h6" gutterBottom>
        API Documentation
      </Typography>
      
      <List>
        <ListItemButton onClick={() => toggleSection('quickstart')}>
          <ListItemIcon>
            <PlayArrowOutlined />
          </ListItemIcon>
          <ListItemText primary="Quick Start" />
          {expandedSections.includes('quickstart') ? <ExpandLessOutlined /> : <ExpandMoreOutlined />}
        </ListItemButton>
        <Collapse in={expandedSections.includes('quickstart')}>
          <List component="div" disablePadding>
            <ListItemButton sx={{ pl: 4 }} onClick={() => setTabValue(0)}>
              <ListItemText primary="Getting Started" />
            </ListItemButton>
            <ListItemButton sx={{ pl: 4 }} onClick={() => setTabValue(1)}>
              <ListItemText primary="Authentication" />
            </ListItemButton>
          </List>
        </Collapse>

        <ListItemButton onClick={() => toggleSection('endpoints')}>
          <ListItemIcon>
            <ApiOutlined />
          </ListItemIcon>
          <ListItemText primary="API Endpoints" />
          {expandedSections.includes('endpoints') ? <ExpandLessOutlined /> : <ExpandMoreOutlined />}
        </ListItemButton>
        <Collapse in={expandedSections.includes('endpoints')}>
          <List component="div" disablePadding>
            {allTags.slice(1).map(tag => (
              <ListItemButton 
                key={tag} 
                sx={{ pl: 4 }} 
                onClick={() => {
                  setSelectedTag(tag);
                  setTabValue(2);
                }}
              >
                <ListItemText primary={tag.charAt(0).toUpperCase() + tag.slice(1)} />
              </ListItemButton>
            ))}
          </List>
        </Collapse>

        <ListItemButton onClick={() => setTabValue(3)}>
          <ListItemIcon>
            <CodeOutlined />
          </ListItemIcon>
          <ListItemText primary="SDKs & Examples" />
        </ListItemButton>

        <ListItemButton onClick={() => setTabValue(4)}>
          <ListItemIcon>
            <SecurityOutlined />
          </ListItemIcon>
          <ListItemText primary="Rate Limits" />
        </ListItemButton>
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: 280,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
            position: 'relative',
            height: 'auto',
            border: 'none',
            borderRight: 1,
            borderColor: 'divider'
          },
        }}
      >
        {sidebarContent}
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Container maxWidth="xl">
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Box>
              <Typography variant="h3" component="h1" gutterBottom fontWeight={600}>
                API Documentation
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Complete REST API reference for Watcher AI hallucination detection platform
              </Typography>
            </Box>
            
            <Box display="flex" gap={2}>
              <Button
                variant="outlined"
                startIcon={<DownloadOutlined />}
                href="/api/openapi.json"
                target="_blank"
              >
                OpenAPI Spec
              </Button>
              <Button
                variant="contained"
                startIcon={<LaunchOutlined />}
                component={Link}
                href="/sdk"
              >
                Python SDK
              </Button>
            </Box>
          </Box>

          {/* Breadcrumbs */}
          <Breadcrumbs sx={{ mb: 3 }}>
            <MuiLink component={Link} href="/" color="inherit">
              Dashboard
            </MuiLink>
            <Typography color="text.primary">API Documentation</Typography>
          </Breadcrumbs>

          {/* Main Content Tabs */}
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                <Tab label="Getting Started" icon={<PlayArrowOutlined />} />
                <Tab label="Authentication" icon={<KeyOutlined />} />
                <Tab label="API Reference" icon={<ApiOutlined />} />
                <Tab label="SDKs & Examples" icon={<CodeOutlined />} />
                <Tab label="Rate Limits" icon={<SpeedOutlined />} />
              </Tabs>
            </Box>

            {/* Getting Started Tab */}
            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={4}>
                <Grid size={{ xs: 12, md: 8 }}>
                  <Stack spacing={4}>
                    <Box>
                      <Typography variant="h4" gutterBottom>
                        Welcome to Watcher AI API
                      </Typography>
                      <Typography variant="body1" paragraph>
                        The Watcher AI API provides powerful hallucination detection capabilities for AI agents and language models. 
                        Our REST API allows you to integrate real-time and batch analysis into your applications with enterprise-grade reliability.
                      </Typography>
                    </Box>

                    <Alert severity="info">
                      <Typography variant="body2">
                        <strong>Base URL:</strong> <code>https://api.watcher.mothership-ai.com/v1</code>
                      </Typography>
                    </Alert>

                    <Box>
                      <Typography variant="h5" gutterBottom>
                        Quick Example
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                        <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`curl -X POST "https://api.watcher.mothership-ai.com/v1/test-agent" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_output": "The Eiffel Tower is 324 meters tall and was built in 1889.",
    "context": "Architecture and history question"
  }'`}
                        </Typography>
                        <Box display="flex" justifyContent="flex-end" mt={1}>
                          <IconButton 
                            size="small" 
                            onClick={() => copyToClipboard(`curl -X POST "https://api.watcher.mothership-ai.com/v1/test-agent" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_output": "The Eiffel Tower is 324 meters tall and was built in 1889.",
    "context": "Architecture and history question"
  }'`)}
                          >
                            <ContentCopyOutlined />
                          </IconButton>
                        </Box>
                      </Paper>
                    </Box>

                    <Box>
                      <Typography variant="h5" gutterBottom>
                        Response Format
                      </Typography>
                      <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                        <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`{
  "flagged": false,
  "confidence": 0.92,
  "reasoning": "Information appears accurate based on known facts",
  "categories": [],
  "processing_time_ms": 187
}`}
                        </Typography>
                      </Paper>
                    </Box>
                  </Stack>
                </Grid>

                <Grid size={{ xs: 12, md: 4 }}>
                  <Stack spacing={3}>
                    <Card variant="outlined">
                      <CardHeader title="Key Features" />
                      <CardContent>
                        <List dense>
                          <ListItem>
                            <ListItemIcon>
                              <CheckCircleOutlined color="success" />
                            </ListItemIcon>
                            <ListItemText primary="Real-time analysis" secondary="Sub-second response times" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <CheckCircleOutlined color="success" />
                            </ListItemIcon>
                            <ListItemText primary="Batch processing" secondary="Handle thousands of requests" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <CheckCircleOutlined color="success" />
                            </ListItemIcon>
                            <ListItemText primary="Webhook notifications" secondary="Real-time event streaming" />
                          </ListItem>
                          <ListItem>
                            <ListItemIcon>
                              <CheckCircleOutlined color="success" />
                            </ListItemIcon>
                            <ListItemText primary="Enterprise security" secondary="SOC 2 compliant" />
                          </ListItem>
                        </List>
                      </CardContent>
                    </Card>

                    <Card variant="outlined">
                      <CardHeader title="Need Help?" />
                      <CardContent>
                        <Stack spacing={2}>
                          <Button variant="outlined" fullWidth startIcon={<MenuBookOutlined />}>
                            View Examples
                          </Button>
                          <Button variant="outlined" fullWidth startIcon={<CodeOutlined />}>
                            Python SDK
                          </Button>
                          <Button variant="outlined" fullWidth startIcon={<LaunchOutlined />}>
                            Support Portal
                          </Button>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Stack>
                </Grid>
              </Grid>
            </TabPanel>

            {/* Authentication Tab */}
            <TabPanel value={tabValue} index={1}>
              <Stack spacing={4}>
                <Box>
                  <Typography variant="h4" gutterBottom>
                    Authentication
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Watcher AI uses API keys for authentication. Include your API key in the <code>X-API-Key</code> header with every request.
                  </Typography>
                </Box>

                <Alert severity="warning">
                  <Typography variant="body2">
                    <strong>Keep your API key secure!</strong> Never expose it in client-side code or public repositories.
                  </Typography>
                </Alert>

                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card variant="outlined">
                      <CardHeader title="Getting Your API Key" />
                      <CardContent>
                        <Stack spacing={2}>
                          <Typography variant="body2">
                            1. Sign up for a Watcher AI account
                          </Typography>
                          <Typography variant="body2">
                            2. Navigate to Settings → API Keys
                          </Typography>
                          <Typography variant="body2">
                            3. Click "Generate New Key"
                          </Typography>
                          <Typography variant="body2">
                            4. Copy and securely store your key
                          </Typography>
                          <Button variant="contained" startIcon={<KeyOutlined />}>
                            Generate API Key
                          </Button>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>

                  <Grid size={{ xs: 12, md: 6 }}>
                    <Card variant="outlined">
                      <CardHeader title="Authentication Example" />
                      <CardContent>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                          <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`# Using cURL
curl -H "X-API-Key: watcher_api_key_..." \\
     https://api.watcher.mothership-ai.com/v1/test-agent

# Using Python requests
import requests

headers = {
    'X-API-Key': 'watcher_api_key_...',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://api.watcher.mothership-ai.com/v1/test-agent',
    headers=headers,
    json={'agent_output': 'Your text here'}
)`}
                          </Typography>
                        </Paper>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Stack>
            </TabPanel>

            {/* API Reference Tab */}
            <TabPanel value={tabValue} index={2}>
              <Box display="flex" gap={2} mb={3} alignItems="center">
                <TextField
                  placeholder="Search endpoints..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchOutlined sx={{ mr: 1, color: 'text.secondary' }} />
                  }}
                  size="small"
                  sx={{ minWidth: 300 }}
                />
                
                <Stack direction="row" spacing={1}>
                  {allTags.map(tag => (
                    <Chip
                      key={tag}
                      label={tag.charAt(0).toUpperCase() + tag.slice(1)}
                      onClick={() => setSelectedTag(tag)}
                      color={selectedTag === tag ? 'primary' : 'default'}
                      variant={selectedTag === tag ? 'filled' : 'outlined'}
                      size="small"
                    />
                  ))}
                </Stack>
              </Box>

              <Stack spacing={3}>
                <AnimatePresence>
                  {filteredEndpoints.map((endpoint, index) => (
                    <motion.div
                      key={endpoint.path + endpoint.method}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.2, delay: index * 0.05 }}
                    >
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreOutlined />}>
                          <Box display="flex" alignItems="center" gap={2} width="100%">
                            <Chip
                              label={endpoint.method}
                              color={getMethodColor(endpoint.method) as any}
                              size="small"
                              sx={{ minWidth: 60, fontWeight: 'bold' }}
                            />
                            <Typography variant="body1" fontFamily="monospace" sx={{ flex: 1 }}>
                              {endpoint.path}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {endpoint.summary}
                            </Typography>
                            {endpoint.authentication && (
                              <Tooltip title="Requires authentication">
                                <KeyOutlined color="warning" fontSize="small" />
                              </Tooltip>
                            )}
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Stack spacing={3}>
                            <Typography variant="body2">
                              {endpoint.description}
                            </Typography>

                            {endpoint.parameters && endpoint.parameters.length > 0 && (
                              <Box>
                                <Typography variant="h6" gutterBottom>Parameters</Typography>
                                <TableContainer component={Paper} variant="outlined">
                                  <Table size="small">
                                    <TableHead>
                                      <TableRow>
                                        <TableCell>Name</TableCell>
                                        <TableCell>Type</TableCell>
                                        <TableCell>Required</TableCell>
                                        <TableCell>Description</TableCell>
                                      </TableRow>
                                    </TableHead>
                                    <TableBody>
                                      {endpoint.parameters.map((param, idx) => (
                                        <TableRow key={idx}>
                                          <TableCell>
                                            <Typography variant="body2" fontFamily="monospace">
                                              {param.name}
                                            </Typography>
                                          </TableCell>
                                          <TableCell>
                                            <Chip label={param.type} size="small" variant="outlined" />
                                          </TableCell>
                                          <TableCell>
                                            <Chip 
                                              label={param.required ? 'Required' : 'Optional'} 
                                              color={param.required ? 'error' : 'default'}
                                              size="small" 
                                              variant="outlined" 
                                            />
                                          </TableCell>
                                          <TableCell>
                                            <Typography variant="body2">
                                              {param.description}
                                            </Typography>
                                          </TableCell>
                                        </TableRow>
                                      ))}
                                    </TableBody>
                                  </Table>
                                </TableContainer>
                              </Box>
                            )}

                            {endpoint.requestBody && (
                              <Box>
                                <Typography variant="h6" gutterBottom>Request Body</Typography>
                                <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                                  <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
                                    {JSON.stringify(endpoint.requestBody?.example, null, 2)}
                                  </Typography>
                                  <Box display="flex" justifyContent="flex-end" mt={1}>
                                    <IconButton 
                                      size="small" 
                                      onClick={() => copyToClipboard(JSON.stringify(endpoint.requestBody?.example, null, 2))}
                                    >
                                      <ContentCopyOutlined />
                                    </IconButton>
                                  </Box>
                                </Paper>
                              </Box>
                            )}

                            <Box>
                              <Typography variant="h6" gutterBottom>Responses</Typography>
                              <Stack spacing={2}>
                                {endpoint.responses.map((response, idx) => (
                                  <Box key={idx}>
                                    <Box display="flex" alignItems="center" gap={2} mb={1}>
                                      <Chip
                                        label={response.status}
                                        color={response.status < 300 ? 'success' : response.status < 400 ? 'info' : 'error'}
                                        size="small"
                                      />
                                      <Typography variant="body2">
                                        {response.description}
                                      </Typography>
                                    </Box>
                                    {response.example && (
                                      <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                                        <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
                                          {JSON.stringify(response.example, null, 2)}
                                        </Typography>
                                        <Box display="flex" justifyContent="flex-end" mt={1}>
                                          <IconButton 
                                            size="small" 
                                            onClick={() => copyToClipboard(JSON.stringify(response.example, null, 2))}
                                          >
                                            <ContentCopyOutlined />
                                          </IconButton>
                                        </Box>
                                      </Paper>
                                    )}
                                  </Box>
                                ))}
                              </Stack>
                            </Box>

                            {endpoint.rateLimit && (
                              <Alert severity="info">
                                <Typography variant="body2">
                                  <strong>Rate Limit:</strong> {endpoint.rateLimit}
                                </Typography>
                              </Alert>
                            )}
                          </Stack>
                        </AccordionDetails>
                      </Accordion>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </Stack>
            </TabPanel>

            {/* SDKs & Examples Tab */}
            <TabPanel value={tabValue} index={3}>
              <Grid container spacing={4}>
                <Grid size={{ xs: 12, md: 6 }}>
                  <Card variant="outlined">
                    <CardHeader title="Python SDK" />
                    <CardContent>
                      <Stack spacing={2}>
                        <Typography variant="body2">
                          Official Python SDK with full API coverage and type hints.
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                          <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`pip install watcher-ai

from watcher_ai import WatcherClient

client = WatcherClient(api_key="your_key")
result = client.test_agent(
    agent_output="Your text here",
    context="Optional context"
)
print(f"Flagged: {result.flagged}")
print(f"Confidence: {result.confidence}")`}
                          </Typography>
                        </Paper>
                        <Button variant="contained" component={Link} href="/sdk">
                          View Python SDK Docs
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid size={{ xs: 12, md: 6 }}>
                  <Card variant="outlined">
                    <CardHeader title="JavaScript/Node.js" />
                    <CardContent>
                      <Stack spacing={2}>
                        <Typography variant="body2">
                          JavaScript SDK for browser and Node.js applications.
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                          <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`npm install @watcher-ai/sdk

import { WatcherClient } from '@watcher-ai/sdk';

const client = new WatcherClient({
  apiKey: 'your_key'
});

const result = await client.testAgent({
  agentOutput: 'Your text here',
  context: 'Optional context'
});

console.log('Flagged:', result.flagged);`}
                          </Typography>
                        </Paper>
                        <Button variant="outlined" disabled>
                          Coming Soon
                        </Button>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </TabPanel>

            {/* Rate Limits Tab */}
            <TabPanel value={tabValue} index={4}>
              <Stack spacing={4}>
                <Box>
                  <Typography variant="h4" gutterBottom>
                    Rate Limits
                  </Typography>
                  <Typography variant="body1" paragraph>
                    Watcher AI implements rate limiting to ensure fair usage and optimal performance for all users.
                  </Typography>
                </Box>

                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 8 }}>
                    <TableContainer component={Paper} variant="outlined">
                      <Table>
                        <TableHead>
                          <TableRow>
                            <TableCell>Plan</TableCell>
                            <TableCell>Requests per Minute</TableCell>
                            <TableCell>Requests per Day</TableCell>
                            <TableCell>Concurrent Requests</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>
                              <Chip label="Free" color="default" size="small" />
                            </TableCell>
                            <TableCell>10</TableCell>
                            <TableCell>1,000</TableCell>
                            <TableCell>2</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>
                              <Chip label="Pro" color="primary" size="small" />
                            </TableCell>
                            <TableCell>100</TableCell>
                            <TableCell>50,000</TableCell>
                            <TableCell>10</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>
                              <Chip label="Enterprise" color="success" size="small" />
                            </TableCell>
                            <TableCell>1,000</TableCell>
                            <TableCell>Unlimited</TableCell>
                            <TableCell>50</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>

                  <Grid size={{ xs: 12, md: 4 }}>
                    <Card variant="outlined">
                      <CardHeader title="Rate Limit Headers" />
                      <CardContent>
                        <Typography variant="body2" paragraph>
                          Every API response includes rate limit information:
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50' }}>
                          <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333' }}>
{`X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1635724800`}
                          </Typography>
                        </Paper>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Alert severity="info">
                  <Typography variant="body2">
                    <strong>Need higher limits?</strong> Contact our sales team for custom enterprise plans with dedicated resources.
                  </Typography>
                </Alert>
              </Stack>
            </TabPanel>
          </Card>
        </Container>
      </Box>
    </Box>
  );
}
