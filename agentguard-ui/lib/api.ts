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
};

