# 🚀 Complete Deployment Guide: Watcher AI

## Overview
This guide will help you deploy your Watcher AI platform with:
- **Frontend**: Vercel (watcher.mothership-ai.com)
- **Backend**: Render (watcher-api.onrender.com)

## 📋 Prerequisites

### Required Accounts
1. **Vercel Account**: [vercel.com](https://vercel.com)
2. **Render Account**: [render.com](https://render.com)
3. **GitHub Repository**: Already set up ✅
4. **Claude API Key**: From Anthropic ✅

### Domain Setup
- **Primary Domain**: `watcher.mothership-ai.com`
- **API Subdomain**: `api.watcher.mothership-ai.com` (optional, can use Render URL)

---

## 🔧 Part 1: Backend Deployment on Render

### Step 1: Create Render Services

1. **Log into Render Dashboard**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Connect your GitHub account if not already connected

2. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - **Name**: `watcher-postgres`
   - **Database Name**: `watcher_ai`
   - **User**: `watcher_admin`
   - **Region**: Oregon (US West)
   - **Plan**: Starter ($7/month)
   - Click "Create Database"
   - **Save the connection details** (you'll need them)

3. **Create Redis Instance**
   - Click "New +" → "Redis"
   - **Name**: `watcher-redis`
   - **Region**: Oregon (US West)
   - **Plan**: Starter ($7/month)
   - Click "Create Redis"

4. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect to your GitHub repository: `seanebones-lang/mars`
   - **Name**: `watcher-api`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (uses root)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn src.api.main_realtime:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter ($7/month)

### Step 2: Configure Environment Variables

In your Render web service, add these environment variables:

```bash
# Core Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PORT=10000

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
MAX_CONCURRENT_REQUESTS=100

# Database Configuration (use your actual Render database URL)
DATABASE_URL=postgresql://watcher_admin:PASSWORD@HOST:PORT/watcher_ai

# Redis Configuration (use your actual Render Redis URL)
REDIS_URL=redis://red-xxxxx:PORT

# CORS Configuration
CORS_ORIGINS=https://watcher.mothership-ai.com,https://watcher-ai.vercel.app

# Claude API (use your actual key)
CLAUDE_API_KEY=your_claude_api_key_here

# Security Keys (generate secure random strings)
JWT_SECRET_KEY=your_jwt_secret_key_here_64_chars_minimum
ENCRYPTION_KEY=your_encryption_key_here_32_chars_minimum
WEBHOOK_SECRET=your_webhook_secret_here

# MLflow Configuration
MLFLOW_TRACKING_URI=./mlruns
MLFLOW_EXPERIMENT_NAME=agentguard_production

# Application Settings
APP_NAME=Watcher AI
APP_VERSION=1.0.0
COMPANY_NAME=Mothership AI
SUPPORT_EMAIL=support@mothership-ai.com
MAX_UPLOAD_SIZE=100MB
RATE_LIMIT_PER_MINUTE=1000
SESSION_TIMEOUT_HOURS=24
```

### Step 3: Deploy Backend

1. **Trigger Deployment**
   - Click "Create Web Service"
   - Render will automatically deploy from your GitHub repository
   - Monitor the build logs for any errors

2. **Verify Deployment**
   - Once deployed, your API will be available at: `https://watcher-api.onrender.com`
   - Test the health endpoint: `https://watcher-api.onrender.com/health`

---

## 🌐 Part 2: Frontend Deployment on Vercel

### Step 1: Prepare Vercel Deployment

1. **Install Vercel CLI** (optional)
   ```bash
   npm i -g vercel
   ```

2. **Log into Vercel Dashboard**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Connect your GitHub account

### Step 2: Create Vercel Project

1. **Import Project**
   - Click "New Project"
   - Import from GitHub: `seanebones-lang/mars`
   - **Framework Preset**: Next.js
   - **Root Directory**: `agentguard-ui`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`

### Step 3: Configure Environment Variables

In Vercel project settings, add these environment variables:

```bash
# API Configuration (update with your actual Render URL)
NEXT_PUBLIC_API_URL=https://watcher-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://watcher-api.onrender.com

# Application Configuration
NEXT_PUBLIC_APP_NAME=Watcher AI
NEXT_PUBLIC_APP_DESCRIPTION=Real-Time Hallucination Defense for Enterprise AI Systems
NEXT_PUBLIC_DOMAIN=watcher.mothership-ai.com
NEXT_PUBLIC_COMPANY_NAME=Mothership AI
NEXT_PUBLIC_COMPANY_URL=https://mothership-ai.com

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_MONITORING=true
NEXT_PUBLIC_ENABLE_WEBHOOKS=true
NEXT_PUBLIC_ENABLE_BATCH_PROCESSING=true
NEXT_PUBLIC_ENABLE_MULTI_TENANT=true

# Security Configuration
NEXT_PUBLIC_ENABLE_HTTPS_ONLY=true
NEXT_PUBLIC_ENABLE_SECURITY_HEADERS=true
NEXT_PUBLIC_ENABLE_CSP=true

# Performance Configuration
NEXT_PUBLIC_ENABLE_COMPRESSION=true
NEXT_PUBLIC_ENABLE_CACHING=true

# Contact Information
NEXT_PUBLIC_SUPPORT_EMAIL=support@mothership-ai.com
NEXT_PUBLIC_SALES_EMAIL=sales@mothership-ai.com
NEXT_PUBLIC_LEGAL_EMAIL=legal@mothership-ai.com
NEXT_PUBLIC_PRIVACY_EMAIL=privacy@mothership-ai.com
NEXT_PUBLIC_LICENSING_EMAIL=licensing@mothership-ai.com

# Social Links
NEXT_PUBLIC_LINKEDIN_URL=https://linkedin.com/in/sean-mcdonnell-077b15b8
NEXT_PUBLIC_GITHUB_URL=https://github.com/seanebones-lang

# Version Information
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_BUILD_DATE=2025-01-25
NEXT_PUBLIC_COMMIT_SHA=2bff0f6
```

### Step 4: Configure Custom Domain

1. **Add Domain in Vercel**
   - Go to Project Settings → Domains
   - Add `watcher.mothership-ai.com`
   - Follow Vercel's DNS configuration instructions

2. **DNS Configuration**
   - Add CNAME record: `watcher` → `cname.vercel-dns.com`
   - Or A record pointing to Vercel's IP addresses

### Step 5: Deploy Frontend

1. **Deploy**
   - Click "Deploy" in Vercel dashboard
   - Monitor build logs for any errors

2. **Verify Deployment**
   - Test at your Vercel URL first
   - Then test at `watcher.mothership-ai.com` once DNS propagates

---

## 🔗 Part 3: Integration & Testing

### Step 1: Update CORS Settings

Update your Render backend environment variables:
```bash
CORS_ORIGINS=https://watcher.mothership-ai.com,https://your-vercel-app.vercel.app
```

### Step 2: Test Integration

1. **Health Checks**
   - Backend: `https://watcher-api.onrender.com/health`
   - Frontend: `https://watcher.mothership-ai.com`

2. **API Integration**
   - Test API calls from frontend to backend
   - Verify WebSocket connections work
   - Test authentication flow

3. **Feature Testing**
   - Test agent monitoring
   - Test custom rules
   - Test performance dashboard
   - Test legal pages

### Step 3: Performance Optimization

1. **Backend Optimization**
   - Monitor Render metrics
   - Optimize database queries
   - Configure Redis caching

2. **Frontend Optimization**
   - Monitor Vercel analytics
   - Optimize bundle size
   - Configure CDN settings

---

## 🛡️ Part 4: Security & Monitoring

### Security Checklist

- ✅ HTTPS enforced on both frontend and backend
- ✅ CORS properly configured
- ✅ Security headers implemented
- ✅ Environment variables secured
- ✅ Database access restricted
- ✅ API rate limiting enabled

### Monitoring Setup

1. **Render Monitoring**
   - Enable health checks
   - Set up alerts for downtime
   - Monitor resource usage

2. **Vercel Monitoring**
   - Enable Vercel Analytics
   - Monitor Core Web Vitals
   - Set up deployment notifications

---

## 🚨 Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Node.js version compatibility
   - Verify all dependencies are listed
   - Check environment variables

2. **API Connection Issues**
   - Verify CORS settings
   - Check API URL configuration
   - Test network connectivity

3. **Database Connection Issues**
   - Verify database URL format
   - Check connection limits
   - Verify credentials

### Support Resources

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)

---

## 📞 Need Help?

If you encounter any issues during deployment:

1. **Check the logs** in both Vercel and Render dashboards
2. **Verify environment variables** are correctly set
3. **Test locally** to isolate deployment-specific issues
4. **Contact support** if needed:
   - Vercel: [vercel.com/support](https://vercel.com/support)
   - Render: [render.com/support](https://render.com/support)

---

## 🎉 Congratulations!

Once deployed, your Watcher AI platform will be live at:
- **Frontend**: https://watcher.mothership-ai.com
- **Backend**: https://watcher-api.onrender.com
- **API Docs**: https://watcher-api.onrender.com/docs

Your enterprise-grade AI hallucination detection platform is now ready for production use!

---

*This deployment guide was created for the Watcher AI project by Sean McDonnell - Mothership AI*
