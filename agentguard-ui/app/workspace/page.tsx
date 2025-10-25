'use client';

import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Tabs,
  Tab,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Folder as FolderIcon,
  Star as StarIcon,
  Settings as SettingsIcon,
  Key as KeyIcon,
  Add as AddIcon,
  TrendingUp,
  Speed,
  CheckCircle,
  Warning,
  Refresh,
  Code,
  Rocket,
  Psychology,
  Group,
} from '@mui/icons-material';

interface Project {
  project_id: string;
  name: string;
  description: string;
  status: string;
  tags: string[];
  test_count: number;
  agent_count: number;
  created_at: string;
  updated_at: string;
}

interface DashboardStats {
  total_projects: number;
  total_tests: number;
  total_agents: number;
  total_favorites: number;
  queries_this_month: number;
  queries_limit: number;
  avg_accuracy: number;
  avg_latency_ms: number;
}

interface APIKey {
  key_id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
}

export default function WorkspacePage() {
  const [activeTab, setActiveTab] = useState(0);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [createProjectOpen, setCreateProjectOpen] = useState(false);
  const [createKeyOpen, setCreateKeyOpen] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '', tags: '' });
  const [newKey, setNewKey] = useState({ name: '', description: '' });

  useEffect(() => {
    loadWorkspaceData();
  }, []);

  const loadWorkspaceData = async () => {
    try {
      setLoading(true);
      
      // In production, fetch from API with authentication
      // For now, use mock data
      const mockStats: DashboardStats = {
        total_projects: 3,
        total_tests: 127,
        total_agents: 8,
        total_favorites: 12,
        queries_this_month: 450,
        queries_limit: 1000,
        avg_accuracy: 0.94,
        avg_latency_ms: 85,
      };

      const mockProjects: Project[] = [
        {
          project_id: 'proj_1',
          name: 'Healthcare Chatbot',
          description: 'Medical Q&A agent with HIPAA compliance',
          status: 'active',
          tags: ['healthcare', 'production'],
          test_count: 45,
          agent_count: 3,
          created_at: '2025-10-15T10:00:00Z',
          updated_at: '2025-10-24T15:30:00Z',
        },
        {
          project_id: 'proj_2',
          name: 'Customer Support AI',
          description: 'Multi-turn conversation agent',
          status: 'active',
          tags: ['support', 'staging'],
          test_count: 62,
          agent_count: 2,
          created_at: '2025-10-10T09:00:00Z',
          updated_at: '2025-10-23T14:20:00Z',
        },
        {
          project_id: 'proj_3',
          name: 'RAG Pipeline Test',
          description: 'Document retrieval and generation',
          status: 'active',
          tags: ['rag', 'experimental'],
          test_count: 20,
          agent_count: 3,
          created_at: '2025-10-20T11:00:00Z',
          updated_at: '2025-10-24T16:45:00Z',
        },
      ];

      const mockApiKeys: APIKey[] = [
        {
          key_id: 'key_1',
          name: 'Production API Key',
          key_prefix: 'ag_live_abc',
          scopes: ['read', 'write'],
          is_active: true,
          created_at: '2025-10-01T10:00:00Z',
          last_used_at: '2025-10-24T12:30:00Z',
        },
        {
          key_id: 'key_2',
          name: 'Development Key',
          key_prefix: 'ag_test_xyz',
          scopes: ['read'],
          is_active: true,
          created_at: '2025-10-15T14:00:00Z',
          last_used_at: '2025-10-23T09:15:00Z',
        },
      ];

      setStats(mockStats);
      setProjects(mockProjects);
      setApiKeys(mockApiKeys);
    } catch (error) {
      console.error('Error loading workspace:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = () => {
    // In production, POST to /workspace/projects
    console.log('Creating project:', newProject);
    setCreateProjectOpen(false);
    setNewProject({ name: '', description: '', tags: '' });
    loadWorkspaceData();
  };

  const handleCreateKey = () => {
    // In production, POST to /workspace/api-keys
    console.log('Creating API key:', newKey);
    setCreateKeyOpen(false);
    setNewKey({ name: '', description: '' });
    loadWorkspaceData();
  };

  const renderDashboard = () => (
    <Grid container spacing={3}>
      {/* Stats Cards */}
      <Grid item xs={12} md={3}>
        <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" fontWeight="bold">{stats?.total_projects || 0}</Typography>
                <Typography variant="body2">Active Projects</Typography>
              </Box>
              <FolderIcon sx={{ fontSize: 48, opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', color: 'white' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" fontWeight="bold">{stats?.total_tests || 0}</Typography>
                <Typography variant="body2">Total Tests</Typography>
              </Box>
              <CheckCircle sx={{ fontSize: 48, opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: 'white' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" fontWeight="bold">{stats?.total_agents || 0}</Typography>
                <Typography variant="body2">Agents Monitored</Typography>
              </Box>
              <Psychology sx={{ fontSize: 48, opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={3}>
        <Card sx={{ background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', color: 'white' }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography variant="h4" fontWeight="bold">{(stats?.avg_accuracy || 0) * 100}%</Typography>
                <Typography variant="body2">Avg Accuracy</Typography>
              </Box>
              <TrendingUp sx={{ fontSize: 48, opacity: 0.8 }} />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Usage Progress */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Monthly Usage</Typography>
              <Chip 
                label={`${stats?.queries_this_month || 0} / ${stats?.queries_limit || 0} queries`}
                color="primary"
              />
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={((stats?.queries_this_month || 0) / (stats?.queries_limit || 1)) * 100}
              sx={{ height: 10, borderRadius: 5 }}
            />
            <Box display="flex" justifyContent="space-between" mt={1}>
              <Typography variant="caption" color="text.secondary">
                {((stats?.queries_this_month || 0) / (stats?.queries_limit || 1) * 100).toFixed(1)}% used
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {(stats?.queries_limit || 0) - (stats?.queries_this_month || 0)} remaining
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12}>
        <Card>
          <CardHeader title="Quick Actions" />
          <CardContent>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<AddIcon />}
                  onClick={() => setCreateProjectOpen(true)}
                  sx={{ py: 2 }}
                >
                  New Project
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Rocket />}
                  sx={{ py: 2 }}
                >
                  Deploy Agent
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Code />}
                  sx={{ py: 2 }}
                >
                  View Docs
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<Group />}
                  sx={{ py: 2 }}
                >
                  Join Community
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Projects */}
      <Grid item xs={12}>
        <Card>
          <CardHeader 
            title="Recent Projects" 
            action={
              <Button size="small" onClick={() => setActiveTab(1)}>View All</Button>
            }
          />
          <CardContent>
            <List>
              {projects.slice(0, 3).map((project, index) => (
                <React.Fragment key={project.project_id}>
                  {index > 0 && <Divider />}
                  <ListItem>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: 'primary.main' }}>
                        <FolderIcon />
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={project.name}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            {project.description}
                          </Typography>
                          <Box display="flex" gap={1} mt={1}>
                            {project.tags.map((tag) => (
                              <Chip key={tag} label={tag} size="small" />
                            ))}
                          </Box>
                        </Box>
                      }
                    />
                    <Box textAlign="right">
                      <Typography variant="body2" color="text.secondary">
                        {project.test_count} tests
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {project.agent_count} agents
                      </Typography>
                    </Box>
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderProjects = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">My Projects</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateProjectOpen(true)}
        >
          New Project
        </Button>
      </Box>

      <Grid container spacing={3}>
        {projects.map((project) => (
          <Grid item xs={12} md={6} lg={4} key={project.project_id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardHeader
                title={project.name}
                subheader={new Date(project.updated_at).toLocaleDateString()}
                action={
                  <IconButton size="small">
                    <StarIcon />
                  </IconButton>
                }
              />
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  {project.description}
                </Typography>
                <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                  {project.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" />
                  ))}
                </Box>
                <Divider sx={{ my: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Tests</Typography>
                    <Typography variant="h6">{project.test_count}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Agents</Typography>
                    <Typography variant="h6">{project.agent_count}</Typography>
                  </Grid>
                </Grid>
              </CardContent>
              <Box p={2} pt={0}>
                <Button fullWidth variant="outlined">Open Project</Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderAPIKeys = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">API Keys</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateKeyOpen(true)}
        >
          Create API Key
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        API keys are used to authenticate requests to the AgentGuard API. Keep them secure and never share them publicly.
      </Alert>

      <Grid container spacing={3}>
        {apiKeys.map((key) => (
          <Grid item xs={12} key={key.key_id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="start">
                  <Box>
                    <Typography variant="h6">{key.name}</Typography>
                    <Typography variant="body2" color="text.secondary" fontFamily="monospace" mt={1}>
                      {key.key_prefix}•••••••••••••
                    </Typography>
                    <Box display="flex" gap={1} mt={2}>
                      {key.scopes.map((scope) => (
                        <Chip key={scope} label={scope} size="small" />
                      ))}
                    </Box>
                  </Box>
                  <Box textAlign="right">
                    <Chip 
                      label={key.is_active ? 'Active' : 'Inactive'}
                      color={key.is_active ? 'success' : 'default'}
                      size="small"
                    />
                    <Typography variant="caption" display="block" mt={1} color="text.secondary">
                      Created: {new Date(key.created_at).toLocaleDateString()}
                    </Typography>
                    {key.last_used_at && (
                      <Typography variant="caption" display="block" color="text.secondary">
                        Last used: {new Date(key.last_used_at).toLocaleDateString()}
                      </Typography>
                    )}
                  </Box>
                </Box>
                <Box display="flex" gap={1} mt={2}>
                  <Button size="small" color="error">Revoke</Button>
                  <Button size="small">View Details</Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
          <Box textAlign="center">
            <Typography variant="h6" gutterBottom>Loading your workspace...</Typography>
            <LinearProgress sx={{ width: 200, mx: 'auto', mt: 2 }} />
          </Box>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Box mb={4}>
        <Typography variant="h3" component="h1" gutterBottom fontWeight={700}>
          My Workspace
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your AI agents, projects, and integrations
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 4 }}>
        <Tabs value={activeTab} onChange={(_, v) => setActiveTab(v)}>
          <Tab icon={<DashboardIcon />} label="Dashboard" iconPosition="start" />
          <Tab icon={<FolderIcon />} label="Projects" iconPosition="start" />
          <Tab icon={<KeyIcon />} label="API Keys" iconPosition="start" />
          <Tab icon={<StarIcon />} label="Favorites" iconPosition="start" />
          <Tab icon={<SettingsIcon />} label="Settings" iconPosition="start" />
        </Tabs>
      </Box>

      {activeTab === 0 && renderDashboard()}
      {activeTab === 1 && renderProjects()}
      {activeTab === 2 && renderAPIKeys()}
      {activeTab === 3 && (
        <Alert severity="info">Favorites feature coming soon!</Alert>
      )}
      {activeTab === 4 && (
        <Alert severity="info">Settings feature coming soon!</Alert>
      )}

      {/* Create Project Dialog */}
      <Dialog open={createProjectOpen} onClose={() => setCreateProjectOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Project</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Project Name"
            value={newProject.name}
            onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description"
            value={newProject.description}
            onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
            margin="normal"
            multiline
            rows={3}
          />
          <TextField
            fullWidth
            label="Tags (comma-separated)"
            value={newProject.tags}
            onChange={(e) => setNewProject({ ...newProject, tags: e.target.value })}
            margin="normal"
            placeholder="production, healthcare, experimental"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateProjectOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateProject} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* Create API Key Dialog */}
      <Dialog open={createKeyOpen} onClose={() => setCreateKeyOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create API Key</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            The API key will only be shown once. Make sure to copy and store it securely.
          </Alert>
          <TextField
            fullWidth
            label="Key Name"
            value={newKey.name}
            onChange={(e) => setNewKey({ ...newKey, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Description (optional)"
            value={newKey.description}
            onChange={(e) => setNewKey({ ...newKey, description: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateKeyOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateKey} variant="contained">Create Key</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}

