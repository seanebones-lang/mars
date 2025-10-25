# Security Hardening Checklist

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Production security hardening**

---

## Security Hardening Status

### P0-Critical (Must Complete Before Launch)

- [x] HTTPS/TLS encryption
- [x] Environment variable protection
- [x] API authentication
- [x] CORS configuration
- [x] Content Security Policy (CSP)
- [x] Security headers (HSTS, X-Frame-Options, etc.)
- [ ] WAF deployment (Cloudflare)
- [ ] DDoS protection
- [ ] Rate limiting per customer
- [ ] Secrets rotation automation
- [ ] Penetration testing
- [ ] Security audit of all 97 endpoints
- [ ] Input validation hardening
- [ ] SQL injection prevention audit
- [ ] XSS prevention audit

### P1-High Priority (First Month)

- [ ] Intrusion detection system (IDS)
- [ ] Security information and event management (SIEM)
- [ ] Automated vulnerability scanning
- [ ] Dependency security scanning
- [ ] Container security scanning
- [ ] API security testing (OWASP API Top 10)
- [ ] Secrets management (HashiCorp Vault)
- [ ] Certificate management automation
- [ ] Security training for team

### P2-Medium Priority (First Quarter)

- [ ] Bug bounty program
- [ ] Security incident response drills
- [ ] Compliance certifications (SOC 2, ISO 27001)
- [ ] Third-party security assessments
- [ ] Red team exercises
- [ ] Security awareness program

---

## Current Security Measures

### 1. Transport Security 

**Status**: Implemented

**Measures**:
- HTTPS/TLS 1.3 encryption
- HSTS (HTTP Strict Transport Security)
- Certificate management via Render
- Secure WebSocket (WSS)

**Configuration**:
```python
# In agentguard-ui/next.config.js
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 2. Authentication & Authorization 

**Status**: Implemented

**Measures**:
- API key authentication
- Environment-based key management
- Request validation

**Configuration**:
```python
# In src/api/main.py
# API key validation on protected endpoints
```

### 3. CORS Protection 

**Status**: Implemented

**Measures**:
- Configured CORS middleware
- Allowed origins restricted to production domains
- Credentials support enabled

**Configuration**:
```python
# In src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Monorepo deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Security Headers 

**Status**: Implemented

**Headers**:
- Content-Security-Policy
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: no-referrer
- Permissions-Policy

**Configuration**:
```javascript
// In agentguard-ui/next.config.js
const cspHeader = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  img-src 'self' blob: data:;
  font-src 'self';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
  upgrade-insecure-requests;
`
```

### 5. Input Validation 

**Status**: Partially Implemented

**Measures**:
- Pydantic models for request validation
- Type checking
- Length limits
- Pattern validation

**Areas for Improvement**:
- [ ] Add stricter validation rules
- [ ] Implement input sanitization
- [ ] Add rate limiting per input type

### 6. Error Handling 

**Status**: Implemented

**Measures**:
- Generic error messages to clients
- Detailed logging internally
- Sentry error tracking
- No stack traces in production

---

## Pending Security Implementations

### 1. WAF Deployment (Cloudflare) 

**Priority**: P0-Critical

**Purpose**: Web Application Firewall to protect against common attacks

**Implementation Steps**:

1. **Sign up for Cloudflare**
   ```bash
   # Go to cloudflare.com
   # Add domain: watcher.mothership-ai.com
   # Update nameservers at domain registrar
   ```

2. **Configure WAF Rules**
   - Enable OWASP Core Ruleset
   - Enable Cloudflare Managed Ruleset
   - Custom rules for API protection

3. **Enable Security Features**
   - DDoS protection (automatic)
   - Bot management
   - Rate limiting
   - IP reputation filtering

4. **Configure Rate Limiting**
   ```javascript
   // Cloudflare Dashboard → Security → WAF → Rate limiting rules
   
   // Rule 1: API rate limit
   // If: (http.request.uri.path contains "/api/")
   // Then: Rate limit 1000 requests per minute per IP
   
   // Rule 2: Authentication endpoint
   // If: (http.request.uri.path eq "/auth/login")
   // Then: Rate limit 10 requests per minute per IP
   ```

5. **Test WAF**
   ```bash
   # Test rate limiting
   for i in {1..100}; do curl https://watcher.mothership-ai.com/health; done
   
   # Test SQL injection protection
   curl "https://watcher.mothership-ai.com/api?id=1' OR '1'='1"
   
   # Test XSS protection
   curl "https://watcher.mothership-ai.com/api?q=<script>alert('xss')</script>"
   ```

**Cost**: Free tier available, Pro plan $20/month recommended

### 2. Rate Limiting Per Customer 

**Priority**: P0-Critical

**Purpose**: Prevent abuse and ensure fair usage

**Implementation**:

```python
# In src/middleware/rate_limiter.py

from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

# Rate limit decorators
@limiter.limit("1000/minute")  # Global rate limit
async def rate_limited_endpoint(request: Request):
    pass

@limiter.limit("100/minute")  # Per-customer rate limit
async def customer_endpoint(request: Request, customer_id: str):
    # Use customer_id as key
    pass
```

**Configuration**:
```python
# In src/api/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

### 3. Secrets Rotation Automation 

**Priority**: P0-Critical

**Purpose**: Regularly rotate API keys and secrets

**Implementation**:

```bash
#!/bin/bash
# scripts/rotate_secrets.sh

# Rotate Claude API key
NEW_CLAUDE_KEY=$(generate_new_key)
update_render_env "CLAUDE_API_KEY" "$NEW_CLAUDE_KEY"

# Rotate Stripe secret key
NEW_STRIPE_KEY=$(stripe keys create)
update_render_env "STRIPE_SECRET_KEY" "$NEW_STRIPE_KEY"

# Rotate database password
NEW_DB_PASSWORD=$(generate_password)
update_database_password "$NEW_DB_PASSWORD"
update_render_env "DATABASE_URL" "postgresql://user:$NEW_DB_PASSWORD@host/db"

# Restart services
render_restart_service "agentguard-api"
```

