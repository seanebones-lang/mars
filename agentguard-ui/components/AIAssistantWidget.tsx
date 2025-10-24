'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Fab,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  Chip,
  Divider,
  Button,
  Collapse,
  CircularProgress,
  Alert,
  Stack,
  Tooltip,
  Badge
} from '@mui/material';
import {
  ChatOutlined,
  CloseOutlined,
  SendOutlined,
  SmartToyOutlined,
  PersonOutlined,
  MinimizeOutlined,
  ExpandMoreOutlined,
  ExpandLessOutlined,
  HelpOutlineOutlined,
  AutoAwesomeOutlined,
  LightbulbOutlined,
  BugReportOutlined,
  SchoolOutlined
} from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { motion, AnimatePresence } from 'framer-motion';
import { agentGuardApi } from '@/lib/api';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  suggestions?: string[];
  isTyping?: boolean;
}

interface AIAssistantWidgetProps {
  position?: 'bottom-right' | 'bottom-left';
}

const SYSTEM_KNOWLEDGE = `You are the Watcher AI Assistant, an expert guide for the Watcher AI platform - a comprehensive hallucination detection and testing platform for AI agents. You have complete knowledge of every feature and can help users from complete beginners to tech experts.

## PLATFORM OVERVIEW
Watcher AI is an enterprise-grade platform for detecting hallucinations, fabrications, and reliability issues in AI agent outputs. It uses Claude 4.5 Sonnet with self-consistency sampling and statistical models for accurate detection.

## KEY FEATURES & NAVIGATION

### 1. DASHBOARD (/)
- Real-time metrics: Total tests, accuracy rates, latency, alerts
- Quick test form for immediate hallucination checking
- Results table with historical analysis
- Performance summaries and trends

### 2. LIVE MONITOR (/monitor)
- Real-time hallucination detection from multiple simulated agents
- WebSocket streaming with <100ms latency
- Visual/audio alerts for high-risk detections
- Connection status monitoring
- Draggable stats overlay with system metrics

### 3. WORKSTATIONS (/workstations)
- Monitor 150+ workstations across enterprise
- Interactive world map with real-time status
- Grid/List/Map view modes
- CPU, Memory, Disk usage monitoring
- Agent deployment and management
- Heatmap visualization for performance metrics

### 4. ANALYTICS (/analytics)
- Time series charts for detection trends
- Agent performance comparisons
- Risk distribution analysis
- Processing volume metrics
- ROI calculations and insights

### 5. TESTING TOOLS
- **Quick Test (/freeform)**: Paste any AI output for instant analysis
- **Demo Mode (/demo)**: Simulated agent scenarios for testing
- **Debug Tools (/debug)**: Advanced debugging with session history
- **Batch Processing (/batch)**: Upload CSV/JSON files for bulk analysis

### 6. DEPLOYMENT & INTEGRATION
- **Webhooks (/webhooks)**: Slack, Teams, Email, Custom notifications
- **Python SDK (/sdk)**: Complete API integration with examples
- **API Documentation (/docs)**: Full REST API reference
- **Rate Limits**: Tiered quotas (Free: 10/min, Pro: 100/min, Enterprise: 1000/min)

### 7. ENTERPRISE FEATURES
- Multi-tenant architecture with data isolation
- Custom detection rules and templates
- Compliance & audit trails (SOC2, GDPR, HIPAA)
- Performance monitoring and alerting
- User authentication & RBAC
- Alert escalation with on-call scheduling

## TECHNICAL ARCHITECTURE
- **Backend**: FastAPI with Claude 4.5 Sonnet API
- **Frontend**: React 19 + Next.js 16 + Material-UI v7
- **Database**: PostgreSQL + Redis + Neo4j (graph DB for RAG)
- **Deployment**: Vercel (frontend) + Render (backend)
- **Monitoring**: Prometheus + custom metrics

## DETECTION METHODS
1. **LLM-as-a-Judge**: Claude evaluates outputs against ground truth
2. **Self-Consistency**: Multiple evaluations with voting consensus
3. **Statistical Models**: Token-level entropy and confidence scoring
4. **Custom Rules**: Regex, keywords, domain-specific patterns
5. **RAG Integration**: Contextual retrieval for similar cases

## COMMON TASKS & GUIDANCE

### For Beginners:
- Start with Quick Test (/freeform) - just paste AI text and click analyze
- Check Dashboard for overview of system health
- Use Demo Mode to see how detection works with examples

### For Developers:
- Install Python SDK: pip install watcher-ai
- Get API key from Settings → API Keys
- Check /docs for complete API reference
- Use webhooks for real-time notifications

### For Enterprise Admins:
- Configure workstation monitoring from /workstations
- Set up custom detection rules for your domain
- Configure compliance settings and audit trails
- Manage user roles and permissions

## TROUBLESHOOTING
- Connection issues: Check /monitor for WebSocket status
- API errors: Verify API key and rate limits in /performance
- Slow responses: Monitor system metrics in stats overlay
- Integration help: Check /sdk for Python examples

You should provide step-by-step guidance, suggest relevant features, and adapt your communication style to the user's technical level. Always be helpful, encouraging, and provide specific next steps.`;

