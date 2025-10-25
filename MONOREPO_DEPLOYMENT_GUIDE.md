# AgentGuard Monorepo Deployment Guide

## Overview

This repository contains both the **backend API** (Python/FastAPI) and **frontend UI** (Next.js) in a single monorepo structure, configured to deploy both services on Render.com.

## Repository Structure

```
mars/
├── src/                          # Backend API (Python)
│   ├── api/                      # FastAPI endpoints
│   ├── services/                 # Business logic
│   └── models/                   # Data models
├── agentguard-ui/                # Frontend UI (Next.js)
│   ├── app/                      # Next.js pages
│   ├── components/               # React components
│   └── lib/                      # Utilities
├── requirements-render.txt       # Backend dependencies
├── render.yaml                   # Render deployment config
└── Procfile                      # Backend start command
```

## Deployment Configuration

### Two Services on Render

The `render.yaml` configures **two separate web services**:

1. **agentguard-api** (Backend)
   - Python/FastAPI
   - Handles all API requests
   - Serves 97 REST endpoints
   - URL: `https://agentguard-api.onrender.com`

2. **agentguard-ui** (Frontend)
   - Next.js/React
   - User interface
   - Proxies API requests to backend
   - URL: `https://agentguard-ui.onrender.com`

### How They Connect

The frontend automatically connects to the backend using Render's service discovery:

```yaml
# In render.yaml for frontend
envVars:
  - key: NEXT_PUBLIC_API_URL
    fromService:
      type: web
      name: agentguard-api
      envVarKey: RENDER_EXTERNAL_URL
```

This means:
- Frontend knows backend URL automatically
- No manual configuration needed
- Works in all environments

## Deployment Steps

### Step 1: Push to GitHub

All code is already committed and pushed:
```bash
git status  # Should show "nothing to commit, working tree clean"
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up or log in
3. Connect your GitHub account

### Step 3: Deploy from Dashboard

**Option A: Automatic (Recommended)**
1. Click "New" → "Blueprint"
2. Select your GitHub repository: `seanebones-lang/mars`
3. Render will detect `render.yaml` automatically
4. Click "Apply"
5. Render will create BOTH services automatically

**Option B: Manual**
1. Create Backend Service:
   - Click "New" → "Web Service"
   - Connect repository
   - Name: `agentguard-api`
   - Root Directory: `.`
   - Build Command: `pip install -r requirements-render.txt`
   - Start Command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2`

2. Create Frontend Service:
   - Click "New" → "Web Service"
   - Connect same repository
   - Name: `agentguard-ui`
   - Root Directory: `agentguard-ui`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`

### Step 4: Set Environment Variables

**For Backend (agentguard-api)**:

Required:
```
CLAUDE_API_KEY=your_claude_api_key_here
```

Optional:
```
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

**For Frontend (agentguard-ui)**:

Most are set automatically by render.yaml, but you can override:
```
NEXT_PUBLIC_API_URL=https://agentguard-api.onrender.com
```

### Step 5: Monitor Deployment

Watch both services deploy:

**Backend Logs** should show:
```
Installing dependencies...
✓ Successfully installed all packages
Starting service...
INFO: Started server process
INFO: Starting AgentGuard API server
INFO: Application startup complete.
```

**Frontend Logs** should show:
```
Installing dependencies...
✓ npm install complete
Building Next.js application...
✓ Build complete
Starting server...
✓ Server started on port 10000
```

### Step 6: Verify Deployment

Test both services:

```bash
# Backend API
curl https://agentguard-api.onrender.com/health
# Should return: {"status":"healthy",...}

# Frontend UI
curl https://agentguard-ui.onrender.com
# Should return HTML page

# API through frontend proxy
curl https://agentguard-ui.onrender.com/api/health
# Should return: {"status":"healthy",...}
```

## Service URLs

After deployment, you'll have:

- **Frontend**: `https://agentguard-ui.onrender.com`
  - Main user interface
  - All pages and features
  - API proxy at `/api/*`

- **Backend**: `https://agentguard-api.onrender.com`
  - Direct API access
  - API documentation at `/docs`
  - Health check at `/health`

## Features Available

### Backend (97 Endpoints)
✅ Prompt Injection Detection  
✅ Multi-Model Consensus  
✅ Multimodal Detection  
✅ Bias & Fairness Auditing  
✅ Red Teaming  
✅ Compliance Reporting  
✅ PII Protection  
✅ RAG Security  
✅ Parental Controls  
✅ Model Hosting  
✅ MCP Gateway  
✅ Stream Handling  

### Frontend (Full UI)
✅ Dashboard  
✅ Real-time Monitoring  
✅ Batch Testing  
✅ Analytics  
✅ Agent Console  
✅ Workstation Management  
✅ Custom Rules  
✅ Webhooks  
✅ Performance Metrics  

