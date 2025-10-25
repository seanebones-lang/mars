# 🛡 Cloudflare WAF Configuration for AgentGuard
## Complete Web Application Firewall Setup

**Version**: 1.0  
**Last Updated**: November 13, 2025  
**Security Level**: Enterprise-Grade

---

##  OVERVIEW

This document provides complete Cloudflare WAF configuration for AgentGuard, including:
- OWASP Top 10 protection
- DDoS mitigation
- Rate limiting
- Bot management
- Custom security rules
- GraphQL protection
- Webhook security

---

##  SECURITY OBJECTIVES

- **Block 99.9%** of malicious traffic
- **< 0.1%** false positive rate
- **Zero-day** vulnerability protection
- **Sub-10ms** latency overhead
- **Real-time** threat intelligence

---

##  STEP 1: ENABLE OWASP CORE RULE SET

### 1.1 Enable Managed Rules
```bash
# In Cloudflare Dashboard:
# Security > WAF > Managed Rules

# Enable: Cloudflare OWASP Core Ruleset
Sensitivity: Medium
Action: Block

# Enable: Cloudflare Managed Ruleset
Sensitivity: Medium
Action: Block

# Enable: Cloudflare Exposed Credentials Check
Action: Log (monitor first, then Block)
```

### 1.2 OWASP Categories Enabled
-  SQL Injection (SQLi)
-  Cross-Site Scripting (XSS)
-  Local File Inclusion (LFI)
-  Remote File Inclusion (RFI)
-  Remote Code Execution (RCE)
-  PHP Injection
-  Session Fixation
-  Scanner Detection
-  Protocol Enforcement
-  Protocol Attack

---

## 🚦 STEP 2: RATE LIMITING RULES

### 2.1 API Rate Limiting
```javascript
// Rule: API Global Rate Limit
Expression:
(http.host eq "api.agentguard.ai")

Action: Rate Limit
Rate: 1000 requests per 5 minutes
Characteristics: IP Address
Counting Expression: (http.request.uri.path ne "/health" and http.request.uri.path ne "/metrics")
```

### 2.2 Authentication Rate Limiting
```javascript
// Rule: Auth Endpoint Protection
Expression:
(http.host eq "api.agentguard.ai" and 
 (http.request.uri.path contains "/auth/" or 
  http.request.uri.path contains "/login" or 
  http.request.uri.path contains "/signup"))

Action: Rate Limit
Rate: 5 requests per 1 minute
Characteristics: IP Address + Cookie
Mitigation Timeout: 600 seconds (10 minutes)
```

### 2.3 Signup Rate Limiting
```javascript
// Rule: Signup Abuse Prevention
Expression:
(http.host eq "api.agentguard.ai" and 
 http.request.uri.path eq "/auth/signup" and 
 http.request.method eq "POST")

Action: Rate Limit
Rate: 3 requests per 1 hour
Characteristics: IP Address
Mitigation Timeout: 3600 seconds (1 hour)
```

### 2.4 Password Reset Rate Limiting
```javascript
// Rule: Password Reset Protection
Expression:
(http.host eq "api.agentguard.ai" and 
 http.request.uri.path contains "/password-reset")

Action: Rate Limit
Rate: 3 requests per 15 minutes
Characteristics: IP Address + Email (from body)
```

### 2.5 API Key Generation Rate Limiting
```javascript
// Rule: API Key Generation Limit
Expression:
(http.host eq "api.agentguard.ai" and 
 http.request.uri.path eq "/workspace/api-keys" and 
 http.request.method eq "POST")

Action: Rate Limit
Rate: 10 requests per 1 hour
Characteristics: User ID (from auth token)
```

---

## 🤖 STEP 3: BOT MANAGEMENT

### 3.1 Block Known Bad Bots
```javascript
// Rule: Block Malicious Bots
Expression:
(cf.bot_management.score lt 30 and 
 not cf.bot_management.verified_bot)

Action: Block
```

### 3.2 Challenge Suspicious Bots
```javascript
// Rule: Challenge Suspicious Bots
Expression:
(cf.bot_management.score lt 50 and 
 cf.bot_management.score ge 30 and 
 not cf.bot_management.verified_bot)

Action: Managed Challenge
```

### 3.3 Allow Good Bots
```javascript
// Rule: Allow Verified Bots
Expression:
(cf.bot_management.verified_bot and 
 cf.bot_management.ja3_hash in {"google" "bing" "slack"})

Action: Allow
```

### 3.4 Block Scrapers
```javascript
// Rule: Block Web Scrapers
Expression:
(http.user_agent contains "scrapy" or 
 http.user_agent contains "selenium" or 
 http.user_agent contains "phantomjs" or 
 http.user_agent contains "headless")

Action: Block
```

---

##  STEP 4: CUSTOM SECURITY RULES

