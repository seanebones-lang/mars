"""
Custom Detection Rules Engine
Allows enterprises to define custom hallucination detection patterns and thresholds.
"""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of custom detection rules."""
    PATTERN_MATCH = "pattern_match"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    DOMAIN_SPECIFIC = "domain_specific"
    FACTUAL_ACCURACY = "factual_accuracy"
    CONSISTENCY_CHECK = "consistency_check"
    BIAS_DETECTION = "bias_detection"


class RuleSeverity(Enum):
    """Severity levels for rule violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleCategory(Enum):
    """Categories for organizing rules."""
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    TECHNICAL = "technical"
    GENERAL = "general"
    SAFETY = "safety"
    COMPLIANCE = "compliance"


@dataclass
class CustomRule:
    """Custom detection rule definition."""
    rule_id: str
    name: str
    description: str
    rule_type: RuleType
    category: RuleCategory
    severity: RuleSeverity
    pattern: Optional[str] = None  # Regex pattern for pattern matching
    threshold: Optional[float] = None  # Confidence threshold
    keywords: List[str] = None  # Keywords to match
    enabled: bool = True
    created_by: str = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class RuleViolation:
    """Result of a rule violation."""
    rule_id: str
    rule_name: str
    severity: RuleSeverity
    confidence: float
    matched_text: str
    explanation: str
    suggestions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DetectionResult:
    """Enhanced detection result with custom rules."""
    original_result: Dict[str, Any]
    custom_violations: List[RuleViolation]
    overall_risk_score: float
    risk_factors: List[str]
    recommendations: List[str]
    
    def __post_init__(self):
        if self.risk_factors is None:
            self.risk_factors = []
        if self.recommendations is None:
            self.recommendations = []


