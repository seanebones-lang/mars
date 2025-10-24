# Vercel Deployment Guide - AgentGuard

## Multi-Environment Setup (Dev, Staging, Production)

This guide walks through deploying AgentGuard to Vercel with three separate environments.

---

## Prerequisites

1. Vercel account (sign up at vercel.com)
2. GitHub repository connected: `https://github.com/seanebones-lang/mars`
3. Backend API deployed (AWS/GCP/Railway) or running locally for development

---

## Quick Deploy (Single Command)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from agentguard-ui directory
cd agentguard-ui
vercel --prod
```

---

## Environment Strategy

### 1. **Development** (dev.agentguard.ai)
- Auto-deploys from `dev` branch
- Points to development backend API
- Used for testing new features
- Lower rate limits, debug mode enabled

### 2. **Staging** (staging.agentguard.ai)
- Auto-deploys from `staging` branch
- Points to staging backend API
- Client demos and pre-release testing
- Production-like environment

### 3. **Production** (agentguard.ai)
- Auto-deploys from `main` branch
- Points to production backend API
- Live customer environment
- Full monitoring, logging, alerts

---

## Step-by-Step Multi-Environment Setup

### Step 1: Create Git Branches

```bash
cd /Users/seanmcdonnell/Desktop/HAL

# Create development branch
git checkout -b dev
git push -u origin dev

# Create staging branch
git checkout -b staging
git push -u origin staging

# Back to main (production)
git checkout main
```

### Step 2: Deploy to Vercel (Web UI Method)

#### A. Development Environment

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `seanebones-lang/mars` repository
3. Configure:
   - **Project Name:** `agentguard-dev`
   - **Framework:** Next.js
   - **Root Directory:** `agentguard-ui`
   - **Branch:** `dev`
   - **Build Command:** `npm run build`
   - **Output Directory:** `.next`
4. Add Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   # or your dev backend URL
   ```
5. Deploy

#### B. Staging Environment

1. Same repository, new project
2. Configure:
   - **Project Name:** `agentguard-staging`
   - **Root Directory:** `agentguard-ui`
   - **Branch:** `staging`
3. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://api-staging.agentguard.ai
   ```
4. Deploy

#### C. Production Environment

1. Same repository, new project
2. Configure:
   - **Project Name:** `agentguard`
   - **Root Directory:** `agentguard-ui`
   - **Branch:** `main`
3. Environment Variables:
   ```
   NEXT_PUBLIC_API_URL=https://api.agentguard.ai
   ```
4. Deploy

### Step 3: Deploy via Vercel CLI (Alternative)

```bash
cd agentguard-ui

# Development
vercel --prod --name agentguard-dev \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000

# Staging
vercel --prod --name agentguard-staging \
  -e NEXT_PUBLIC_API_URL=https://api-staging.agentguard.ai

# Production
vercel --prod --name agentguard \
  -e NEXT_PUBLIC_API_URL=https://api.agentguard.ai
```

---

## Environment Variables Configuration

### Required Variables (All Environments)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API endpoint | `https://api.agentguard.ai` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_APP_ENV` | Environment name | `production` |
| `NEXT_PUBLIC_ENABLE_ANALYTICS` | Enable tracking | `true` |
| `NEXT_PUBLIC_SENTRY_DSN` | Error tracking | - |

### Setting Variables in Vercel

1. Go to project settings: `vercel.com/<project>/settings/environment-variables`
2. Add variables for each environment:
   - **Production:** Only affects `main` branch
   - **Preview:** Affects `dev` and `staging` branches
   - **Development:** Local development

---

## Custom Domains

### Development
- Vercel auto-assigns: `agentguard-dev.vercel.app`
- Custom: `dev.agentguard.ai` (add in Vercel Domains)

### Staging
- Vercel auto-assigns: `agentguard-staging.vercel.app`
- Custom: `staging.agentguard.ai`

### Production
- Vercel auto-assigns: `agentguard.vercel.app`
- Custom: `agentguard.ai` or `app.agentguard.ai`

**Add Custom Domain:**
1. Go to project settings → Domains
2. Add domain (e.g., `agentguard.ai`)
3. Configure DNS with your registrar:
   ```
   A     @       76.76.21.21
   CNAME www     cname.vercel-dns.com
   ```

---

## Deployment Workflow

### Feature Development Flow

```bash
# 1. Work on feature in dev branch
git checkout dev
# ... make changes ...
git commit -m "Add webhook monitoring feature"
git push origin dev

# → Auto-deploys to dev.agentguard.ai

# 2. Test in dev, then promote to staging
git checkout staging
git merge dev
git push origin staging

# → Auto-deploys to staging.agentguard.ai

# 3. Client approval, promote to production
git checkout main
git merge staging
git push origin main

# → Auto-deploys to agentguard.ai
```

