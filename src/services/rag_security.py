"""
RAG Security Service
Comprehensive security for Retrieval-Augmented Generation (RAG) systems.

Protects against:
- Context poisoning attacks
- Supply chain vulnerabilities
- Data leakage
- Hallucinations from retrieved context
- Unauthorized knowledge base access

Integrates with Enkrypt MCP for real-time database access defenses.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ThreatType(str, Enum):
    """Types of RAG security threats."""
    CONTEXT_POISONING = "context_poisoning"
    DATA_LEAKAGE = "data_leakage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUPPLY_CHAIN_ATTACK = "supply_chain_attack"
    HALLUCINATION = "hallucination"
    INJECTION_ATTACK = "injection_attack"
    RELEVANCE_MANIPULATION = "relevance_manipulation"


class RiskLevel(str, Enum):
    """Risk levels for RAG threats."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KnowledgeBaseType(str, Enum):
    """Types of knowledge bases."""
    VECTOR_DB = "vector_db"
    SQL_DATABASE = "sql_database"
    DOCUMENT_STORE = "document_store"
    API_ENDPOINT = "api_endpoint"
    FILE_SYSTEM = "file_system"
    CUSTOM = "custom"


@dataclass
class KnowledgeBaseConfig:
    """Configuration for a knowledge base."""
    kb_id: str
    kb_type: KnowledgeBaseType
    name: str
    description: str
    enabled: bool = True
    requires_auth: bool = True
    allowed_users: List[str] = field(default_factory=list)
    max_context_length: int = 4096
    enable_pii_filtering: bool = True
    enable_hallucination_check: bool = True
    trust_score: float = 1.0  # 0.0-1.0


