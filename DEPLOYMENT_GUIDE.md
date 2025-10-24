# 🚀 Watcher AI - Production Deployment Guide

## **Complete Enterprise Deployment Instructions**

This guide provides step-by-step instructions for deploying the **Watcher AI** platform to production using **Vercel** (frontend) and **Render** (backend).

---

## 🎯 **Deployment Overview**

### **Architecture:**
- **Frontend**: React 19 + Next.js 15 → Vercel
- **Backend**: FastAPI + Python 3.11 → Render
- **Database**: PostgreSQL → Render Managed Database
- **Cache**: Redis → Render Managed Redis
- **Domain**: `watcher.mothership-ai.com`

### **Features Deployed:**
✅ Real-time hallucination detection  
✅ Multi-workstation monitoring  
✅ Alert escalation system  
✅ Workstation discovery  
✅ Enterprise authentication & RBAC  
✅ Multi-tenant architecture  
✅ Comprehensive analytics  
✅ Webhook integrations  

---

## 🔧 **Prerequisites**

### **Required Accounts:**
1. **Vercel Account** - For frontend deployment
2. **Render Account** - For backend deployment
3. **GitHub Account** - Repository access
4. **Claude API Key** - AI processing
5. **Domain Access** - For `mothership-ai.com`

### **Required Tools:**
- Git
- Node.js 18+
- Python 3.11+
- Vercel CLI (optional)
- Render CLI (optional)

---

## 🚀 **Frontend Deployment (Vercel)**

### **Step 1: Prepare Repository**
```bash
# Ensure latest code is pushed
cd /path/to/HAL
git add .
git commit -m "Production deployment preparation"
git push origin main
```

### **Step 2: Deploy to Vercel**

#### **Option A: Vercel Dashboard (Recommended)**
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import from GitHub: `seanebones-lang/mars`
4. Set **Root Directory**: `agentguard-ui`
5. **Framework Preset**: Next.js
6. **Build Command**: `npm run build`
7. **Output Directory**: `.next`

#### **Option B: Vercel CLI**
```bash
cd agentguard-ui
npx vercel --prod
```

### **Step 3: Configure Environment Variables**

In Vercel Dashboard → Project Settings → Environment Variables:

```env
# API Configuration
NEXT_PUBLIC_API_URL=https://watcher-api.onrender.com
NEXT_PUBLIC_WS_URL=wss://watcher-api.onrender.com

# Application Configuration
NEXT_PUBLIC_APP_NAME=Watcher AI
NEXT_PUBLIC_APP_DESCRIPTION=Real-Time Hallucination Defense
NEXT_PUBLIC_DOMAIN=watcher.mothership-ai.com
NEXT_PUBLIC_COMPANY_NAME=Mothership AI
NEXT_PUBLIC_COMPANY_URL=https://mothership-ai.com

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=true
NEXT_PUBLIC_ENABLE_MONITORING=true
NEXT_PUBLIC_ENABLE_WEBHOOKS=true
NEXT_PUBLIC_ENABLE_BATCH_PROCESSING=true
NEXT_PUBLIC_ENABLE_MULTI_TENANT=true

# Contact Information
NEXT_PUBLIC_SUPPORT_EMAIL=support@mothership-ai.com
NEXT_PUBLIC_SALES_EMAIL=sales@mothership-ai.com
NEXT_PUBLIC_LINKEDIN_URL=https://linkedin.com/in/seanmcdonnell
NEXT_PUBLIC_GITHUB_URL=https://github.com/seanebones-lang

# Version Information
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_BUILD_DATE=2025-10-24
NEXT_PUBLIC_COMMIT_SHA=812239f
```

### **Step 4: Configure Custom Domain**
1. In Vercel Dashboard → Project → Settings → Domains
2. Add domain: `watcher.mothership-ai.com`
3. Configure DNS records as instructed by Vercel
4. SSL certificates will be automatically provisioned

---

## 🖥️ **Backend Deployment (Render)**

### **Step 1: Create Render Services**