const QUICK_SUGGESTIONS = [
  "How do I test my AI agent for hallucinations?",
  "Show me the live monitoring dashboard",
  "How to set up batch processing?",
  "Explain the workstation monitoring",
  "Help with Python SDK integration",
  "What are the detection methods?",
  "How to configure webhooks?",
  "Troubleshoot connection issues"
];

export default function AIAssistantWidget({ position = 'bottom-right' }: AIAssistantWidgetProps) {
  const theme = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: "👋 Hi! I'm your Watcher AI Assistant. I know everything about this platform and can help you with any task - from basic testing to enterprise deployment. What would you like to learn about?",
      timestamp: new Date(),
      suggestions: QUICK_SUGGESTIONS.slice(0, 4)
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSendMessage = async (content?: string) => {
    const messageContent = content || inputValue.trim();
    if (!messageContent || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      // Create a comprehensive prompt for Claude that includes system knowledge
      const prompt = `${SYSTEM_KNOWLEDGE}

User Question: "${messageContent}"

Please provide a helpful, detailed response as the Watcher AI Assistant. Include:
1. Direct answer to their question
2. Step-by-step guidance if applicable
3. Relevant feature suggestions
4. Next steps they should take

Adapt your tone to their technical level and be encouraging. If they're asking about a specific feature, provide navigation instructions and explain the benefits.`;

      // Use the existing API to get Claude's response
      const response = await agentGuardApi.testAgent({
        agent_output: prompt,
        ground_truth: "Provide helpful, accurate guidance about the Watcher AI platform based on the system knowledge provided. Be conversational, helpful, and provide specific actionable steps.",
        conversation_history: []
      });

      // Extract the explanation as the assistant's response
      const assistantContent = response.details?.claude_explanation || "I'm here to help! Could you please rephrase your question?";
      
      // Generate contextual suggestions based on the user's question
      const suggestions = generateSuggestions(messageContent);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        suggestions: suggestions.length > 0 ? suggestions : undefined
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Show notification if widget is closed
      if (!isOpen) {
        setHasNewMessage(true);
      }

    } catch (error) {
      console.error('AI Assistant error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: "I apologize, but I'm having trouble connecting right now. Here are some quick tips:\n\n• Try the Quick Test at /freeform for immediate hallucination checking\n• Check the Dashboard for system overview\n• Visit /docs for API documentation\n• Use /monitor for real-time detection\n\nPlease try asking again in a moment!",
        timestamp: new Date(),
        suggestions: ["Go to Quick Test", "Open Dashboard", "View Documentation", "Check Live Monitor"]
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateSuggestions = (userMessage: string): string[] => {
    const message = userMessage.toLowerCase();
    
    if (message.includes('test') || message.includes('check') || message.includes('analyze')) {
      return ["Go to Quick Test", "Try Demo Mode", "Upload Batch File", "View API Docs"];
    }
    
    if (message.includes('monitor') || message.includes('live') || message.includes('real-time')) {
      return ["Open Live Monitor", "Check Workstations", "View Analytics", "Configure Alerts"];
    }
    
    if (message.includes('workstation') || message.includes('enterprise') || message.includes('deploy')) {
      return ["View Workstations", "Setup Python SDK", "Configure Webhooks", "Check Performance"];
    }
    
    if (message.includes('api') || message.includes('sdk') || message.includes('integrate')) {
      return ["View API Docs", "Python SDK Guide", "Webhook Setup", "Rate Limits Info"];
    }
    
    if (message.includes('error') || message.includes('problem') || message.includes('issue')) {
      return ["Debug Tools", "Check Performance", "View System Status", "Contact Support"];
    }
    
    return ["Explore Dashboard", "Try Quick Test", "View Documentation", "Check Live Monitor"];
  };

  const handleSuggestionClick = (suggestion: string) => {
    // Handle navigation suggestions
    const navigationMap: { [key: string]: string } = {
      "Go to Quick Test": "/freeform",
      "Open Dashboard": "/",
      "View Documentation": "/docs",
      "Check Live Monitor": "/monitor",
      "Open Live Monitor": "/monitor",
      "View Workstations": "/workstations",
      "Check Workstations": "/workstations",
      "View Analytics": "/analytics",
      "Try Demo Mode": "/demo",
      "Debug Tools": "/debug",
      "Upload Batch File": "/batch",
      "Setup Python SDK": "/sdk",
      "Python SDK Guide": "/sdk",
      "Configure Webhooks": "/webhooks",
      "Webhook Setup": "/webhooks",
      "Check Performance": "/performance",
      "View API Docs": "/docs"
    };

    if (navigationMap[suggestion]) {
      window.location.href = navigationMap[suggestion];
    } else {
      // Send as a message
      handleSendMessage(suggestion);
    }
  };

  const toggleWidget = () => {
    setIsOpen(!isOpen);
    setHasNewMessage(false);
    if (!isOpen) {
      setIsMinimized(false);
    }
  };

  const positionStyles = {
    'bottom-right': { bottom: 24, right: 24 },
    'bottom-left': { bottom: 24, left: 24 }
  };

  return (
    <Box sx={{ position: 'fixed', zIndex: 1300, ...positionStyles[position] }}>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.2 }}
          >
            <Paper
              elevation={8}
              sx={{
                width: 380,
                height: isMinimized ? 60 : 500,
                mb: 2,
                borderRadius: 3,
                overflow: 'hidden',
                border: `1px solid ${theme.palette.divider}`,
                background: theme.palette.background.paper
              }}
            >
              {/* Header */}
              <Box
                sx={{
                  p: 2,
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <Box display="flex" alignItems="center" gap={1}>
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.dark' }}>
                    <SmartToyOutlined />
                  </Avatar>
                  <Box>
                    <Typography variant="subtitle2" fontWeight={600}>
                      Watcher AI Assistant
                    </Typography>
                    <Typography variant="caption" sx={{ opacity: 0.9 }}>
                      Powered by Claude 4.5 Sonnet
                    </Typography>
                  </Box>
                </Box>
                
                <Box display="flex" alignItems="center">
                  <Tooltip title={isMinimized ? "Expand" : "Minimize"}>
                    <IconButton
                      size="small"
                      sx={{ color: 'inherit', mr: 1 }}
                      onClick={() => setIsMinimized(!isMinimized)}
                    >
                      {isMinimized ? <ExpandLessOutlined /> : <MinimizeOutlined />}
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Close">
                    <IconButton
                      size="small"
                      sx={{ color: 'inherit' }}
                      onClick={toggleWidget}
                    >
                      <CloseOutlined />
                    </IconButton>
                  </Tooltip>
                </Box>
              </Box>

              <Collapse in={!isMinimized}>
                {/* Messages */}
                <Box
                  sx={{
                    height: 360,
                    overflowY: 'auto',
                    p: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2
                  }}
                >
                  {messages.map((message) => (
                    <Box key={message.id}>
                      <Box
                        display="flex"
                        justifyContent={message.type === 'user' ? 'flex-end' : 'flex-start'}
                        alignItems="flex-start"
                        gap={1}
                      >
                        {message.type === 'assistant' && (
                          <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main' }}>
                            <AutoAwesomeOutlined sx={{ fontSize: 14 }} />
                          </Avatar>
                        )}
                        
                        <Paper
                          sx={{
                            p: 1.5,
                            maxWidth: '75%',
                            bgcolor: message.type === 'user' ? 'primary.main' : 'grey.100',
                            color: message.type === 'user' ? 'primary.contrastText' : 'text.primary',
                            borderRadius: 2,
                            ...(theme.palette.mode === 'dark' && message.type === 'assistant' && {
                              bgcolor: 'grey.800'
                            })
                          }}
                        >
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {message.content}
                          </Typography>
                        </Paper>
                        
                        {message.type === 'user' && (
                          <Avatar sx={{ width: 24, height: 24, bgcolor: 'grey.400' }}>
                            <PersonOutlined sx={{ fontSize: 14 }} />
                          </Avatar>
                        )}
                      </Box>
                      
                      {/* Suggestions */}
                      {message.suggestions && (
                        <Box mt={1} display="flex" flexWrap="wrap" gap={0.5}>
                          {message.suggestions.map((suggestion, index) => (
                            <Chip
                              key={index}
                              label={suggestion}
                              size="small"
                              variant="outlined"
                              clickable
                              onClick={() => handleSuggestionClick(suggestion)}
                              sx={{
                                fontSize: '0.75rem',
                                height: 24,
                                '&:hover': {
                                  bgcolor: 'primary.50'
                                }
                              }}
                            />
                          ))}
                        </Box>
                      )}
                    </Box>
                  ))}
                  
                  {isLoading && (
                    <Box display="flex" alignItems="center" gap={1}>
                      <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main' }}>
                        <AutoAwesomeOutlined sx={{ fontSize: 14 }} />
                      </Avatar>
                      <Paper sx={{ p: 1.5, bgcolor: 'grey.100' }}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <CircularProgress size={16} />
                          <Typography variant="body2" color="text.secondary">
                            Thinking...
                          </Typography>
                        </Box>
                      </Paper>
                    </Box>
                  )}
                  
                  <div ref={messagesEndRef} />
                </Box>

                <Divider />

                {/* Input */}
                <Box sx={{ p: 2 }}>
                  <Box display="flex" gap={1}>
                    <TextField
                      ref={inputRef}
                      fullWidth
                      size="small"
                      placeholder="Ask me anything about Watcher AI..."
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      disabled={isLoading}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          borderRadius: 2
                        }
                      }}
                    />
                    <IconButton
                      color="primary"
                      onClick={() => handleSendMessage()}
                      disabled={!inputValue.trim() || isLoading}
                      sx={{
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                        '&:hover': {
                          bgcolor: 'primary.dark'
                        },
                        '&.Mui-disabled': {
                          bgcolor: 'grey.300'
                        }
                      }}
                    >
                      <SendOutlined />
                    </IconButton>
                  </Box>
                  
                  <Box display="flex" gap={0.5} mt={1} flexWrap="wrap">
                    <Chip
                      icon={<HelpOutlineOutlined />}
                      label="Help"
                      size="small"
                      variant="outlined"
                      clickable
                      onClick={() => handleSendMessage("I need help getting started with Watcher AI")}
                    />
                    <Chip
                      icon={<LightbulbOutlined />}
                      label="Features"
                      size="small"
                      variant="outlined"
                      clickable
                      onClick={() => handleSendMessage("What are the main features of Watcher AI?")}
                    />
                    <Chip
                      icon={<SchoolOutlined />}
                      label="Tutorial"
                      size="small"
                      variant="outlined"
                      clickable
                      onClick={() => handleSendMessage("Give me a step-by-step tutorial")}
                    />
                  </Box>
                </Box>
              </Collapse>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>

      {/* FAB */}
      <Tooltip title="AI Assistant - Ask me anything!">
        <Fab
          color="primary"
          onClick={toggleWidget}
          sx={{
            background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
            '&:hover': {
              background: `linear-gradient(45deg, ${theme.palette.primary.dark}, ${theme.palette.primary.main})`,
              transform: 'scale(1.1)'
            },
            transition: 'all 0.2s ease-in-out'
          }}
        >
          <Badge
            badgeContent={hasNewMessage ? "!" : 0}
            color="error"
            sx={{
              '& .MuiBadge-badge': {
                fontSize: '0.75rem',
                minWidth: 16,
                height: 16
              }
            }}
          >
            <ChatOutlined />
          </Badge>
        </Fab>
      </Tooltip>
    </Box>
  );
}
