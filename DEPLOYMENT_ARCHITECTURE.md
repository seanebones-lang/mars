# AgentGuard Deployment Architecture

**Mothership AI - watcher.mothership-ai.com**  
**Contact:** info@mothership-ai.com

---

##  Critical Information

### THIS IS A COMPLETE MONOREPO ON RENDER

**Everything deploys from this single repository:**
-  Backend API (Python/FastAPI)
-  Frontend UI (Next.js/React)
-  Single git repository
-  Single `render.yaml` configuration
-  Automatic deployment on `git push origin main`

**What we DO NOT use:**
- ❌ NO Vercel
- ❌ NO separate repositories
- ❌ NO manual deployment steps
- ❌ NO multiple deployment platforms

---

##  Repository Structure

```
mars/ (This repository - deployed to Render)
├── src/                          # Backend API
│   ├── api/                      # FastAPI endpoints (97 endpoints)
│   ├── services/                 # Business logic (32 services)
│   ├── judges/                   # Detection algorithms
│   └── models/                   # Data models
│
├── agentguard-ui/                # Frontend UI
│   ├── app/                      # Next.js 16 pages
│   ├── components/               # React 19 components
│   ├── lib/                      # Utilities
│   └── package.json              # Frontend dependencies
│
├── render.yaml                   # ⭐ MASTER DEPLOYMENT CONFIG
├── requirements-render.txt       # Backend dependencies
├── Procfile                      # Backend start command
└── README.md                     # System documentation
```

---

##  Deployment Flow

### Single Command Deployment

```bash
# Make changes
git add .
git commit -m "Your changes"
git push origin main

# Render automatically:
# 1. Detects the push
# 2. Reads render.yaml
# 3. Builds backend (agentguard-api)
# 4. Builds frontend (agentguard-ui)
# 5. Deploys both services
# 6. Connects them automatically
```

### What Happens on Render

1. **Backend Service (agentguard-api)**
   - Installs Python dependencies from `requirements-render.txt`
   - Starts FastAPI with `uvicorn src.api.main:app`
   - Exposes API at `https://agentguard-api.onrender.com`
   - Health check at `/health`

2. **Frontend Service (agentguard-ui)**
   - Installs Node dependencies from `agentguard-ui/package.json`
   - Builds Next.js with `npm run build`
   - Starts with `npm start`
   - Automatically connects to backend via `NEXT_PUBLIC_API_URL`
   - Exposes UI at `https://agentguard-ui.onrender.com`

---

##  Configuration Files

### render.yaml (Master Configuration)

This file controls EVERYTHING:

```yaml
services:
  # Backend API
  - type: web
    name: agentguard-api
    env: python
    buildCommand: pip install -r requirements-render.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2
    
  # Frontend UI
  - type: web
    name: agentguard-ui
    env: node
    rootDir: agentguard-ui
    buildCommand: npm install && npm run build
    startCommand: npm start
    envVars:
      - key: NEXT_PUBLIC_API_URL
        fromService:
          name: agentguard-api  # Automatic connection!
```

### Key Features

- **Automatic Service Discovery**: Frontend automatically gets backend URL
- **Single Source of Truth**: All config in one file
- **Environment Variables**: Managed in render.yaml and Render dashboard
- **Auto-Deploy**: Push to main = automatic deployment

---

##  URLs and Endpoints

### Production URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Backend API | `https://agentguard-api.onrender.com` | REST API (97 endpoints) |
| Frontend UI | `https://agentguard-ui.onrender.com` | Web interface |
| API Docs | `https://agentguard-api.onrender.com/docs` | Swagger/OpenAPI |
| Health Check | `https://agentguard-api.onrender.com/health` | System status |
| WebSocket | `wss://agentguard-api.onrender.com/ws/monitor` | Real-time monitoring |

### Custom Domain (Future)

- **Primary**: `watcher.mothership-ai.com` → Frontend UI
- **API**: `api.watcher.mothership-ai.com` → Backend API

---

##  Environment Variables

### Backend (Set in Render Dashboard)

**Required:**
```bash
CLAUDE_API_KEY=sk-ant-api03-...     # Anthropic Claude API
STRIPE_SECRET_KEY=sk_live_...       # Payment processing
```

**Optional:**
```bash
OPENAI_API_KEY=sk-proj-...          # Multi-model consensus
GOOGLE_API_KEY=AIzaSy...            # Multimodal detection
DATABASE_URL=postgresql://...        # PostgreSQL (uses SQLite if not set)
REDIS_URL=redis://...                # Caching (in-memory if not set)
```

### Frontend (Set in render.yaml)

**Automatically configured:**
```bash
NEXT_PUBLIC_API_URL                 # From backend service
NEXT_PUBLIC_COMPANY_NAME            # Mothership AI
NEXT_PUBLIC_DOMAIN                  # watcher.mothership-ai.com
NEXT_PUBLIC_SUPPORT_EMAIL           # info@mothership-ai.com
# ... and 15+ more variables
```

