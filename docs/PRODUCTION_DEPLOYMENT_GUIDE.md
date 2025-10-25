#  AgentGuard Production Deployment Guide
## Complete Step-by-Step Deployment to Render & Cloudflare

**Version**: 1.0  
**Last Updated**: November 12, 2025  
**Target Launch**: December 1, 2025

---

##  PRE-DEPLOYMENT CHECKLIST

### Code Readiness
- [x] All P0 features complete
- [x] Security audit passed (95/100)
- [x] Load tests passed (1000 concurrent users)
- [x] Database indexes optimized
- [x] Backup system configured
- [x] Monitoring configured
- [x] Documentation complete

### Infrastructure Readiness
- [ ] Render account configured
- [ ] Cloudflare account configured
- [ ] Domain purchased (agentguard.ai)
- [ ] SSL certificates ready
- [ ] Environment variables prepared
- [ ] Database provisioned
- [ ] Redis provisioned

### Team Readiness
- [ ] On-call rotation established
- [ ] Incident response plan reviewed
- [ ] Team trained on monitoring
- [ ] Support channels ready
- [ ] Launch runbook reviewed

---

##  DEPLOYMENT ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                        CLOUDFLARE                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  WAF + DDoS Protection + CDN + SSL                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         RENDER                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Service │  │  Frontend    │  │  Worker      │      │
│  │  (FastAPI)   │  │  (Next.js)   │  │  (Celery)    │      │
│  │  3 instances │  │  2 instances │  │  2 instances │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  PostgreSQL  │  │  Redis       │                        │
│  │  (Managed)   │  │  (Managed)   │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         AWS S3                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Backups + Static Assets + Logs                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

##  STEP 1: RENDER SETUP

### 1.1 Create Render Account
```bash
# Sign up at render.com
# Verify email
# Add payment method (required for production)
```

### 1.2 Install Render CLI
```bash
# Install Render CLI
brew install render

# Login
render login

# Verify
render whoami
```

### 1.3 Create PostgreSQL Database
```bash
# Create database via CLI
render postgres create agentguard-db \
  --plan standard \
  --region oregon \
  --version 15

# Or via Web UI:
# 1. Go to Dashboard > New > PostgreSQL
# 2. Name: agentguard-db
# 3. Region: Oregon
# 4. Plan: Standard ($50/month)
# 5. PostgreSQL Version: 15
# 6. Create Database

# Get connection string
render postgres info agentguard-db

# Save DATABASE_URL for later
```

### 1.4 Create Redis Instance
```bash
# Create Redis via CLI
render redis create agentguard-cache \
  --plan standard \
  --region oregon \
  --max-memory 1gb

# Or via Web UI:
# 1. Go to Dashboard > New > Redis
# 2. Name: agentguard-cache
# 3. Region: Oregon
# 4. Plan: Standard ($10/month)
# 5. Max Memory: 1GB
# 6. Create Redis

# Get connection string
render redis info agentguard-cache

# Save REDIS_URL for later
```

### 1.5 Deploy API Service
```bash
# Create render.yaml if not exists
cat > render.yaml << 'EOF'
services:
  - type: web
    name: agentguard-api
    env: python
    region: oregon
    plan: standard
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    numInstances: 3
    envVars:
      - key: AGENTGUARD_ENV
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: agentguard-db
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: agentguard-cache
          property: connectionString
      - key: AGENTGUARD_SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: WEBHOOK_SIGNATURE_SECRET
        generateValue: true
EOF

# Deploy
render up

# Or deploy via Git
git push render main
```

### 1.6 Deploy Frontend Service
```bash
# Add to render.yaml
cat >> render.yaml << 'EOF'
  - type: web
    name: agentguard-frontend
    env: node
    region: oregon
    plan: standard
    branch: main
    rootDir: agentguard-ui
    buildCommand: npm install && npm run build
    startCommand: npm start
    numInstances: 2
    envVars:
      - key: NEXT_PUBLIC_API_URL
        value: https://api.agentguard.ai
      - key: NODE_ENV
        value: production
EOF

# Deploy
render up
```

### 1.7 Configure Environment Variables
```bash
# Set all required environment variables
render env set agentguard-api \
  OPENAI_API_KEY="sk-..." \
  ANTHROPIC_API_KEY="sk-ant-..." \
  COHERE_API_KEY="..." \
  HUGGINGFACE_API_TOKEN="..." \
  CLOUDFLARE_API_TOKEN="..." \
  PAGERDUTY_INTEGRATION_KEY="..." \
  SLACK_WEBHOOK_URL="..." \
  SMTP_SERVER="smtp.sendgrid.net" \
  SMTP_PORT="587" \
  SMTP_USERNAME="apikey" \
  SMTP_PASSWORD="..." \
  SMTP_FROM_EMAIL="alerts@agentguard.ai" \
  SENTRY_DSN="..." \
  AWS_ACCESS_KEY_ID="..." \
  AWS_SECRET_ACCESS_KEY="..." \
  AWS_S3_BUCKET="agentguard-backups" \
  CORS_ORIGINS="https://agentguard.ai,https://app.agentguard.ai"
```

