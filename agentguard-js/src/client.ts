/**
 * AgentGuard SDK Client
 * Official JavaScript/TypeScript client for the AgentGuard AI Safety Platform
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import FormData from 'form-data';
import * as types from './types';

export class AgentGuardError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: string
  ) {
    super(message);
    this.name = 'AgentGuardError';
  }
}

export class AgentGuardClient {
  private client: AxiosInstance;
  private apiKey: string;

  constructor(config: types.AgentGuardConfig) {
    this.apiKey = config.apiKey;
    
    this.client = axios.create({
      baseURL: config.baseUrl || 'https://api.agentguard.io',
      timeout: config.timeout || 30000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
    });

    // Add retry logic
    if (config.retries && config.retries > 0) {
      this.client.interceptors.response.use(
        response => response,
        async error => {
          const retries = config.retries || 0;
          if (error.config && error.config.__retryCount < retries) {
            error.config.__retryCount = error.config.__retryCount || 0;
            error.config.__retryCount++;
            
            // Exponential backoff
            const delay = Math.pow(2, error.config.__retryCount) * 1000;
            await new Promise(resolve => setTimeout(resolve, delay));
            
            return this.client.request(error.config);
          }
          return Promise.reject(error);
        }
      );
    }
  }

  private handleError(error: AxiosError): never {
    if (error.response) {
      const data = error.response.data as types.ErrorResponse;
      throw new AgentGuardError(
        data.error || 'API request failed',
        error.response.status,
        data.details
      );
    } else if (error.request) {
      throw new AgentGuardError('No response from server', undefined, error.message);
    } else {
      throw new AgentGuardError('Request setup failed', undefined, error.message);
    }
  }

  /**
   * Prompt Injection Detection
   * Detects and prevents prompt injection attacks
   */
  async detectPromptInjection(
    request: types.PromptInjectionRequest
  ): Promise<types.PromptInjectionResult> {
    try {
      const response = await this.client.post('/prompt-injection/detect', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Multi-Model Consensus Detection
   * Uses ensemble voting across multiple models for improved accuracy
   */
  async detectHallucination(
    request: types.MultiModelConsensusRequest
  ): Promise<types.MultiModelConsensusResult> {
    try {
      const response = await this.client.post('/multi-model/detect', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Multimodal Hallucination Detection
   * Detects hallucinations across text, image, video, and audio
   */
  async detectMultimodal(
    request: types.MultimodalDetectionRequest
  ): Promise<types.MultimodalDetectionResult> {
    try {
      const formData = new FormData();
      formData.append('text_description', request.text_description);
      
      if (request.image) {
        formData.append('image', request.image);
      }
      if (request.video) {
        formData.append('video', request.video);
      }
      if (request.audio) {
        formData.append('audio', request.audio);
      }
      if (request.check_consistency !== undefined) {
        formData.append('check_consistency', String(request.check_consistency));
      }

      const response = await this.client.post('/multimodal/detect-image', formData, {
        headers: {
          ...formData.getHeaders(),
          'Authorization': `Bearer ${this.apiKey}`,
        },
      });
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Bias and Fairness Auditing
   * Detects bias and provides fairness metrics
   */
  async auditBias(
    request: types.BiasAuditRequest
  ): Promise<types.BiasDetectionResult> {
    try {
      const response = await this.client.post('/bias/audit', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Red Team Simulation
   * Runs automated adversarial testing
   */
  async runRedTeamSimulation(
    request: types.RedTeamSimulationRequest
  ): Promise<types.RedTeamReport> {
    try {
      const response = await this.client.post('/redteam/simulate', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Get Available Attack Vectors
   * Lists all available attack vectors for red teaming
   */
  async getAttackVectors(): Promise<types.AttackVector[]> {
    try {
      const response = await this.client.get('/redteam/get-attack-vectors');
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Generate Compliance Report
   * Creates comprehensive compliance report across multiple frameworks
   */
  async generateComplianceReport(
    request?: types.ComplianceReportRequest
  ): Promise<types.ComplianceReport> {
    try {
      const response = await this.client.post('/compliance/report', request || {});
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * PII Detection and Redaction
   * Detects and optionally redacts personally identifiable information
   */
  async detectPII(
    request: types.PIIDetectionRequest
  ): Promise<types.PIIDetectionResult> {
    try {
      const response = await this.client.post('/pii-protection/detect', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * RAG Security Check
   * Validates security of RAG (Retrieval-Augmented Generation) systems
   */
  async checkRAGSecurity(
    request: types.RAGSecurityRequest
  ): Promise<types.RAGSecurityResult> {
    try {
      const response = await this.client.post('/rag-security/validate', request);
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }

  /**
   * Health Check
   * Checks API health and availability
   */
  async healthCheck(): Promise<{ status: string; [key: string]: any }> {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error) {
      this.handleError(error as AxiosError);
    }
  }
}