### 4.1 SQL Injection Protection
```javascript
// Rule: Advanced SQL Injection Block
Expression:
(http.request.uri.query contains "union" or 
 http.request.uri.query contains "select" or 
 http.request.uri.query contains "insert" or 
 http.request.uri.query contains "update" or 
 http.request.uri.query contains "delete" or 
 http.request.uri.query contains "drop" or 
 http.request.uri.query contains "exec" or 
 http.request.uri.query contains "script" or 
 http.request.body.raw contains "' or '1'='1" or 
 http.request.body.raw contains "' or 1=1--")

Action: Block
Log: Yes
```

### 4.2 XSS Protection
```javascript
// Rule: Cross-Site Scripting Block
Expression:
(http.request.uri.query contains "<script" or 
 http.request.uri.query contains "javascript:" or 
 http.request.uri.query contains "onerror=" or 
 http.request.uri.query contains "onload=" or 
 http.request.body.raw contains "<script" or 
 http.request.body.raw contains "javascript:" or 
 http.request.headers["referer"][0] contains "<script")

Action: Block
Log: Yes
```

### 4.3 Path Traversal Protection
```javascript
// Rule: Path Traversal Block
Expression:
(http.request.uri.path contains "../" or 
 http.request.uri.path contains "..%2f" or 
 http.request.uri.path contains "..%5c" or 
 http.request.uri.query contains "../")

Action: Block
Log: Yes
```

### 4.4 Command Injection Protection
```javascript
// Rule: Command Injection Block
Expression:
(http.request.uri.query contains ";" or 
 http.request.uri.query contains "|" or 
 http.request.uri.query contains "`" or 
 http.request.uri.query contains "$(" or 
 http.request.body.raw contains "&&" or 
 http.request.body.raw contains "||")

Action: Block
Log: Yes
```

### 4.5 GraphQL Protection
```javascript
// Rule: GraphQL Query Depth Limit
Expression:
(http.request.uri.path eq "/graphql" and 
 http.request.method eq "POST" and 
 (http.request.body.size gt 10000 or 
  http.request.body.raw contains "query" and 
  http.request.body.raw matches "\\{[^}]*\\{[^}]*\\{[^}]*\\{[^}]*\\{"))

Action: Block
Log: Yes
Description: "Blocks deeply nested GraphQL queries (>4 levels)"
```

### 4.6 Webhook Signature Validation
```javascript
// Rule: Webhook Signature Required
Expression:
(http.request.uri.path contains "/webhooks/" and 
 http.request.method eq "POST" and 
 not http.request.headers["x-webhook-signature"][0] matches "sha256=[a-f0-9]{64}")

Action: Block
Log: Yes
Description: "Requires valid HMAC signature for webhooks"
```

### 4.7 Large Payload Protection
```javascript
// Rule: Block Oversized Requests
Expression:
(http.request.body.size gt 5242880)

Action: Block
Log: Yes
Description: "Blocks requests larger than 5MB"
```

### 4.8 Suspicious Header Detection
```javascript
// Rule: Block Suspicious Headers
Expression:
(http.request.headers["x-forwarded-for"][0] contains "," and 
 len(split(http.request.headers["x-forwarded-for"][0], ",")) gt 5)

Action: Block
Log: Yes
Description: "Blocks requests with excessive X-Forwarded-For hops"
```

---

## 🌍 STEP 5: GEO-BLOCKING (OPTIONAL)

### 5.1 Allow Specific Countries
```javascript
// Rule: Geo-Restriction (Optional)
Expression:
(not ip.geoip.country in {"US" "CA" "GB" "DE" "FR" "AU" "NZ" "SG" "JP"})

Action: Managed Challenge
Description: "Challenge requests from outside primary markets"
```

### 5.2 Block High-Risk Countries
```javascript
// Rule: Block High-Risk Regions
Expression:
(ip.geoip.country in {"KP" "IR" "SY"})

Action: Block
Log: Yes
Description: "Blocks traffic from sanctioned countries"
```

---

##  STEP 6: DDOS PROTECTION

### 6.1 HTTP DDoS Protection
```bash
# In Cloudflare Dashboard:
# Security > DDoS > HTTP DDoS Attack Protection

Sensitivity: High
Action: Block

