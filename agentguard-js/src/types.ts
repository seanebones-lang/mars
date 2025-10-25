/**
 * AgentGuard SDK Types
 * Type definitions for all AgentGuard API requests and responses
 */

// Common types
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type BiasType = 'gender' | 'racial' | 'age' | 'ableist' | 'non_inclusive';
export type AttackType = 'prompt_injection' | 'jailbreak' | 'data_exfiltration' | 'privilege_escalation' | 'denial_of_service';
export type VotingStrategy = 'MAJORITY' | 'WEIGHTED' | 'UNANIMOUS' | 'CASCADING' | 'ADAPTIVE';

// Prompt Injection Detection
export interface PromptInjectionRequest {
  prompt: string;
  context?: string;
}

export interface PromptInjectionResult {
  is_injection: boolean;
  risk_level: RiskLevel;
  confidence: number;
  patterns_detected: Array<{
    pattern_id: string;
    pattern_name: string;
    severity: string;
  }>;
  recommendations: string[];
  processing_time: number;
}

// Multi-Model Consensus
export interface MultiModelConsensusRequest {
  text: string;
  context?: string;
  strategy?: VotingStrategy;
  context_complexity?: number;
  budget_constraint?: number;
}

export interface MultiModelConsensusResult {
  is_hallucination: boolean;
  confidence: number;
  risk_level: RiskLevel;
  model_votes: Record<string, {
    is_hallucination: boolean;
    confidence: number;
    reasoning: string;
  }>;
  consensus_method: string;
  cost_savings?: number;
  models_selected?: string[];
  recommendations: string[];
  processing_time: number;
}

// Multimodal Detection
export interface MultimodalDetectionRequest {
  text_description: string;
  image?: File | Buffer;
  video?: File | Buffer;
  audio?: File | Buffer;
  check_consistency?: boolean;
}

export interface MultimodalDetectionResult {
  is_hallucination: boolean;
  risk_level: RiskLevel;
  confidence: number;
  consistency_score: number;
  modality_scores: Record<string, number>;
  detected_objects?: string[];
  cross_modal_issues: string[];
  recommendations: string[];
  processing_time: number;
}

// Bias and Fairness Auditing
export interface BiasAuditRequest {
  text: string;
  context?: string;
  check_types?: BiasType[];
}

export interface BiasDetectionResult {
  has_bias: boolean;
  bias_types: BiasType[];
  severity: RiskLevel;
  confidence: number;
  detected_instances: Array<{
    bias_type: BiasType;
    text_segment: string;
    explanation: string;
    alternative_suggestion: string;
  }>;
  fairness_score: number;
  recommendations: string[];
  compliance_status: Record<string, boolean>;
  processing_time: number;
}

// Red Teaming
export interface RedTeamSimulationRequest {
  target_prompt: string;
  attack_types?: AttackType[];
  num_attacks?: number;
  severity_threshold?: string;
}

export interface AttackVector {
  attack_id: string;
  attack_type: AttackType;
  payload: string;
  expected_behavior: string;
  severity: string;
}

export interface AttackResult {
  attack_id: string;
  attack_type: AttackType;
  payload: string;
  success: boolean;
  response: string;
  risk_score: number;
  vulnerabilities: string[];
}

export interface RedTeamReport {
  total_attacks: number;
  successful_attacks: number;
  success_rate: number;
  attack_results: AttackResult[];
  vulnerabilities_found: string[];
  risk_score: number;
  recommendations: string[];
  compliance_gaps: Record<string, string[]>;
  processing_time: number;
}

// Compliance
export interface ComplianceReportRequest {
  scope?: string[];
  include_recommendations?: boolean;
}

export interface ComplianceReport {
  overall_status: 'compliant' | 'partial' | 'non_compliant';
  frameworks: Record<string, {
    status: 'compliant' | 'partial' | 'non_compliant';
    score: number;
    requirements_met: number;
    total_requirements: number;
    gaps: string[];
    recommendations: string[];
  }>;
  generated_at: string;
  next_review_date: string;
}

// PII Protection
export interface PIIDetectionRequest {
  text: string;
  redact?: boolean;
  entity_types?: string[];
}

export interface PIIDetectionResult {
  has_pii: boolean;
  entities_found: Array<{
    entity_type: string;
    text: string;
    start: number;
    end: number;
    confidence: number;
  }>;
  redacted_text?: string;
  risk_level: RiskLevel;
  compliance_standards: string[];
}

// RAG Security
export interface RAGSecurityRequest {
  query: string;
  retrieved_contexts: string[];
  check_injection?: boolean;
  check_poisoning?: boolean;
}

export interface RAGSecurityResult {
  is_safe: boolean;
  risk_level: RiskLevel;
  threats_detected: Array<{
    threat_type: string;
    severity: string;
    description: string;
  }>;
  context_integrity_score: number;
  recommendations: string[];
}

// Client Configuration
export interface AgentGuardConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  retries?: number;
}

// Error Response
export interface ErrorResponse {
  error: string;
  status_code: number;
  details?: string;
}

