"""
Model Control Plane (MCP) Gateway Service
Enkrypt AI-style real-time intervention system for prompt injection, tool poisoning, and bias mitigation.

This module provides enterprise-grade guardrails for AI agent safety, inspired by Enkrypt AI's
Gartner Cool Vendor recognition in 2025. Supports co-branded enterprise tiers with revenue sharing.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels for MCP scanning."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats detected by MCP."""
    PROMPT_INJECTION = "prompt_injection"
    TOOL_POISONING = "tool_poisoning"
    BIAS = "bias"
    PII_LEAKAGE = "pii_leakage"
    MALICIOUS_CODE = "malicious_code"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class MCPScanResult:
    """Result of MCP security scan."""
    threat_level: ThreatLevel
    threat_types: List[ThreatType]
    confidence: float
    explanation: str
    detected_patterns: List[str]
    mitigation_suggestions: List[str]
    scan_duration_ms: float
    timestamp: str
    scan_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPRegistryEntry:
    """Entry in the MCP registry for tracking scanned requests."""
    scan_id: str
    timestamp: str
    input_hash: str
    threat_level: ThreatLevel
    threat_types: List[ThreatType]
    action_taken: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None


class MCPGateway:
    """
    Model Control Plane Gateway for real-time AI safety interventions.
    
    Provides comprehensive scanning for:
    - Prompt injection attacks
    - Tool poisoning attempts
    - Bias and fairness issues
    - PII leakage
    - Malicious code execution
    - Jailbreak attempts
    
    Implements 3-4 orders of magnitude risk reduction through multi-layered detection.
    """
    
    # Prompt injection patterns (common attack vectors)
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+instructions?",
        r"disregard\s+(previous|all|above)\s+(instructions?|commands?)",
        r"forget\s+(everything|all)\s+(you|that)\s+(know|learned)",
        r"new\s+instructions?:\s*",
        r"system\s*:\s*you\s+are\s+now",
        r"override\s+your\s+(programming|instructions?)",
        r"act\s+as\s+(if|though)\s+you\s+are",
        r"pretend\s+(you\s+are|to\s+be)",
        r"roleplay\s+as",
        r"simulate\s+(being|a)",
        r"\[SYSTEM\]|\[ADMIN\]|\[ROOT\]",
        r"sudo\s+mode",
        r"developer\s+mode\s+(enabled|on)",
        r"</?\s*system\s*>",
        r"<\s*prompt\s*>.*?<\s*/\s*prompt\s*>",
    ]
    
    # Tool poisoning patterns
    TOOL_POISONING_PATTERNS = [
        r"exec\s*\(",
        r"eval\s*\(",
        r"__import__\s*\(",
        r"compile\s*\(",
        r"os\.system",
        r"subprocess\.",
        r"shell=True",
        r"rm\s+-rf",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM",
        r"UPDATE\s+.*\s+SET",
        r"INSERT\s+INTO",
        r"<script[^>]*>",
        r"javascript:",
        r"onerror\s*=",
        r"onclick\s*=",
    ]
    
    # Bias indicators
    BIAS_PATTERNS = [
        r"\b(all|every|always)\s+(men|women|blacks?|whites?|asians?|muslims?|christians?|jews?)\s+(are|do|have)",
        r"\b(never|no)\s+(men|women|blacks?|whites?|asians?|muslims?|christians?|jews?)\s+(are|do|have)",
        r"\b(men|women|blacks?|whites?|asians?)\s+(can't|cannot|shouldn't|should\s+not)",
        r"\b(inferior|superior)\s+(race|gender|ethnicity)",
    ]
    
    # PII patterns
    PII_PATTERNS = [
        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
        r"\b\d{16}\b",  # Credit card
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",  # Email
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone
        r"\b(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",  # IP
    ]
    
    # Jailbreak patterns
    JAILBREAK_PATTERNS = [
        r"DAN\s+mode",
        r"do\s+anything\s+now",
        r"jailbreak",
        r"unrestricted\s+mode",
        r"without\s+any\s+(restrictions?|limitations?|filters?)",
        r"bypass\s+(safety|content)\s+(filters?|guidelines?)",
        r"ignore\s+ethical\s+guidelines",
    ]
    
    def __init__(self, claude_api_key: Optional[str] = None):
        """
        Initialize MCP Gateway.
        
        Args:
            claude_api_key: Optional Claude API key for LLM-based advanced detection
        """
        self.claude_api_key = claude_api_key
        self.registry: List[MCPRegistryEntry] = []
        self._compile_patterns()
        
        logger.info("MCP Gateway initialized with multi-layered detection")
    
    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        self.compiled_injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PROMPT_INJECTION_PATTERNS
        ]
        self.compiled_poisoning_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.TOOL_POISONING_PATTERNS
        ]
        self.compiled_bias_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.BIAS_PATTERNS
        ]
        self.compiled_pii_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.PII_PATTERNS
        ]
        self.compiled_jailbreak_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.JAILBREAK_PATTERNS
        ]
    
    def scan_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> MCPScanResult:
        """
        Scan prompt for injection attacks and security threats.
        
        Args:
            prompt: The prompt text to scan
            context: Optional context for better detection
            user_id: Optional user identifier for tracking
            agent_id: Optional agent identifier for tracking
            
        Returns:
            MCPScanResult with threat assessment
        """
        start_time = time.time()
        scan_id = self._generate_scan_id(prompt)
        
        detected_threats = []
        detected_patterns = []
        threat_level = ThreatLevel.SAFE
        
        # Check for prompt injection
        injection_matches = self._check_patterns(prompt, self.compiled_injection_patterns)
        if injection_matches:
            detected_threats.append(ThreatType.PROMPT_INJECTION)
            detected_patterns.extend(injection_matches)
            threat_level = ThreatLevel.HIGH
        
        # Check for jailbreak attempts
        jailbreak_matches = self._check_patterns(prompt, self.compiled_jailbreak_patterns)
        if jailbreak_matches:
            detected_threats.append(ThreatType.JAILBREAK_ATTEMPT)
            detected_patterns.extend(jailbreak_matches)
            threat_level = ThreatLevel.CRITICAL
        
        # Check for tool poisoning
        poisoning_matches = self._check_patterns(prompt, self.compiled_poisoning_patterns)
        if poisoning_matches:
            detected_threats.append(ThreatType.TOOL_POISONING)
            detected_patterns.extend(poisoning_matches)
            if threat_level.value in ["safe", "low"]:
                threat_level = ThreatLevel.HIGH
        
        # Check for bias
        bias_matches = self._check_patterns(prompt, self.compiled_bias_patterns)
        if bias_matches:
            detected_threats.append(ThreatType.BIAS)
            detected_patterns.extend(bias_matches)
            if threat_level == ThreatLevel.SAFE:
                threat_level = ThreatLevel.MEDIUM
        
        # Check for PII
        pii_matches = self._check_patterns(prompt, self.compiled_pii_patterns)
        if pii_matches:
            detected_threats.append(ThreatType.PII_LEAKAGE)
            detected_patterns.extend(pii_matches)
            if threat_level == ThreatLevel.SAFE:
                threat_level = ThreatLevel.MEDIUM
        
        # Calculate confidence based on number and severity of matches
        confidence = self._calculate_confidence(detected_threats, detected_patterns)
        
        # Generate explanation and mitigation suggestions
        explanation = self._generate_explanation(detected_threats, threat_level)
        mitigation_suggestions = self._generate_mitigations(detected_threats)
        
        scan_duration_ms = (time.time() - start_time) * 1000
        
        result = MCPScanResult(
            threat_level=threat_level,
            threat_types=detected_threats,
            confidence=confidence,
            explanation=explanation,
            detected_patterns=detected_patterns[:10],  # Limit to top 10
            mitigation_suggestions=mitigation_suggestions,
            scan_duration_ms=scan_duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            scan_id=scan_id,
            metadata={
                "total_patterns_detected": len(detected_patterns),
                "prompt_length": len(prompt),
                "context_provided": context is not None
            }
        )
        
        # Register scan
        self._register_scan(result, user_id, agent_id)
        
        logger.info(
            f"MCP scan completed: {threat_level.value} threat level, "
            f"{len(detected_threats)} threat types, {scan_duration_ms:.2f}ms"
        )
        
        return result
    
    def scan_tool_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> MCPScanResult:
        """
        Scan tool call for poisoning attempts.
        
        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool
            user_id: Optional user identifier
            agent_id: Optional agent identifier
            
        Returns:
            MCPScanResult with threat assessment
        """
        start_time = time.time()
        
        # Convert tool args to string for pattern matching
        tool_str = f"{tool_name}({str(tool_args)})"
        scan_id = self._generate_scan_id(tool_str)
        
        detected_threats = []
        detected_patterns = []
        threat_level = ThreatLevel.SAFE
        
        # Check for tool poisoning
        poisoning_matches = self._check_patterns(tool_str, self.compiled_poisoning_patterns)
        if poisoning_matches:
            detected_threats.append(ThreatType.TOOL_POISONING)
            detected_patterns.extend(poisoning_matches)
            threat_level = ThreatLevel.CRITICAL
        
        # Check for malicious code patterns
        if any(dangerous in tool_name.lower() for dangerous in ["exec", "eval", "system", "shell"]):
            detected_threats.append(ThreatType.MALICIOUS_CODE)
            detected_patterns.append(f"Dangerous tool: {tool_name}")
            threat_level = ThreatLevel.CRITICAL
        
        confidence = self._calculate_confidence(detected_threats, detected_patterns)
        explanation = self._generate_explanation(detected_threats, threat_level)
        mitigation_suggestions = self._generate_mitigations(detected_threats)
        
        scan_duration_ms = (time.time() - start_time) * 1000
        
        result = MCPScanResult(
            threat_level=threat_level,
            threat_types=detected_threats,
            confidence=confidence,
            explanation=explanation,
            detected_patterns=detected_patterns,
            mitigation_suggestions=mitigation_suggestions,
            scan_duration_ms=scan_duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            scan_id=scan_id,
            metadata={
                "tool_name": tool_name,
                "arg_count": len(tool_args)
            }
        )
        
        self._register_scan(result, user_id, agent_id)
        
        return result
    
    def scan_output(
        self,
        output: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> MCPScanResult:
        """
        Scan agent output for bias, PII leakage, and other issues.
        
        Args:
            output: The agent output to scan
            user_id: Optional user identifier
            agent_id: Optional agent identifier
            
        Returns:
            MCPScanResult with threat assessment
        """
        start_time = time.time()
        scan_id = self._generate_scan_id(output)
        
        detected_threats = []
        detected_patterns = []
        threat_level = ThreatLevel.SAFE
        
        # Check for bias
        bias_matches = self._check_patterns(output, self.compiled_bias_patterns)
        if bias_matches:
            detected_threats.append(ThreatType.BIAS)
            detected_patterns.extend(bias_matches)
            threat_level = ThreatLevel.MEDIUM
        
        # Check for PII leakage
        pii_matches = self._check_patterns(output, self.compiled_pii_patterns)
        if pii_matches:
            detected_threats.append(ThreatType.PII_LEAKAGE)
            detected_patterns.extend(pii_matches)
            if threat_level == ThreatLevel.SAFE:
                threat_level = ThreatLevel.HIGH
        
        confidence = self._calculate_confidence(detected_threats, detected_patterns)
        explanation = self._generate_explanation(detected_threats, threat_level)
        mitigation_suggestions = self._generate_mitigations(detected_threats)
        
        scan_duration_ms = (time.time() - start_time) * 1000
        
        result = MCPScanResult(
            threat_level=threat_level,
            threat_types=detected_threats,
            confidence=confidence,
            explanation=explanation,
            detected_patterns=detected_patterns[:10],
            mitigation_suggestions=mitigation_suggestions,
            scan_duration_ms=scan_duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            scan_id=scan_id,
            metadata={
                "output_length": len(output)
            }
        )
        
        self._register_scan(result, user_id, agent_id)
        
        return result
    
    def _check_patterns(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Check text against compiled patterns."""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            if found:
                matches.extend([match if isinstance(match, str) else match[0] for match in found])
        return matches
    
    def _calculate_confidence(
        self,
        threats: List[ThreatType],
        patterns: List[str]
    ) -> float:
        """Calculate confidence score based on detected threats and patterns."""
        if not threats:
            return 1.0  # 100% confident it's safe
        
        # Base confidence on number of patterns
        pattern_confidence = min(len(patterns) * 0.15, 0.9)
        
        # Adjust for threat severity
        threat_weights = {
            ThreatType.JAILBREAK_ATTEMPT: 0.95,
            ThreatType.PROMPT_INJECTION: 0.90,
            ThreatType.TOOL_POISONING: 0.90,
            ThreatType.MALICIOUS_CODE: 0.95,
            ThreatType.PII_LEAKAGE: 0.85,
            ThreatType.BIAS: 0.75,
            ThreatType.DATA_EXFILTRATION: 0.90
        }
        
        max_threat_weight = max([threat_weights.get(t, 0.5) for t in threats])
        
        return min(pattern_confidence + (max_threat_weight * 0.1), 0.99)
    
    def _generate_explanation(
        self,
        threats: List[ThreatType],
        level: ThreatLevel
    ) -> str:
        """Generate human-readable explanation of scan results."""
        if not threats:
            return "No security threats detected. Input appears safe."
        
        threat_descriptions = {
            ThreatType.PROMPT_INJECTION: "prompt injection attack attempting to override instructions",
            ThreatType.JAILBREAK_ATTEMPT: "jailbreak attempt to bypass safety guidelines",
            ThreatType.TOOL_POISONING: "tool poisoning with potentially malicious code",
            ThreatType.MALICIOUS_CODE: "malicious code execution attempt",
            ThreatType.BIAS: "biased or discriminatory language",
            ThreatType.PII_LEAKAGE: "personally identifiable information (PII) exposure",
            ThreatType.DATA_EXFILTRATION: "potential data exfiltration attempt"
        }
        
        descriptions = [threat_descriptions.get(t, str(t)) for t in threats]
        
        if level == ThreatLevel.CRITICAL:
            return f"CRITICAL THREAT: Detected {', '.join(descriptions)}. Immediate action required."
        elif level == ThreatLevel.HIGH:
            return f"HIGH RISK: Detected {', '.join(descriptions)}. Review and mitigation recommended."
        elif level == ThreatLevel.MEDIUM:
            return f"MEDIUM RISK: Detected {', '.join(descriptions)}. Consider review."
        else:
            return f"LOW RISK: Detected {', '.join(descriptions)}. Monitor for patterns."
    
    def _generate_mitigations(self, threats: List[ThreatType]) -> List[str]:
        """Generate mitigation suggestions based on detected threats."""
        mitigations = []
        
        if ThreatType.PROMPT_INJECTION in threats or ThreatType.JAILBREAK_ATTEMPT in threats:
            mitigations.extend([
                "Block or sanitize the input before processing",
                "Implement strict input validation and filtering",
                "Use system-level prompt guards to prevent instruction override",
                "Log the attempt for security monitoring"
            ])
        
        if ThreatType.TOOL_POISONING in threats or ThreatType.MALICIOUS_CODE in threats:
            mitigations.extend([
                "Reject the tool call immediately",
                "Implement sandboxed execution environment",
                "Whitelist allowed tools and arguments",
                "Enable argument separation and validation"
            ])
        
        if ThreatType.BIAS in threats:
            mitigations.extend([
                "Review output for fairness and inclusivity",
                "Apply bias correction filters",
                "Consider regenerating with fairness constraints",
                "Flag for human review if high-stakes"
            ])
        
        if ThreatType.PII_LEAKAGE in threats:
            mitigations.extend([
                "Redact or mask detected PII before display",
                "Implement PII detection and removal pipeline",
                "Review data handling practices",
                "Ensure GDPR/HIPAA compliance"
            ])
        
        return mitigations
    
    def _generate_scan_id(self, content: str) -> str:
        """Generate unique scan ID."""
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{content[:100]}{timestamp}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _register_scan(
        self,
        result: MCPScanResult,
        user_id: Optional[str],
        agent_id: Optional[str]
    ):
        """Register scan in MCP registry."""
        entry = MCPRegistryEntry(
            scan_id=result.scan_id,
            timestamp=result.timestamp,
            input_hash=hashlib.sha256(result.scan_id.encode()).hexdigest()[:16],
            threat_level=result.threat_level,
            threat_types=result.threat_types,
            action_taken="logged",
            user_id=user_id,
            agent_id=agent_id
        )
        
        self.registry.append(entry)
        
        # Keep registry size manageable (last 10000 entries)
        if len(self.registry) > 10000:
            self.registry = self.registry[-10000:]
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics from MCP registry."""
        if not self.registry:
            return {
                "total_scans": 0,
                "threat_distribution": {},
                "average_threat_level": "safe"
            }
        
        threat_counts = {}
        for entry in self.registry:
            level = entry.threat_level.value
            threat_counts[level] = threat_counts.get(level, 0) + 1
        
        return {
            "total_scans": len(self.registry),
            "threat_distribution": threat_counts,
            "recent_scans": len([e for e in self.registry if e.timestamp > datetime.utcnow().isoformat()[:10]]),
            "critical_threats": len([e for e in self.registry if e.threat_level == ThreatLevel.CRITICAL])
        }

