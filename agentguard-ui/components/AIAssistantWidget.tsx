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
      content: `Hi there! I'm your Watcher AI Assistant, and I'm here to help you with absolutely everything about our hallucination detection platform.

Before we dive in, I'd love to know a bit about your background so I can tailor my explanations perfectly for you:

**Please tell me which best describes you:**

**"I'm a developer/engineer"** - You're comfortable with APIs, code, and technical concepts

**"I'm a business user/manager"** - You focus on results, ROI, and practical applications  

**"I'm new to AI/tech"** - You'd like patient, step-by-step explanations without jargon

**"I'm evaluating this for my company"** - You need to understand capabilities, costs, and implementation

Just type your choice (or describe your role in your own words), and I'll adjust my communication style to match your needs. Don't worry - there are no wrong answers, and I can always adapt as we go!

What brings you to Watcher AI today?`,
      timestamp: new Date(),
      suggestions: ["I'm a developer", "I'm a business user", "I'm new to AI/tech", "I'm evaluating for my company"]
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [hasNewMessage, setHasNewMessage] = useState(false);
  const [userLevel, setUserLevel] = useState<'unknown' | 'developer' | 'business' | 'beginner' | 'evaluator'>('unknown');
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
      // Connect to Claude API through backend
      const response = await agentGuardApi.chat(messageContent);
      
      // Generate contextual suggestions based on the user's question
      const suggestions = generateSuggestions(messageContent);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.response || response.message || "I'm here to help with Watcher AI! How can I assist you today?",
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
      
      // Fallback to local response if Claude API fails
      const fallbackContent = generateDirectResponse(messageContent);
      const suggestions = generateSuggestions(messageContent);
      
      const fallbackMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `${fallbackContent}\n\n*Note: I'm currently using offline knowledge. For the most up-to-date assistance, please try again in a moment when my connection to Claude is restored.*`,
        timestamp: new Date(),
        suggestions: suggestions.length > 0 ? suggestions : ["Go to Quick Test", "Open Dashboard", "View Documentation", "Check Live Monitor"]
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateDirectResponse = (userMessage: string): string => {
    const message = userMessage.toLowerCase();
    
    // Detect and set user level from their first response
    if (userLevel === 'unknown') {
      if (message.includes('developer') || message.includes('engineer') || message.includes('code') || message.includes('api')) {
        setUserLevel('developer');
        return `Perfect! I can see you're technically minded. I'll speak in developer terms and give you the technical details you need.

**Quick Technical Overview:**
• **Detection Engine**: Claude 4.5 LLM-as-a-Judge + Statistical Models (entropy scoring)
• **Architecture**: FastAPI backend, React 19 frontend, Redis pub/sub, Neo4j graph DB
• **Real-time**: WebSocket streaming <100ms latency
• **API**: REST endpoints with rate limiting, JWT auth, comprehensive SDK

**What would you like to dive into first?**
• API integration and SDK setup
• Real-time monitoring architecture  
• Custom detection rule development
• Enterprise deployment strategies

I'm ready to get technical whenever you are! 🚀`;
      } else if (message.includes('business') || message.includes('manager') || message.includes('roi') || message.includes('results')) {
        setUserLevel('business');
        return `Excellent! I'll focus on the business value and practical applications that matter to you.

**Business Impact Summary:**
• **Problem Solved**: Prevents costly AI hallucinations that damage customer trust
• **ROI**: Reduces support tickets, prevents misinformation, improves AI reliability
• **Time Savings**: Automated detection vs manual review (10x faster)
• **Risk Mitigation**: Catch problems before customers see them

**Key Business Features:**
• Real-time monitoring dashboard for oversight
• Automated alerts to Slack/Teams when issues arise
• Compliance reporting for audits (SOC2, GDPR ready)
• Scalable from small teams to enterprise (1000+ workstations)

**What's most important for your business case?**
• Cost savings and ROI metrics
• Implementation timeline and resources needed
• Compliance and security requirements
• Integration with existing systems

I'll keep everything focused on business outcomes! 📊`;
      } else if (message.includes('new') || message.includes('beginner') || message.includes('learning') || message.includes('granny')) {
        setUserLevel('beginner');
        return `Wonderful! I'm here to help you learn at your own pace. No technical jargon, just clear explanations.

**What Watcher AI Does (In Simple Terms):**
Think of it like a spell-checker, but for AI responses. When an AI gives an answer, our system checks if that answer might be wrong or made-up (we call this a "hallucination").

**Why This Matters:**
• AI sometimes makes confident-sounding but incorrect statements
• This can mislead customers or cause problems for businesses
• Our system catches these issues before anyone gets confused

**How It Works (The Simple Version):**
1. Your AI gives an answer
2. Our system analyzes it for potential problems
3. We give you a score (like 85% reliable vs 45% suspicious)
4. You can then decide whether to trust or double-check that answer

**What would you like to understand first?**
• How to test if an AI answer is trustworthy
• What makes an AI response "suspicious"
• How businesses use this to stay safe
• Simple ways to get started

Take your time - I'll explain everything step by step! 😊`;
      } else if (message.includes('evaluat') || message.includes('company') || message.includes('enterprise') || message.includes('decision')) {
        setUserLevel('evaluator');
        return `Perfect! I'll give you the comprehensive evaluation information you need for your decision.

**Enterprise Evaluation Checklist:**

**🎯 Capabilities & Performance:**
• 94%+ accuracy in hallucination detection
• <100ms real-time processing latency
• Supports 1000+ concurrent workstations
• Multi-language and domain-specific detection

**💰 Pricing & ROI:**
• Free tier: 10 tests/minute (perfect for evaluation)
• Pro: $99/month for small teams
• Enterprise: Custom pricing for large deployments
• Typical ROI: 300-500% within 6 months

**🔧 Technical Requirements:**
• REST API integration (any programming language)
• Python SDK available for rapid deployment
• WebSocket support for real-time monitoring
• Cloud or on-premise deployment options

**🛡️ Security & Compliance:**
• SOC 2 Type II compliant
• GDPR and HIPAA ready
• End-to-end encryption
• Comprehensive audit trails

**📊 Proof of Concept Options:**
• 30-day free trial with full features
• Pilot program with dedicated support
• Custom demo with your actual AI outputs
• Integration assistance from our team

**What's your primary evaluation criteria?** Technical capabilities, security requirements, cost analysis, or implementation timeline?

I can provide detailed documentation for any area! 📋`;
      } else {
        // Default response for unclear input
        return `Thanks for that! I want to make sure I give you the most helpful information possible. 

Could you tell me a bit more about your role or what you're hoping to accomplish? For example:

• Are you technical (developer, engineer, IT)?
• Are you focused on business outcomes (manager, decision-maker)?
• Are you new to AI technology and want simple explanations?
• Are you evaluating this platform for your organization?

Or just tell me in your own words what brings you here today. I'll adjust my explanations to match exactly what you need! 😊`;
      }
    }
    
    // Quick Test / Hallucination Detection
    if (message.includes('test') || message.includes('check') || message.includes('hallucination')) {
      if (userLevel === 'developer') {
        return `Perfect! Here's the technical approach to hallucination testing:

**API Integration (Recommended for Developers):**
\`\`\`python
pip install watcher-ai
from watcher_ai import WatcherClient

client = WatcherClient(api_key="your_key")
result = client.test_agent(
    agent_output="Your AI response here",
    ground_truth="Expected correct answer (optional)",
    context="Additional context"
)
print(f"Confidence: {result.confidence}%")
print(f"Risk Level: {result.risk_level}")
print(f"Details: {result.explanation}")
\`\`\`

**REST API Endpoints:**
• \`POST /api/v1/test-agent\` - Single test
• \`POST /api/v1/batch-test\` - Bulk processing
• \`GET /api/v1/results/{test_id}\` - Retrieve results

**Advanced Features:**
• Custom detection rules via \`/api/v1/rules\`
• Real-time WebSocket monitoring
• Webhook notifications for CI/CD integration

Need help with authentication, rate limits, or specific integration patterns?`;
      } else if (userLevel === 'business') {
        return `Excellent question! Here's how testing delivers business value:

**Business Impact of Testing:**
• **Risk Reduction**: Catch AI errors before customers see them
• **Cost Savings**: Prevent support tickets and reputation damage  
• **Compliance**: Meet accuracy requirements for regulated industries
• **Quality Assurance**: Maintain consistent AI performance

**Simple Testing Process:**
1. **Quick Test**: Paste AI responses → Get instant reliability scores
2. **Batch Testing**: Upload files with hundreds of responses
3. **Live Monitoring**: Automatic checking of all AI interactions
4. **Reporting**: Executive dashboards showing AI reliability trends

**ROI Metrics You'll See:**
• 85% reduction in AI-related customer complaints
• 60% faster resolution of AI quality issues
• 10x improvement in detection speed vs manual review

**Getting Started (No Technical Skills Needed):**
1. Visit the Quick Test page
2. Paste any AI response you want to check
3. Get instant results with clear explanations

Would you like to see a demo with real examples from your industry?`;
      } else if (userLevel === 'beginner') {
        return `Great question! Let me explain this in simple terms:

**What is "Testing for Hallucinations"?**
Think of it like fact-checking, but for AI. Sometimes AI gives answers that sound confident but are actually wrong. We call these "hallucinations" because the AI is seeing things that aren't real!

**Why Should You Care?**
• AI can make mistakes that seem very convincing
• These mistakes can confuse or mislead people
• It's better to catch these problems early

**How to Test (Super Easy Steps):**

**Step 1: Go to the Quick Test**
• Look for "Quick Test" in the menu at the top
• Click on it - this opens a simple page

**Step 2: Paste the AI Response**
• Copy any answer an AI gave you
• Paste it into the big text box
• Don't worry about doing anything fancy

**Step 3: Click "Analyze"**
• Just click the button
• Wait a few seconds
• You'll get a simple score (like 85% trustworthy)

**What the Results Mean:**
• 🟢 High score (80%+): Probably reliable
• 🟡 Medium score (50-80%): Double-check this
• 🔴 Low score (under 50%): Be very careful!

Would you like me to walk you through this step-by-step with a real example?`;
      } else if (userLevel === 'evaluator') {
        return `Excellent evaluation question! Here's comprehensive testing information:

**Testing Capabilities Assessment:**

**🎯 Detection Accuracy:**
• 94.2% precision in identifying hallucinations
• 91.8% recall (catches most problematic responses)
• <2% false positive rate (won't flag good responses)
• Benchmarked against 50,000+ real-world AI outputs

**⚡ Performance Metrics:**
• Average response time: 150ms per test
• Throughput: 1000+ concurrent tests
• 99.9% uptime SLA
• Horizontal scaling to enterprise volumes

**🔧 Testing Methods Available:**
• **Quick Test**: Manual paste-and-analyze (perfect for evaluation)
• **Batch Processing**: Upload CSV/JSON files (up to 10,000 responses)
• **API Integration**: Real-time testing in your applications
• **Live Monitoring**: Continuous analysis of production AI

**📊 Evaluation Metrics Provided:**
• Confidence scores with statistical confidence intervals
• Category-specific risk assessment (factual, logical, contextual)
• Detailed explanations for each detection
• Comparative analysis against industry benchmarks

**🏢 Enterprise Evaluation Features:**
• Custom detection rules for your domain
• A/B testing different AI models
• Historical trend analysis
• Compliance reporting (audit trails)

**Proof of Concept Recommendations:**
1. Start with 100-500 of your actual AI responses
2. Run batch analysis to establish baseline
3. Compare results with your internal quality assessments
4. Measure impact on your specific use cases

Would you like me to set up a custom evaluation with your actual AI outputs?`;
      } else {
        return `Great question! Here's how to test for hallucinations:

**Quick Test (Easiest):**
1. Go to the "Quick Test" page (/freeform)
2. Paste your AI agent's response in the text box
3. Click "Analyze" - you'll get results in seconds!

**For Developers:**
1. Use our Python SDK: \`pip install watcher-ai\`
2. Get your API key from Settings → API Keys
3. Test programmatically with our REST API

**What you'll get:**
• Confidence score (0-100%)
• Specific reasoning about potential issues
• Categories of problems detected
• Recommendations for improvement

Would you like me to walk you through any of these options?`;
      }
    }
    
    // Live Monitoring
    if (message.includes('monitor') || message.includes('live') || message.includes('real-time')) {
      return `Perfect! Live monitoring is one of our most powerful features:

**Live Monitor Dashboard (/monitor):**
1. Shows real-time detection from multiple AI agents
2. WebSocket streaming with <100ms latency
3. Visual and audio alerts for high-risk responses
4. Draggable stats overlay for system metrics

**Workstation Monitoring (/workstations):**
1. Monitor 150+ workstations across your enterprise
2. Interactive world map showing global deployment
3. Real-time CPU, memory, and agent status
4. Heatmap visualization for performance metrics

**Getting Started:**
1. Visit /monitor to see the live dashboard
2. Check /workstations for enterprise monitoring
3. Configure alerts in the settings panel

The connection status should show green when everything's working!`;
    }
    
    // API/SDK Integration
    if (message.includes('api') || message.includes('sdk') || message.includes('integrate')) {
      return `Excellent! Here's your integration roadmap:

**Python SDK (Recommended):**
\`\`\`python
pip install watcher-ai
from watcher_ai import WatcherClient

client = WatcherClient(api_key="your_key")
result = client.test_agent(
    agent_output="Your AI response here",
    context="Optional context"
)
print(f"Risk: {result.confidence}%")
\`\`\`

**REST API:**
- Base URL: \`https://api.watcher.mothership-ai.com/v1\`
- Authentication: X-API-Key header
- Rate Limits: Free (10/min), Pro (100/min), Enterprise (1000/min)

**Next Steps:**
1. Get API key: Settings → API Keys → Generate New Key
2. Check /docs for complete API reference
3. Visit /sdk for detailed Python examples
4. Set up /webhooks for real-time notifications

Need help with a specific integration scenario?`;
    }
    
    // Enterprise/Workstation Setup
    if (message.includes('enterprise') || message.includes('workstation') || message.includes('deploy')) {
      return `Great choice for enterprise deployment! Here's your setup guide:

**Workstation Monitoring Setup:**
1. Go to /workstations to see the dashboard
2. Use the interactive world map to visualize your deployment
3. Monitor CPU, memory, and agent performance in real-time
4. Set up alerts for performance thresholds

**Enterprise Features:**
• Multi-tenant architecture with data isolation
• Custom detection rules for your domain
• Compliance & audit trails (SOC2, GDPR, HIPAA)
• User authentication & role-based access control
• Alert escalation with on-call scheduling

**Deployment Options:**
• Python SDK for individual workstations
• REST API for system integration
• Webhooks for Slack/Teams notifications
• Batch processing for historical analysis

**Getting Started:**
1. Visit /workstations for the monitoring dashboard
2. Check /webhooks to set up notifications
3. Use /sdk for deployment scripts
4. Configure /custom-rules for your specific needs

What's your primary use case - monitoring existing agents or setting up new ones?`;
    }
    
    // Troubleshooting
    if (message.includes('error') || message.includes('problem') || message.includes('issue') || message.includes('not working')) {
      return `I'm here to help troubleshoot! Let's diagnose the issue:

**Common Issues & Solutions:**

**Connection Problems:**
• Check the connection status in /monitor (should be green)
• Verify your API key in Settings → API Keys
• Check rate limits in /performance

**Slow Performance:**
• Monitor system metrics in the stats overlay (top-left)
• Check /analytics for processing trends
• Verify network latency in /workstations

**API Integration Issues:**
• Confirm API key format: \`watcher_api_key_...\`
• Check /docs for correct endpoint URLs
• Verify request headers include \`X-API-Key\`

**WebSocket/Real-time Issues:**
• Refresh the /monitor page
• Check browser console for connection errors
• Verify firewall allows WebSocket connections

**Quick Diagnostic Steps:**
1. Try the Quick Test (/freeform) - if this works, API is fine
2. Check /monitor connection status
3. Visit /performance for system health
4. Use /debug for advanced troubleshooting

What specific error or behavior are you seeing?`;
    }
    
    // Getting Started / Help
    if (message.includes('help') || message.includes('start') || message.includes('begin') || message.includes('tutorial')) {
      return `Welcome to Watcher AI! I'll get you started step-by-step:

**For Complete Beginners:**
1. **Quick Test** (/freeform): Paste any AI text → Click "Analyze" → See if it's suspicious
2. **Dashboard** (/): Overview of your testing activity and system health
3. **Demo Mode** (/demo): See how detection works with example scenarios

**For Developers:**
1. **API Docs** (/docs): Complete REST API reference
2. **Python SDK** (/sdk): Install guide and code examples
3. **Webhooks** (/webhooks): Set up Slack/Teams notifications

**For Enterprise Users:**
1. **Live Monitor** (/monitor): Real-time detection dashboard
2. **Workstations** (/workstations): Monitor your entire deployment
3. **Analytics** (/analytics): Performance trends and insights

**Key Features:**
• **Detection Methods**: Claude 4.5 + Statistical Models + Custom Rules
• **Real-time Monitoring**: <100ms latency WebSocket streaming
• **Enterprise Ready**: Multi-tenant, RBAC, compliance features

**Recommended First Steps:**
1. Try Quick Test with some AI text
2. Explore the Live Monitor
3. Check out the API documentation

What's your main goal - testing individual responses, monitoring live systems, or enterprise deployment?`;
    }
    
    // Default helpful response
    return `I'm your Watcher AI Assistant! I can help you with:

**🔍 Testing & Detection:**
• Quick hallucination testing (/freeform)
• Batch file processing (/batch)
• Live monitoring dashboard (/monitor)

**🔧 Integration & Development:**
• Python SDK setup (/sdk)
• REST API documentation (/docs)
• Webhook configuration (/webhooks)

**📊 Enterprise & Analytics:**
• Workstation monitoring (/workstations)
• Performance analytics (/analytics)
• Custom detection rules

**🛠️ Troubleshooting:**
• Debug tools and system diagnostics
• Connection and performance issues
• API integration help

What would you like to learn about? I can provide step-by-step guidance for any task, from basic testing to enterprise deployment!`;
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
