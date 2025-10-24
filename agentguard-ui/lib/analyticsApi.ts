/**
 * Analytics API client for graph database and RAG endpoints
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance for analytics API
const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

export interface AnalyticsOverview {
  agent_metrics: {
    total_responses: number;
    avg_hallucination_risk: number;
    avg_confidence: number;
    flagged_responses: number;
    avg_processing_time: number;
    trend: string;
  };
  hallucination_patterns: Array<{
    pattern: string;
    frequency: number;
    severity: string;
  }>;
  time_series: Array<{
    date: string;
    total_responses: number;
    avg_hallucination_risk: number;
    flagged_responses: number;
    avg_processing_time: number;
  }>;
  summary: {
    total_agents: number;
    total_patterns: number;
    data_points: number;
  };
}

export interface AgentMetrics {
  agent_id: string;
  agent_name: string;
  total_responses: number;
  avg_hallucination_risk: number;
  avg_confidence: number;
  flagged_responses: number;
  avg_processing_time: number;
}

export interface SimilarResponse {
  id: string;
  text: string;
  similarity: number;
  hallucination_risk: number;
  confidence: number;
  timestamp: string;
}

export interface RAGTestRequest {
  agent_output: string;
  ground_truth?: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

export interface RAGTestResponse {
  hallucination_risk: number;
  uncertainty: number;
  needs_review: boolean;
  details: {
    claude_explanation?: string;
    statistical_score?: number;
    hallucinated_segments?: string[];
    rag_similar_cases_count?: number;
    rag_pattern_matches?: Array<{
      pattern: string;
      frequency: number;
      severity: string;
      confidence_boost: number;
    }>;
    rag_contextual_explanation?: string;
    rag_confidence_adjustment?: number;
    rag_suggested_corrections?: string[];
  };
}

/**
 * Get comprehensive analytics overview
 */
export const getAnalyticsOverview = async (days: number = 30): Promise<AnalyticsOverview> => {
  const response = await api.get(`/analytics/overview?days=${days}`);
  return response.data.data;
};

/**
 * Get agent performance analytics
 */
export const getAgentAnalytics = async (agentId?: string, days: number = 30): Promise<AgentMetrics | { agents: AgentMetrics[] }> => {
  const params = new URLSearchParams({ days: days.toString() });
  if (agentId) {
    params.append('agent_id', agentId);
  }
  
  const response = await api.get(`/analytics/agents?${params}`);
  return response.data.data;
};

/**
 * Get hallucination patterns
 */
export const getHallucinationPatterns = async (limit: number = 20) => {
  const response = await api.get(`/analytics/patterns?limit=${limit}`);
  return response.data.data;
};

/**
 * Get time series data for charts
 */
export const getTimeSeriesData = async (days: number = 30, interval: 'hour' | 'day' = 'day') => {
  const response = await api.get(`/analytics/timeseries?days=${days}&interval=${interval}`);
  return response.data.data;
};

/**
 * Find similar responses using RAG
 */
export const findSimilarResponses = async (
  queryText: string,
  responseText: string,
  limit: number = 5,
  similarityThreshold: number = 0.7
): Promise<SimilarResponse[]> => {
  const response = await api.post('/analytics/similar', {
    query_text: queryText,
    response_text: responseText,
    limit,
    similarity_threshold: similarityThreshold
  });
  return response.data.data;
};

/**
 * Test agent output with RAG enhancement
 */
export const testAgentWithRAG = async (
  request: RAGTestRequest,
  agentId: string = 'unknown',
  agentName: string = 'Unknown Agent',
  useRAG: boolean = true
): Promise<RAGTestResponse> => {
  const params = new URLSearchParams({
    agent_id: agentId,
    agent_name: agentName,
    use_rag: useRAG.toString()
  });
  
  const response = await api.post(`/test-agent-rag?${params}`, request);
  return response.data;
};