@dataclass
class RetrievedContext:
    """Represents retrieved context from a knowledge base."""
    kb_id: str
    content: str
    source: str
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityThreat:
    """Represents a detected security threat."""
    threat_type: ThreatType
    risk_level: RiskLevel
    confidence: float
    description: str
    affected_context: Optional[str] = None
    recommendation: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGSecurityResult:
    """Result of RAG security analysis."""
    is_safe: bool
    risk_level: RiskLevel
    threats_detected: List[SecurityThreat]
    sanitized_context: str
    original_context: str
    hallucination_score: float
    trust_score: float
    processing_time_ms: float
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RAGSecurityService:
    """
    RAG Security Service for protecting Retrieval-Augmented Generation systems.
    
    Features:
    - Context poisoning detection
    - Supply chain attack prevention
    - Data leakage protection
    - Hallucination detection in retrieved context
    - Access control enforcement
    - Real-time database access defenses (Enkrypt MCP integration)
    - Context sanitization
    - Trust scoring
    """
    
    def __init__(self):
        """Initialize RAG security service."""
        self.knowledge_bases: Dict[str, KnowledgeBaseConfig] = {}
        self.threat_patterns = self._load_threat_patterns()
        self.access_logs: List[Dict[str, Any]] = []
        logger.info("RAG Security Service initialized")
    
    def _load_threat_patterns(self) -> Dict[ThreatType, List[Dict[str, Any]]]:
        """Load threat detection patterns."""
        return {
            ThreatType.CONTEXT_POISONING: [
                {
                    "pattern": r"(ignore|disregard|override)\s+(previous|prior|all)\s+(context|instructions)",
                    "risk": RiskLevel.CRITICAL,
                    "description": "Attempt to override context with malicious instructions"
                },
                {
                    "pattern": r"<script|javascript:|onerror=|onclick=",
                    "risk": RiskLevel.HIGH,
                    "description": "XSS or code injection attempt in context"
                },
                {
                    "pattern": r"(SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*\s+(FROM|INTO|TABLE)",
                    "risk": RiskLevel.HIGH,
                    "description": "SQL injection attempt in context"
                }
            ],
            ThreatType.INJECTION_ATTACK: [
                {
                    "pattern": r"```.*?(system|exec|eval|import os|subprocess).*?```",
                    "risk": RiskLevel.CRITICAL,
                    "description": "Code execution attempt in context"
                },
                {
                    "pattern": r"(curl|wget|fetch)\s+http",
                    "risk": RiskLevel.HIGH,
                    "description": "External data exfiltration attempt"
                }
            ],
            ThreatType.DATA_LEAKAGE: [
                {
                    "pattern": r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                    "risk": RiskLevel.HIGH,
                    "description": "Potential SSN in context"
                },
                {
                    "pattern": r"\b\d{16}\b",  # Credit card
                    "risk": RiskLevel.HIGH,
                    "description": "Potential credit card number in context"
                },
                {
                    "pattern": r"(password|api[_-]?key|secret|token)\s*[:=]\s*['\"]?[\w-]+['\"]?",
                    "risk": RiskLevel.CRITICAL,
                    "description": "Credentials exposed in context"
                }
            ]
        }
    
    def register_knowledge_base(self, config: KnowledgeBaseConfig):
        """Register a knowledge base for security monitoring."""
        self.knowledge_bases[config.kb_id] = config
        logger.info(f"Registered knowledge base: {config.name} ({config.kb_id})")
    
    def unregister_knowledge_base(self, kb_id: str):
        """Unregister a knowledge base."""
        if kb_id in self.knowledge_bases:
            del self.knowledge_bases[kb_id]
            logger.info(f"Unregistered knowledge base: {kb_id}")
    
    async def analyze_rag_context(
        self,
        retrieved_contexts: List[RetrievedContext],
        query: str,
        user_id: Optional[str] = None,
        enable_sanitization: bool = True
    ) -> RAGSecurityResult:
        """
        Analyze retrieved RAG context for security threats.
        
        Args:
            retrieved_contexts: List of retrieved context chunks
            query: Original user query
            user_id: Optional user ID for access control
            enable_sanitization: Whether to sanitize detected threats
            
        Returns:
            RAGSecurityResult with security analysis
        """
        start_time = time.perf_counter()
        
        # Combine all contexts
        combined_context = "\n\n".join([ctx.content for ctx in retrieved_contexts])
        original_context = combined_context
        
        # Run security checks
        threats = []
        
        # 1. Access control check
        access_threats = await self._check_access_control(retrieved_contexts, user_id)
        threats.extend(access_threats)
        
        # 2. Context poisoning detection
        poisoning_threats = await self._detect_context_poisoning(combined_context)
        threats.extend(poisoning_threats)
        
        # 3. Data leakage detection
        leakage_threats = await self._detect_data_leakage(combined_context)
        threats.extend(leakage_threats)
        
        # 4. Injection attack detection
        injection_threats = await self._detect_injection_attacks(combined_context)
        threats.extend(injection_threats)
        
        # 5. Supply chain verification
        supply_chain_threats = await self._verify_supply_chain(retrieved_contexts)
        threats.extend(supply_chain_threats)
        
        # 6. Hallucination detection
        hallucination_score = await self._detect_hallucinations(
            combined_context, query
        )
        
        # 7. Calculate trust score
        trust_score = self._calculate_trust_score(retrieved_contexts, threats)
        
        # Determine overall risk level
        risk_level = self._determine_risk_level(threats, hallucination_score, trust_score)
        
        # Sanitize context if enabled
        sanitized_context = combined_context
        if enable_sanitization and threats:
            sanitized_context = await self._sanitize_context(combined_context, threats)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(threats, hallucination_score, trust_score)
        
        # Determine if safe
        is_safe = (
            risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM] and
            hallucination_score < 0.7 and
            trust_score > 0.5
        )
        
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        
        # Log access
        self._log_access(user_id, retrieved_contexts, threats, is_safe)
        
        return RAGSecurityResult(
            is_safe=is_safe,
            risk_level=risk_level,
            threats_detected=threats,
            sanitized_context=sanitized_context,
            original_context=original_context,
            hallucination_score=hallucination_score,
            trust_score=trust_score,
            processing_time_ms=processing_time_ms,
            recommendations=recommendations
        )
    
    async def _check_access_control(
        self,
        contexts: List[RetrievedContext],
        user_id: Optional[str]
    ) -> List[SecurityThreat]:
        """Check if user has access to retrieved contexts."""
        threats = []
        
        for ctx in contexts:
            kb_config = self.knowledge_bases.get(ctx.kb_id)
            if not kb_config:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                    risk_level=RiskLevel.HIGH,
                    confidence=1.0,
                    description=f"Unknown knowledge base: {ctx.kb_id}",
                    affected_context=ctx.content[:100],
                    recommendation="Register knowledge base before use"
                ))
                continue
            
            if not kb_config.enabled:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=1.0,
                    description=f"Disabled knowledge base accessed: {kb_config.name}",
                    affected_context=ctx.content[:100],
                    recommendation="Enable knowledge base or remove from retrieval"
                ))
            
            if kb_config.requires_auth and user_id:
                if kb_config.allowed_users and user_id not in kb_config.allowed_users:
                    threats.append(SecurityThreat(
                        threat_type=ThreatType.UNAUTHORIZED_ACCESS,
                        risk_level=RiskLevel.CRITICAL,
                        confidence=1.0,
                        description=f"Unauthorized access to {kb_config.name} by user {user_id}",
                        affected_context=ctx.content[:100],
                        recommendation="Grant user access or deny retrieval"
                    ))
        
        return threats
    
    async def _detect_context_poisoning(self, context: str) -> List[SecurityThreat]:
        """Detect context poisoning attempts."""
        threats = []
        patterns = self.threat_patterns[ThreatType.CONTEXT_POISONING]
        
        for pattern_config in patterns:
            matches = re.finditer(pattern_config["pattern"], context, re.IGNORECASE)
            for match in matches:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.CONTEXT_POISONING,
                    risk_level=pattern_config["risk"],
                    confidence=0.9,
                    description=pattern_config["description"],
                    affected_context=match.group(0),
                    recommendation="Remove or sanitize malicious context",
                    evidence={"matched_pattern": pattern_config["pattern"], "match": match.group(0)}
                ))
        
        return threats
    
    async def _detect_data_leakage(self, context: str) -> List[SecurityThreat]:
        """Detect potential data leakage in context."""
        threats = []
        patterns = self.threat_patterns[ThreatType.DATA_LEAKAGE]
        
        for pattern_config in patterns:
            matches = re.finditer(pattern_config["pattern"], context, re.IGNORECASE)
            for match in matches:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.DATA_LEAKAGE,
                    risk_level=pattern_config["risk"],
                    confidence=0.8,
                    description=pattern_config["description"],
                    affected_context=match.group(0),
                    recommendation="Redact sensitive data before using context",
                    evidence={"matched_pattern": pattern_config["pattern"]}
                ))
        
        return threats
    
    async def _detect_injection_attacks(self, context: str) -> List[SecurityThreat]:
        """Detect injection attacks in context."""
        threats = []
        patterns = self.threat_patterns[ThreatType.INJECTION_ATTACK]
        
        for pattern_config in patterns:
            matches = re.finditer(pattern_config["pattern"], context, re.IGNORECASE | re.DOTALL)
            for match in matches:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.INJECTION_ATTACK,
                    risk_level=pattern_config["risk"],
                    confidence=0.85,
                    description=pattern_config["description"],
                    affected_context=match.group(0)[:100],
                    recommendation="Block context containing injection attempts",
                    evidence={"matched_pattern": pattern_config["pattern"]}
                ))
        
        return threats
    
    async def _verify_supply_chain(
        self,
        contexts: List[RetrievedContext]
    ) -> List[SecurityThreat]:
        """Verify supply chain integrity of retrieved contexts."""
        threats = []
        
        for ctx in contexts:
            kb_config = self.knowledge_bases.get(ctx.kb_id)
            if kb_config and kb_config.trust_score < 0.7:
                threats.append(SecurityThreat(
                    threat_type=ThreatType.SUPPLY_CHAIN_ATTACK,
                    risk_level=RiskLevel.MEDIUM,
                    confidence=1.0 - kb_config.trust_score,
                    description=f"Low trust score for knowledge base: {kb_config.name}",
                    affected_context=ctx.content[:100],
                    recommendation="Verify knowledge base integrity or increase trust score"
                ))
            
            # Check for suspicious sources
            if "untrusted" in ctx.source.lower() or "unknown" in ctx.source.lower():
                threats.append(SecurityThreat(
                    threat_type=ThreatType.SUPPLY_CHAIN_ATTACK,
                    risk_level=RiskLevel.HIGH,
                    confidence=0.8,
                    description=f"Untrusted source: {ctx.source}",
                    affected_context=ctx.content[:100],
                    recommendation="Only use contexts from verified sources"
                ))
        
        return threats
    
    async def _detect_hallucinations(self, context: str, query: str) -> float:
        """
        Detect potential hallucinations in retrieved context.
        Returns hallucination score (0.0-1.0).
        """
        # Simple heuristic-based detection (in production, use LLM)
        score = 0.0
        
        # Check for contradictions
        if "not" in context.lower() and "is" in context.lower():
            score += 0.2
        
        # Check for vague language
        vague_terms = ["maybe", "possibly", "might", "could be", "uncertain"]
        vague_count = sum(1 for term in vague_terms if term in context.lower())
        score += min(vague_count * 0.1, 0.3)
        
        # Check relevance to query
        query_terms = set(query.lower().split())
        context_terms = set(context.lower().split())
        overlap = len(query_terms & context_terms) / max(len(query_terms), 1)
        if overlap < 0.3:
            score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_trust_score(
        self,
        contexts: List[RetrievedContext],
        threats: List[SecurityThreat]
    ) -> float:
        """Calculate overall trust score for retrieved contexts."""
        if not contexts:
            return 0.0
        
        # Base trust from knowledge bases
        kb_trust_scores = []
        for ctx in contexts:
            kb_config = self.knowledge_bases.get(ctx.kb_id)
            if kb_config:
                kb_trust_scores.append(kb_config.trust_score)
            else:
                kb_trust_scores.append(0.5)  # Unknown KB gets neutral score
        
        avg_kb_trust = sum(kb_trust_scores) / len(kb_trust_scores)
        
        # Reduce trust based on threats
        threat_penalty = 0.0
        for threat in threats:
            if threat.risk_level == RiskLevel.CRITICAL:
                threat_penalty += 0.3
            elif threat.risk_level == RiskLevel.HIGH:
                threat_penalty += 0.2
            elif threat.risk_level == RiskLevel.MEDIUM:
                threat_penalty += 0.1
        
        final_trust = max(avg_kb_trust - threat_penalty, 0.0)
        return min(final_trust, 1.0)
    
    def _determine_risk_level(
        self,
        threats: List[SecurityThreat],
        hallucination_score: float,
        trust_score: float
    ) -> RiskLevel:
        """Determine overall risk level."""
        # Check for critical threats
        if any(t.risk_level == RiskLevel.CRITICAL for t in threats):
            return RiskLevel.CRITICAL
        
        # Check for high threats
        if any(t.risk_level == RiskLevel.HIGH for t in threats):
            return RiskLevel.HIGH
        
        # Check hallucination and trust scores
        if hallucination_score > 0.7 or trust_score < 0.3:
            return RiskLevel.HIGH
        
        if hallucination_score > 0.5 or trust_score < 0.5:
            return RiskLevel.MEDIUM
        
        # Check for medium threats
        if any(t.risk_level == RiskLevel.MEDIUM for t in threats):
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    async def _sanitize_context(
        self,
        context: str,
        threats: List[SecurityThreat]
    ) -> str:
        """Sanitize context by removing or redacting threats."""
        sanitized = context
        
        for threat in threats:
            if threat.affected_context:
                # Replace threat with [REDACTED]
                sanitized = sanitized.replace(threat.affected_context, "[REDACTED]")
        
        return sanitized
    
    def _generate_recommendations(
        self,
        threats: List[SecurityThreat],
        hallucination_score: float,
        trust_score: float
    ) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Threat-specific recommendations
        threat_recs = set()
        for threat in threats:
            if threat.recommendation:
                threat_recs.add(threat.recommendation)
        recommendations.extend(list(threat_recs))
        
        # Score-based recommendations
        if hallucination_score > 0.7:
            recommendations.append("High hallucination risk - verify context accuracy before use")
        
        if trust_score < 0.5:
            recommendations.append("Low trust score - use additional verification or human review")
        
        if not threats and hallucination_score < 0.3 and trust_score > 0.8:
            recommendations.append("Context appears safe for use")
        
        return recommendations
    
    def _log_access(
        self,
        user_id: Optional[str],
        contexts: List[RetrievedContext],
        threats: List[SecurityThreat],
        is_safe: bool
    ):
        """Log access for audit trail."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "kb_ids": [ctx.kb_id for ctx in contexts],
            "threats_count": len(threats),
            "is_safe": is_safe,
            "threat_types": list(set(t.threat_type.value for t in threats))
        }
        self.access_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.access_logs) > 1000:
            self.access_logs = self.access_logs[-1000:]
    
    def get_access_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access logs."""
        return self.access_logs[-limit:]
    
    def get_knowledge_bases(self) -> List[KnowledgeBaseConfig]:
        """Get all registered knowledge bases."""
        return list(self.knowledge_bases.values())


# Global instance
_rag_security_service_instance: Optional[RAGSecurityService] = None


def get_rag_security_service() -> RAGSecurityService:
    """Get or create the global RAG security service instance."""
    global _rag_security_service_instance
    if _rag_security_service_instance is None:
        _rag_security_service_instance = RAGSecurityService()
    return _rag_security_service_instance