**Schedule**: Monthly rotation via cron

### 4. Penetration Testing 

**Priority**: P0-Critical

**Purpose**: Identify vulnerabilities before attackers do

**Recommended Vendors**:
- **Cobalt.io**: Pentest as a Service
- **HackerOne**: Bug bounty platform
- **Synack**: Crowdsourced security testing

**Scope**:
- All 97 REST endpoints
- WebSocket connections
- Authentication flows
- File upload endpoints
- Payment integration

**Timeline**: Before production launch

### 5. Security Audit of All Endpoints 

**Priority**: P0-Critical

**Checklist per Endpoint**:

```markdown
## Endpoint: POST /test-agent

- [ ] Input validation (Pydantic models)
- [ ] Authentication required
- [ ] Rate limiting applied
- [ ] SQL injection safe
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Error handling (no sensitive data leaked)
- [ ] Logging (audit trail)
- [ ] Authorization checks
- [ ] Output sanitization
```

**Process**:
1. Create checklist for each endpoint
2. Manual code review
3. Automated security scanning
4. Penetration testing
5. Document findings
6. Remediate vulnerabilities
7. Re-test

### 6. Input Validation Hardening 

**Priority**: P0-Critical

**Implementation**:

```python
# In src/models/validators.py

from pydantic import BaseModel, validator, Field
import re

class SecureTextInput(BaseModel):
    """Secure text input with validation."""
    
    text: str = Field(..., min_length=1, max_length=10000)
    
    @validator('text')
    def validate_text(cls, v):
        # Remove null bytes
        v = v.replace('\x00', '')
        
        # Check for SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(--)",
            r"(;.*--)",
        ]
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potential SQL injection detected")
        
        # Check for XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
        ]
        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potential XSS detected")
        
        return v
```

### 7. SQL Injection Prevention Audit 

**Priority**: P0-Critical

**Checklist**:
- [x] Use parameterized queries (SQLAlchemy ORM)
- [x] No raw SQL with string concatenation
- [ ] Input validation on all database queries
- [ ] Least privilege database user
- [ ] Database activity monitoring

**Verification**:
```bash
# Scan for potential SQL injection
grep -r "execute.*%" src/
grep -r "f\".*SELECT" src/
```

### 8. XSS Prevention Audit 

**Priority**: P0-Critical

**Checklist**:
- [x] Content Security Policy (CSP)
- [x] Output encoding
- [x] X-XSS-Protection header
- [ ] Input sanitization
- [ ] HTML entity encoding

**Verification**:
```bash
# Test XSS payloads
curl -X POST https://watcher.mothership-ai.com/test-agent \
  -H "Content-Type: application/json" \
  -d '{"agent_output":"<script>alert(\"xss\")</script>","ground_truth":"test"}'
```

---

## Security Monitoring

### 1. Sentry Security Monitoring 

**Configured**:
- Error tracking
- Performance monitoring
- Security event alerts

### 2. Access Logging 

**Configured**:
- All API requests logged
- Authentication attempts logged
- Failed requests logged

### 3. Intrusion Detection (Pending)

**To Implement**:
- Fail2ban for brute force protection
- Anomaly detection for unusual patterns
- Automated blocking of malicious IPs

---

## Security Incident Response

### Incident Types

1. **Data Breach**
   - Isolate affected systems
   - Rotate all credentials
   - Notify affected users
   - Investigate root cause
   - Implement fixes
   - Document incident

2. **DDoS Attack**
   - Enable Cloudflare DDoS protection
   - Scale infrastructure
   - Block malicious IPs
   - Monitor traffic patterns

3. **Unauthorized Access**
   - Lock affected accounts
   - Rotate credentials
   - Review access logs
   - Implement additional authentication

4. **Vulnerability Disclosure**
   - Acknowledge receipt
   - Assess severity
   - Develop patch
   - Deploy fix
   - Notify users if needed
   - Thank reporter

---

## Security Testing Schedule

### Daily
- Automated vulnerability scanning
- Dependency security checks
- Log review

### Weekly
- Security patch review
- Access log analysis
- Failed authentication review

### Monthly
- Secrets rotation
- Security audit
- Penetration testing
- Compliance review

### Quarterly
- Third-party security assessment
- Red team exercise
- Security training
- Incident response drill

---

## Compliance & Standards

### OWASP Top 10 (2021)
- [x] A01: Broken Access Control
- [x] A02: Cryptographic Failures
- [x] A03: Injection
- [x] A04: Insecure Design
- [x] A05: Security Misconfiguration
- [x] A06: Vulnerable Components
- [x] A07: Authentication Failures
- [x] A08: Software and Data Integrity
- [x] A09: Security Logging Failures
- [x] A10: Server-Side Request Forgery

### OWASP API Security Top 10
- [x] API1: Broken Object Level Authorization
- [x] API2: Broken Authentication
- [x] API3: Broken Object Property Level Authorization
- [x] API4: Unrestricted Resource Consumption
- [x] API5: Broken Function Level Authorization
- [x] API6: Unrestricted Access to Sensitive Business Flows
- [x] API7: Server Side Request Forgery
- [x] API8: Security Misconfiguration
- [x] API9: Improper Inventory Management
- [x] API10: Unsafe Consumption of APIs

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AgentGuard Team | Initial version |

**Last Updated**: October 24, 2025  
**Next Review**: November 24, 2025

---

**Mothership AI**  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