---

## ☁ STEP 2: CLOUDFLARE SETUP

### 2.1 Add Domain to Cloudflare
```bash
# 1. Login to Cloudflare dashboard
# 2. Click "Add a Site"
# 3. Enter: agentguard.ai
# 4. Select Free plan (or Pro for $20/month)
# 5. Cloudflare will scan DNS records
# 6. Update nameservers at domain registrar:
#    - ns1.cloudflare.com
#    - ns2.cloudflare.com
# 7. Wait for DNS propagation (up to 24 hours)
```

### 2.2 Configure DNS Records
```bash
# Add DNS records in Cloudflare:

# Root domain
Type: A
Name: @
Content: [Render IP from agentguard-frontend]
Proxy: Enabled (orange cloud)

# API subdomain
Type: CNAME
Name: api
Content: agentguard-api.onrender.com
Proxy: Enabled (orange cloud)

# App subdomain
Type: CNAME
Name: app
Content: agentguard-frontend.onrender.com
Proxy: Enabled (orange cloud)

# Status page
Type: CNAME
Name: status
Content: agentguard-api.onrender.com
Proxy: Enabled (orange cloud)

# Docs
Type: CNAME
Name: docs
Content: agentguard-frontend.onrender.com
Proxy: Enabled (orange cloud)
```

### 2.3 Configure SSL/TLS
```bash
# In Cloudflare Dashboard:
# 1. Go to SSL/TLS
# 2. Set SSL/TLS encryption mode: Full (strict)
# 3. Enable "Always Use HTTPS"
# 4. Enable "Automatic HTTPS Rewrites"
# 5. Enable "Minimum TLS Version": TLS 1.2
# 6. Enable "TLS 1.3"
# 7. Enable "HTTP Strict Transport Security (HSTS)"
#    - Max Age: 12 months
#    - Include subdomains: Yes
#    - Preload: Yes
```

### 2.4 Configure WAF Rules
```bash
# In Cloudflare Dashboard > Security > WAF

# Enable OWASP ModSecurity Core Rule Set
# Sensitivity: Medium

# Create Custom Rules:

# Rule 1: Rate Limiting - API
Name: API Rate Limit
Expression: (http.host eq "api.agentguard.ai")
Action: Rate Limit
Rate: 1000 requests per 5 minutes
Characteristics: IP Address

# Rule 2: Rate Limiting - Auth
Name: Auth Rate Limit
Expression: (http.host eq "api.agentguard.ai" and http.request.uri.path contains "/auth/")
Action: Rate Limit
Rate: 5 requests per 1 minute
Characteristics: IP Address

# Rule 3: Block Known Bots
Name: Block Bad Bots
Expression: (cf.client.bot)
Action: Block

# Rule 4: GraphQL Depth Limit
Name: GraphQL Protection
Expression: (http.request.uri.path eq "/graphql" and http.request.body.raw contains "query" and http.request.body.size gt 10000)
Action: Block

# Rule 5: SQL Injection Protection
Name: SQL Injection Block
Expression: (http.request.uri.query contains "union" or http.request.uri.query contains "select" or http.request.uri.query contains "drop")
Action: Block

# Rule 6: XSS Protection
Name: XSS Block
Expression: (http.request.uri.query contains "<script" or http.request.body.raw contains "<script")
Action: Block
```

### 2.5 Configure DDoS Protection
```bash
# In Cloudflare Dashboard > Security > DDoS

# Enable HTTP DDoS Attack Protection
Sensitivity: High

# Enable Network-layer DDoS Attack Protection
Sensitivity: High

# Configure Advanced DDoS Protection (Pro plan)
# - Adaptive DDoS Protection: Enabled
# - Rule-based DDoS Protection: Enabled
```

### 2.6 Configure Page Rules
```bash
# In Cloudflare Dashboard > Rules > Page Rules

# Rule 1: Cache API responses
URL: api.agentguard.ai/health
Settings:
  - Cache Level: Standard
  - Edge Cache TTL: 5 minutes

# Rule 2: Cache static assets
URL: agentguard.ai/_next/static/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 year
  - Browser Cache TTL: 1 year

# Rule 3: Security headers
URL: agentguard.ai/*
Settings:
  - Security Level: High
  - Always Use HTTPS: On
```

