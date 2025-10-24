'use client';

import React from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Tabs,
  Tab,
  Button,
  Chip,
  Divider,
  Alert,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Link as MuiLink,
  useTheme
} from '@mui/material';
import {
  Code,
  Download,
  CheckCircle,
  Speed,
  Security,
  ExtensionOutlined,
  CloudDownload,
  GitHub,
  Description
} from '@mui/icons-material';
import { motion } from 'framer-motion';

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
      id={`sdk-tabpanel-${index}`}
      aria-labelledby={`sdk-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function SDKPage() {
  const [tabValue, setTabValue] = React.useState(0);
  const theme = useTheme();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const features = [
    { icon: <Speed />, title: 'High Performance', description: 'Async operations with <100ms latency' },
    { icon: <Security />, title: 'Enterprise Security', description: 'JWT authentication & role-based access' },
    { icon: <ExtensionOutlined />, title: 'Easy ExtensionOutlined', description: 'One-line hallucination detection' },
    { icon: <CheckCircle />, title: 'Type Safety', description: 'Full TypeScript support & validation' }
  ];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography variant="h3" fontWeight={700} gutterBottom>
            Python SDK
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
            Enterprise-grade hallucination detection for your AI systems
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mb: 3 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<Download />}
              sx={{ px: 4 }}
            >
              Install SDK
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<GitHub />}
              sx={{ px: 4 }}
            >
              View on GitHub
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Chip label="v1.0.0" color="primary" />
            <Chip label="Python 3.8+" variant="outlined" />
            <Chip label="Async Support" variant="outlined" />
            <Chip label="Type Hints" variant="outlined" />
          </Box>
        </Box>

        {/* Features Grid */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          {features.map((feature, index) => (
             <Grid size={{ xs: 12, sm: 6, md: 3 }} key={index}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card sx={{ height: '100%', textAlign: 'center' }}>
                  <CardContent>
                    <Box sx={{ color: 'primary.main', mb: 2 }}>
                      {feature.icon}
                    </Box>
                    <Typography variant="h6" fontWeight={600} gutterBottom>
                      {feature.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {feature.description}
                    </Typography>
                  </CardContent>
                </Card>
              </motion.div>
            </Grid>
          ))}
        </Grid>

        {/* Quick Start Alert */}
        <Alert severity="info" sx={{ mb: 4 }}>
          <Typography variant="body2">
            <strong>Quick Start:</strong> Install with <code>pip install watcher-ai-sdk</code> and get started in minutes!
          </Typography>
        </Alert>

        {/* Code Examples Tabs */}
        <Card>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Quick Start" />
              <Tab label="Async Usage" />
              <Tab label="Batch Processing" />
              <Tab label="Custom Rules" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <Typography variant="h6" gutterBottom>
              Basic Usage
            </Typography>
            <Paper sx={{ 
              p: 2, 
              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
              mb: 2,
              overflow: 'auto',
              border: '1px solid',
              borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
            }}>
              <pre style={{
                fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
              }}>{`# Install the SDK
pip install watcher-ai-sdk

# Basic usage
from watcher_ai_sdk import WatcherClient

client = WatcherClient(api_key="your-api-key")

# Detect hallucinations
result = client.detect_hallucination("AI agent output text")

if result.is_hallucination:
    print(f"Risk Level: {result.risk_level}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Recommendations: {result.recommendations}")
`}</pre>
            </Paper>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Typography variant="h6" gutterBottom>
              Async Operations
            </Typography>
            <Paper sx={{ 
              p: 2, 
              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
              mb: 2,
              overflow: 'auto',
              border: '1px solid',
              borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
            }}>
              <pre style={{
                fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
              }}>{`import asyncio
from watcher_ai_sdk import AsyncWatcherClient

async def main():
    client = AsyncWatcherClient(api_key="your-api-key")
    
    # Async detection
    result = await client.detect_hallucination("AI output")
    
    # Batch async processing
    texts = ["text1", "text2", "text3"]
    results = await client.detect_batch(texts)
    
    for result in results:
        print(f"Risk: {result.hallucination_risk:.2f}")

asyncio.run(main())
`}</pre>
            </Paper>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" gutterBottom>
              Batch Processing
            </Typography>
            <Paper sx={{ 
              p: 2, 
              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
              mb: 2,
              overflow: 'auto',
              border: '1px solid',
              borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
            }}>
              <pre style={{
                fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
              }}>{`from watcher_ai_sdk import WatcherClient, BatchItem

client = WatcherClient(api_key="your-api-key")

# Prepare batch items
items = [
    BatchItem(id="1", text="First AI output"),
    BatchItem(id="2", text="Second AI output", ground_truth="Expected output"),
    BatchItem(id="3", text="Third AI output")
]

# Submit batch job
job = client.submit_batch(items)
print(f"Job ID: {job.job_id}")

# Monitor progress
while not job.is_complete:
    job = client.get_batch_status(job.job_id)
    print(f"Progress: {job.progress_percentage:.1f}%")
    time.sleep(5)

# Get results
results = client.get_batch_results(job.job_id)
`}</pre>
            </Paper>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" gutterBottom>
              Custom Rules ExtensionOutlined
            </Typography>
            <Paper sx={{ 
              p: 2, 
              bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
              mb: 2,
              overflow: 'auto',
              border: '1px solid',
              borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
            }}>
              <pre style={{
                fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                margin: 0,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
              }}>{`from watcher_ai_sdk import WatcherClient, CustomRule, RuleType, RuleCategory

client = WatcherClient(api_key="your-api-key")

# Create custom rule
rule = CustomRule(
    rule_id="medical_claims",
    name="Medical Claims Detection",
    description="Flags unverified medical claims",
    rule_type=RuleType.PATTERN_MATCH,
    category=RuleCategory.HEALTHCARE,
    pattern=r"\\b(cures?|treats?|prevents?)\\s+(cancer|diabetes)\\b"
)

# Add rule to system
client.add_custom_rule(rule)

# Enhanced detection with custom rules
result = client.detect_enhanced(
    text="This supplement cures cancer",
    apply_custom_rules=True
)

print(f"Custom violations: {len(result.custom_violations)}")
`}</pre>
            </Paper>
          </TabPanel>
        </Card>

        {/* Installation & Setup */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Installation & Setup
          </Typography>
          
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <CloudDownload sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Install via pip
                  </Typography>
                  <Paper sx={{ 
                    p: 2, 
                    bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                    border: '1px solid',
                    borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
                  }}>
                    <code style={{
                      fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                      fontSize: '0.875rem',
                      color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
                    }}>pip install watcher-ai-sdk</code>
                  </Paper>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    <Security sx={{ mr: 1, verticalAlign: 'middle' }} />
                    Authentication
                  </Typography>
                  <Paper sx={{ 
                    p: 2, 
                    bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
                    border: '1px solid',
                    borderColor: theme.palette.mode === 'dark' ? 'grey.700' : 'grey.200'
                  }}>
                    <code style={{
                      fontFamily: 'Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
                      fontSize: '0.875rem',
                      color: theme.palette.mode === 'dark' ? '#e0e0e0' : '#333333'
                    }}>export WATCHER_API_KEY="your-key"</code>
                  </Paper>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* API Reference */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Key Features
          </Typography>
          
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="One-line hallucination detection"
                secondary="Simple API for immediate integration"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Async/await support"
                secondary="High-performance async operations for scalable applications"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Batch processing"
                secondary="Efficient bulk analysis with progress tracking"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Custom rules integration"
                secondary="Industry-specific detection patterns and thresholds"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Enterprise authentication"
                secondary="JWT-based auth with role-based access control"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="success" />
              </ListItemIcon>
              <ListItemText
                primary="Full type hints"
                secondary="Complete TypeScript-style type safety for Python"
              />
            </ListItem>
          </List>
        </Box>

        {/* Links */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="h6" gutterBottom>
            Resources
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button variant="outlined" startIcon={<Description />}>
              API Documentation
            </Button>
            <Button variant="outlined" startIcon={<GitHub />}>
              GitHub Repository
            </Button>
            <Button variant="outlined" startIcon={<Code />}>
              Example Projects
            </Button>
          </Box>
        </Box>
      </motion.div>
    </Container>
  );
}
