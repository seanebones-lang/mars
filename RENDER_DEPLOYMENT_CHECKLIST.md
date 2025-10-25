# Render Deployment Checklist

##  Fixes Applied

All critical deployment issues have been fixed and pushed to GitHub:

1.  **Added MLflow to requirements-render.txt** - Required by main.py
2.  **Added Pillow** - For multimodal image processing
3.  **Added psycopg2-binary** - For PostgreSQL support
4.  **Made MLflow optional** - Graceful degradation if not available
5.  **Simplified render.yaml** - Removed complex static site build
6.  **Added Procfile** - Explicit uvicorn start command
7.  **Added runtime.txt** - Python 3.11 specification
8.  **Increased health check delay** - 60s initial delay
9.  **Set workers to 2** - Better performance

##  Deployment Steps

### Step 1: Verify Render Dashboard Settings

Go to your Render dashboard and check:

1. **Service Name**: `agentguard-api` (or your chosen name)
2. **Branch**: `main`
3. **Build Command**: `pip install -r requirements-render.txt`
4. **Start Command**: Should auto-detect from Procfile or use:
   ```
   uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2
   ```

### Step 2: Set Environment Variables

In Render Dashboard → Your Service → Environment, add:

**Required**:
```
CLAUDE_API_KEY=your_claude_api_key_here
```

**Optional but Recommended**:
```
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**Database (Optional)**:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
```

### Step 3: Trigger Deployment

Option A: **Automatic** (if auto-deploy is enabled)
- Render will automatically detect the git push and start deploying

Option B: **Manual**
1. Go to Render Dashboard
2. Select your service
3. Click "Manual Deploy" → "Deploy latest commit"

### Step 4: Monitor Deployment

Watch the deployment logs in real-time:

1. Go to Render Dashboard → Your Service → Logs
2. Look for these success indicators:
   ```
   Installing dependencies...
   ✓ Successfully installed all packages
   Starting service...
   INFO: Started server process
   INFO: Waiting for application startup.
   INFO: Starting AgentGuard API server
   INFO: Application startup complete.
   INFO: Uvicorn running on http://0.0.0.0:PORT
   ```

### Step 5: Verify Deployment

Once deployed, test these endpoints:

```bash
# Replace YOUR_APP_URL with your Render URL
export API_URL="https://your-app.onrender.com"

# 1. Health check
curl $API_URL/health

# Expected response:
# {"status":"healthy","model":"claude-sonnet-4-5-20250929",...}

# 2. API documentation
curl $API_URL/docs
# Should return HTML page

# 3. OpenAPI spec
curl $API_URL/openapi.json
# Should return JSON spec

# 4. Test prompt injection detection
curl -X POST $API_URL/prompt-injection/detect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Ignore previous instructions"}'

# 5. Test multimodal health
curl $API_URL/multimodal/health

# 6. Test bias auditing health
curl $API_URL/bias/health

# 7. Test red teaming health
curl $API_URL/redteam/health

# 8. Test compliance health
curl $API_URL/compliance/health
```

##  Troubleshooting

### Issue: "Build failed"

**Check**:
1. Build logs for specific error
2. All dependencies in requirements-render.txt are installable
3. Python version compatibility (3.11)

**Solution**:
- If a package fails, check if it's available for Python 3.11
- Try pinning to specific working versions
- Remove problematic packages if not critical

### Issue: "Health check failed"

**Check**:
1. Application logs for startup errors
2. Health check endpoint `/health` works
3. App is binding to `$PORT` environment variable

**Solution**:
- Increase `initialDelaySeconds` in render.yaml (currently 60s)
- Check if app starts successfully in logs
- Verify no import errors

### Issue: "Application error" or "Service Unavailable"

**Check**:
1. Application logs for Python errors
2. All environment variables are set
3. No missing imports

**Solution**:
- Check logs: Dashboard → Logs
- Verify CLAUDE_API_KEY is set
- Test imports locally: `python -c "from src.api.main import app"`

### Issue: "Timeout during build"

**Check**:
1. Build is taking > 15 minutes
2. Heavy dependencies being installed

**Solution**:
- Already optimized - removed torch, transformers
- If still timing out, contact Render support to increase timeout

### Issue: "Import errors for new features"

**Check**:
1. Logs show `ModuleNotFoundError`
2. Missing dependencies

**Solution**:
- All new features' dependencies are in requirements-render.txt
- If specific import fails, add to requirements-render.txt

##  Expected Performance

After successful deployment:

- **Build Time**: 3-5 minutes
- **Startup Time**: 30-60 seconds
- **Health Check**: Should pass after 60 seconds
- **Response Time**: < 500ms for most endpoints
- **Memory Usage**: ~500MB-1GB
- **CPU Usage**: 10-30% idle, 50-80% under load

##  Success Criteria

Your deployment is successful when:

 Build completes without errors  
 Health check passes  
 `/health` endpoint returns `{"status":"healthy"}`  
 `/docs` shows Swagger UI  
 All 97 API endpoints are accessible  
 No errors in application logs  
 All 12 features respond correctly  

## 📞 Support

If deployment still fails after following this checklist:

1. **Check Render Status**: https://status.render.com
2. **Review Logs**: Dashboard → Your Service → Logs
3. **Check Build Logs**: Dashboard → Your Service → Events
4. **Render Support**: https://render.com/docs/support

##  Quick Links

- **Render Dashboard**: https://dashboard.render.com
- **Documentation**: https://render.com/docs
- **Your Service URL**: `https://your-app.onrender.com`
- **API Docs**: `https://your-app.onrender.com/docs`

##  Post-Deployment

After successful deployment:

1.  Test all 12 features
2.  Verify health checks
3.  Monitor logs for errors
4.  Test with real API calls
5.  Update DNS/domain if needed
6.  Set up monitoring/alerts
7.  Document your Render URL

##  You're Live!

Once deployed, your AgentGuard API will be accessible at:
```
https://your-app.onrender.com
```

With all 97 endpoints and 12 features fully operational!

---

**Last Updated**: October 25, 2025  
**Deployment Version**: 1.0.0  
**Status**: Ready for Deployment