---

## Backend API Deployment Options

The frontend needs a backend API. Deploy backend using one of these:

### Option 1: Railway (Easiest)
```bash
# Install Railway CLI
npm i -g @railway/cli

# Deploy backend
railway login
railway init
railway up

# Get API URL: https://agentguard-backend-production.up.railway.app
```

### Option 2: AWS ECS (Production-Grade)
- Use Docker container from `Dockerfile`
- Deploy to ECS Fargate
- Setup ALB for HTTPS
- Configure CloudWatch for logs

### Option 3: GCP Cloud Run
```bash
gcloud run deploy agentguard-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Option 4: Local Development
- Run backend locally: `uvicorn src.api.main:app --port 8000`
- Use ngrok for public URL: `ngrok http 8000`
- Set `NEXT_PUBLIC_API_URL=https://abc123.ngrok.io`

---

## Monitoring & Analytics

### Vercel Analytics (Built-in)
- Automatically enabled
- View at: `vercel.com/<project>/analytics`
- Tracks page views, performance, real user metrics

### Custom Monitoring
Add to `app/layout.tsx`:

```typescript
// Sentry for error tracking
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_APP_ENV
});

// Google Analytics
import { GoogleAnalytics } from '@next/third-parties/google'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <GoogleAnalytics gaId="G-XXXXXXXXXX" />
      </body>
    </html>
  )
}
```

---

## Troubleshooting

### Build Fails

**Error:** `Module not found: Can't resolve '@mui/material'`

**Fix:**
```bash
cd agentguard-ui
npm install
git add package-lock.json
git commit -m "Update dependencies"
git push
```

### API Connection Issues

**Error:** `Network Error` or `Failed to fetch`

**Fix:** Check environment variables
```bash
vercel env ls
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://your-backend-api.com
```

### Next.js Build Timeout

**Error:** Build exceeds 15 minute limit

**Fix:** Add to `next.config.ts`:
```typescript
module.exports = {
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: true, // Only if necessary
  },
  experimental: {
    workerThreads: false,
    cpus: 1
  }
}
```

---

## Cost Estimation

### Vercel Pricing (as of Oct 2025)

**Hobby (Free):**
- 100 GB bandwidth/month
- Unlimited deployments
- Good for dev/staging

**Pro ($20/month per team):**
- 1 TB bandwidth
- Advanced analytics
- Password protection
- Recommended for production

**Enterprise (Custom):**
- Dedicated support
- SSO, RBAC
- 99.99% SLA

### Recommended Setup
- **Development:** Hobby (free)
- **Staging:** Hobby or Pro
- **Production:** Pro ($20/month)

---

## Security Best Practices

### 1. Environment Secrets
- Never commit API keys
- Use Vercel environment variables
- Rotate keys regularly

### 2. CORS Configuration
Backend `main.py` should allow only your domains:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agentguard.ai",
        "https://staging.agentguard.ai",
        "https://dev.agentguard.ai"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Authentication
Add API key validation:
```typescript
// lib/api.ts
agentGuardApi.interceptors.request.use(config => {
  config.headers['X-API-Key'] = process.env.NEXT_PUBLIC_API_KEY;
  return config;
});
```

---

## Deployment Checklist

### Pre-Deploy
- [ ] All files committed to git
- [ ] `npm run build` succeeds locally
- [ ] Environment variables documented
- [ ] Backend API deployed and accessible
- [ ] CORS configured on backend

### Deploy
- [ ] Development deployed and tested
- [ ] Staging deployed and tested
- [ ] Production deployed
- [ ] Custom domains configured
- [ ] SSL certificates active

### Post-Deploy
- [ ] Test all features (Quick Test, Demo, Metrics)
- [ ] Verify API connection
- [ ] Check analytics setup
- [ ] Monitor error rates
- [ ] Setup alerts (Slack, PagerDuty)

---

## Support & Resources

- **Vercel Docs:** https://vercel.com/docs
- **Next.js Deployment:** https://nextjs.org/docs/deployment
- **Repository:** https://github.com/seanebones-lang/mars
- **Backend API Docs:** http://localhost:8000/docs

---

## Quick Commands Reference

```bash
# Deploy production
cd agentguard-ui && vercel --prod

# Deploy to specific environment
vercel --prod --name agentguard-dev

# View deployment logs
vercel logs

# List environment variables
vercel env ls

# Add environment variable
vercel env add NEXT_PUBLIC_API_URL

# Rollback deployment
vercel rollback

# Remove deployment
vercel remove agentguard-dev
```

---

**Ready to deploy!** Start with development environment, test thoroughly, then promote to staging and production.

