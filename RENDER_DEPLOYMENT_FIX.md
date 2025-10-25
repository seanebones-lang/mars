# Render Deployment Issues & Fixes

## Issues Identified

### 1. **MLflow Dependency Missing from requirements-render.txt**
The main app imports `mlflow` but it's not in the lightweight requirements file.

**Error**: `ModuleNotFoundError: No module named 'mlflow'`

### 2. **Heavy Dependencies in requirements-render.txt**
Some dependencies might cause build timeouts or memory issues:
- `torch` (huge, not needed for API)
- `transformers` (large)
- `sentence-transformers` (large)

### 3. **Static Site Build Will Fail**
The render.yaml includes a static site for docs that tries to import the app, which will fail if dependencies are missing.

### 4. **Missing PIL/Pillow for Multimodal**
Multimodal detection needs Pillow for image processing.

### 5. **Database Connection String Format**
Render uses a specific format for PostgreSQL connection strings.

## Fixes Required

### Fix 1: Update requirements-render.txt

Add missing dependencies and remove heavy ones:

```txt
# Core Framework
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
python-dotenv>=1.0.0

# CRITICAL SECURITY
bleach>=6.1.0
cryptography>=41.0.7
python-multipart>=0.0.6
bcrypt>=4.1.2
pyotp>=2.9.0

# AI/ML - Lightweight
anthropic>=0.39.0

# MLflow (REQUIRED for main.py)
mlflow>=2.17.0

# Data Processing
numpy>=1.26.0
pandas>=2.0.0

# Image Processing (for multimodal)
Pillow>=10.0.0

# Database & Storage
aiosqlite>=0.19.0
redis>=5.0.0
psycopg2-binary>=2.9.0  # PostgreSQL adapter

# Web & API
aiohttp>=3.9.0
jinja2>=3.1.0
websockets>=12.0

# Security & Authentication
pyjwt>=2.8.0
qrcode>=7.4.0

# Communication
aiosmtplib>=3.0.0

# System Monitoring
psutil>=5.9.0

# Essential utilities
requests>=2.31.0
scipy>=1.11.0
```

### Fix 2: Make MLflow Optional in main.py

Wrap MLflow imports to make them optional:

```python
# Try to import MLflow, but don't fail if it's not available
try:
    import mlflow
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not available - experiment tracking disabled")

# Configure MLflow only if available
if MLFLOW_AVAILABLE:
    try:
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "agentguard_prototype"))
    except Exception as e:
        logger.warning(f"MLflow configuration failed: {e}")
```

### Fix 3: Simplify render.yaml

Remove the static site build (it's complex and not critical):

```yaml
services:
  - type: web
    name: agentguard-api
    env: python
    region: oregon
    plan: starter
    buildCommand: pip install -r requirements-render.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
      - key: CLAUDE_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false
      - key: GOOGLE_API_KEY
        sync: false
    
    autoDeploy: true
    branch: main
```

### Fix 4: Add Procfile (Alternative Start Method)

Create a `Procfile` for Render:

```
web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT --workers 2
```

### Fix 5: Add runtime.txt

Specify Python version:

```
python-3.11.0
```

## Deployment Steps

1. **Update requirements-render.txt** with the fixed version
2. **Make MLflow optional** in main.py
3. **Simplify render.yaml** to remove complex builds
4. **Add Procfile** for explicit start command
5. **Add runtime.txt** for Python version
6. **Set environment variables** in Render dashboard:
   - `CLAUDE_API_KEY`
   - `OPENAI_API_KEY` (optional)
   - `GOOGLE_API_KEY` (optional)
   - `DATABASE_URL` (if using database)
   - `REDIS_URL` (if using Redis)

7. **Commit and push** changes
8. **Trigger manual deploy** in Render dashboard

## Quick Fix Commands

```bash
# Update requirements
cat > requirements-render.txt << 'EOF'
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
python-dotenv>=1.0.0
bleach>=6.1.0
cryptography>=41.0.7
python-multipart>=0.0.6
bcrypt>=4.1.2
pyotp>=2.9.0
anthropic>=0.39.0
mlflow>=2.17.0
numpy>=1.26.0
pandas>=2.0.0
Pillow>=10.0.0
aiosqlite>=0.19.0
redis>=5.0.0
psycopg2-binary>=2.9.0
aiohttp>=3.9.0
jinja2>=3.1.0
websockets>=12.0
pyjwt>=2.8.0
qrcode>=7.4.0
aiosmtplib>=3.0.0
psutil>=5.9.0
requests>=2.31.0
scipy>=1.11.0
EOF

# Create Procfile
echo "web: uvicorn src.api.main:app --host 0.0.0.0 --port \$PORT --workers 2" > Procfile

# Create runtime.txt
echo "python-3.11.0" > runtime.txt

# Commit and push
git add requirements-render.txt Procfile runtime.txt
git commit -m "fix: Update Render deployment configuration"
git push origin main
```

## Verification

After deployment, test these endpoints:

```bash
# Health check
curl https://your-app.onrender.com/health

# API docs
curl https://your-app.onrender.com/docs

# Test detection
curl -X POST https://your-app.onrender.com/prompt-injection/detect \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

## Common Render Errors

### "Build failed"
- Check build logs for missing dependencies
- Ensure requirements-render.txt has all imports used in code

### "Health check failed"
- Verify `/health` endpoint works locally
- Check if app is binding to correct port (`$PORT`)
- Increase `initialDelaySeconds` in health check config

### "Application error"
- Check application logs in Render dashboard
- Verify all environment variables are set
- Check for import errors or missing dependencies

### "Timeout during build"
- Remove heavy dependencies (torch, transformers)
- Use lighter alternatives
- Increase build timeout in Render settings

## Support

If issues persist:
1. Check Render logs: Dashboard → Your Service → Logs
2. Check build logs: Dashboard → Your Service → Events
3. Test locally: `uvicorn src.api.main:app --port 8000`
4. Verify all imports work: `python -c "from src.api.main import app"`
