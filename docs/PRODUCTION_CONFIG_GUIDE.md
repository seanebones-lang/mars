# 🚀 Production Configuration Guide

Complete guide for configuring AgentGuard for production deployment on Render with Cloudflare.

---

## 📋 Prerequisites

- [ ] Render account created
- [ ] Cloudflare account created
- [ ] Domain name registered
- [ ] GitHub repository ready
- [ ] API keys obtained (Claude, Stripe, etc.)

---

## 🔧 Step 1: Render Configuration (30 minutes)

### 1.1 Create Web Service

1. Log into [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure service:

```yaml
Name: agentguard-api
Environment: Python 3.11
Region: Oregon (US West)
Branch: main
Build Command: pip install -r requirements.txt
Start Command: gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
Instance Type: Starter ($7/month) or Standard ($25/month)
```

### 1.2 Environment Variables

Add these in Render Dashboard → Environment:

**Critical Variables** (Add First):
```bash
# AI APIs
CLAUDE_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...

# Database (Render provides this automatically)
DATABASE_URL=postgresql://...  # Auto-populated by Render

# Security
JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
API_KEY_SALT=<generate-with-openssl-rand-hex-32>
SESSION_SECRET=<generate-with-openssl-rand-hex-32>

# Application
NODE_ENV=production
PYTHON_ENV=production
LOG_LEVEL=INFO
```

**Generate Secure Secrets**:
```bash
# Run locally to generate secrets
openssl rand -hex 32  # For JWT_SECRET_KEY
openssl rand -hex 32  # For API_KEY_SALT
openssl rand -hex 32  # For SESSION_SECRET
```

**Additional Variables**:
```bash
# URLs
APP_URL=https://agentguard.ai
API_URL=https://api.agentguard.ai
FRONTEND_URL=https://agentguard.ai

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG...
SMTP_FROM_EMAIL=noreply@agentguard.ai

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
SENTRY_ENVIRONMENT=production

# Redis (add Redis service first)
REDIS_URL=redis://...  # From Render Redis service

# Workspace Database
WORKSPACE_DATABASE_URL=postgresql://...  # Same as DATABASE_URL or separate

# Rate Limiting
RATE_LIMIT_FREE=10
RATE_LIMIT_PRO=100
RATE_LIMIT_BUSINESS=1000

# Features
ENABLE_STREAMING=true
ENABLE_BATCH_PROCESSING=true
ENABLE_WEBHOOKS=true
ENABLE_WORKSPACE=true

# CORS
CORS_ORIGINS=https://agentguard.ai,https://app.agentguard.ai

# Performance
WORKER_PROCESSES=4
WORKER_THREADS=2
WORKER_TIMEOUT=30
```

### 1.3 Add PostgreSQL Database

1. In Render Dashboard → **"New +"** → **"PostgreSQL"**
2. Configure:
```yaml
Name: agentguard-db
Region: Oregon (US West)
PostgreSQL Version: 15
Plan: Starter ($7/month) or Standard ($20/month)
```
3. Copy `DATABASE_URL` to web service environment

### 1.4 Add Redis

1. In Render Dashboard → **"New +"** → **"Redis"**
2. Configure:
```yaml
Name: agentguard-redis
Region: Oregon (US West)
Plan: Starter ($10/month)
```
3. Copy `REDIS_URL` to web service environment

### 1.5 Deploy

1. Click **"Create Web Service"**
2. Wait for initial deployment (~5 minutes)
3. Verify at: `https://agentguard-api.onrender.com/health`

---

## 🌐 Step 2: Cloudflare Configuration (30 minutes)

### 2.1 Add Domain to Cloudflare

1. Log into [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Click **"Add a Site"**
3. Enter your domain: `agentguard.ai`
4. Select **Free Plan**
5. Copy Cloudflare nameservers
6. Update nameservers at your domain registrar
7. Wait for DNS propagation (~5-30 minutes)

### 2.2 DNS Configuration

Add these DNS records:

```
Type    Name    Content                             Proxy
A       @       <Render-IP-Address>                 Proxied (Orange Cloud)
A       api     <Render-IP-Address>                 Proxied (Orange Cloud)
A       app     <Render-IP-Address>                 Proxied (Orange Cloud)
CNAME   www     agentguard.ai                       Proxied (Orange Cloud)
TXT     @       "v=spf1 include:sendgrid.net ~all"  DNS Only
```

**Get Render IP Address**:
```bash
# Resolve your Render URL
nslookup agentguard-api.onrender.com
# Use the IP address returned
```

### 2.3 SSL/TLS Configuration

1. Go to **SSL/TLS** → **Overview**
2. Set encryption mode: **Full (strict)**
3. Enable **Always Use HTTPS**
4. Enable **Automatic HTTPS Rewrites**
5. Enable **Minimum TLS Version**: TLS 1.2

### 2.4 Speed Optimization

1. Go to **Speed** → **Optimization**
2. Enable **Auto Minify**: JavaScript, CSS, HTML
3. Enable **Brotli** compression
4. Enable **Rocket Loader** (for frontend)
5. Go to **Caching** → **Configuration**
6. Set **Caching Level**: Standard
7. Set **Browser Cache TTL**: 4 hours

### 2.5 Security Settings

1. Go to **Security** → **Settings**
2. Set **Security Level**: Medium
3. Enable **Bot Fight Mode**
4. Go to **Firewall** → **Tools**
5. Enable **Browser Integrity Check**
6. Enable **Challenge Passage**: 30 minutes

---

## 🛡️ Step 3: Cloudflare WAF Rules (1 hour)

### 3.1 Rate Limiting Rules

Create these WAF rules:

**Rule 1: API Rate Limiting**
```
Rule Name: API Rate Limit
Expression: (http.request.uri.path contains "/api/")
Action: Rate Limit
Rate: 100 requests per minute per IP
Duration: 60 seconds
Response: 429 Too Many Requests
```

**Rule 2: Authentication Endpoint Protection**
```
Rule Name: Auth Rate Limit
Expression: (http.request.uri.path eq "/auth/login")
Action: Rate Limit
Rate: 5 requests per minute per IP
Duration: 300 seconds
Response: 429 with custom message
```

### 3.2 Security Rules

**Rule 3: SQL Injection Protection**
```
Rule Name: SQL Injection Block
Expression: (http.request.uri.query contains "union select" or 
            http.request.uri.query contains "drop table" or
            http.request.body contains "union select")
Action: Block
Response: 403 Forbidden
```

**Rule 4: XSS Protection**
```
Rule Name: XSS Block
Expression: (http.request.uri.query contains "<script" or
            http.request.body contains "<script")
Action: Block
Response: 403 Forbidden
```

**Rule 5: GraphQL Depth Limit** (if using GraphQL)
```
Rule Name: GraphQL Depth Limit
Expression: (http.request.uri.path eq "/graphql")
Action: Challenge
Challenge Type: Managed Challenge
```

**Rule 6: Webhook Protection**
```
Rule Name: Webhook Signature Required
Expression: (http.request.uri.path contains "/webhooks/" and
            not http.request.headers["X-Webhook-Signature"])
Action: Block
Response: 401 Unauthorized
```

### 3.3 Geographic Rules (Optional)

**Rule 7: Block Suspicious Countries**
```
Rule Name: Geo Block
Expression: (ip.geoip.country in {"CN" "RU" "KP"})
Action: Challenge
Challenge Type: Managed Challenge
```

---

## 🔗 Step 4: Connect Render to Cloudflare (15 minutes)

### 4.1 Custom Domain in Render

1. Go to Render Dashboard → Your Service → **Settings**
2. Scroll to **Custom Domains**
3. Click **"Add Custom Domain"**
4. Add: `api.agentguard.ai`
5. Copy the CNAME target provided
6. Add CNAME record in Cloudflare (if not already added)

### 4.2 Verify SSL

1. Wait 5-10 minutes for SSL provisioning
2. Test: `https://api.agentguard.ai/health`
3. Verify SSL certificate in browser

---

## 🗄️ Step 5: Database Setup (30 minutes)

### 5.1 Run Migrations

```bash
# Connect to Render shell
render shell -s agentguard-api

# Run migrations
python -m alembic upgrade head

# Or if using SQLAlchemy directly
python scripts/init_db.py
```

### 5.2 Add Indexes

```bash
# Connect to database
psql $DATABASE_URL

# Run optimization script
\i scripts/add_workspace_indexes.sql

# Verify indexes
\di
```

### 5.3 Initial Data

```bash
# Create admin user (if applicable)
python scripts/create_admin.py

# Load initial data
python scripts/seed_data.py
```

---

## 📊 Step 6: Monitoring Setup (30 minutes)

### 6.1 Sentry Configuration

1. Create account at [sentry.io](https://sentry.io)
2. Create new project: **Python/FastAPI**
3. Copy DSN
4. Add to Render environment: `SENTRY_DSN=...`
5. Redeploy service

### 6.2 Uptime Monitoring

**Option A: UptimeRobot (Free)**
1. Create account at [uptimerobot.com](https://uptimerobot.com)
2. Add monitor:
   - Type: HTTPS
   - URL: `https://api.agentguard.ai/health`
   - Interval: 5 minutes
3. Add alert contacts

**Option B: Render Built-in**
1. Go to Render Dashboard → Service → **Health Checks**
2. Enable health check
3. Path: `/health`
4. Expected status: 200

### 6.3 Log Aggregation

**Option A: Render Logs**
- View in Render Dashboard → Service → **Logs**
- Limited retention (7 days on free plan)

**Option B: Better Stack (Logtail)**
1. Create account at [betterstack.com](https://betterstack.com)
2. Create source
3. Add to Render environment:
```bash
LOGTAIL_SOURCE_TOKEN=...
```
4. Update logging configuration

---

## 🧪 Step 7: Testing (30 minutes)

### 7.1 Health Check

```bash
curl https://api.agentguard.ai/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

### 7.2 API Endpoint Test

```bash
# Test authentication
curl -X POST https://api.agentguard.ai/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test"}'

# Test hallucination detection
curl -X POST https://api.agentguard.ai/test-agent \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "Test output",
    "ground_truth": "Expected output"
  }'
```

### 7.3 Performance Test

```bash
# Install Apache Bench
brew install apache-bench  # macOS
# or
sudo apt-get install apache2-utils  # Linux

# Run load test
ab -n 1000 -c 10 https://api.agentguard.ai/health

# Expected: >100 requests/second
```

### 7.4 SSL Test

Visit: https://www.ssllabs.com/ssltest/analyze.html?d=api.agentguard.ai

Expected grade: **A or A+**

---

## 📝 Step 8: Documentation Updates (15 minutes)

### 8.1 Update API Documentation

Update base URL in docs:
```markdown
Base URL: https://api.agentguard.ai
```

### 8.2 Update SDK Examples

```python
# Python SDK
client = AgentGuardClient(
    api_key="your_key",
    base_url="https://api.agentguard.ai"
)
```

```typescript
// TypeScript SDK
const client = new AgentGuardClient({
  apiKey: 'your_key',
  baseUrl: 'https://api.agentguard.ai'
});
```

---

## ✅ Verification Checklist

### Infrastructure
- [ ] Render web service deployed
- [ ] PostgreSQL database created
- [ ] Redis cache configured
- [ ] All environment variables set
- [ ] Custom domain connected
- [ ] SSL certificate active

### Cloudflare
- [ ] Domain added to Cloudflare
- [ ] DNS records configured
- [ ] SSL/TLS set to Full (strict)
- [ ] WAF rules created
- [ ] Rate limiting enabled
- [ ] Bot protection enabled

### Database
- [ ] Migrations run successfully
- [ ] Indexes created
- [ ] Initial data loaded
- [ ] Backup configured

### Monitoring
- [ ] Sentry error tracking active
- [ ] Uptime monitoring configured
- [ ] Log aggregation working
- [ ] Health check passing

### Testing
- [ ] Health endpoint responds
- [ ] API endpoints working
- [ ] SSL grade A or A+
- [ ] Performance acceptable (>100 req/s)
- [ ] Rate limiting working
- [ ] WAF rules blocking attacks

---

## 🚨 Troubleshooting

### Issue: "502 Bad Gateway"

**Cause**: Service not responding  
**Solution**:
1. Check Render logs
2. Verify environment variables
3. Check database connection
4. Restart service

### Issue: "SSL Certificate Error"

**Cause**: SSL not provisioned  
**Solution**:
1. Wait 10-15 minutes
2. Verify DNS propagation
3. Check Cloudflare SSL settings
4. Contact Render support

### Issue: "Database Connection Failed"

**Cause**: Invalid DATABASE_URL  
**Solution**:
1. Verify DATABASE_URL in Render
2. Check database is running
3. Test connection manually:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: "Rate Limiting Too Aggressive"

**Cause**: WAF rules too strict  
**Solution**:
1. Review Cloudflare Firewall Events
2. Adjust rate limits
3. Whitelist known IPs
4. Use Managed Challenge instead of Block

---

## 📞 Support

**Render Support**: https://render.com/docs  
**Cloudflare Support**: https://support.cloudflare.com  
**AgentGuard Team**: support@agentguard.ai

---

## 🎉 Success!

Your AgentGuard instance is now running in production!

**Next Steps**:
1. Setup automated backups
2. Configure monitoring alerts
3. Run load tests
4. Begin beta testing

---

**Last Updated**: October 25, 2025  
**Version**: 1.0  
**Status**: Production Ready ✅

