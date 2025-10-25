# 🚀 Complete Deployment Guide: AgentGuard

## Overview
**UPDATED: October 2025** - Both frontend and backend now deployed on Render for unified infrastructure management.

This guide will help you deploy your AgentGuard platform with:
- **Frontend**: Render Static Site (agentguard-ui.onrender.com)
- **Backend**: Render Web Service (agentguard-api.onrender.com)
- **Database**: Render PostgreSQL (Managed)
- **Cache**: Render Redis (Managed)

**Architecture Benefits**:
- Unified platform management
- Simplified CORS configuration
- Consistent monitoring and logging
- Cost-effective scaling
- Single vendor relationship

## 📋 Prerequisites

### Required Accounts
1. **Render Account**: [render.com](https://render.com) ✅
2. **GitHub Repository**: Already set up ✅
3. **Claude API Key**: From Anthropic ✅
4. **Optional**: Custom domain for production deployment

### Domain Setup (Optional)
- **Primary Domain**: `agentguard.mothership-ai.com` (or your custom domain)
- **API Subdomain**: `api.agentguard.mothership-ai.com` (or use Render URL)

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

4. **Create Backend Web Service**
   - Click "New +" → "Web Service"
   - Connect to your GitHub repository: `seanebones-lang/mars`
   - **Name**: `agentguard-api`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (uses root)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Starter ($7/month) or higher for production

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

# CORS Configuration (update with your actual frontend URL)
CORS_ORIGINS=https://agentguard-ui.onrender.com,https://agentguard.mothership-ai.com

# Claude API (use your actual key)
CLAUDE_API_KEY=your_claude_api_key_here
OPENAI_API_KEY=your_openai_api_key_here_optional

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
   - Once deployed, your API will be available at: `https://agentguard-api.onrender.com`
   - Test the health endpoint: `https://agentguard-api.onrender.com/health`

---

## 🌐 Part 2: Frontend Deployment on Render

### Step 1: Create Frontend Static Site

1. **Create Static Site Service**
   - Click "New +" → "Static Site"
   - Connect to your GitHub repository: `seanebones-lang/mars`
   - **Name**: `agentguard-ui`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: `agentguard-ui`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `out` (for Next.js static export) or `.next` (for Next.js server)
   - **Plan**: Starter (Free for static sites)

**Note**: If using Next.js with server-side features, deploy as a Web Service instead:
   - **Runtime**: Node
   - **Build Command**: `cd agentguard-ui && npm install && npm run build`
   - **Start Command**: `cd agentguard-ui && npm start`

### Step 2: Configure Environment Variables

In Render static site/web service settings, add these environment variables:

```bash
# API Configuration (update with your actual Render backend URL)
NEXT_PUBLIC_API_URL=https://agentguard-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://agentguard-api.onrender.com

# Application Configuration
NEXT_PUBLIC_APP_NAME=AgentGuard
NEXT_PUBLIC_APP_DESCRIPTION=Enterprise AI Agent Safety and Hallucination Detection Platform
NEXT_PUBLIC_DOMAIN=agentguard.mothership-ai.com
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
NEXT_PUBLIC_BUILD_DATE=2025-10-24
NEXT_PUBLIC_COMMIT_SHA=latest
```

### Step 3: Configure Custom Domain (Optional)

1. **Add Domain in Render**
   - Go to Service Settings → Custom Domains
   - Add `agentguard.mothership-ai.com`
   - Follow Render's DNS configuration instructions

2. **DNS Configuration**
   - Add CNAME record: `agentguard` → `agentguard-ui.onrender.com`
   - Or use Render's provided DNS instructions

### Step 4: Deploy Frontend

1. **Trigger Deployment**
   - Click "Create Static Site" or "Create Web Service"
   - Render will automatically deploy from your GitHub repository
   - Monitor the build logs for any errors

2. **Verify Deployment**
   - Test at your Render URL: `https://agentguard-ui.onrender.com`
   - Test at custom domain once DNS propagates (if configured)

---

## 🔗 Part 3: Integration & Testing

### Step 1: Update CORS Settings

Update your Render backend environment variables to include your frontend URL:
```bash
CORS_ORIGINS=https://agentguard-ui.onrender.com,https://agentguard.mothership-ai.com
```

**Note**: With both services on Render, CORS configuration is simplified and more secure.

### Step 2: Test Integration

1. **Health Checks**
   - Backend: `https://agentguard-api.onrender.com/health`
   - Frontend: `https://agentguard-ui.onrender.com`

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
   - Monitor Render analytics
   - Optimize bundle size
   - Configure caching headers

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

1. **Render Backend Monitoring**
   - Enable health checks for API service
   - Set up alerts for downtime and errors
   - Monitor resource usage (CPU, memory, requests)
   - Configure log aggregation

2. **Render Frontend Monitoring**
   - Enable health checks for frontend service
   - Monitor deployment status
   - Track build times and errors
   - Set up deployment notifications

3. **Unified Monitoring Benefits**
   - Single dashboard for all services
   - Consistent logging format
   - Simplified alert management
   - Integrated metrics across stack

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

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Render Community**: [community.render.com](https://community.render.com)
- **Next.js Docs**: [nextjs.org/docs](https://nextjs.org/docs)
- **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

## 📞 Need Help?

If you encounter any issues during deployment:

1. **Check the logs** in Render dashboard for both services
2. **Verify environment variables** are correctly set in both frontend and backend
3. **Test locally** to isolate deployment-specific issues
4. **Verify CORS configuration** matches your deployed URLs
5. **Contact support** if needed:
   - Render Support: [render.com/support](https://render.com/support)
   - Render Community: [community.render.com](https://community.render.com)

---

## 🎉 Congratulations!

Once deployed, your AgentGuard platform will be live at:
- **Frontend**: https://agentguard-ui.onrender.com (or your custom domain)
- **Backend**: https://agentguard-api.onrender.com (or your custom domain)
- **API Docs**: https://agentguard-api.onrender.com/docs
- **Health Check**: https://agentguard-api.onrender.com/health

Your enterprise-grade AI agent safety and hallucination detection platform is now ready for production use!

## 🚀 Next Steps

1. **Configure Custom Domains** (if not already done)
2. **Set up monitoring and alerts** in Render dashboard
3. **Configure backup strategies** for database
4. **Implement CI/CD pipelines** for automated deployments
5. **Review security settings** and enable additional protections
6. **Load test your deployment** to verify scalability
7. **Document your deployment** for team reference

## 📊 Render-Specific Advantages

- **Unified Infrastructure**: All services on one platform
- **Auto-scaling**: Automatic resource scaling based on demand
- **Zero-downtime Deploys**: Rolling deployments with health checks
- **Managed Services**: PostgreSQL and Redis fully managed
- **DDoS Protection**: Built-in security features
- **Global CDN**: Fast content delivery worldwide
- **Cost Efficiency**: Pay only for what you use

---

*This deployment guide was updated October 2025 for the AgentGuard project by Sean McDonnell - Mothership AI*