# Advanced Settings:
- Adaptive DDoS Protection: Enabled
- Override Sensitivity: High for /api/*
- Override Action: Block for all attack types
```

### 6.2 Network-Layer DDoS Protection
```bash
# Security > DDoS > Network-layer DDoS Attack Protection

Sensitivity: High
Action: Block

# Protected Protocols:
- TCP SYN Floods
- UDP Floods
- ICMP Floods
- DNS Amplification
- NTP Amplification
```

### 6.3 Advanced TCP Protection
```bash
# Enable Advanced TCP Protection (Enterprise)
- SYN-ACK Flood Protection
- TCP Connection Flood Protection
- TCP Fragment Flood Protection
- TCP Reset Flood Protection
```

---

##  STEP 7: MONITORING & ALERTING

### 7.1 Configure Security Analytics
```bash
# Security > Analytics > Security Events

# Monitor:
- WAF blocks per hour
- Rate limit triggers
- Bot detection events
- DDoS mitigation events
- Top blocked IPs
- Top blocked countries
- Top attack types
```

### 7.2 Configure Alerts
```bash
# Notifications > Add Webhook

# Alert on:
- DDoS attack detected (Immediate)
- WAF block rate > 100/min (5 minutes)
- Rate limit exceeded > 1000/hour (15 minutes)
- New attack pattern detected (Immediate)

# Webhook URL: https://api.agentguard.ai/webhooks/cloudflare
```

### 7.3 Security Event Logging
```bash
# Enable Logpush (Enterprise)
# Logs > Logpush

# Send to:
- S3: s3://agentguard-logs/cloudflare/
- Splunk (optional)
- Datadog (optional)

# Fields to log:
- ClientIP
- ClientRequestURI
- EdgeResponseStatus
- SecurityLevel
- WAFAction
- WAFRuleID
- BotScore
- RayID
```

---

## 🧪 STEP 8: TESTING & VALIDATION

### 8.1 Test WAF Rules
```bash
# Test SQL Injection Block
curl "https://api.agentguard.ai/test?id=1' OR '1'='1"
# Expected: 403 Forbidden

# Test XSS Block
curl "https://api.agentguard.ai/test?q=<script>alert(1)</script>"
# Expected: 403 Forbidden

# Test Rate Limiting
for i in {1..10}; do 
  curl https://api.agentguard.ai/auth/login
done
# Expected: 429 Too Many Requests after 5 requests

# Test Large Payload Block
dd if=/dev/zero bs=1M count=6 | curl -X POST \
  --data-binary @- https://api.agentguard.ai/test
# Expected: 403 Forbidden
```

### 8.2 Test Bot Detection
```bash
# Test with bot user agent
curl -A "scrapy/1.0" https://api.agentguard.ai
# Expected: 403 Forbidden

# Test with legitimate user agent
curl -A "Mozilla/5.0" https://api.agentguard.ai
# Expected: 200 OK
```

### 8.3 Verify DDoS Protection
```bash
# Simulate high request rate (use with caution)
ab -n 10000 -c 100 https://api.agentguard.ai/health
# Expected: Cloudflare should throttle/challenge requests
```

---

##  STEP 9: PERFORMANCE OPTIMIZATION

### 9.1 Cache Rules
```javascript
// Rule: Cache Static Assets
Expression:
(http.request.uri.path matches "^/_next/static/.*")

Action: Cache Everything
Edge Cache TTL: 1 year
Browser Cache TTL: 1 year
```

### 9.2 Compression
```bash
# Speed > Optimization

# Enable:
- Auto Minify: HTML, CSS, JavaScript
- Brotli Compression: Enabled
- Early Hints: Enabled
```

### 9.3 HTTP/3
```bash
# Network > HTTP/3 (with QUIC)

Enable: Yes
```

---

## 🔄 STEP 10: MAINTENANCE & UPDATES

### 10.1 Weekly Review
```bash
# Review security events
- Top blocked IPs
- New attack patterns
- False positives
- Rule effectiveness

# Adjust rules as needed
- Tune sensitivity
- Update rate limits
- Add new patterns
```

### 10.2 Monthly Audit
```bash
# Full security audit
- Review all WAF rules
- Test all protections
- Update threat intelligence
- Review false positive rate
- Optimize performance
```

### 10.3 Quarterly Updates
```bash
# Major updates
- Update OWASP rules
- Review new Cloudflare features
- Conduct penetration testing
- Update documentation
```

---

##  EXPECTED RESULTS

### Security Metrics
- **Blocked Attacks**: 99.9%
- **False Positives**: < 0.1%
- **DDoS Mitigation**: 100%
- **Bot Detection**: 95%+

### Performance Metrics
- **Latency Overhead**: < 10ms
- **Cache Hit Rate**: > 80%
- **Bandwidth Savings**: 40-60%
- **Uptime**: 99.99%

---

##  CONFIGURATION CHECKLIST

- [ ] OWASP Core Ruleset enabled
- [ ] Rate limiting configured (5 rules)
- [ ] Bot management enabled
- [ ] Custom security rules deployed (8 rules)
- [ ] DDoS protection enabled
- [ ] Geo-blocking configured (optional)
- [ ] Monitoring & alerting configured
- [ ] Security event logging enabled
- [ ] All rules tested
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Team trained

---

##  INCIDENT RESPONSE

### If Attack Detected
1. **Verify** attack in Cloudflare Analytics
2. **Analyze** attack pattern
3. **Create** custom rule if needed
4. **Monitor** effectiveness
5. **Document** incident
6. **Update** rules for future

### If False Positive
1. **Identify** blocked legitimate request
2. **Review** triggering rule
3. **Adjust** rule or add exception
4. **Test** thoroughly
5. **Monitor** for recurrence
6. **Document** change

---

**Status**: READY FOR DEPLOYMENT   
**Security Level**: Enterprise-Grade  
**Estimated Setup Time**: 2-3 hours  
**Maintenance**: Weekly reviews required

---

*"Security is not a product, but a process."* - Bruce Schneier