---

##  System Architecture

### Service Communication

```
┌─────────────────────────────────────────────────┐
│  USER (Browser)                                 │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  Frontend UI (Next.js)                          │
│  https://agentguard-ui.onrender.com            │
│                                                 │
│  - React 19 components                          │
│  - Real-time dashboard                          │
│  - WebSocket client                             │
└────────────────┬────────────────────────────────┘
                 │
                 │ API Calls
                 │ (NEXT_PUBLIC_API_URL)
                 ▼
┌─────────────────────────────────────────────────┐
│  Backend API (FastAPI)                          │
│  https://agentguard-api.onrender.com           │
│                                                 │
│  - 97 REST endpoints                            │
│  - 32 services                                  │
│  - 12 major features                            │
│  - WebSocket server                             │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  External Services                              │
│                                                 │
│  - Anthropic Claude API                         │
│  - OpenAI API (optional)                        │
│  - Google Gemini API (optional)                 │
│  - Stripe API                                   │
└─────────────────────────────────────────────────┘
```

### Data Flow

1. User accesses `https://agentguard-ui.onrender.com`
2. Frontend loads and reads `NEXT_PUBLIC_API_URL`
3. Frontend makes API calls to `https://agentguard-api.onrender.com`
4. Backend processes requests using AI services
5. Backend returns results to frontend
6. Frontend displays results to user

---

##  Deployment Steps

### First-Time Setup

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Create Render Blueprint**
   - Go to [dashboard.render.com](https://dashboard.render.com)
   - Click **New** → **Blueprint**
   - Connect repository: `seanebones-lang/mars`
   - Render reads `render.yaml` and creates both services

3. **Set Environment Variables**
   - Go to **agentguard-api** service
   - Click **Environment**
   - Add:
     - `CLAUDE_API_KEY`
     - `STRIPE_SECRET_KEY`
   - Click **Save Changes**

4. **Deploy**
   - Render automatically deploys both services
   - Wait 5-10 minutes for initial build
   - Check health: `https://agentguard-api.onrender.com/health`

### Ongoing Deployments

```bash
# Just push to main - that's it!
git add .
git commit -m "Your changes"
git push origin main

# Render automatically:
# - Builds backend
# - Builds frontend
# - Deploys both
# - Zero downtime
```

---

##  Monitoring and Health Checks

### Health Check Endpoints

```bash
# Backend health
curl https://agentguard-api.onrender.com/health

# Frontend health
curl https://agentguard-ui.onrender.com/

# API metrics
curl https://agentguard-api.onrender.com/metrics
```

### Render Dashboard

- **Logs**: Real-time logs for both services
- **Metrics**: CPU, memory, request count
- **Events**: Deployment history
- **Shell**: Access to service shell

---

##  Troubleshooting

### Backend Not Starting

1. Check Render logs for errors
2. Verify `CLAUDE_API_KEY` is set
3. Check `requirements-render.txt` dependencies
4. Verify Python version in `runtime.txt`

### Frontend Not Connecting to Backend

1. Check `NEXT_PUBLIC_API_URL` in frontend logs
2. Verify backend is running: `/health` endpoint
3. Check CORS settings in `src/api/main.py`
4. Verify `render.yaml` service connection

### Deployment Failing

1. Check `render.yaml` syntax
2. Verify all required files exist
3. Check build logs in Render dashboard
4. Ensure git push was successful

---

##  Key Documentation

- [README.md](README.md) - Complete system documentation
- [MONOREPO_DEPLOYMENT_GUIDE.md](MONOREPO_DEPLOYMENT_GUIDE.md) - Detailed deployment guide
- [MONOREPO_VALIDATION_REPORT.md](MONOREPO_VALIDATION_REPORT.md) - System validation
- [render.yaml](render.yaml) - Master deployment configuration

---

##  Important Notes

### Why Monorepo on Render?

1. **Simplicity**: One repository, one deployment
2. **Consistency**: Same codebase for frontend and backend
3. **Automatic Connection**: Services connect automatically
4. **Cost-Effective**: Single platform, predictable pricing
5. **Easy Management**: One dashboard, one workflow

### What Changed from Vercel?

**Before (Incorrect):**
- Backend on Render
- Frontend on Vercel
- Manual CORS configuration
- Separate deployments
- Complex environment variable management

**Now (Correct):**
-  Everything on Render
-  Single deployment
-  Automatic service connection
-  Simplified configuration
-  One source of truth

---

##  Quick Reference

### Deploy Everything
```bash
git push origin main
```

### Check Status
```bash
curl https://agentguard-api.onrender.com/health
curl https://agentguard-ui.onrender.com/
```

### View Logs
```bash
# Go to dashboard.render.com
# Select service → Logs tab
```

### Update Environment Variables
```bash
# Go to dashboard.render.com
# Select service → Environment tab
# Add/edit variables → Save
```

---

**Mothership AI**  
Building the future of AI safety

[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