## Troubleshooting

### Backend Won't Start

**Check**:
1. Build logs for Python errors
2. `CLAUDE_API_KEY` is set
3. All dependencies installed

**Solution**:
```bash
# Test locally first
cd /path/to/mars
pip install -r requirements-render.txt
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend Won't Build

**Check**:
1. Build logs for npm errors
2. `package.json` is valid
3. Node version compatibility

**Solution**:
```bash
# Test locally first
cd /path/to/mars/agentguard-ui
npm install
npm run build
npm start
```

### Frontend Can't Connect to Backend

**Check**:
1. Backend is running and healthy
2. `NEXT_PUBLIC_API_URL` is set correctly
3. CORS is configured on backend

**Solution**:
- Verify backend URL in frontend environment variables
- Check backend CORS settings (should allow frontend domain)
- Test backend health endpoint directly

### "Service Unavailable" Errors

**Check**:
1. Both services are running
2. Health checks are passing
3. No deployment errors

**Solution**:
- Check Render dashboard for service status
- Review logs for both services
- Verify environment variables are set

## Performance Optimization

### Backend
- Uses 2 workers for better concurrency
- Health check delay of 60s for startup
- Lightweight dependencies (no torch/transformers)

### Frontend
- Standalone output for faster cold starts
- Image optimization enabled
- Compression enabled
- Static asset caching

## Monitoring

### Health Checks

Backend:
```bash
curl https://agentguard-api.onrender.com/health
```

Frontend:
```bash
curl https://agentguard-ui.onrender.com
```

### Logs

Access logs in Render Dashboard:
- Backend: Dashboard → agentguard-api → Logs
- Frontend: Dashboard → agentguard-ui → Logs

### Metrics

Backend metrics:
```bash
curl https://agentguard-api.onrender.com/metrics
```

## Scaling

### Horizontal Scaling

Render supports auto-scaling:
1. Go to service settings
2. Enable auto-scaling
3. Set min/max instances
4. Set CPU/memory thresholds

### Vertical Scaling

Upgrade service plan:
- Starter: 512MB RAM
- Standard: 2GB RAM
- Pro: 4GB+ RAM

## Cost Optimization

### Free Tier
- Both services can run on free tier
- Backend: Free (with spin-down)
- Frontend: Free (with spin-down)

### Paid Plans
- Starter: $7/month per service
- Standard: $25/month per service
- Pro: $85/month per service

### Recommendations
- Start with free tier for testing
- Upgrade backend to Starter for production
- Upgrade frontend to Starter if high traffic

## Custom Domains

### Add Custom Domain

1. Go to service settings
2. Click "Custom Domain"
3. Add your domain:
   - Backend: `api.yourdomain.com`
   - Frontend: `app.yourdomain.com` or `yourdomain.com`
4. Update DNS records as instructed
5. SSL certificates are automatic

### Update Configuration

After adding custom domains, update:

**Frontend `.env.production`**:
```
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Backend CORS**:
```
CORS_ORIGINS=https://app.yourdomain.com,https://yourdomain.com
```

## Continuous Deployment

### Auto-Deploy

Both services auto-deploy on push to `main`:
```bash
git add .
git commit -m "Update feature"
git push origin main
# Render automatically deploys both services
```

### Manual Deploy

Trigger manual deploy in Render Dashboard:
1. Go to service
2. Click "Manual Deploy"
3. Select "Deploy latest commit"

## Support

### Documentation
- Backend API: `https://agentguard-api.onrender.com/docs`
- Frontend: `https://agentguard-ui.onrender.com`
- This Guide: `MONOREPO_DEPLOYMENT_GUIDE.md`

### Render Support
- Dashboard: https://dashboard.render.com
- Docs: https://render.com/docs
- Support: https://render.com/support

### Project Support
- GitHub: https://github.com/seanebones-lang/mars
- Issues: https://github.com/seanebones-lang/mars/issues

## Success Checklist

After deployment, verify:

- [ ] Backend health check passes
- [ ] Frontend loads successfully
- [ ] Frontend can call backend API
- [ ] All 12 features work
- [ ] Real-time monitoring works
- [ ] Batch testing works
- [ ] Analytics display correctly
- [ ] No console errors
- [ ] Performance is acceptable
- [ ] SSL certificates are active

## You're Live! 🎉

Once both services are deployed and verified:

**Frontend URL**: `https://agentguard-ui.onrender.com`  
**Backend URL**: `https://agentguard-api.onrender.com`  
**API Docs**: `https://agentguard-api.onrender.com/docs`

Your complete AI safety platform is now live with:
- 97 API endpoints
- 12 major features
- Full web interface
- Real-time monitoring
- Production-ready infrastructure

---

**Last Updated**: October 25, 2025  
**Version**: 1.0.0  
**Status**: Production Ready - Monorepo Deployment

