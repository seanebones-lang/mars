# Cloudflare WAF Setup Guide

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Web Application Firewall deployment**

---

## Overview

This guide provides step-by-step instructions for setting up Cloudflare WAF (Web Application Firewall) to protect the AgentGuard platform.

### Benefits
- **DDoS Protection**: Automatic mitigation of DDoS attacks
- **Bot Management**: Block malicious bots and scrapers
- **Rate Limiting**: Prevent abuse and brute force attacks
- **OWASP Protection**: Defend against OWASP Top 10 vulnerabilities
- **SSL/TLS**: Free SSL certificates with automatic renewal
- **CDN**: Global content delivery network for faster performance

---

## Step 1: Sign Up for Cloudflare

1. Go to [cloudflare.com](https://cloudflare.com)
2. Click "Sign Up" and create an account
3. Verify your email address

**Cost**: Free tier available, Pro plan ($20/month) recommended for production

---

## Step 2: Add Domain

1. Click "Add a Site" in Cloudflare dashboard
2. Enter domain: `mothership-ai.com`
3. Click "Add Site"
4. Select plan:
   - **Free**: Basic DDoS protection, SSL, CDN
   - **Pro** ($20/month): WAF, advanced DDoS, image optimization
   - **Business** ($200/month): Custom WAF rules, PCI compliance
   - **Enterprise** (custom): Dedicated support, SLA

**Recommendation**: Start with Pro plan

---

## Step 3: Update Nameservers

1. Cloudflare will provide two nameservers (e.g., `ns1.cloudflare.com`, `ns2.cloudflare.com`)
2. Go to your domain registrar (e.g., GoDaddy, Namecheap)
3. Update nameservers to Cloudflare's nameservers
4. Wait for DNS propagation (can take up to 24 hours)

**Verification**:
```bash
dig NS mothership-ai.com
# Should show Cloudflare nameservers
```

---

## Step 4: Configure DNS Records

1. In Cloudflare dashboard, go to DNS tab
2. Add DNS records for AgentGuard:

```
Type    Name                Value                           Proxy Status
A       @                   <main-website-ip>              Proxied
CNAME   watcher             agentguard-api.onrender.com    Proxied
CNAME   www                 mothership-ai.com              Proxied
```

**Important**: Enable "Proxied" (orange cloud) to route traffic through Cloudflare WAF

---

## Step 5: Enable SSL/TLS

1. Go to SSL/TLS tab
2. Set SSL/TLS encryption mode to **Full (strict)**
3. Enable "Always Use HTTPS"
4. Enable "Automatic HTTPS Rewrites"
5. Set Minimum TLS Version to **TLS 1.2**

**Configuration**:
```
SSL/TLS Encryption: Full (strict)
Always Use HTTPS: On
Automatic HTTPS Rewrites: On
Minimum TLS Version: TLS 1.2
TLS 1.3: On
```

---

## Step 6: Enable WAF (Web Application Firewall)

1. Go to Security → WAF
2. Enable "Managed Rules"
3. Enable the following rulesets:
   - **Cloudflare Managed Ruleset**: Core WAF rules
   - **Cloudflare OWASP Core Ruleset**: OWASP Top 10 protection
   - **Cloudflare Exposed Credentials Check**: Prevent credential stuffing

**Configuration**:
```yaml
Managed Rules:
  - Cloudflare Managed Ruleset: On
  - Cloudflare OWASP Core Ruleset: On
  - Cloudflare Exposed Credentials Check: On
```

---

## Step 7: Configure Rate Limiting

1. Go to Security → WAF → Rate limiting rules
2. Create the following rules:

### Rule 1: API Rate Limit (General)
```yaml
Name: API Rate Limit
If: (http.request.uri.path contains "/api/")
Then: Rate limit
  - 1000 requests per minute per IP
  - Action: Block
  - Duration: 60 seconds
```

### Rule 2: Authentication Rate Limit
```yaml
Name: Authentication Rate Limit
If: (http.request.uri.path eq "/auth/login")
Then: Rate limit
  - 10 requests per minute per IP
  - Action: Challenge (CAPTCHA)
  - Duration: 300 seconds
```

### Rule 3: Expensive Endpoints
```yaml
Name: Expensive Endpoints Rate Limit
If: (http.request.uri.path contains "/multimodal/detect")
Then: Rate limit
  - 20 requests per minute per IP
  - Action: Block
  - Duration: 60 seconds
```

### Rule 4: Health Check (Allow High Traffic)
```yaml
Name: Health Check Allow
If: (http.request.uri.path eq "/health")
Then: Skip rate limiting
```

---

## Step 8: Configure Firewall Rules

1. Go to Security → WAF → Firewall rules
2. Create the following custom rules:

### Rule 1: Block Known Malicious IPs
```yaml
Name: Block Malicious IPs
If: (ip.geoip.country in {"CN" "RU" "KP"} and cf.threat_score > 10)
Then: Block
```

### Rule 2: Challenge Suspicious Requests
```yaml
Name: Challenge Suspicious
If: (cf.threat_score > 30)
Then: Managed Challenge
```

### Rule 3: Block SQL Injection Attempts
```yaml
Name: Block SQL Injection
If: (http.request.uri.query contains "UNION SELECT" or http.request.uri.query contains "DROP TABLE")
Then: Block
```

### Rule 4: Block XSS Attempts
```yaml
Name: Block XSS
If: (http.request.uri.query contains "<script" or http.request.uri.query contains "javascript:")
Then: Block
```

### Rule 5: Allow Legitimate Bots
```yaml
Name: Allow Good Bots
If: (cf.client.bot and not cf.verified_bot_category in {"Search Engine" "Monitoring"})
Then: Challenge
```

---

## Step 9: Enable DDoS Protection

1. Go to Security → DDoS
2. DDoS protection is **automatically enabled** on all plans
3. Configure sensitivity:
   - **High**: More aggressive (may have false positives)
   - **Medium**: Balanced (recommended)
   - **Low**: Less aggressive (may miss some attacks)

**Recommendation**: Set to Medium

---

## Step 10: Configure Bot Management (Pro+ only)

1. Go to Security → Bots
2. Enable "Bot Fight Mode" (Free) or "Super Bot Fight Mode" (Pro+)
3. Configure bot management:
   - **Definitely automated**: Block
   - **Likely automated**: Challenge
   - **Verified bots**: Allow

**Configuration**:
```yaml
Bot Fight Mode: On
Definitely automated: Block
Likely automated: Challenge
Verified bots: Allow
```

---

## Step 11: Enable Security Headers

1. Go to Security → Settings
2. Enable the following security headers:

```yaml
Security Headers:
  - HTTP Strict Transport Security (HSTS): On
    - Max Age: 31536000 (1 year)
    - Include Subdomains: On
    - Preload: On
  
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: no-referrer
```

---

## Step 12: Configure Page Rules

1. Go to Rules → Page Rules
2. Create the following page rules:

### Rule 1: Cache Static Assets
```yaml
URL: watcher.mothership-ai.com/static/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month
```

### Rule 2: Bypass Cache for API
```yaml
URL: watcher.mothership-ai.com/api/*
Settings:
  - Cache Level: Bypass
```

### Rule 3: Force HTTPS
```yaml
URL: http://watcher.mothership-ai.com/*
Settings:
  - Always Use HTTPS: On
```

---

## Step 13: Enable Analytics

1. Go to Analytics → Traffic
2. Enable the following:
   - **Web Analytics**: Track traffic and performance
   - **Security Analytics**: Monitor threats and attacks
   - **Bot Analytics**: Track bot activity

---

## Step 14: Test WAF Configuration

### Test 1: SQL Injection Protection
```bash
# Should be blocked by WAF
curl "https://watcher.mothership-ai.com/api?id=1' OR '1'='1"

# Expected: 403 Forbidden or Cloudflare challenge page
```

### Test 2: XSS Protection
```bash
# Should be blocked by WAF
curl "https://watcher.mothership-ai.com/api?q=<script>alert('xss')</script>"

# Expected: 403 Forbidden
```

### Test 3: Rate Limiting
```bash
# Should be rate limited after 1000 requests
for i in {1..1100}; do
  curl https://watcher.mothership-ai.com/health
done

# Expected: 429 Too Many Requests after 1000 requests
```

### Test 4: DDoS Protection
```bash
# Simulate high traffic (use load testing tool)
locust -f tests/load/locustfile.py \
  --headless \
  --users 10000 \
  --spawn-rate 1000 \
  --run-time 1m \
  --host=https://watcher.mothership-ai.com

# Cloudflare should automatically mitigate
```

### Test 5: SSL/TLS
```bash
# Check SSL configuration
curl -I https://watcher.mothership-ai.com

# Should see:
# - HTTP/2 200
# - strict-transport-security header
# - Valid SSL certificate
```

---

## Step 15: Monitor and Tune

### Daily Monitoring
1. Check Security → Analytics for threats
2. Review blocked requests
3. Adjust rules if false positives

### Weekly Review
1. Analyze traffic patterns
2. Update rate limits if needed
3. Review firewall rule effectiveness

### Monthly Audit
1. Review all WAF rules
2. Update OWASP ruleset
3. Test all protection mechanisms

---

## Troubleshooting

### Issue: Legitimate Traffic Blocked

**Symptoms**: Users report 403 errors

**Solution**:
1. Go to Security → Overview
2. Check "Activity Log" for blocked requests
3. Identify the rule blocking legitimate traffic
4. Add exception or adjust rule sensitivity

### Issue: False Positives in Rate Limiting

**Symptoms**: Users hit rate limits too quickly

**Solution**:
1. Go to Security → WAF → Rate limiting rules
2. Increase rate limit threshold
3. Or add exception for specific IPs/paths

### Issue: Performance Degradation

**Symptoms**: Slow response times

**Solution**:
1. Check if WAF rules are too aggressive
2. Disable "Challenge" actions temporarily
3. Use "Log" mode to test rules before enforcing

---

## Cost Optimization

### Free Plan
- Basic DDoS protection
- SSL/TLS
- CDN
- Limited WAF rules

**Best For**: Development and staging

### Pro Plan ($20/month)
- Advanced DDoS protection
- Full WAF with OWASP rules
- Bot management
- Image optimization

**Best For**: Production (recommended)

### Business Plan ($200/month)
- Custom WAF rules
- PCI compliance
- 100% uptime SLA
- Dedicated support

**Best For**: Enterprise customers

---

## Integration with AgentGuard

### Update Render Configuration

1. In Render dashboard, update environment variables:
```bash
CLOUDFLARE_ENABLED=true
CLOUDFLARE_ZONE_ID=<your-zone-id>
CLOUDFLARE_API_TOKEN=<your-api-token>
```

2. Update `render.yaml`:
```yaml
services:
  - type: web
    name: agentguard-api
    env: python
    envVars:
      - key: CLOUDFLARE_ENABLED
        value: true
```

### Update Application Code

Add Cloudflare detection:
```python
# In src/api/main.py

def is_cloudflare_request(request: Request) -> bool:
    """Check if request is coming through Cloudflare."""
    return "CF-Ray" in request.headers

@app.middleware("http")
async def cloudflare_middleware(request: Request, call_next):
    """Handle Cloudflare-specific headers."""
    if is_cloudflare_request(request):
        # Get real IP from Cloudflare header
        real_ip = request.headers.get("CF-Connecting-IP")
        if real_ip:
            request.state.client_ip = real_ip
    
    response = await call_next(request)
    return response
```

---

## Security Checklist

- [ ] Cloudflare account created
- [ ] Domain added to Cloudflare
- [ ] Nameservers updated
- [ ] DNS records configured
- [ ] SSL/TLS enabled (Full strict mode)
- [ ] WAF enabled with OWASP rules
- [ ] Rate limiting rules configured
- [ ] Firewall rules configured
- [ ] DDoS protection enabled
- [ ] Bot management enabled
- [ ] Security headers configured
- [ ] Page rules configured
- [ ] Analytics enabled
- [ ] WAF tested (SQL injection, XSS, rate limiting)
- [ ] Monitoring configured
- [ ] Team trained on Cloudflare dashboard

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

