'use client';

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
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
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Stack,
  Badge
} from '@mui/material';
import {
  TuneOutlined,
  AddOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayArrowOutlined,
  PauseOutlined,
  ExpandMoreOutlined,
  SecurityOutlined,
  BusinessOutlined,
  LocalHospitalOutlined,
  AccountBalanceOutlined,
  SchoolOutlined,
  FactoryOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ErrorOutlined,
  InfoOutlined,
  CodeOutlined,
  SaveOutlined,
  CancelOutlined,
  VisibilityOutlined,
  ContentCopyOutlined,
  UploadOutlined,
  DownloadOutlined
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '@/lib/store';
import toast from 'react-hot-toast';

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
      id={`custom-rules-tabpanel-${index}`}
      aria-labelledby={`custom-rules-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

interface CustomRule {
  id: string;
  name: string;
  description: string;
  industry: string;
  category: 'hallucination' | 'bias' | 'safety' | 'compliance' | 'quality';
  severity: 'low' | 'medium' | 'high' | 'critical';
  pattern: string;
  regex_pattern?: string;
  keywords: string[];
  enabled: boolean;
  created_at: string;
  updated_at: string;
  usage_count: number;
  accuracy: number;
  false_positive_rate: number;
}

const INDUSTRY_CONFIGS = {
  healthcare: {
    name: 'Healthcare',
    icon: <LocalHospitalOutlined />,
    color: '#E53E3E',
    description: 'Medical compliance and safety rules'
  },
  finance: {
    name: 'Financial Services',
    icon: <AccountBalanceOutlined />,
    color: '#38A169',
    description: 'Financial regulations and compliance'
  },
  education: {
    name: 'Education',
    icon: <SchoolOutlined />,
    color: '#3182CE',
    description: 'Educational content and safety standards'
  },
  manufacturing: {
    name: 'Manufacturing',
    icon: <FactoryOutlined />,
    color: '#D69E2E',
    description: 'Industrial safety and operational rules'
  },
  technology: {
    name: 'Technology',
    icon: <BusinessOutlined />,
    color: '#805AD5',
    description: 'Tech industry specific guidelines'
  },
  general: {
    name: 'General',
    icon: <SecurityOutlined />,
    color: '#718096',
    description: 'Universal detection rules'
  }
};

const CATEGORY_CONFIGS = {
  hallucination: { name: 'Hallucination', color: '#E53E3E', icon: <ErrorOutlined /> },
  bias: { name: 'Bias Detection', color: '#D69E2E', icon: <WarningOutlined /> },
  safety: { name: 'Safety', color: '#38A169', icon: <SecurityOutlined /> },
  compliance: { name: 'Compliance', color: '#3182CE', icon: <CheckCircleOutlined /> },
  quality: { name: 'Quality', color: '#805AD5', icon: <InfoOutlined /> }
};

const SEVERITY_CONFIGS = {
  low: { name: 'Low', color: '#38A169' },
  medium: { name: 'Medium', color: '#D69E2E' },
  high: { name: 'High', color: '#E53E3E' },
  critical: { name: 'Critical', color: '#9B2C2C' }
};

export default function CustomRulesPage() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState<CustomRule[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingRule, setEditingRule] = useState<CustomRule | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    industry: 'general',
    category: 'hallucination' as CustomRule['category'],
    severity: 'medium' as CustomRule['severity'],
    pattern: '',
    regex_pattern: '',
    keywords: [] as string[],
    enabled: true
  });
  const [keywordInput, setKeywordInput] = useState('');
  
  const { apiUrl } = useStore();

  useEffect(() => {
    loadCustomRules();
  }, []);

  const loadCustomRules = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration - in production this would come from the backend
      const mockRules: CustomRule[] = [
        {
          id: '1',
          name: 'Medical Dosage Validation',
          description: 'Prevents AI from providing specific medical dosage recommendations',
          industry: 'healthcare',
          category: 'safety',
          severity: 'critical',
          pattern: 'Detects when AI provides specific drug dosages without proper disclaimers',
          regex_pattern: '\\b\\d+\\s*(mg|ml|tablets?)\\b(?!.*consult.*doctor)',
          keywords: ['dosage', 'medication', 'prescription', 'mg', 'ml', 'tablets'],
          enabled: true,
          created_at: '2025-01-15T10:00:00Z',
          updated_at: '2025-01-20T14:30:00Z',
          usage_count: 1247,
          accuracy: 94.2,
          false_positive_rate: 2.1
        },
        {
          id: '2',
          name: 'Financial Advice Disclaimer',
          description: 'Ensures financial recommendations include proper disclaimers',
          industry: 'finance',
          category: 'compliance',
          severity: 'high',
          pattern: 'Flags financial advice without regulatory disclaimers',
          regex_pattern: '\\b(invest|buy|sell|stock|portfolio)\\b(?!.*not financial advice)',
          keywords: ['investment', 'financial advice', 'stock', 'portfolio', 'trading'],
          enabled: true,
          created_at: '2025-01-10T09:15:00Z',
          updated_at: '2025-01-18T16:45:00Z',
          usage_count: 892,
          accuracy: 91.8,
          false_positive_rate: 3.4
        },
        {
          id: '3',
          name: 'Bias in Hiring Language',
          description: 'Detects potentially biased language in recruitment contexts',
          industry: 'general',
          category: 'bias',
          severity: 'medium',
          pattern: 'Identifies language that may introduce hiring bias',
          regex_pattern: '\\b(young|energetic|native speaker|culture fit)\\b',
          keywords: ['hiring', 'recruitment', 'candidate', 'cultural fit', 'young'],
          enabled: true,
          created_at: '2025-01-12T11:20:00Z',
          updated_at: '2025-01-19T13:10:00Z',
          usage_count: 456,
          accuracy: 87.5,
          false_positive_rate: 5.2
        },
        {
          id: '4',
          name: 'Manufacturing Safety Protocols',
          description: 'Ensures safety protocols are mentioned in manufacturing guidance',
          industry: 'manufacturing',
          category: 'safety',
          severity: 'high',
          pattern: 'Validates safety protocol mentions in manufacturing instructions',
          regex_pattern: '\\b(operate|machinery|equipment)\\b(?!.*(safety|PPE|protective))',
          keywords: ['machinery', 'equipment', 'safety', 'PPE', 'protocols'],
          enabled: false,
          created_at: '2025-01-08T08:30:00Z',
          updated_at: '2025-01-16T10:20:00Z',
          usage_count: 234,
          accuracy: 89.3,
          false_positive_rate: 4.1
        },
        {
          id: '5',
          name: 'Educational Content Accuracy',
          description: 'Validates educational content for factual accuracy',
          industry: 'education',
          category: 'quality',
          severity: 'medium',
          pattern: 'Checks educational content against known facts',
          keywords: ['education', 'learning', 'facts', 'history', 'science'],
          enabled: true,
          created_at: '2025-01-14T15:45:00Z',
          updated_at: '2025-01-21T09:30:00Z',
          usage_count: 678,
          accuracy: 92.1,
          false_positive_rate: 2.8
        }
      ];

      setRules(mockRules);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load custom rules:', error);
      toast.error('Failed to load custom rules');
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleCreateRule = () => {
    setEditingRule(null);
    setFormData({
      name: '',
      description: '',
      industry: 'general',
      category: 'hallucination',
      severity: 'medium',
      pattern: '',
      regex_pattern: '',
      keywords: [],
      enabled: true
    });
    setOpenDialog(true);
  };

  const handleEditRule = (rule: CustomRule) => {
    setEditingRule(rule);
    setFormData({
      name: rule.name,
      description: rule.description,
      industry: rule.industry,
      category: rule.category,
      severity: rule.severity,
      pattern: rule.pattern,
      regex_pattern: rule.regex_pattern || '',
      keywords: rule.keywords,
      enabled: rule.enabled
    });
    setOpenDialog(true);
  };

  const handleSaveRule = async () => {
    try {
      if (!formData.name || !formData.description || !formData.pattern) {
        toast.error('Please fill in all required fields');
        return;
      }

      const ruleData = {
        ...formData,
        id: editingRule?.id || Date.now().toString(),
        created_at: editingRule?.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
        usage_count: editingRule?.usage_count || 0,
        accuracy: editingRule?.accuracy || 0,
        false_positive_rate: editingRule?.false_positive_rate || 0
      };

      if (editingRule) {
        setRules(prev => prev.map(rule => rule.id === editingRule.id ? ruleData : rule));
        toast.success('Rule updated successfully');
      } else {
        setRules(prev => [...prev, ruleData]);
        toast.success('Rule created successfully');
      }

      setOpenDialog(false);
    } catch (error) {
      console.error('Failed to save rule:', error);
      toast.error('Failed to save rule');
    }
  };

  const handleDeleteRule = async (ruleId: string) => {
    try {
      setRules(prev => prev.filter(rule => rule.id !== ruleId));
      toast.success('Rule deleted successfully');
    } catch (error) {
      console.error('Failed to delete rule:', error);
      toast.error('Failed to delete rule');
    }
  };

  const handleToggleRule = async (ruleId: string, enabled: boolean) => {
    try {
      setRules(prev => prev.map(rule => 
        rule.id === ruleId ? { ...rule, enabled, updated_at: new Date().toISOString() } : rule
      ));
      toast.success(`Rule ${enabled ? 'enabled' : 'disabled'} successfully`);
    } catch (error) {
      console.error('Failed to toggle rule:', error);
      toast.error('Failed to toggle rule');
    }
  };

  const handleAddKeyword = () => {
    if (keywordInput.trim() && !formData.keywords.includes(keywordInput.trim())) {
      setFormData(prev => ({
        ...prev,
        keywords: [...prev.keywords, keywordInput.trim()]
      }));
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setFormData(prev => ({
      ...prev,
      keywords: prev.keywords.filter(k => k !== keyword)
    }));
  };

  const filteredRules = rules.filter(rule => {
    if (selectedIndustry !== 'all' && rule.industry !== selectedIndustry) return false;
    if (selectedCategory !== 'all' && rule.category !== selectedCategory) return false;
    return true;
  });

  const ruleStats = {
    total: rules.length,
    enabled: rules.filter(r => r.enabled).length,
    disabled: rules.filter(r => !r.enabled).length,
    byIndustry: Object.keys(INDUSTRY_CONFIGS).reduce((acc, industry) => {
      acc[industry] = rules.filter(r => r.industry === industry).length;
      return acc;
    }, {} as Record<string, number>),
    byCategory: Object.keys(CATEGORY_CONFIGS).reduce((acc, category) => {
      acc[category] = rules.filter(r => r.category === category).length;
      return acc;
    }, {} as Record<string, number>)
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

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
            <Typography variant="h3" fontWeight={700} gutterBottom>
              Custom Detection Rules
            </Typography>
            <Typography variant="h6" color="primary.main" fontWeight={600} gutterBottom>
              Industry-Specific AI Governance
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Configure specialized rules for your industry and use case
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <Button
              variant="outlined"
              startIcon={<UploadOutlined />}
              onClick={() => toast.success('Import functionality coming soon')}
            >
              Import Rules
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadOutlined />}
              onClick={() => toast.success('Export functionality coming soon')}
            >
              Export Rules
            </Button>
            <Button
              variant="contained"
              startIcon={<AddOutlined />}
              onClick={handleCreateRule}
              size="large"
            >
              Create Rule
            </Button>
          </Box>
        </Box>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TuneOutlined color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Rules</Typography>
                </Box>
                <Typography variant="h4" color="primary">
                  {ruleStats.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active detection rules
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <CheckCircleOutlined color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">Enabled</Typography>
                </Box>
                <Typography variant="h4" color="success">
                  {ruleStats.enabled}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Currently active
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <PauseOutlined color="warning" sx={{ mr: 1 }} />
                  <Typography variant="h6">Disabled</Typography>
                </Box>
                <Typography variant="h4" color="warning">
                  {ruleStats.disabled}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Temporarily inactive
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <BusinessOutlined color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">Industries</Typography>
                </Box>
                <Typography variant="h4" color="info">
                  {Object.keys(INDUSTRY_CONFIGS).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Supported sectors
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filter Rules
          </Typography>
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Industry</InputLabel>
                <Select
                  value={selectedIndustry}
                  label="Industry"
                  onChange={(e) => setSelectedIndustry(e.target.value)}
                >
                  <MenuItem value="all">All Industries</MenuItem>
                  {Object.entries(INDUSTRY_CONFIGS).map(([key, config]) => (
                    <MenuItem key={key} value={key}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {config.icon}
                        {config.name}
                        <Badge badgeContent={ruleStats.byIndustry[key]} color="primary" sx={{ ml: 1 }} />
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={selectedCategory}
                  label="Category"
                  onChange={(e) => setSelectedCategory(e.target.value)}
                >
                  <MenuItem value="all">All Categories</MenuItem>
                  {Object.entries(CATEGORY_CONFIGS).map(([key, config]) => (
                    <MenuItem key={key} value={key}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {config.icon}
                        {config.name}
                        <Badge badgeContent={ruleStats.byCategory[key]} color="primary" sx={{ ml: 1 }} />
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {/* Rules List */}
        <Paper>
          <List>
            <AnimatePresence>
              {filteredRules.map((rule, index) => (
                <motion.div
                  key={rule.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <ListItem sx={{ py: 2 }}>
                    <ListItemIcon>
                      <Box sx={{ color: INDUSTRY_CONFIGS[rule.industry as keyof typeof INDUSTRY_CONFIGS]?.color }}>
                        {INDUSTRY_CONFIGS[rule.industry as keyof typeof INDUSTRY_CONFIGS]?.icon}
                      </Box>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="h6">{rule.name}</Typography>
                          <Chip
                            label={INDUSTRY_CONFIGS[rule.industry as keyof typeof INDUSTRY_CONFIGS]?.name}
                            size="small"
                            sx={{ 
                              bgcolor: INDUSTRY_CONFIGS[rule.industry as keyof typeof INDUSTRY_CONFIGS]?.color + '20',
                              color: INDUSTRY_CONFIGS[rule.industry as keyof typeof INDUSTRY_CONFIGS]?.color
                            }}
                          />
                          <Chip
                            label={CATEGORY_CONFIGS[rule.category]?.name}
                            size="small"
                            sx={{ 
                              bgcolor: CATEGORY_CONFIGS[rule.category]?.color + '20',
                              color: CATEGORY_CONFIGS[rule.category]?.color
                            }}
                          />
                          <Chip
                            label={SEVERITY_CONFIGS[rule.severity]?.name}
                            size="small"
                            sx={{ 
                              bgcolor: SEVERITY_CONFIGS[rule.severity]?.color + '20',
                              color: SEVERITY_CONFIGS[rule.severity]?.color
                            }}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" sx={{ mb: 1 }}>
                            {rule.description}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            <Typography variant="caption" color="text.secondary">
                              Usage: {rule.usage_count.toLocaleString()}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Accuracy: {rule.accuracy.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              FP Rate: {rule.false_positive_rate.toFixed(1)}%
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Updated: {new Date(rule.updated_at).toLocaleDateString()}
                            </Typography>
                          </Box>
                          <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {rule.keywords.slice(0, 5).map((keyword) => (
                              <Chip
                                key={keyword}
                                label={keyword}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                            {rule.keywords.length > 5 && (
                              <Chip
                                label={`+${rule.keywords.length - 5} more`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={rule.enabled}
                              onChange={(e) => handleToggleRule(rule.id, e.target.checked)}
                              color="primary"
                            />
                          }
                          label=""
                        />
                        <Tooltip title="View Details">
                          <IconButton onClick={() => toast.success('View details functionality coming soon')}>
                            <VisibilityOutlined />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit Rule">
                          <IconButton onClick={() => handleEditRule(rule)}>
                            <EditOutlined />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Duplicate Rule">
                          <IconButton onClick={() => toast.success('Duplicate functionality coming soon')}>
                            <ContentCopyOutlined />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Rule">
                          <IconButton 
                            onClick={() => handleDeleteRule(rule.id)}
                            color="error"
                          >
                            <DeleteOutlined />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  {index < filteredRules.length - 1 && <Divider />}
                </motion.div>
              ))}
            </AnimatePresence>
          </List>

          {filteredRules.length === 0 && (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <TuneOutlined sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No rules found
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                {selectedIndustry !== 'all' || selectedCategory !== 'all' 
                  ? 'Try adjusting your filters or create a new rule'
                  : 'Get started by creating your first custom detection rule'
                }
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddOutlined />}
                onClick={handleCreateRule}
              >
                Create First Rule
              </Button>
            </Box>
          )}
        </Paper>

        {/* Create/Edit Rule Dialog */}
        <Dialog
          open={openDialog}
          onClose={() => setOpenDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TuneOutlined />
              {editingRule ? 'Edit Custom Rule' : 'Create Custom Rule'}
            </Box>
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Rule Name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  required
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth required>
                  <InputLabel>Industry</InputLabel>
                  <Select
                    value={formData.industry}
                    label="Industry"
                    onChange={(e) => setFormData(prev => ({ ...prev, industry: e.target.value }))}
                  >
                    {Object.entries(INDUSTRY_CONFIGS).map(([key, config]) => (
                      <MenuItem key={key} value={key}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {config.icon}
                          {config.name}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth required>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={formData.category}
                    label="Category"
                    onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value as CustomRule['category'] }))}
                  >
                    {Object.entries(CATEGORY_CONFIGS).map(([key, config]) => (
                      <MenuItem key={key} value={key}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {config.icon}
                          {config.name}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth required>
                  <InputLabel>Severity</InputLabel>
                  <Select
                    value={formData.severity}
                    label="Severity"
                    onChange={(e) => setFormData(prev => ({ ...prev, severity: e.target.value as CustomRule['severity'] }))}
                  >
                    {Object.entries(SEVERITY_CONFIGS).map(([key, config]) => (
                      <MenuItem key={key} value={key}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              bgcolor: config.color
                            }}
                          />
                          {config.name}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  multiline
                  rows={2}
                  required
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Detection Pattern"
                  value={formData.pattern}
                  onChange={(e) => setFormData(prev => ({ ...prev, pattern: e.target.value }))}
                  multiline
                  rows={3}
                  required
                  helperText="Describe what this rule should detect"
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth
                  label="Regex Pattern (Optional)"
                  value={formData.regex_pattern}
                  onChange={(e) => setFormData(prev => ({ ...prev, regex_pattern: e.target.value }))}
                  helperText="Advanced: Regular expression for pattern matching"
                  InputProps={{
                    startAdornment: <CodeOutlined sx={{ mr: 1, color: 'text.secondary' }} />
                  }}
                />
              </Grid>
              <Grid size={12}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Keywords
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    {formData.keywords.map((keyword) => (
                      <Chip
                        key={keyword}
                        label={keyword}
                        onDelete={() => handleRemoveKeyword(keyword)}
                        size="small"
                      />
                    ))}
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      size="small"
                      placeholder="Add keyword"
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                    />
                    <Button
                      variant="outlined"
                      onClick={handleAddKeyword}
                      disabled={!keywordInput.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                </Box>
              </Grid>
              <Grid size={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enabled}
                      onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    />
                  }
                  label="Enable rule immediately"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)} startIcon={<CancelOutlined />}>
              Cancel
            </Button>
            <Button 
              onClick={handleSaveRule} 
              variant="contained" 
              startIcon={<SaveOutlined />}
            >
              {editingRule ? 'Update Rule' : 'Create Rule'}
            </Button>
          </DialogActions>
        </Dialog>
      </motion.div>
    </Container>
  );
}
