"""
PII Protection and Data Leakage Prevention Service
Detects and redacts personally identifiable information (PII) and sensitive data.

Supports HIPAA, GDPR, CCPA, and other privacy regulations.

Author: AgentGuard Engineering Team
Date: October 2025
Version: 1.0.0
"""

import logging
import re
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


class PIIType(str, Enum):
    """Types of personally identifiable information."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"
    MAC_ADDRESS = "mac_address"
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    DATE_OF_BIRTH = "date_of_birth"
    ADDRESS = "address"
    NAME = "name"
    MEDICAL_RECORD = "medical_record"
    BANK_ACCOUNT = "bank_account"
    ROUTING_NUMBER = "routing_number"
    API_KEY = "api_key"
    PASSWORD = "password"
    USERNAME = "username"
    CUSTOM = "custom"


class RedactionStrategy(str, Enum):
    """Strategy for redacting PII."""
    MASK = "mask"  # Replace with ***
    HASH = "hash"  # Replace with hash
    TOKEN = "token"  # Replace with reversible token
    REMOVE = "remove"  # Remove entirely
    PARTIAL = "partial"  # Show partial (e.g., last 4 digits)


class ComplianceStandard(str, Enum):
    """Compliance standards."""
    HIPAA = "hipaa"
    GDPR = "gdpr"
    CCPA = "ccpa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    FERPA = "ferpa"
    CUSTOM = "custom"


@dataclass
class PIIPattern:
    """Pattern for detecting PII."""
    pattern_id: str
    pii_type: PIIType
    name: str
    regex: str
    description: str
    compliance_standards: List[ComplianceStandard]
    default_strategy: RedactionStrategy
    examples: List[str] = field(default_factory=list)
    _compiled: Optional[re.Pattern] = field(default=None, repr=False)
    
    def __post_init__(self):
        """Compile regex pattern."""
        self._compiled = re.compile(self.regex, re.IGNORECASE | re.MULTILINE)
    
    def find_all(self, text: str) -> List[Tuple[str, int, int]]:
        """Find all matches in text. Returns list of (match, start, end)."""
        matches = []
        for match in self._compiled.finditer(text):
            matches.append((match.group(0), match.start(), match.end()))
        return matches


@dataclass
class PIIDetection:
    """A detected PII instance."""
    pii_type: PIIType
    pattern_id: str
    value: str
    start_pos: int
    end_pos: int
    confidence: float
    compliance_standards: List[ComplianceStandard]


@dataclass
class RedactionResult:
    """Result of PII detection and redaction."""
    original_text: str
    redacted_text: str
    detections: List[PIIDetection]
    redaction_map: Dict[str, str]  # original -> redacted
    compliance_violations: List[ComplianceStandard]
    processing_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_text": self.original_text,
            "redacted_text": self.redacted_text,
            "detections": [
                {
                    "pii_type": d.pii_type.value,
                    "pattern_id": d.pattern_id,
                    "value": d.value,
                    "start_pos": d.start_pos,
                    "end_pos": d.end_pos,
                    "confidence": d.confidence,
                    "compliance_standards": [cs.value for cs in d.compliance_standards]
                }
                for d in self.detections
            ],
            "redaction_map": self.redaction_map,
            "compliance_violations": [cv.value for cv in self.compliance_violations],
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


class PIIProtectionService:
    """
    PII Protection and Data Leakage Prevention Service.
    
    Detects and redacts PII according to various compliance standards:
    - HIPAA (Healthcare)
    - GDPR (EU Privacy)
    - CCPA (California Privacy)
    - PCI-DSS (Payment Card)
    - SOC2 (Security)
    - FERPA (Education)
    """
    
    # PII Detection Patterns
    PATTERNS = [
        PIIPattern(
            pattern_id="pii-email",
            pii_type=PIIType.EMAIL,
            name="Email Address",
            regex=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            description="Email addresses",
            compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA, ComplianceStandard.HIPAA],
            default_strategy=RedactionStrategy.MASK,
            examples=["john.doe@example.com", "user@domain.co.uk"]
        ),
        PIIPattern(
            pattern_id="pii-phone-us",
            pii_type=PIIType.PHONE,
            name="US Phone Number",
            regex=r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
            description="US phone numbers",
            compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.CCPA, ComplianceStandard.HIPAA],
            default_strategy=RedactionStrategy.PARTIAL,
            examples=["(555) 123-4567", "+1-555-123-4567", "555.123.4567"]
        ),
        PIIPattern(
            pattern_id="pii-ssn",
            pii_type=PIIType.SSN,
            name="US Social Security Number",
            regex=r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b',
            description="US Social Security Numbers",
            compliance_standards=[ComplianceStandard.HIPAA, ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.MASK,
            examples=["123-45-6789", "123 45 6789"]
        ),
        PIIPattern(
            pattern_id="pii-credit-card",
            pii_type=PIIType.CREDIT_CARD,
            name="Credit Card Number",
            regex=r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b',
            description="Credit card numbers (Visa, MC, Amex, Discover)",
            compliance_standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.PARTIAL,
            examples=["4532015112830366", "5425233430109903"]
        ),
        PIIPattern(
            pattern_id="pii-ip-v4",
            pii_type=PIIType.IP_ADDRESS,
            name="IPv4 Address",
            regex=r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            description="IPv4 addresses",
            compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.HASH,
            examples=["192.168.1.1", "10.0.0.1"]
        ),
        PIIPattern(
            pattern_id="pii-mac",
            pii_type=PIIType.MAC_ADDRESS,
            name="MAC Address",
            regex=r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b',
            description="MAC addresses",
            compliance_standards=[ComplianceStandard.GDPR, ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.HASH,
            examples=["00:1B:44:11:3A:B7", "00-1B-44-11-3A-B7"]
        ),
        PIIPattern(
            pattern_id="pii-dob",
            pii_type=PIIType.DATE_OF_BIRTH,
            name="Date of Birth",
            regex=r'\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12][0-9]|3[01])[-/](?:19|20)\d{2}\b',
            description="Dates of birth (MM/DD/YYYY or MM-DD-YYYY)",
            compliance_standards=[ComplianceStandard.HIPAA, ComplianceStandard.GDPR],
            default_strategy=RedactionStrategy.MASK,
            examples=["01/15/1990", "12-25-1985"]
        ),
        PIIPattern(
            pattern_id="pii-medical-record",
            pii_type=PIIType.MEDICAL_RECORD,
            name="Medical Record Number",
            regex=r'\b(?:MRN|Medical Record|Patient ID)[\s:#-]*([A-Z0-9]{6,12})\b',
            description="Medical record numbers",
            compliance_standards=[ComplianceStandard.HIPAA],
            default_strategy=RedactionStrategy.MASK,
            examples=["MRN: ABC123456", "Medical Record #123456789"]
        ),
        PIIPattern(
            pattern_id="pii-bank-account",
            pii_type=PIIType.BANK_ACCOUNT,
            name="Bank Account Number",
            regex=r'\b(?:Account|Acct)[\s:#-]*([0-9]{8,17})\b',
            description="Bank account numbers",
            compliance_standards=[ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.MASK,
            examples=["Account: 123456789", "Acct #987654321"]
        ),
        PIIPattern(
            pattern_id="pii-api-key",
            pii_type=PIIType.API_KEY,
            name="API Key",
            regex=r'\b(?:api[_-]?key|apikey|api[_-]?secret)[\s:=]+["\']?([A-Za-z0-9_\-]{20,})["\']?\b',
            description="API keys and secrets",
            compliance_standards=[ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.MASK,
            examples=["api_key: sk_live_abc123xyz", "apikey=prod_key_xyz"]
        ),
        PIIPattern(
            pattern_id="pii-password",
            pii_type=PIIType.PASSWORD,
            name="Password",
            regex=r'\b(?:password|passwd|pwd)[\s:=]+["\']?([^\s"\']{8,})["\']?\b',
            description="Passwords",
            compliance_standards=[ComplianceStandard.SOC2],
            default_strategy=RedactionStrategy.MASK,
            examples=["password: MySecret123", "pwd=SuperSecret!"]
        ),
    ]
    
    def __init__(self):
        """Initialize PII protection service."""
        self.patterns = self.PATTERNS
        self._compile_patterns()
        self.token_map: Dict[str, str] = {}  # For reversible tokenization
        logger.info(f"PII Protection Service initialized with {len(self.patterns)} patterns")
    
    def _compile_patterns(self):
        """Ensure all patterns are compiled."""
        for pattern in self.patterns:
            if pattern._compiled is None:
                pattern._compiled = re.compile(pattern.regex, re.IGNORECASE | re.MULTILINE)
    
    def detect_pii(
        self,
        text: str,
        compliance_standard: Optional[ComplianceStandard] = None
    ) -> List[PIIDetection]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan for PII
            compliance_standard: Filter patterns by compliance standard
            
        Returns:
            List of detected PII instances
        """
        detections = []
        
        for pattern in self.patterns:
            # Filter by compliance standard if specified
            if compliance_standard and compliance_standard not in pattern.compliance_standards:
                continue
            
            matches = pattern.find_all(text)
            for value, start, end in matches:
                detection = PIIDetection(
                    pii_type=pattern.pii_type,
                    pattern_id=pattern.pattern_id,
                    value=value,
                    start_pos=start,
                    end_pos=end,
                    confidence=0.95,  # High confidence for regex matches
                    compliance_standards=pattern.compliance_standards
                )
                detections.append(detection)
        
        # Sort by position
        detections.sort(key=lambda d: d.start_pos)
        return detections
    
    def redact_pii(
        self,
        text: str,
        strategy: Optional[Dict[PIIType, RedactionStrategy]] = None,
        compliance_standard: Optional[ComplianceStandard] = None
    ) -> RedactionResult:
        """
        Detect and redact PII in text.
        
        Args:
            text: Text to redact
            strategy: Custom redaction strategies per PII type
            compliance_standard: Compliance standard to enforce
            
        Returns:
            RedactionResult with redacted text and metadata
        """
        start_time = time.perf_counter()
        
        # Detect PII
        detections = self.detect_pii(text, compliance_standard)
        
        # Build redacted text
        redacted_text = text
        redaction_map = {}
        compliance_violations = set()
        
        # Process detections in reverse order to maintain positions
        for detection in reversed(detections):
            # Determine redaction strategy
            pattern = next(p for p in self.patterns if p.pattern_id == detection.pattern_id)
            redact_strategy = pattern.default_strategy
            if strategy and detection.pii_type in strategy:
                redact_strategy = strategy[detection.pii_type]
            
            # Apply redaction
            redacted_value = self._apply_redaction(
                detection.value,
                detection.pii_type,
                redact_strategy
            )
            
            # Replace in text
            redacted_text = (
                redacted_text[:detection.start_pos] +
                redacted_value +
                redacted_text[detection.end_pos:]
            )
            
            # Track redaction
            redaction_map[detection.value] = redacted_value
            
            # Track compliance violations
            if compliance_standard and compliance_standard in detection.compliance_standards:
                compliance_violations.add(compliance_standard)
        
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        
        return RedactionResult(
            original_text=text,
            redacted_text=redacted_text,
            detections=detections,
            redaction_map=redaction_map,
            compliance_violations=list(compliance_violations),
            processing_time_ms=processing_time_ms
        )
    
    def _apply_redaction(
        self,
        value: str,
        pii_type: PIIType,
        strategy: RedactionStrategy
    ) -> str:
        """Apply redaction strategy to a value."""
        if strategy == RedactionStrategy.MASK:
            return "***REDACTED***"
        
        elif strategy == RedactionStrategy.HASH:
            hash_obj = hashlib.sha256(value.encode())
            return f"[HASH:{hash_obj.hexdigest()[:16]}]"
        
        elif strategy == RedactionStrategy.TOKEN:
            # Generate reversible token
            token = f"[TOKEN:{len(self.token_map):04d}]"
            self.token_map[token] = value
            return token
        
        elif strategy == RedactionStrategy.REMOVE:
            return ""
        
        elif strategy == RedactionStrategy.PARTIAL:
            # Show last 4 characters for certain types
            if pii_type in [PIIType.CREDIT_CARD, PIIType.PHONE, PIIType.SSN]:
                if len(value) > 4:
                    return "***" + value[-4:]
                return "***"
            return "***REDACTED***"
        
        return "***REDACTED***"
    
    def detokenize(self, text: str) -> str:
        """Reverse tokenization (for TOKEN strategy)."""
        result = text
        for token, original in self.token_map.items():
            result = result.replace(token, original)
        return result
    
    def add_custom_pattern(
        self,
        pattern_id: str,
        pii_type: PIIType,
        name: str,
        regex: str,
        description: str,
        compliance_standards: List[ComplianceStandard],
        default_strategy: RedactionStrategy = RedactionStrategy.MASK
    ):
        """Add a custom PII detection pattern."""
        pattern = PIIPattern(
            pattern_id=pattern_id,
            pii_type=pii_type,
            name=name,
            regex=regex,
            description=description,
            compliance_standards=compliance_standards,
            default_strategy=default_strategy
        )
        self.patterns.append(pattern)
        logger.info(f"Added custom pattern: {pattern_id}")


# Global instance
_pii_service_instance: Optional[PIIProtectionService] = None


def get_pii_protection_service() -> PIIProtectionService:
    """Get or create the global PII protection service instance."""
    global _pii_service_instance
    if _pii_service_instance is None:
        _pii_service_instance = PIIProtectionService()
    return _pii_service_instance

