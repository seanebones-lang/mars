'use client';

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Label,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Badge,
  Alert,
  AlertDescription,
  Progress,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  Switch,
} from '@/components/ui';
import { 
  Play, 
  Save, 
  Download, 
  Upload, 
  Settings, 
  Code, 
  Terminal, 
  FileText, 
  Shield, 
  Zap,
  GitBranch,
  Container,
  Webhook,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  Database,
  Globe
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'testing' | 'deployed' | 'archived';
  created_at: string;
  updated_at: string;
  safety_score: number;
  deployment_url?: string;
  webhook_url?: string;
}

interface AgentConfig {
  name: string;
  description: string;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  safety_rules: string[];
  deployment_settings: {
    auto_scale: boolean;
    max_instances: number;
    timeout_seconds: number;
    memory_limit: string;
  };
}

interface TestResult {
  id: string;
  timestamp: string;
  input: string;
  output: string;
  safety_score: number;
  issues: string[];
  passed: boolean;
}

export default function AgentConsole() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentConfig, setAgentConfig] = useState<AgentConfig>({
    name: '',
    description: '',
    model: 'claude-3-sonnet',
    temperature: 0.7,
    max_tokens: 1000,
    system_prompt: '',
    safety_rules: [],
    deployment_settings: {
      auto_scale: true,
      max_instances: 10,
      timeout_seconds: 30,
      memory_limit: '1GB'
    }
  });
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isTestingAgent, setIsTestingAgent] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [activeTab, setActiveTab] = useState('editor');
  const [showDeployDialog, setShowDeployDialog] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    // Mock data for demonstration
    const mockAgents: Agent[] = [
      {
        id: 'agent_1',
        name: 'Customer Support Bot',
        description: 'Handles customer inquiries with safety validation',
        status: 'deployed',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        safety_score: 0.94,
        deployment_url: 'https://api.example.com/agents/customer-support',
        webhook_url: 'https://api.example.com/webhooks/customer-support'
      },
      {
        id: 'agent_2',
        name: 'Content Moderator',
        description: 'Reviews and moderates user-generated content',
        status: 'testing',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        safety_score: 0.97
      },
      {
        id: 'agent_3',
        name: 'Financial Advisor',
        description: 'Provides financial guidance with compliance checks',
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        safety_score: 0.89
      }
    ];
    setAgents(mockAgents);
  };

  const createNewAgent = () => {
    const newAgent: Agent = {
      id: `agent_${Date.now()}`,
      name: 'New Agent',
      description: 'A new AI agent',
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      safety_score: 0.0
    };
    setAgents([...agents, newAgent]);
    setSelectedAgent(newAgent);
    setAgentConfig({
      name: newAgent.name,
      description: newAgent.description,
      model: 'claude-3-sonnet',
      temperature: 0.7,
      max_tokens: 1000,
      system_prompt: 'You are a helpful AI assistant. Always prioritize safety and accuracy in your responses.',
      safety_rules: ['No harmful content', 'Verify factual claims', 'Respect privacy'],
      deployment_settings: {
        auto_scale: true,
        max_instances: 10,
        timeout_seconds: 30,
        memory_limit: '1GB'
      }
    });
  };

  const saveAgent = async () => {
    if (!selectedAgent) return;

    // Update the agent with current config
    const updatedAgent = {
      ...selectedAgent,
      name: agentConfig.name,
      description: agentConfig.description,
      updated_at: new Date().toISOString()
    };

    setAgents(agents.map(a => a.id === selectedAgent.id ? updatedAgent : a));
    setSelectedAgent(updatedAgent);

    // Mock API call
    console.log('Saving agent configuration:', agentConfig);
  };

  const testAgent = async () => {
    if (!testInput.trim()) return;

    setIsTestingAgent(true);
    
    try {
      // Mock testing with safety validation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockOutput = `Based on your input "${testInput}", here's my response: This is a sample AI response that would be generated by your agent. The response has been validated for safety and accuracy.`;
      
      const testResult: TestResult = {
        id: `test_${Date.now()}`,
        timestamp: new Date().toISOString(),
        input: testInput,
        output: mockOutput,
        safety_score: Math.random() * 0.3 + 0.7, // Random score between 0.7-1.0
        issues: Math.random() > 0.8 ? ['Minor: Response could be more specific'] : [],
        passed: Math.random() > 0.2 // 80% pass rate
      };

      setTestResults([testResult, ...testResults]);
      setTestInput('');
    } catch (error) {
      console.error('Testing failed:', error);
    } finally {
      setIsTestingAgent(false);
    }
  };

  const deployAgent = async () => {
    if (!selectedAgent) return;

    // Mock deployment
    const deployedAgent = {
      ...selectedAgent,
      status: 'deployed' as const,
      deployment_url: `https://api.agentguard.com/agents/${selectedAgent.id}`,
      webhook_url: `https://api.agentguard.com/webhooks/${selectedAgent.id}`
    };

    setAgents(agents.map(a => a.id === selectedAgent.id ? deployedAgent : a));
    setSelectedAgent(deployedAgent);
    setShowDeployDialog(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'deployed': return 'bg-green-100 text-green-800';
      case 'testing': return 'bg-yellow-100 text-yellow-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'archived': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSafetyScoreColor = (score: number) => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Agent Console</h1>
        <p className="text-gray-600 mt-2">Create, test, and deploy AI agents with built-in safety validation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Agent List Sidebar */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                My Agents
                <Button onClick={createNewAgent} size="sm">
                  <Code className="h-4 w-4 mr-1" />
                  New
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedAgent?.id === agent.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedAgent(agent)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-sm">{agent.name}</h3>
                    <Badge className={getStatusColor(agent.status)}>
                      {agent.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{agent.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      Safety: <span className={getSafetyScoreColor(agent.safety_score)}>
                        {(agent.safety_score * 100).toFixed(0)}%
                      </span>
                    </span>
                    {agent.status === 'deployed' && (
                      <Globe className="h-3 w-3 text-green-600" />
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Main Console Area */}
        <div className="lg:col-span-3">
          {selectedAgent ? (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="editor" className="flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Editor
                </TabsTrigger>
                <TabsTrigger value="testing" className="flex items-center gap-2">
                  <Play className="h-4 w-4" />
                  Testing
                </TabsTrigger>
                <TabsTrigger value="safety" className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Safety
                </TabsTrigger>
                <TabsTrigger value="deployment" className="flex items-center gap-2">
                  <Container className="h-4 w-4" />
                  Deploy
                </TabsTrigger>
                <TabsTrigger value="monitoring" className="flex items-center gap-2">
                  <Eye className="h-4 w-4" />
                  Monitor
                </TabsTrigger>
              </TabsList>

              <TabsContent value="editor" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      Agent Configuration
                      <Button onClick={saveAgent} className="flex items-center gap-2">
                        <Save className="h-4 w-4" />
                        Save
                      </Button>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="agentName">Agent Name</Label>
                        <Input
                          id="agentName"
                          value={agentConfig.name}
                          onChange={(e) => setAgentConfig({...agentConfig, name: e.target.value})}
                          placeholder="Enter agent name"
                        />
                      </div>
                      <div>
                        <Label htmlFor="model">Model</Label>
                        <Select
                          value={agentConfig.model}
                          onValueChange={(value) => setAgentConfig({...agentConfig, model: value})}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                            <SelectItem value="claude-3-haiku">Claude 3 Haiku</SelectItem>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="description">Description</Label>
                      <Input
                        id="description"
                        value={agentConfig.description}
                        onChange={(e) => setAgentConfig({...agentConfig, description: e.target.value})}
                        placeholder="Describe what this agent does"
                      />
                    </div>

                    <div>
                      <Label htmlFor="systemPrompt">System Prompt</Label>
                      <Textarea
                        id="systemPrompt"
                        value={agentConfig.system_prompt}
                        onChange={(e) => setAgentConfig({...agentConfig, system_prompt: e.target.value})}
                        placeholder="Define the agent's behavior and personality"
                        rows={6}
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="temperature">Temperature: {agentConfig.temperature}</Label>
                        <input
                          type="range"
                          id="temperature"
                          min="0"
                          max="1"
                          step="0.1"
                          value={agentConfig.temperature}
                          onChange={(e) => setAgentConfig({...agentConfig, temperature: parseFloat(e.target.value)})}
                          className="w-full"
                        />
                      </div>
                      <div>
                        <Label htmlFor="maxTokens">Max Tokens</Label>
                        <Input
                          id="maxTokens"
                          type="number"
                          value={agentConfig.max_tokens}
                          onChange={(e) => setAgentConfig({...agentConfig, max_tokens: parseInt(e.target.value)})}
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="testing" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Test Your Agent</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="testInput">Test Input</Label>
                      <Textarea
                        id="testInput"
                        value={testInput}
                        onChange={(e) => setTestInput(e.target.value)}
                        placeholder="Enter a message to test your agent"
                        rows={3}
                      />
                    </div>
                    <Button 
                      onClick={testAgent} 
                      disabled={isTestingAgent || !testInput.trim()}
                      className="w-full"
                    >
                      {isTestingAgent ? (
                        <>
                          <Clock className="h-4 w-4 mr-2 animate-spin" />
                          Testing...
                        </>
                      ) : (
                        <>
                          <Play className="h-4 w-4 mr-2" />
                          Test Agent
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>

                {testResults.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Test Results</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {testResults.map((result) => (
                        <div key={result.id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-500">
                              {new Date(result.timestamp).toLocaleString()}
                            </span>
                            <div className="flex items-center gap-2">
                              <span className={`text-sm ${getSafetyScoreColor(result.safety_score)}`}>
                                Safety: {(result.safety_score * 100).toFixed(0)}%
                              </span>
                              {result.passed ? (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              ) : (
                                <AlertTriangle className="h-4 w-4 text-red-600" />
                              )}
                            </div>
                          </div>
                          <div className="space-y-2">
                            <div>
                              <Label className="text-xs">Input:</Label>
                              <p className="text-sm bg-gray-50 p-2 rounded">{result.input}</p>
                            </div>
                            <div>
                              <Label className="text-xs">Output:</Label>
                              <p className="text-sm bg-blue-50 p-2 rounded">{result.output}</p>
                            </div>
                            {result.issues.length > 0 && (
                              <div>
                                <Label className="text-xs">Issues:</Label>
                                <ul className="text-sm text-red-600">
                                  {result.issues.map((issue, idx) => (
                                    <li key={idx}>• {issue}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </TabsContent>

              <TabsContent value="safety" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Safety Configuration</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Safety Rules</Label>
                      <div className="space-y-2 mt-2">
                        {agentConfig.safety_rules.map((rule, index) => (
                          <div key={index} className="flex items-center gap-2">
                            <Input
                              value={rule}
                              onChange={(e) => {
                                const newRules = [...agentConfig.safety_rules];
                                newRules[index] = e.target.value;
                                setAgentConfig({...agentConfig, safety_rules: newRules});
                              }}
                              placeholder="Enter safety rule"
                            />
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                const newRules = agentConfig.safety_rules.filter((_, i) => i !== index);
                                setAgentConfig({...agentConfig, safety_rules: newRules});
                              }}
                            >
                              Remove
                            </Button>
                          </div>
                        ))}
                        <Button
                          variant="outline"
                          onClick={() => {
                            setAgentConfig({
                              ...agentConfig,
                              safety_rules: [...agentConfig.safety_rules, '']
                            });
                          }}
                        >
                          Add Rule
                        </Button>
                      </div>
                    </div>

                    <Alert>
                      <Shield className="h-4 w-4" />
                      <AlertDescription>
                        All agent outputs are automatically validated against these safety rules and our 
                        built-in hallucination detection system before being delivered.
                      </AlertDescription>
                    </Alert>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="deployment" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Deployment Settings</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center justify-between">
                        <Label>Auto Scaling</Label>
                        <Switch
                          checked={agentConfig.deployment_settings.auto_scale}
                          onCheckedChange={(checked) => setAgentConfig({
                            ...agentConfig,
                            deployment_settings: {
                              ...agentConfig.deployment_settings,
                              auto_scale: checked
                            }
                          })}
                        />
                      </div>
                      <div>
                        <Label>Max Instances</Label>
                        <Input
                          type="number"
                          value={agentConfig.deployment_settings.max_instances}
                          onChange={(e) => setAgentConfig({
                            ...agentConfig,
                            deployment_settings: {
                              ...agentConfig.deployment_settings,
                              max_instances: parseInt(e.target.value)
                            }
                          })}
                        />
                      </div>
                      <div>
                        <Label>Timeout (seconds)</Label>
                        <Input
                          type="number"
                          value={agentConfig.deployment_settings.timeout_seconds}
                          onChange={(e) => setAgentConfig({
                            ...agentConfig,
                            deployment_settings: {
                              ...agentConfig.deployment_settings,
                              timeout_seconds: parseInt(e.target.value)
                            }
                          })}
                        />
                      </div>
                      <div>
                        <Label>Memory Limit</Label>
                        <Select
                          value={agentConfig.deployment_settings.memory_limit}
                          onValueChange={(value) => setAgentConfig({
                            ...agentConfig,
                            deployment_settings: {
                              ...agentConfig.deployment_settings,
                              memory_limit: value
                            }
                          })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="512MB">512MB</SelectItem>
                            <SelectItem value="1GB">1GB</SelectItem>
                            <SelectItem value="2GB">2GB</SelectItem>
                            <SelectItem value="4GB">4GB</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>

                    <Dialog open={showDeployDialog} onOpenChange={setShowDeployDialog}>
                      <DialogTrigger asChild>
                        <Button className="w-full" disabled={selectedAgent?.status === 'deployed'}>
                          <Container className="h-4 w-4 mr-2" />
                          {selectedAgent?.status === 'deployed' ? 'Already Deployed' : 'Deploy Agent'}
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Deploy Agent</DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                          <p>Are you sure you want to deploy this agent? It will be available via API and webhook endpoints.</p>
                          <div className="flex gap-2">
                            <Button onClick={deployAgent} className="flex-1">
                              Deploy
                            </Button>
                            <Button variant="outline" onClick={() => setShowDeployDialog(false)} className="flex-1">
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </DialogContent>
                    </Dialog>

                    {selectedAgent?.deployment_url && (
                      <div className="space-y-2">
                        <Label>Deployment URLs</Label>
                        <div className="space-y-2">
                          <div>
                            <Label className="text-xs">API Endpoint:</Label>
                            <Input value={selectedAgent.deployment_url} readOnly />
                          </div>
                          {selectedAgent.webhook_url && (
                            <div>
                              <Label className="text-xs">Webhook URL:</Label>
                              <Input value={selectedAgent.webhook_url} readOnly />
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="monitoring" className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Zap className="h-5 w-5" />
                        Requests
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">1,247</div>
                      <p className="text-sm text-gray-600">Last 24 hours</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Avg Response
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">87ms</div>
                      <p className="text-sm text-gray-600">Response time</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Shield className="h-5 w-5" />
                        Safety Score
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">94%</div>
                      <p className="text-sm text-gray-600">Current average</p>
                    </CardContent>
                  </Card>
                </div>

                <Card>
                  <CardHeader>
                    <CardTitle>Recent Activity</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { time: '2 minutes ago', event: 'Agent responded to user query', status: 'success' },
                        { time: '5 minutes ago', event: 'Safety validation passed', status: 'success' },
                        { time: '12 minutes ago', event: 'High confidence response generated', status: 'success' },
                        { time: '18 minutes ago', event: 'Response flagged for review', status: 'warning' },
                        { time: '25 minutes ago', event: 'Agent deployment successful', status: 'success' }
                      ].map((activity, index) => (
                        <div key={index} className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            activity.status === 'success' ? 'bg-green-500' : 
                            activity.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm">{activity.event}</p>
                            <p className="text-xs text-gray-500">{activity.time}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          ) : (
            <Card className="h-96 flex items-center justify-center">
              <div className="text-center">
                <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Agent Selected</h3>
                <p className="text-gray-600 mb-4">Select an agent from the sidebar or create a new one to get started.</p>
                <Button onClick={createNewAgent}>
                  <Code className="h-4 w-4 mr-2" />
                  Create New Agent
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