class CustomRulesEngine:
    """Enterprise custom detection rules engine."""
    
    def __init__(self, db_path: str = "custom_rules.db"):
        self.db_path = db_path
        self.rules: Dict[str, CustomRule] = {}
        self.rule_templates = self._init_rule_templates()
        
        # Initialize database
        self._init_database()
        
        # Load existing rules
        self._load_rules()
    
    def _init_database(self):
        """Initialize SQLite database for custom rules."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    rule_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    pattern TEXT,
                    threshold REAL,
                    keywords TEXT,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rule_violations (
                    violation_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    agent_output TEXT NOT NULL,
                    matched_text TEXT,
                    confidence REAL,
                    severity TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rule_performance (
                    rule_id TEXT,
                    date DATE,
                    violations_count INTEGER DEFAULT 0,
                    false_positives INTEGER DEFAULT 0,
                    true_positives INTEGER DEFAULT 0,
                    accuracy REAL,
                    PRIMARY KEY (rule_id, date)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rules_category ON custom_rules(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rules_enabled ON custom_rules(enabled)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_rule_id ON rule_violations(rule_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON rule_violations(timestamp)")
            
            conn.commit()
    
    def _init_rule_templates(self) -> Dict[str, CustomRule]:
        """Initialize pre-built rule templates for common use cases."""
        templates = {}
        
        # Healthcare Rules
        templates["healthcare_drug_names"] = CustomRule(
            rule_id="healthcare_drug_names",
            name="Unverified Drug Names",
            description="Detects mentions of drug names that may need verification",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.HEALTHCARE,
            severity=RuleSeverity.HIGH,
            pattern=r'\b(?:aspirin|ibuprofen|acetaminophen|metformin|lisinopril|atorvastatin|amlodipine|metoprolol|omeprazole|losartan)\b',
            keywords=["medication", "drug", "prescription", "dosage"],
            metadata={
                "description": "Flags common drug names for medical accuracy verification",
                "false_positive_rate": "low"
            }
        )
        
        templates["healthcare_medical_claims"] = CustomRule(
            rule_id="healthcare_medical_claims",
            name="Medical Claims Verification",
            description="Flags definitive medical claims that need verification",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.HEALTHCARE,
            severity=RuleSeverity.CRITICAL,
            pattern=r'\b(?:cures?|treats?|prevents?|eliminates?|guaranteed?)\s+(?:cancer|diabetes|heart disease|covid|aids)\b',
            keywords=["cure", "treatment", "prevention", "medical claim"],
            metadata={
                "description": "Detects potentially dangerous medical claims",
                "requires_immediate_review": True
            }
        )
        
        # Finance Rules
        templates["finance_investment_advice"] = CustomRule(
            rule_id="finance_investment_advice",
            name="Investment Advice Detection",
            description="Flags potential investment advice that may require disclaimers",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.FINANCE,
            severity=RuleSeverity.HIGH,
            pattern=r'\b(?:buy|sell|invest in|purchase|guaranteed returns?|risk-free|sure thing)\b.*\b(?:stock|bond|crypto|bitcoin|investment|portfolio)\b',
            keywords=["investment", "financial advice", "trading", "returns"],
            metadata={
                "requires_disclaimer": True,
                "compliance_note": "May require SEC compliance review"
            }
        )
        
        templates["finance_price_predictions"] = CustomRule(
            rule_id="finance_price_predictions",
            name="Price Prediction Claims",
            description="Detects specific price predictions that may be misleading",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.FINANCE,
            severity=RuleSeverity.MEDIUM,
            pattern=r'\b(?:will reach|going to|predicted to be|expected to hit)\s+\$[\d,]+\b',
            keywords=["price prediction", "forecast", "target price"],
            metadata={
                "disclaimer_required": "Past performance does not guarantee future results"
            }
        )
        
        # Legal Rules
        templates["legal_advice_detection"] = CustomRule(
            rule_id="legal_advice_detection",
            name="Legal Advice Detection",
            description="Flags content that may constitute legal advice",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.LEGAL,
            severity=RuleSeverity.HIGH,
            pattern=r'\b(?:you should|must|required to|legally obligated|sue|lawsuit|liable|contract requires)\b',
            keywords=["legal advice", "obligation", "liability", "contract"],
            metadata={
                "disclaimer_required": "This is not legal advice. Consult a qualified attorney."
            }
        )
        
        # Technical Rules
        templates["tech_security_claims"] = CustomRule(
            rule_id="tech_security_claims",
            name="Security Claims Verification",
            description="Flags security-related claims that need verification",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.TECHNICAL,
            severity=RuleSeverity.HIGH,
            pattern=r'\b(?:100% secure|completely safe|unhackable|bulletproof security|zero vulnerabilities)\b',
            keywords=["security", "encryption", "protection", "vulnerability"],
            metadata={
                "verification_required": True,
                "security_team_review": True
            }
        )
        
        # Bias Detection Rules
        templates["bias_gender_assumptions"] = CustomRule(
            rule_id="bias_gender_assumptions",
            name="Gender Bias Detection",
            description="Detects potential gender bias in responses",
            rule_type=RuleType.PATTERN_MATCH,
            category=RuleCategory.GENERAL,
            severity=RuleSeverity.MEDIUM,
            pattern=r'\b(?:men are better at|women should|typical male|typical female|boys will be boys|girls are naturally)\b',
            keywords=["gender", "stereotype", "assumption"],
            metadata={
                "bias_type": "gender",
                "sensitivity_training": True
            }
        )
        
        # Confidence Threshold Rules
        templates["low_confidence_threshold"] = CustomRule(
            rule_id="low_confidence_threshold",
            name="Low Confidence Threshold",
            description="Flags responses with confidence below 70%",
            rule_type=RuleType.CONFIDENCE_THRESHOLD,
            category=RuleCategory.GENERAL,
            severity=RuleSeverity.LOW,
            threshold=0.7,
            metadata={
                "applies_to": "all_responses",
                "action": "request_human_review"
            }
        )
        
        return templates
    
    def _load_rules(self):
        """Load custom rules from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM custom_rules WHERE enabled = 1")
                
                for row in cursor.fetchall():
                    rule = CustomRule(
                        rule_id=row['rule_id'],
                        name=row['name'],
                        description=row['description'],
                        rule_type=RuleType(row['rule_type']),
                        category=RuleCategory(row['category']),
                        severity=RuleSeverity(row['severity']),
                        pattern=row['pattern'],
                        threshold=row['threshold'],
                        keywords=json.loads(row['keywords']) if row['keywords'] else [],
                        enabled=bool(row['enabled']),
                        created_by=row['created_by'],
                        created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                        updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                        metadata=json.loads(row['metadata']) if row['metadata'] else {}
                    )
                    self.rules[rule.rule_id] = rule
                    
            logger.info(f"Loaded {len(self.rules)} custom rules")
            
        except Exception as e:
            logger.error(f"Error loading custom rules: {e}")
    
    def add_rule(self, rule: CustomRule, user_id: str = None) -> bool:
        """Add a new custom rule."""
        try:
            rule.created_by = user_id
            rule.created_at = datetime.utcnow()
            rule.updated_at = datetime.utcnow()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO custom_rules (
                        rule_id, name, description, rule_type, category, severity,
                        pattern, threshold, keywords, enabled, created_by,
                        created_at, updated_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.name, rule.description, rule.rule_type.value,
                    rule.category.value, rule.severity.value, rule.pattern,
                    rule.threshold, json.dumps(rule.keywords), rule.enabled,
                    rule.created_by, rule.created_at, rule.updated_at,
                    json.dumps(rule.metadata)
                ))
                conn.commit()
            
            self.rules[rule.rule_id] = rule
            logger.info(f"Added custom rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding custom rule: {e}")
            return False
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any], user_id: str = None) -> bool:
        """Update an existing custom rule."""
        if rule_id not in self.rules:
            return False
        
        try:
            rule = self.rules[rule_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            rule.updated_at = datetime.utcnow()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE custom_rules SET
                        name = ?, description = ?, rule_type = ?, category = ?,
                        severity = ?, pattern = ?, threshold = ?, keywords = ?,
                        enabled = ?, updated_at = ?, metadata = ?
                    WHERE rule_id = ?
                """, (
                    rule.name, rule.description, rule.rule_type.value,
                    rule.category.value, rule.severity.value, rule.pattern,
                    rule.threshold, json.dumps(rule.keywords), rule.enabled,
                    rule.updated_at, json.dumps(rule.metadata), rule_id
                ))
                conn.commit()
            
            logger.info(f"Updated custom rule: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating custom rule: {e}")
            return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a custom rule."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM custom_rules WHERE rule_id = ?", (rule_id,))
                conn.commit()
            
            if rule_id in self.rules:
                del self.rules[rule_id]
            
            logger.info(f"Deleted custom rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting custom rule: {e}")
            return False
    
    def evaluate_text(self, text: str, original_confidence: float = None) -> List[RuleViolation]:
        """Evaluate text against all custom rules."""
        violations = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            violation = self._evaluate_single_rule(rule, text, original_confidence)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _evaluate_single_rule(self, rule: CustomRule, text: str, original_confidence: float = None) -> Optional[RuleViolation]:
        """Evaluate text against a single rule."""
        try:
            if rule.rule_type == RuleType.PATTERN_MATCH:
                return self._evaluate_pattern_rule(rule, text)
            
            elif rule.rule_type == RuleType.CONFIDENCE_THRESHOLD:
                return self._evaluate_confidence_rule(rule, text, original_confidence)
            
            elif rule.rule_type == RuleType.DOMAIN_SPECIFIC:
                return self._evaluate_domain_rule(rule, text)
            
            # Add more rule type evaluations as needed
            
        except Exception as e:
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
        
        return None
    
    def _evaluate_pattern_rule(self, rule: CustomRule, text: str) -> Optional[RuleViolation]:
        """Evaluate pattern-based rule."""
        if not rule.pattern:
            return None
        
        try:
            matches = re.finditer(rule.pattern, text, re.IGNORECASE)
            match_list = list(matches)
            
            if match_list:
                matched_text = match_list[0].group()
                confidence = min(1.0, len(match_list) * 0.3)  # More matches = higher confidence
                
                return RuleViolation(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    confidence=confidence,
                    matched_text=matched_text,
                    explanation=f"Pattern match found: '{matched_text}' matches rule '{rule.name}'",
                    suggestions=self._generate_suggestions(rule, matched_text),
                    metadata={
                        "pattern": rule.pattern,
                        "matches_count": len(match_list),
                        "category": rule.category.value
                    }
                )
        
        except re.error as e:
            logger.error(f"Invalid regex pattern in rule {rule.rule_id}: {e}")
        
        return None
    
    def _evaluate_confidence_rule(self, rule: CustomRule, text: str, original_confidence: float) -> Optional[RuleViolation]:
        """Evaluate confidence threshold rule."""
        if original_confidence is None or rule.threshold is None:
            return None
        
        if original_confidence < rule.threshold:
            return RuleViolation(
                rule_id=rule.rule_id,
                rule_name=rule.name,
                severity=rule.severity,
                confidence=1.0 - original_confidence,  # Lower original confidence = higher violation confidence
                matched_text=text[:100] + "..." if len(text) > 100 else text,
                explanation=f"Response confidence ({original_confidence:.2f}) below threshold ({rule.threshold:.2f})",
                suggestions=[
                    "Request human review for low-confidence responses",
                    "Provide additional context or clarification",
                    "Consider rephrasing the response"
                ],
                metadata={
                    "original_confidence": original_confidence,
                    "threshold": rule.threshold,
                    "confidence_gap": rule.threshold - original_confidence
                }
            )
        
        return None
    
    def _evaluate_domain_rule(self, rule: CustomRule, text: str) -> Optional[RuleViolation]:
        """Evaluate domain-specific rule."""
        # Check for keyword matches
        if rule.keywords:
            keyword_matches = []
            for keyword in rule.keywords:
                if keyword.lower() in text.lower():
                    keyword_matches.append(keyword)
            
            if keyword_matches:
                confidence = min(1.0, len(keyword_matches) / len(rule.keywords))
                
                return RuleViolation(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    confidence=confidence,
                    matched_text=", ".join(keyword_matches),
                    explanation=f"Domain-specific keywords detected: {', '.join(keyword_matches)}",
                    suggestions=self._generate_suggestions(rule, ", ".join(keyword_matches)),
                    metadata={
                        "matched_keywords": keyword_matches,
                        "domain": rule.category.value
                    }
                )
        
        return None
    
    def _generate_suggestions(self, rule: CustomRule, matched_text: str) -> List[str]:
        """Generate suggestions based on rule type and matched content."""
        suggestions = []
        
        if rule.category == RuleCategory.HEALTHCARE:
            suggestions.extend([
                "Verify medical information with qualified healthcare professionals",
                "Add appropriate medical disclaimers",
                "Consider recommending consultation with a doctor"
            ])
        
        elif rule.category == RuleCategory.FINANCE:
            suggestions.extend([
                "Add financial disclaimer about investment risks",
                "Clarify that this is not personalized financial advice",
                "Recommend consulting with a financial advisor"
            ])
        
        elif rule.category == RuleCategory.LEGAL:
            suggestions.extend([
                "Add disclaimer that this is not legal advice",
                "Recommend consulting with a qualified attorney",
                "Clarify jurisdictional limitations"
            ])
        
        elif rule.severity == RuleSeverity.CRITICAL:
            suggestions.extend([
                "Immediate human review required",
                "Consider removing or significantly modifying the content",
                "Escalate to subject matter expert"
            ])
        
        # Add rule-specific suggestions from metadata
        if "suggestions" in rule.metadata:
            suggestions.extend(rule.metadata["suggestions"])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def get_rule_templates(self) -> Dict[str, CustomRule]:
        """Get available rule templates."""
        return self.rule_templates
    
    def install_template(self, template_id: str, user_id: str = None) -> bool:
        """Install a rule template as an active rule."""
        if template_id not in self.rule_templates:
            return False
        
        template = self.rule_templates[template_id]
        return self.add_rule(template, user_id)
    
    def get_rules_by_category(self, category: RuleCategory) -> List[CustomRule]:
        """Get rules filtered by category."""
        return [rule for rule in self.rules.values() if rule.category == category and rule.enabled]
    
    def get_rule_performance(self, rule_id: str, days: int = 30) -> Dict[str, Any]:
        """Get performance metrics for a specific rule."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get violation counts
                cursor = conn.execute("""
                    SELECT COUNT(*) as total_violations,
                           AVG(confidence) as avg_confidence
                    FROM rule_violations 
                    WHERE rule_id = ? AND timestamp >= datetime('now', '-{} days')
                """.format(days), (rule_id,))
                
                stats = cursor.fetchone()
                
                return {
                    "rule_id": rule_id,
                    "period_days": days,
                    "total_violations": stats['total_violations'] if stats else 0,
                    "avg_confidence": stats['avg_confidence'] if stats else 0.0,
                    "violations_per_day": (stats['total_violations'] / days) if stats and stats['total_violations'] else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting rule performance: {e}")
            return {"error": str(e)}
    
    def record_violation(self, violation: RuleViolation, agent_output: str, user_id: str = None):
        """Record a rule violation for analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                violation_id = f"{violation.rule_id}-{int(datetime.utcnow().timestamp() * 1000000)}"
                
                conn.execute("""
                    INSERT INTO rule_violations (
                        violation_id, rule_id, agent_output, matched_text,
                        confidence, severity, user_id, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    violation_id, violation.rule_id, agent_output,
                    violation.matched_text, violation.confidence,
                    violation.severity.value, user_id, json.dumps(violation.metadata)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording violation: {e}")


# Global custom rules engine instance
_custom_rules_engine: Optional[CustomRulesEngine] = None

def get_custom_rules_engine() -> CustomRulesEngine:
    """Get or create custom rules engine instance."""
    global _custom_rules_engine
    if _custom_rules_engine is None:
        _custom_rules_engine = CustomRulesEngine()
    return _custom_rules_engine