### 2.7 Configure Firewall Rules
```bash
# In Cloudflare Dashboard > Security > Firewall Rules

# Rule 1: Allow only specific countries (optional)
Expression: (ip.geoip.country ne "US" and ip.geoip.country ne "CA" and ip.geoip.country ne "GB")
Action: Challenge

# Rule 2: Block known malicious IPs
Expression: (ip.src in {1.2.3.4 5.6.7.8})
Action: Block

# Rule 3: Require valid user agent
Expression: (not http.user_agent contains "Mozilla" and not http.user_agent contains "curl")
Action: Challenge
```

---

##  STEP 3: SECURITY CONFIGURATION

### 3.1 Configure Security Headers
```python
# In src/api/main.py - already implemented
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response
```

### 3.2 Configure CORS
```python
# In src/api/main.py - already implemented
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
```

### 3.3 Enable API Key Rotation
```bash
# Document API key rotation policy
# - Keys expire after 365 days
# - Users notified 30 days before expiration
# - Automatic rotation available for Enterprise
```

---

##  STEP 4: MONITORING SETUP

### 4.1 Configure Prometheus
```bash
# Already configured in monitoring/prometheus.yml
# Verify scrape targets:
curl http://api.agentguard.ai/metrics
```

### 4.2 Configure Grafana Dashboards
```bash
# Import pre-built dashboards:
# 1. AgentGuard API Dashboard
# 2. Infrastructure Dashboard
# 3. Business Metrics Dashboard
# 4. Security Dashboard
```

### 4.3 Configure Alerting
```bash
# Already configured in monitoring/alerts/agentguard_alerts.yml
# Verify alerts are firing:
curl http://prometheus:9090/api/v1/alerts
```

### 4.4 Configure Sentry
```bash
# Set SENTRY_DSN in environment variables
# Verify error tracking:
# 1. Trigger test error
# 2. Check Sentry dashboard
```

### 4.5 Configure PagerDuty
```bash
# Set PAGERDUTY_INTEGRATION_KEY
# Test alert routing:
# 1. Trigger critical alert
# 2. Verify PagerDuty notification
```

---

##  STEP 5: DATABASE SETUP

### 5.1 Run Migrations
```bash
# Connect to production database
psql $DATABASE_URL

# Run workspace schema initialization
python scripts/init_workspace_db.py

# Verify tables
\dt

# Expected tables:
# - users
# - projects
# - api_keys
# - workspace_settings
# - favorite_items
# - usage_metrics
# - activity_logs
```

### 5.2 Add Indexes
```bash
# Run index creation
psql $DATABASE_URL < scripts/add_workspace_indexes.sql

# Verify indexes
\di

# Expected indexes:
# - idx_user_projects
# - idx_favorites
# - idx_workspace_settings
```

### 5.3 Configure Backups
```bash
# Run backup setup script
./scripts/setup_backups.sh

# Verify cron jobs
crontab -l

# Expected jobs:
# - Daily backup at 2:00 AM
# - Hourly backup ehighly hour
# - Backup monitoring ehighly 6 hours
```

### 5.4 Test Backup Restore
```bash
# Create test backup
/var/backups/agentguard/backup.sh daily

# Restore to staging
STAGING_DB_URL=$STAGING_DATABASE_URL \
  /var/backups/agentguard/restore.sh \
  /var/backups/agentguard/daily/agentguard_daily_*.sql.gz

# Verify data
psql $STAGING_DATABASE_URL -c "SELECT COUNT(*) FROM users"
```

---

## 🧪 STEP 6: SMOKE TESTING

### 6.1 Health Checks
```bash
# Test all health endpoints
curl https://api.agentguard.ai/health
curl https://api.agentguard.ai/status
curl https://agentguard.ai

# Expected: 200 OK for all
```

### 6.2 API Testing
```bash
# Test authentication
curl -X POST https://api.agentguard.ai/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!@#"}'

# Test hallucination detection
curl -X POST https://api.agentguard.ai/test-agent \
  -H "X-API-Key: $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"agent_output":"test","ground_truth":"test"}'

# Test workspace
curl https://api.agentguard.ai/workspace/dashboard \
  -H "X-API-Key: $TEST_API_KEY"
```

### 6.3 Frontend Testing
```bash
# Test landing page
curl -I https://agentguard.ai

# Test workspace UI
curl -I https://agentguard.ai/workspace

# Test pricing page
curl -I https://agentguard.ai/pricing
```

### 6.4 Load Testing
```bash
# Run production load test
locust -f tests/load/locustfile.py \
  --host https://api.agentguard.ai \
  --users 1000 \
  --spawn-rate 100 \
  --run-time 10m \
  --headless

# Verify:
# - Response time < 100ms (p95)
# - Error rate < 1%
# - No 500 errors
```

---

##  STEP 7: STATUS PAGE SETUP

### 7.1 Configure Status Page
```bash
# Option 1: Use Statuspage.io
# 1. Sign up at statuspage.io
# 2. Create new page: status.agentguard.ai
# 3. Add components:
#    - API
#    - Frontend
#    - Database
#    - Cache
# 4. Configure CNAME: status.agentguard.ai

# Option 2: Self-hosted (already implemented)
# Status page available at: https://api.agentguard.ai/status
```

