# AgentGuard Setup Guide

## Prerequisites

### System Requirements
- **OS**: macOS, Linux, or Windows with WSL2
- **Python**: 3.12 or higher
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 2GB for dependencies and models

### API Requirements
- **Claude API Key**: Anthropic Sonnet 4.5 access
  - Sign up at https://console.anthropic.com/
  - Generate API key from dashboard
  - Dev tier provides 10K-100K tokens/day

## Installation Steps

### 1. Clone Repository

```bash
cd ~/Desktop/ms-ai-hal
# Repository already cloned
```

### 2. Create Virtual Environment

```bash
# Create venv
python3.12 -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will install:
# - FastAPI 0.120+ (API framework)
# - Anthropic 0.71+ (Claude API client)
# - PyTorch 2.9+ (ML backend)
# - Transformers 4.57+ (NLP models)
# - MLflow 3.5+ (experiment tracking)
# - pytest 8.4+ (testing)
```

**Note**: PyTorch installation may take 5-10 minutes depending on internet speed.

### 4. Configure Environment

```bash
# Create .env file
touch .env

# Add your Claude API key
echo "CLAUDE_API_KEY=your_actual_api_key_here" >> .env

# Add other configuration
cat >> .env << EOF
MLFLOW_TRACKING_URI=./mlruns
MLFLOW_EXPERIMENT_NAME=agentguard_prototype
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
```

**Important**: Replace `your_actual_api_key_here` with your real Claude API key.

### 5. Verify Installation

```bash
# Test imports
python -c "import fastapi, anthropic, torch, transformers; print('All dependencies loaded successfully')"

# Check GPU availability (optional)
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

## Running the Application

### Start API Server

```bash
# Method 1: Direct Python
python -m src.api.main

# Method 2: Uvicorn with auto-reload (development)
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Method 3: Production mode
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify Server Running

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "model": "claude-sonnet-4-5-20250929",
#   "claude_api": "configured",
#   ...
# }
```

### Access Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Root Info**: http://localhost:8000/

## Testing Your First Agent

### Using cURL

```bash
curl -X POST "http://localhost:8000/test-agent" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_output": "Reboot the quantum router to fix the server",
    "ground_truth": "No quantum router exists; use standard diagnostics",
    "conversation_history": []
  }'
```

### Using Python

```python
import requests

response = requests.post(
    "http://localhost:8000/test-agent",
    json={
        "agent_output": "Reboot the quantum router to fix the server",
        "ground_truth": "No quantum router exists; use standard diagnostics",
        "conversation_history": []
    }
)

print(response.json())
```

### Using the Interactive Docs

1. Navigate to http://localhost:8000/docs
2. Click on `/test-agent` endpoint
3. Click "Try it out"
4. Enter request body
5. Click "Execute"
6. View response

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View coverage report
open htmlcov/index.html  # macOS
# or: xdg-open htmlcov/index.html  # Linux

# Run specific test file
pytest tests/test_judges.py -v

# Run only unit tests (skip integration)
pytest tests/ -v -m "not integration"
```

## Docker Deployment (Optional)

### Build Image

```bash
docker build -t agentguard:latest .
```

### Run with Docker Compose

```bash
# Make sure .env file has CLAUDE_API_KEY set
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access from Docker

- API: http://localhost:8000
- Logs mounted at: `./logs/`
- MLflow data mounted at: `./mlruns/`

## Troubleshooting

### Issue: "Claude API key not configured"

**Solution**: Ensure `.env` file exists with valid `CLAUDE_API_KEY`:
```bash
cat .env | grep CLAUDE_API_KEY
```

### Issue: "Module not found" errors

**Solution**: Ensure virtual environment is activated:
```bash
which python  # Should show venv path
pip list | grep fastapi  # Verify packages installed
```

### Issue: PyTorch/Transformers slow to load

**Solution**: First run downloads models (~500MB). Subsequent runs will be faster.
```bash
# Pre-download models
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('distilbert-base-uncased'); AutoModelForCausalLM.from_pretrained('distilbert-base-uncased')"
```

### Issue: Port 8000 already in use

**Solution**: Use different port or kill existing process:
```bash
# Use different port
export API_PORT=8001
python -m src.api.main

# Or kill existing process (macOS/Linux)
lsof -ti:8000 | xargs kill
```

### Issue: MLflow directory permissions

**Solution**: Ensure mlruns directory is writable:
```bash
mkdir -p mlruns
chmod 755 mlruns
```

## Next Steps

1. **Load Sample Data**: Review `data/sample_scenarios.json` for test cases
2. **Run Experiments**: Use MLflow UI to track evaluations
3. **Tune Weights**: Adjust ensemble weights in `config/config.yaml`
4. **Add Scenarios**: Create domain-specific test cases for your use case
5. **Monitor Performance**: Check logs in `logs/agentguard.log`

## Production Deployment

For production deployment:

1. **Security**: 
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Enable HTTPS with TLS certificates
   - Configure CORS origins restrictively

2. **Monitoring**:
   - Set up Prometheus metrics export
   - Configure alerting for API failures
   - Monitor Claude API usage and costs

3. **Scaling**:
   - Deploy to Kubernetes or AWS ECS
   - Use load balancer for multiple instances
   - Implement rate limiting and caching

4. **Compliance**:
   - Enable audit logging
   - Anonymize sensitive data
   - Configure data retention policies

## Support

For issues or questions:
- Check logs: `logs/agentguard.log`
- Review test failures: `pytest tests/ -v`
- Validate configuration: `config/config.yaml`

---

**Quick Start Summary**:
```bash
# 1. Create venv and activate
python3.12 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
echo "CLAUDE_API_KEY=your_key" >> .env

# 4. Run server
python -m src.api.main

# 5. Test
curl http://localhost:8000/health
```

