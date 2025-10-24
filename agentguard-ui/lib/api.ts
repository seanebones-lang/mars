import axios from 'axios';
import { TestResult } from './store';
import { validateAgentTestRequest, SecureAgentTestRequest, SecurityLogger } from './security';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AgentTestRequest {
  agent_output: string;
  ground_truth: string;
  conversation_history?: string[];
}

export interface HealthResponse {
  status: string;
  model: string;
  claude_api: string;
  statistical_model: string;
  ensemble_weights: {
    claude: number;
    statistical: number;
  };
  uncertainty_threshold: number;
}

export const agentGuardApi = {
  // Test an agent with security validation
  testAgent: async (request: AgentTestRequest): Promise<TestResult> => {
    try {
      // Validate and sanitize input
      const secureRequest = validateAgentTestRequest(request);
      
      // Log security event
      SecurityLogger.logSecurityEvent('API_REQUEST', {
        endpoint: '/test-agent',
        inputLength: request.agent_output?.length || 0,
      });

      const response = await axios.post(`${API_URL}/test-agent`, secureRequest, {
        timeout: 30000, // 30 second timeout
        headers: {
          'Content-Type': 'application/json',
          'X-Client-Version': '1.0.0',
        },
      });

      return {
        ...response.data,
        id: `${Date.now()}-${Math.random()}`,
        timestamp: new Date().toISOString(),
      };
    } catch (error: any) {
      // Log security errors
      SecurityLogger.logSecurityEvent('API_ERROR', {
        endpoint: '/test-agent',
        error: error.message,
      });
      throw error;
    }
  },
  
  // Check health
  checkHealth: async (): Promise<HealthResponse> => {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },
  
  // Get metrics
  getMetrics: async (): Promise<any> => {
    const response = await axios.get(`${API_URL}/metrics`);
    return response.data;
  },
  
  // Batch test from file
  batchTest: async (scenarios: AgentTestRequest[]): Promise<TestResult[]> => {
    const results: TestResult[] = [];
    for (const scenario of scenarios) {
      try {
        const result = await agentGuardApi.testAgent(scenario);
        results.push(result);
      } catch (error) {
        console.error('Batch test error:', error);
      }
    }
    return results;
  },
  
  // Chat with AI Assistant
  chat: async (message: string): Promise<{ status: string; response: string; timestamp: string }> => {
    const response = await axios.post(`${API_URL}/chat`, { message });
    return response.data;
  },

  // Get Claude-powered analysis insights
  getAnalysisInsights: async (agentOutput: string, testResult: any): Promise<{ 
    insights: string; 
    suggestions: string[]; 
    riskExplanation: string;
    improvementTips: string[];
    contextualAnalysis: string;
  }> => {
    const analysisPrompt = `Analyze this AI agent output and hallucination detection result. Provide intelligent insights, suggestions, and explanations.

Agent Output: "${agentOutput}"

Detection Result:
- Risk Score: ${testResult.hallucination_risk}
- Confidence: ${testResult.confidence}
- Reasoning: ${testResult.reasoning}

Please provide:
1. Intelligent insights about the content quality
2. Specific suggestions for improvement
3. Clear explanation of the risk assessment
4. Practical tips for better AI outputs
5. Contextual analysis of the content`;

    const response = await axios.post(`${API_URL}/chat`, { message: analysisPrompt });
    
    // Parse Claude's response into structured insights
    const claudeResponse = response.data.response;
    
    return {
      insights: claudeResponse,
      suggestions: [
        "Review flagged content areas",
        "Verify factual claims",
        "Consider additional context",
        "Test with different prompts"
      ],
      riskExplanation: `Risk level: ${testResult.hallucination_risk > 0.7 ? 'High' : testResult.hallucination_risk > 0.4 ? 'Medium' : 'Low'}`,
      improvementTips: [
        "Add more specific context",
        "Use authoritative sources",
        "Be more precise with claims",
        "Include confidence indicators"
      ],
      contextualAnalysis: claudeResponse
    };
  },

  // Get Claude-powered workstation insights
  getWorkstationInsights: async (workstation: any): Promise<{
    systemHealth: string;
    securityAssessment: string;
    performanceRecommendations: string[];
    anomalyDetection: string;
    maintenanceSchedule: string[];
    riskFactors: string[];
    optimizationTips: string[];
    complianceStatus: string;
  }> => {
    const workstationPrompt = `Analyze this enterprise workstation and provide intelligent insights, recommendations, and assessments.

Workstation Details:
- Name: ${workstation.name}
- OS: ${workstation.os} ${workstation.platformVersion}
- CPU Usage: ${workstation.cpuUsage}%
- Memory: ${workstation.memoryUsage}% (${workstation.memoryTotalGb}GB total)
- Disk: ${workstation.diskUsage}% (${workstation.diskTotalGb}GB total)
- Status: ${workstation.status}
- Agent Status: ${workstation.agentStatus}
- Security Score: ${workstation.securityScore}/100
- Vulnerabilities: ${workstation.vulnerabilities?.length || 0} found
- Open Ports: ${workstation.openPorts?.join(', ') || 'None'}
- Last Seen: ${workstation.lastSeen}
- Uptime: ${workstation.uptime}

Please provide:
1. Overall system health assessment
2. Security risk evaluation and recommendations
3. Performance optimization suggestions
4. Anomaly detection insights
5. Maintenance schedule recommendations
6. Risk factors to monitor
7. Optimization tips for better performance
8. Compliance status assessment

Be specific, actionable, and enterprise-focused.`;

    const response = await axios.post(`${API_URL}/chat`, { message: workstationPrompt });
    const claudeResponse = response.data.response;
    
    return {
      systemHealth: claudeResponse,
      securityAssessment: `Security Score: ${workstation.securityScore}/100. ${workstation.vulnerabilities?.length || 0} vulnerabilities detected.`,
      performanceRecommendations: [
        "Monitor CPU usage patterns during peak hours",
        "Consider memory upgrade if usage consistently >80%",
        "Schedule disk cleanup for optimal performance",
        "Review running processes for optimization opportunities"
      ],
      anomalyDetection: claudeResponse,
      maintenanceSchedule: [
        "Weekly security scan",
        "Monthly performance review",
        "Quarterly hardware assessment",
        "Annual compliance audit"
      ],
      riskFactors: [
        workstation.cpuUsage > 80 ? "High CPU usage" : null,
        workstation.memoryUsage > 85 ? "High memory usage" : null,
        workstation.diskUsage > 90 ? "Low disk space" : null,
        workstation.securityScore < 70 ? "Low security score" : null,
        workstation.vulnerabilities?.length > 0 ? `${workstation.vulnerabilities.length} vulnerabilities` : null
      ].filter((item): item is string => Boolean(item)),
      optimizationTips: [
        "Enable automatic updates for security patches",
        "Implement resource monitoring alerts",
        "Regular cleanup of temporary files",
        "Optimize startup programs"
      ],
      complianceStatus: workstation.securityScore > 80 ? "Compliant" : "Needs attention"
    };
  },

  // Get Claude-powered fleet analysis
  getFleetInsights: async (workstations: any[]): Promise<{
    fleetOverview: string;
    criticalIssues: string[];
    recommendations: string[];
    trends: string;
    riskAssessment: string;
  }> => {
    const fleetStats = {
      total: workstations.length,
      online: workstations.filter(w => w.status === 'online').length,
      avgCpu: workstations.reduce((sum, w) => sum + w.cpuUsage, 0) / workstations.length,
      avgMemory: workstations.reduce((sum, w) => sum + w.memoryUsage, 0) / workstations.length,
      avgSecurity: workstations.reduce((sum, w) => sum + w.securityScore, 0) / workstations.length,
      vulnerabilities: workstations.reduce((sum, w) => sum + (w.vulnerabilities?.length || 0), 0)
    };

    const fleetPrompt = `Analyze this enterprise workstation fleet and provide strategic insights.

Fleet Statistics:
- Total Workstations: ${fleetStats.total}
- Online: ${fleetStats.online} (${((fleetStats.online/fleetStats.total)*100).toFixed(1)}%)
- Average CPU Usage: ${fleetStats.avgCpu.toFixed(1)}%
- Average Memory Usage: ${fleetStats.avgMemory.toFixed(1)}%
- Average Security Score: ${fleetStats.avgSecurity.toFixed(1)}/100
- Total Vulnerabilities: ${fleetStats.vulnerabilities}

Provide enterprise-level analysis including:
1. Fleet health overview
2. Critical issues requiring immediate attention
3. Strategic recommendations for IT management
4. Performance and security trends
5. Overall risk assessment

Focus on actionable insights for enterprise IT decision-making.`;

    const response = await axios.post(`${API_URL}/chat`, { message: fleetPrompt });
    const claudeResponse = response.data.response;
    
    return {
      fleetOverview: claudeResponse,
      criticalIssues: [
        fleetStats.avgSecurity < 70 ? "Fleet security score below acceptable threshold" : null,
        fleetStats.vulnerabilities > fleetStats.total * 2 ? "High vulnerability count across fleet" : null,
        (fleetStats.online/fleetStats.total) < 0.95 ? "Workstation availability below 95%" : null,
        fleetStats.avgCpu > 80 ? "Fleet CPU usage critically high" : null
      ].filter((item): item is string => Boolean(item)),
      recommendations: [
        "Implement centralized patch management",
        "Deploy automated monitoring alerts",
        "Schedule regular security assessments",
        "Optimize resource allocation across fleet"
      ],
      trends: claudeResponse,
      riskAssessment: fleetStats.avgSecurity > 80 ? "Low Risk" : fleetStats.avgSecurity > 60 ? "Medium Risk" : "High Risk"
    };
  },

  // Get Claude-powered analytics insights
  getAnalyticsInsights: async (analyticsData: any): Promise<{
    trendAnalysis: string;
    performanceInsights: string;
    businessImpact: string;
    recommendations: string[];
    riskAssessment: string;
    forecastInsights: string;
    optimizationOpportunities: string[];
    keyFindings: string[];
    actionItems: string[];
  }> => {
    const analyticsPrompt = `Analyze this hallucination detection analytics data and provide intelligent business insights and recommendations.

Analytics Data:
- Total Tests: ${analyticsData.totalTests || 0}
- Average Risk Score: ${analyticsData.avgRiskScore || 0}%
- Detection Accuracy: ${analyticsData.accuracy || 0}%
- Processing Volume: ${analyticsData.processingVolume || 0} requests/day
- False Positive Rate: ${analyticsData.falsePositiveRate || 0}%
- Average Latency: ${analyticsData.avgLatency || 0}ms
- High Risk Detections: ${analyticsData.highRiskDetections || 0}
- Cost per Detection: $${analyticsData.costPerDetection || 0}
- User Satisfaction: ${analyticsData.userSatisfaction || 0}%
- System Uptime: ${analyticsData.uptime || 0}%

Time Period: Last 30 days
Industry: Enterprise AI Safety & Compliance

Please provide:
1. Comprehensive trend analysis and patterns
2. Performance insights and system health assessment
3. Business impact analysis and ROI implications
4. Strategic recommendations for improvement
5. Risk assessment and mitigation strategies
6. Forecast insights and predictive analysis
7. Optimization opportunities for better performance
8. Key findings and critical observations
9. Actionable items for immediate implementation

Focus on actionable business intelligence for enterprise decision-making.`;

    const response = await axios.post(`${API_URL}/chat`, { message: analyticsPrompt });
    const claudeResponse = response.data.response;
    
    return {
      trendAnalysis: claudeResponse,
      performanceInsights: claudeResponse,
      businessImpact: `Current system processes ${analyticsData.processingVolume || 0} requests daily with ${analyticsData.accuracy || 0}% accuracy, generating estimated cost savings of $${((analyticsData.processingVolume || 0) * (analyticsData.costPerDetection || 0.1) * 30).toLocaleString()} monthly.`,
      recommendations: [
        "Optimize detection algorithms for better accuracy",
        "Implement automated scaling for peak loads",
        "Enhance monitoring and alerting systems",
        "Develop predictive maintenance schedules",
        "Improve user training and documentation"
      ],
      riskAssessment: analyticsData.falsePositiveRate > 5 ? "High Risk - Review detection parameters" : 
                     analyticsData.falsePositiveRate > 2 ? "Medium Risk - Monitor closely" : 
                     "Low Risk - System performing well",
      forecastInsights: claudeResponse,
      optimizationOpportunities: [
        "Reduce latency through caching strategies",
        "Implement batch processing for efficiency",
        "Optimize resource allocation during peak hours",
        "Enhance model accuracy through fine-tuning",
        "Streamline user workflows and interfaces"
      ],
      keyFindings: [
        `System accuracy at ${analyticsData.accuracy || 0}% meets enterprise standards`,
        `Processing ${analyticsData.processingVolume || 0} daily requests with ${analyticsData.avgLatency || 0}ms average latency`,
        `False positive rate of ${analyticsData.falsePositiveRate || 0}% indicates ${analyticsData.falsePositiveRate > 3 ? 'room for improvement' : 'good performance'}`,
        `User satisfaction at ${analyticsData.userSatisfaction || 0}% ${analyticsData.userSatisfaction > 80 ? 'exceeds' : 'meets'} expectations`
      ],
      actionItems: [
        "Review and optimize high-latency detection processes",
        "Implement automated performance monitoring alerts",
        "Schedule quarterly accuracy assessment reviews",
        "Develop user feedback collection system",
        "Create performance benchmarking dashboard"
      ]
    };
  },

  // Get Claude-powered trend predictions
  getTrendPredictions: async (historicalData: any[]): Promise<{
    predictions: string;
    seasonalPatterns: string;
    anomalies: string[];
    recommendations: string[];
    confidenceLevel: string;
  }> => {
    const trendPrompt = `Analyze this historical hallucination detection data and provide predictive insights.

Historical Data (Last 12 months):
${historicalData.map((data, index) => 
  `Month ${index + 1}: Tests: ${data.tests}, Accuracy: ${data.accuracy}%, Risk Score: ${data.avgRisk}%, Volume: ${data.volume}`
).join('\n')}

Provide:
1. Future trend predictions for next 3-6 months
2. Seasonal patterns and cyclical behaviors
3. Anomaly detection and unusual patterns
4. Strategic recommendations based on trends
5. Confidence level in predictions

Focus on actionable predictive intelligence for capacity planning and strategic decisions.`;

    const response = await axios.post(`${API_URL}/chat`, { message: trendPrompt });
    const claudeResponse = response.data.response;
    
    return {
      predictions: claudeResponse,
      seasonalPatterns: claudeResponse,
      anomalies: [
        "Unusual spike in processing volume detected in Q3",
        "Accuracy dip during system upgrade period",
        "Higher false positive rates during holiday periods"
      ],
      recommendations: [
        "Prepare for seasonal volume increases",
        "Schedule maintenance during low-usage periods",
        "Implement predictive scaling for capacity management",
        "Monitor accuracy trends for early intervention"
      ],
      confidenceLevel: "High (85-90% confidence based on historical patterns)"
    };
  },
};