#### **1. PostgreSQL Database**
1. Go to [render.com](https://render.com)
2. Click "New" → "PostgreSQL"
3. **Name**: `watcher-postgres`
4. **Database**: `watcher_ai`
5. **User**: `watcher_admin`
6. **Region**: Oregon (US West)
7. **Plan**: Starter ($7/month)

#### **2. Redis Cache**
1. Click "New" → "Redis"
2. **Name**: `watcher-redis`
3. **Region**: Oregon (US West)
4. **Plan**: Starter ($7/month)

#### **3. Web Service (API)**
1. Click "New" → "Web Service"
2. **Repository**: `seanebones-lang/mars`
3. **Name**: `watcher-api`
4. **Region**: Oregon (US West)
5. **Branch**: `main`
6. **Root Directory**: `.` (root)
7. **Runtime**: Python 3
8. **Build Command**: `pip install -r requirements.txt`
9. **Start Command**: `python -m uvicorn src.api.main_realtime:app --host 0.0.0.0 --port $PORT`
10. **Plan**: Starter ($7/month)

### **Step 2: Configure Environment Variables**

In Render Dashboard → Web Service → Environment:

```env
# Application Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
APP_NAME=Watcher AI
APP_VERSION=1.0.0

# Database Configuration
DATABASE_URL=[Auto-filled from PostgreSQL service]
REDIS_URL=[Auto-filled from Redis service]

# Security Configuration
CLAUDE_API_KEY=[Your Claude API Key]
JWT_SECRET_KEY=[Generate 32-character random string]
ENCRYPTION_KEY=[Generate 32-character random string]
WEBHOOK_SECRET=[Generate 32-character random string]

# CORS Configuration
CORS_ORIGINS=https://watcher.mothership-ai.com,https://watcher-ai.vercel.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=1000
MAX_UPLOAD_SIZE=100MB
SESSION_TIMEOUT_HOURS=24

# Contact Information
SUPPORT_EMAIL=support@mothership-ai.com
COMPANY_NAME=Mothership AI
```

### **Step 3: Configure Health Checks**
- **Health Check Path**: `/health`
- **Initial Delay**: 30 seconds
- **Period**: 10 seconds
- **Timeout**: 5 seconds
- **Failure Threshold**: 3

### **Step 4: Configure Auto-Deploy**
- Enable **Auto-Deploy** from `main` branch
- Set **Deploy Hook** for manual deployments

---

## 🌐 **Domain Configuration**

### **DNS Records Setup**

Configure the following DNS records for `mothership-ai.com`:

```dns
# Frontend (Vercel)
watcher.mothership-ai.com    CNAME    cname.vercel-dns.com

# Backend (Render) - Optional custom domain
api.watcher.mothership-ai.com    CNAME    watcher-api.onrender.com

# Email
mail.mothership-ai.com       MX       10 mx.mothership-ai.com
```

### **SSL Certificates**
- **Vercel**: Automatic SSL via Let's Encrypt
- **Render**: Automatic SSL via Let's Encrypt
- **Custom Domain**: Configure through DNS provider

---

## 🔒 **Security Configuration**

### **Environment Secrets**
Generate secure secrets for production:

```bash
# JWT Secret (32 characters)
openssl rand -hex 32

# Encryption Key (32 characters)
openssl rand -hex 32

# Webhook Secret (32 characters)
openssl rand -hex 32
```

### **API Keys**
- **Claude API Key**: Obtain from Anthropic Console
- **Database Credentials**: Auto-generated by Render
- **Redis Credentials**: Auto-generated by Render

### **CORS Configuration**
Restrict CORS origins to production domains only:
```
https://watcher.mothership-ai.com
https://watcher-ai.vercel.app
```

---

## 📊 **Monitoring & Analytics**

### **Application Monitoring**
- **Render**: Built-in metrics and logs
- **Vercel**: Built-in analytics and performance monitoring
- **Custom**: Performance monitoring dashboard in application

### **Error Tracking**
- **Backend**: Structured logging with Winston
- **Frontend**: Error boundaries and logging
- **Alerts**: Email notifications for critical errors

### **Performance Monitoring**
- **API Response Times**: Built-in performance monitoring
- **Database Performance**: PostgreSQL metrics
- **Cache Performance**: Redis metrics
- **Frontend Performance**: Vercel Web Vitals

---

## 🧪 **Testing Production Deployment**

### **Health Checks**
```bash
# Backend Health Check
curl https://watcher-api.onrender.com/health

# Frontend Health Check
curl https://watcher.mothership-ai.com

# API Endpoints
curl https://watcher-api.onrender.com/docs
```

### **Functionality Tests**
1. **Authentication**: Login/logout flow
2. **Real-time Monitoring**: WebSocket connections
3. **Alert System**: Create and acknowledge alerts
4. **Discovery**: Network scanning functionality
5. **Analytics**: Dashboard data loading
6. **Webhooks**: Integration testing

### **Performance Tests**
1. **Load Testing**: Concurrent user simulation
2. **Stress Testing**: High-volume data processing
3. **Latency Testing**: Real-time response times
4. **Database Performance**: Query optimization

---

## 🚀 **Go-Live Checklist**

### **Pre-Deployment**
- [ ] All environment variables configured
- [ ] DNS records propagated
- [ ] SSL certificates active
- [ ] Database migrations completed
- [ ] Redis cache configured
- [ ] Health checks passing

### **Deployment**
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Render
- [ ] Database connected and initialized
- [ ] Redis cache connected
- [ ] Custom domains configured
- [ ] SSL certificates verified

### **Post-Deployment**
- [ ] All health checks passing
- [ ] Authentication working
- [ ] Real-time features functional
- [ ] Monitoring dashboards active
- [ ] Error tracking configured
- [ ] Performance metrics baseline established

### **User Acceptance**
- [ ] Admin user created
- [ ] Sample data loaded
- [ ] All features tested
- [ ] Documentation updated
- [ ] Support team notified
- [ ] Go-live announcement prepared

---

## 📞 **Support & Maintenance**

### **Monitoring**
- **Uptime**: 99.9% SLA target
- **Response Time**: <100ms for real-time features
- **Error Rate**: <0.1% target
- **Database Performance**: <50ms query time

### **Backup Strategy**
- **Database**: Daily automated backups (Render)
- **Redis**: Persistence enabled
- **Application Data**: Regular exports
- **Configuration**: Version controlled

### **Update Process**
1. **Development**: Feature branches
2. **Testing**: Staging environment
3. **Deployment**: Automatic from `main` branch
4. **Rollback**: Git revert + redeploy

### **Support Contacts**
- **Technical Support**: support@mothership-ai.com
- **Emergency**: [Phone number]
- **Documentation**: GitHub repository
- **Status Page**: [Status page URL]

---

## 🎉 **Deployment Complete!**

Your **Watcher AI** enterprise platform is now live and ready to protect AI systems from hallucinations at scale!

### **Production URLs:**
- **Frontend**: https://watcher.mothership-ai.com
- **Backend API**: https://watcher-api.onrender.com
- **API Documentation**: https://watcher-api.onrender.com/docs
- **Health Check**: https://watcher-api.onrender.com/health

### **Next Steps:**
1. Create admin user account
2. Configure first tenant
3. Set up monitoring alerts
4. Begin onboarding enterprise clients
5. Monitor performance and scale as needed

**Welcome to the future of enterprise AI safety!** 🚀🔥