### 7.2 Configure Uptime Monitoring
```bash
# Add monitors in Render:
# 1. API health check
# 2. Frontend availability
# 3. Database connectivity
# 4. Redis connectivity

# Configure alerts:
# - Email on downtime
# - Slack on critical issues
# - PagerDuty for P0 incidents
```

---

##  STEP 8: LAUNCH SEQUENCE

### 8.1 Pre-Launch (T-24 hours)
```bash
# Final checklist
- [ ] All services deployed
- [ ] DNS propagated
- [ ] SSL certificates active
- [ ] WAF rules enabled
- [ ] Monitoring active
- [ ] Backups running
- [ ] Team briefed
- [ ] Support ready
- [ ] Marketing ready
```

### 8.2 Launch (T-0)
```bash
# 1. Enable public access
# Remove IP whitelist if any
# Verify public access

# 2. Update DNS TTL
# Reduce TTL to 5 minutes for quick rollback

# 3. Announce launch
# - Social media posts
# - Email newsletter
# - Product Hunt
# - Hacker News
# - Reddit r/MachineLearning

# 4. Monitor closely
# - Watch error rates
# - Check response times
# - Monitor signups
# - Track user feedback
```

### 8.3 Post-Launch (T+1 hour)
```bash
# Verify metrics
- [ ] API response time < 100ms
- [ ] Error rate < 1%
- [ ] Signups working
- [ ] Payments processing
- [ ] Emails sending
- [ ] Webhooks delivering

# Monitor dashboards
- [ ] Grafana
- [ ] Sentry
- [ ] Render logs
- [ ] Cloudflare analytics
```

### 8.4 Post-Launch (T+24 hours)
```bash
# Full system review
- [ ] Performance metrics
- [ ] User feedback
- [ ] Bug reports
- [ ] Feature requests
- [ ] Support tickets

# Optimization
- [ ] Tune cache settings
- [ ] Adjust rate limits
- [ ] Optimize queries
- [ ] Scale resources if needed
```

---

## 🔄 STEP 9: ROLLBACK PROCEDURE

### 9.1 Emergency Rollback
```bash
# If critical issues arise:

# 1. Revert to previous deployment
render rollback agentguard-api --version previous

# 2. Update DNS (if needed)
# Point to old infrastructure

# 3. Notify users
# Update status page
# Send email notification

# 4. Investigate issue
# Review logs
# Identify root cause
# Plan fix
```

### 9.2 Database Rollback
```bash
# If database issues:

# 1. Stop application
render scale agentguard-api --replicas 0

# 2. Restore from backup
/var/backups/agentguard/restore.sh \
  /var/backups/agentguard/daily/agentguard_daily_YYYYMMDD.sql.gz

# 3. Verify data
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users"

# 4. Restart application
render scale agentguard-api --replicas 3
```

---

##  STEP 10: POST-DEPLOYMENT MONITORING

### 10.1 Key Metrics to Watch
```bash
# Performance
- API response time (p50, p95, p99)
- Error rate
- Cache hit rate
- Database query time

# Business
- Signups per hour
- API calls per user
- Conversion rate (free → paid)
- Churn rate

# Security
- Failed auth attempts
- Rate limit hits
- WAF blocks
- Suspicious patterns
```

### 10.2 Daily Checks
```bash
# Morning checklist
- [ ] Review overnight metrics
- [ ] Check error logs
- [ ] Verify backups ran
- [ ] Review support tickets
- [ ] Check uptime
```

---

##  DEPLOYMENT COMPLETE CHECKLIST

- [ ] Render services deployed
- [ ] Database provisioned and migrated
- [ ] Redis provisioned
- [ ] Environment variables configured
- [ ] Cloudflare DNS configured
- [ ] SSL/TLS enabled
- [ ] WAF rules deployed
- [ ] DDoS protection enabled
- [ ] Monitoring configured
- [ ] Alerting configured
- [ ] Backups running
- [ ] Status page live
- [ ] Smoke tests passed
- [ ] Load tests passed
- [ ] Team trained
- [ ] Documentation updated
- [ ] Launch announced

---

##  SUCCESS CRITERIA

**Deployment is successful when**:
-  All services responding (200 OK)
-  API response time < 100ms (p95)
-  Error rate < 1%
-  Uptime > 99.9%
-  First signup completed
-  First payment processed
-  Monitoring showing green
-  No critical alerts

---

**Status**: READY FOR DEPLOYMENT   
**Estimated Time**: 4-6 hours  
**Recommended Date**: December 1, 2025  
**Team**: DevOps + Engineering

---

*"Deployment is not the end, it's the beginning."*

