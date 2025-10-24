/**
 * Enterprise Security Utilities
 * Critical input validation and sanitization for AgentGuard platform
 */

// Using built-in sanitization instead of DOMPurify to avoid ESM issues
// import DOMPurify from 'isomorphic-dompurify';

// Security configuration
const SECURITY_CONFIG = {
  MAX_INPUT_LENGTH: 50000,
  MAX_QUERY_LENGTH: 10000,
  ALLOWED_HTML_TAGS: [], // No HTML allowed in inputs
  BLOCKED_PATTERNS: [
    // SQL Injection patterns
    /(\b(union|select|insert|update|delete|drop|exec|script|alert|eval|expression)\b)/gi,
    // XSS patterns
    /<script[^>]*>.*?<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    // Command injection patterns
    /(\||&|;|`|\$\(|\$\{)/g,
    // Path traversal
    /\.\.\//g,
  ],
};

/**
 * Sanitize user input to prevent XSS and injection attacks
 */
export function sanitizeInput(input: string): string {
  if (!input || typeof input !== 'string') {
    return '';
  }

  // Length validation
  if (input.length > SECURITY_CONFIG.MAX_INPUT_LENGTH) {
    throw new Error(`Input exceeds maximum length of ${SECURITY_CONFIG.MAX_INPUT_LENGTH} characters`);
  }

  // Check for malicious patterns
  for (const pattern of SECURITY_CONFIG.BLOCKED_PATTERNS) {
    if (pattern.test(input)) {
      throw new Error('Input contains potentially malicious content');
    }
  }

  // Sanitize HTML and dangerous characters using built-in methods
  let sanitized = input
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+\s*=/gi, '') // Remove event handlers
    .replace(/&lt;script.*?&gt;.*?&lt;\/script&gt;/gi, '') // Remove script tags
    .replace(/<script.*?>.*?<\/script>/gi, ''); // Remove script tags

  // Additional character escaping
  return sanitized
    .replace(/[<>]/g, '') // Remove any remaining angle brackets
    .trim();
}

/**
 * Validate and sanitize API request data
 */
export interface SecureAgentTestRequest {
  agent_output: string;
  ground_truth: string;
  conversation_history?: string[];
  agent_id?: string;
  agent_name?: string;
}

export function validateAgentTestRequest(data: any): SecureAgentTestRequest {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid request data');
  }

  const { agent_output, ground_truth, conversation_history, agent_id, agent_name } = data;

  // Required fields validation
  if (!agent_output || typeof agent_output !== 'string') {
    throw new Error('agent_output is required and must be a string');
  }

  if (!ground_truth || typeof ground_truth !== 'string') {
    throw new Error('ground_truth is required and must be a string');
  }

  // Sanitize inputs
  const sanitizedRequest: SecureAgentTestRequest = {
    agent_output: sanitizeInput(agent_output),
    ground_truth: sanitizeInput(ground_truth),
  };

  // Optional fields
  if (conversation_history && Array.isArray(conversation_history)) {
    if (conversation_history.length > 50) {
      throw new Error('Conversation history too long (max 50 messages)');
    }
    sanitizedRequest.conversation_history = conversation_history.map(msg => 
      sanitizeInput(String(msg))
    );
  }

  if (agent_id && typeof agent_id === 'string') {
    sanitizedRequest.agent_id = sanitizeInput(agent_id);
  }

  if (agent_name && typeof agent_name === 'string') {
    sanitizedRequest.agent_name = sanitizeInput(agent_name);
  }

  return sanitizedRequest;
}

/**
 * Validate file uploads
 */
export function validateFileUpload(file: File): void {
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const ALLOWED_TYPES = ['application/json', 'text/csv', 'text/plain'];

  if (!file) {
    throw new Error('No file provided');
  }

  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`);
  }

  if (!ALLOWED_TYPES.includes(file.type)) {
    throw new Error(`File type ${file.type} not allowed. Allowed types: ${ALLOWED_TYPES.join(', ')}`);
  }

  // Check file name for path traversal
  if (file.name.includes('..') || file.name.includes('/') || file.name.includes('\\')) {
    throw new Error('Invalid file name');
  }
}

/**
 * Rate limiting helper
 */
class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private readonly maxRequests: number;
  private readonly windowMs: number;

  constructor(maxRequests: number = 100, windowMs: number = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  isAllowed(identifier: string): boolean {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];
    
    // Remove old requests outside the window
    const validRequests = requests.filter(time => now - time < this.windowMs);
    
    if (validRequests.length >= this.maxRequests) {
      return false;
    }

    // Add current request
    validRequests.push(now);
    this.requests.set(identifier, validRequests);
    
    return true;
  }

  getRemainingRequests(identifier: string): number {
    const now = Date.now();
    const requests = this.requests.get(identifier) || [];
    const validRequests = requests.filter(time => now - time < this.windowMs);
    
    return Math.max(0, this.maxRequests - validRequests.length);
  }
}

export const clientRateLimiter = new RateLimiter(50, 60000); // 50 requests per minute

/**
 * Secure API client with built-in validation
 */
export class SecureApiClient {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async secureRequest<T>(
    endpoint: string, 
    data?: any, 
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'POST'
  ): Promise<T> {
    // Rate limiting check
    const clientId = this.getClientId();
    if (!clientRateLimiter.isAllowed(clientId)) {
      throw new Error('Rate limit exceeded. Please try again later.');
    }

    // Input validation for POST/PUT requests
    if ((method === 'POST' || method === 'PUT') && data) {
      if (endpoint.includes('test-agent')) {
        data = validateAgentTestRequest(data);
      }
    }

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      'X-Client-Version': '1.0.0',
      'X-Request-ID': this.generateRequestId(),
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
      credentials: 'same-origin',
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    return response.json();
  }

  private getClientId(): string {
    // Use a combination of IP and user agent for rate limiting
    return `${window.navigator.userAgent.slice(0, 50)}_${Date.now().toString().slice(-6)}`;
  }

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

/**
 * Security event logger
 */
export class SecurityLogger {
  static logSecurityEvent(event: string, details: any = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      event,
      details,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // In production, send to security monitoring service
    if (process.env.NODE_ENV === 'production') {
      // Send to security monitoring endpoint
      fetch('/api/security/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logEntry),
      }).catch(console.error);
    } else {
      console.warn('Security Event:', logEntry);
    }
  }
}

/**
 * Content Security Policy violation handler
 */
export function setupCSPViolationHandler() {
  document.addEventListener('securitypolicyviolation', (event) => {
    SecurityLogger.logSecurityEvent('CSP_VIOLATION', {
      violatedDirective: event.violatedDirective,
      blockedURI: event.blockedURI,
      originalPolicy: event.originalPolicy,
      sourceFile: event.sourceFile,
      lineNumber: event.lineNumber,
    });
  });
}

// Initialize CSP violation handler
if (typeof window !== 'undefined') {
  setupCSPViolationHandler();
}
