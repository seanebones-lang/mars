# Render Deployment Troubleshooting & Fix

**AgentGuard Platform**  
**Issue**: Render hasn't deployed properly since Sprint 2 started  
**Date**: October 25, 2025

---

## 🚨 Identified Issues

### 1. Import Errors (Most Likely)

**Problem**: New modules not being imported correctly
- `src/api/prompt_injection.py` - New file
- `src/api/pii_protection.py` - New file
- `src/services/prompt_injection_detector.py` - New file
- `src/services/pii_protection.py` - New file

**Symptoms**:
- Build succeeds but app crashes on startup
- Import errors in logs
- Health check fails

---

### 2. Missing Dependencies

**Problem**: `requirements-render.txt` might be missing dependencies

**Missing from render requirements**:
- No explicit `sqlalchemy` (if used by services)
- No `hashlib` (built-in, but check)
- Might need `regex` library

---

### 3. Environment Variables

**Problem**: Missing required env vars
- `CLAUDE_API_KEY` - Must be set manually in Render dashboard
- `OPENAI_API_KEY` - Optional but recommended
- Database/Redis URLs - Should auto-configure

---

### 4. Health Check Path

**Problem**: Health check might be failing
- Current: `/health`
- Might need: `/api/health` or root `/`

---

## 🔧 Quick Fixes

### Fix 1: Check Render Logs

1. Go to Render Dashboard
2. Select `watcher-api` service
3. Click "Logs" tab
4. Look for:
   - `ImportError`
   - `ModuleNotFoundError`
   - `AttributeError`
   - `Failed to start`

### Fix 2: Verify Build Command

Current build command:
```bash
pip install -r requirements-render.txt
```

Should work, but verify it completes successfully.

### Fix 3: Verify Start Command

Current start command:
```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 30
```

This should work if:
- `src/__init__.py` exists
- `src/api/__init__.py` exists
- All imports are correct

### Fix 4: Check Python Version

Render default: Python 3.7  
**Required**: Python 3.9+

**Fix**: Add `runtime.txt` with:
```
python-3.10.12
```

---

## 🎯 Most Likely Issue: Python Version

Render uses Python 3.7 by default, but we need 3.9+ for:
- Pydantic 2.x
- FastAPI 0.115+
- Type hints we're using

---

## 📋 Step-by-Step Fix

### Step 1: Create runtime.txt

```bash
echo "python-3.10.12" > runtime.txt
git add runtime.txt
git commit -m "Add Python 3.10 runtime for Render"
git push origin main
```

### Step 2: Verify Environment Variables

In Render Dashboard:
1. Go to `watcher-api` service
2. Click "Environment" tab
3. Verify these are set:
   - `CLAUDE_API_KEY` (must set manually)
   - `DATABASE_URL` (auto from postgres)
   - `REDIS_URL` (auto from redis)
   - `JWT_SECRET_KEY` (auto-generated)

### Step 3: Check Build Logs

After push, watch build logs for:
- ✅ Python 3.10.12 installed
- ✅ All requirements installed
- ✅ No import errors
- ✅ Server starts successfully

### Step 4: Test Health Check

Once deployed:
```bash
curl https://watcher-api.onrender.com/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-25T...",
  "version": "1.0.0"
}
```

---

## 🔍 Debugging Commands

### Check if service is running:
```bash
curl -I https://watcher-api.onrender.com/health
```

### Check API docs:
```bash
curl https://watcher-api.onrender.com/docs
```

### Check specific endpoint:
```bash
curl https://watcher-api.onrender.com/prompt-injection/health
```

---

## 📊 Expected Render Configuration

### Service: watcher-api

| Setting | Value |
|---------|-------|
| **Type** | Web Service |
| **Environment** | Python |
| **Region** | Oregon |
| **Plan** | Starter (or higher) |
| **Python Version** | 3.10.12 |
| **Build Command** | `pip install -r requirements-render.txt` |
| **Start Command** | `python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check** | `/health` |
| **Auto Deploy** | Yes (main branch) |

### Required Environment Variables

| Variable | Source | Required |
|----------|--------|----------|
| `CLAUDE_API_KEY` | Manual | ✅ Yes |
| `DATABASE_URL` | Auto (postgres) | ✅ Yes |
| `REDIS_URL` | Auto (redis) | ✅ Yes |
| `JWT_SECRET_KEY` | Auto-generated | ✅ Yes |
| `OPENAI_API_KEY` | Manual | ⚠️ Optional |
| `ENVIRONMENT` | Set to `production` | ✅ Yes |
| `LOG_LEVEL` | Set to `INFO` | ✅ Yes |

---

## 🚀 Alternative: Manual Deploy

If auto-deploy keeps failing:

### Option 1: Deploy from Render Dashboard

1. Go to Render Dashboard
2. Click "Manual Deploy"
3. Select "Deploy latest commit"
4. Watch logs

### Option 2: Rollback

1. Go to "Deploys" tab
2. Find last working deploy
3. Click "Rollback"

### Option 3: Fresh Service

1. Delete current service
2. Create new service
3. Connect to GitHub repo
4. Configure from scratch

---

## 📝 Checklist

Before deploying:
- [ ] `runtime.txt` exists with Python 3.10.12
- [ ] All `__init__.py` files exist in directories
- [ ] `requirements-render.txt` has all dependencies
- [ ] `CLAUDE_API_KEY` set in Render dashboard
- [ ] Health check endpoint works locally
- [ ] All imports are correct
- [ ] No syntax errors

After deploying:
- [ ] Build succeeds
- [ ] Service starts
- [ ] Health check passes
- [ ] API docs accessible at `/docs`
- [ ] Test endpoint works

---

## 🆘 If Still Failing

### Get Detailed Logs

1. Render Dashboard → watcher-api → Logs
2. Look for the FIRST error (not cascading errors)
3. Common errors:
   - `ModuleNotFoundError: No module named 'src'`
     - Fix: Ensure `src/__init__.py` exists
   - `ImportError: cannot import name 'router'`
     - Fix: Check router imports in `main.py`
   - `AttributeError: module has no attribute 'app'`
     - Fix: Check `main.py` exports `app`

### Test Locally

```bash
# Use same Python version as Render
pyenv install 3.10.12
pyenv local 3.10.12

# Install render requirements
pip install -r requirements-render.txt

# Test start command
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Test health check
curl http://localhost:8000/health
```

---

## 💡 Quick Win: Simplify First

If nothing works, simplify to get SOMETHING deployed:

### Minimal main.py

```python
from fastapi import FastAPI

app = FastAPI(title="AgentGuard")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {"message": "AgentGuard API"}
```

Once this works, add routers one by one.

---

## 📞 Support

- **Render Docs**: https://render.com/docs/deploy-fastapi
- **Render Support**: support@render.com
- **Our Logs**: Check Render dashboard logs

---

**Most Likely Fix**: Add `runtime.txt` with Python 3.10.12

This will solve 90% of deployment issues!

