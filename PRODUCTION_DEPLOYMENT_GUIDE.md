# AgentGuard Production Deployment Guide

**Mothership AI - Watcher Platform**  
**Product URL:** [watcher.mothership-ai.com](https://watcher.mothership-ai.com)  
**Contact:** [info@mothership-ai.com](mailto:info@mothership-ai.com)

##  IMPORTANT: Monorepo Deployment on Render

**This system is deployed as a COMPLETE MONOREPO on Render.com**
- Both backend API and frontend UI deploy from this single repository
- NO VERCEL - Everything runs on Render
- Single `render.yaml` configuration manages both services
- Automatic deployment on git push to main

## Overview

This guide provides comprehensive instructions for deploying AgentGuard to production environments, including configuration, security hardening, monitoring, and maintenance procedures.

## System Requirements

### Minimum Requirements
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps
- **OS**: Linux (Ubuntu 22.04+ recommended)

### Recommended Production Requirements
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Storage**: 200+ GB SSD
- **Network**: 1 Gbps
- **OS**: Linux (Ubuntu 22.04 LTS)

## Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] Database (PostgreSQL) provisioned
- [ ] Redis cache provisioned
- [ ] API keys obtained (Claude, OpenAI, etc.)
- [ ] SSL/TLS certificates acquired
- [ ] Monitoring tools configured
- [ ] Backup strategy implemented
- [ ] Security review completed
- [ ] Load testing performed
- [ ] Documentation reviewed

## Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)

```bash
# Clone repository
git clone https://github.com/agentguard/agentguard.git
cd agentguard

# Copy environment file
cp .env.example .env

# Edit environment variables
nano .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
curl http://localhost:8000/health
```

### Option 2: Kubernetes (Recommended for Scale)

```bash
# Create namespace
kubectl create namespace agentguard

# Create secrets
kubectl create secret generic agentguard-secrets \
  --from-env-file=.env \
  --namespace=agentguard

# Deploy application
kubectl apply -f k8s/ --namespace=agentguard

# Verify deployment
kubectl get pods --namespace=agentguard
kubectl get services --namespace=agentguard

# Check health
kubectl port-forward service/agentguard 8000:8000 --namespace=agentguard
curl http://localhost:8000/health
```

### Option 3: Cloud Platforms

#### AWS Deployment

```bash
# Using AWS ECS
aws ecs create-cluster --cluster-name agentguard-prod

# Create task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster agentguard-prod \
  --service-name agentguard-api \
  --task-definition agentguard:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

#### Google Cloud Platform

```bash
# Deploy to Cloud Run
gcloud run deploy agentguard \
  --image gcr.io/your-project/agentguard:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Render.com

```bash
# Deploy using render.yaml
render deploy

# Or use Render Dashboard
# 1. Connect GitHub repository
# 2. Select render.yaml
# 3. Click "Create Services"
```

## Environment Configuration

### Required Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@db-host:5432/agentguard
REDIS_URL=redis://redis-host:6379/0

# AI Model API Keys
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key

# Security
JWT_SECRET=your_secure_jwt_secret_min_32_chars
API_KEY_SECRET=your_secure_api_key_secret

# Monitoring
SENTRY_DSN=your_sentry_dsn
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

### Optional Environment Variables

```bash
# Feature Flags
ENABLE_MULTIMODAL=true
ENABLE_BIAS_AUDITING=true
ENABLE_RED_TEAMING=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Caching
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

## Database Setup

### PostgreSQL Initialization

```sql
-- Create database
CREATE DATABASE agentguard;

-- Create user
CREATE USER agentguard_user WITH ENCRYPTED PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE agentguard TO agentguard_user;

-- Connect to database
\c agentguard

-- Create tables (run migrations)
-- Tables will be created automatically on first run
```

### Redis Configuration

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Security Hardening

### 1. SSL/TLS Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.agentguard.io;
    
    ssl_certificate /etc/ssl/certs/agentguard.crt;
    ssl_certificate_key /etc/ssl/private/agentguard.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. Firewall Rules

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 80/tcp    # HTTP (redirect to HTTPS)
sudo ufw enable

# AWS Security Group
# Inbound: 443 (HTTPS), 22 (SSH from bastion)
# Outbound: All
```

### 3. API Key Management

```python
# Generate secure API keys
import secrets

api_key = secrets.token_urlsafe(32)
print(f"API Key: {api_key}")

# Store in environment or secrets manager
# AWS Secrets Manager, GCP Secret Manager, etc.
```

### 4. Rate Limiting

```python
# Configure rate limits in .env
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000
RATE_LIMIT_PER_DAY=50000
```

## Monitoring and Observability

### 1. Health Checks

```bash
# Basic health check
curl https://api.agentguard.io/health

# Detailed status
curl https://api.agentguard.io/monitor/status
```

### 2. Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentguard'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
```

### 3. Logging

```python
# Configure structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_obj)

# Apply to handlers
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### 4. Error Tracking (Sentry)

```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1
)
```

## Scaling Configuration

### Horizontal Scaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agentguard-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agentguard
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Load Balancing

```nginx
# nginx load balancer
upstream agentguard_backend {
    least_conn;
    server backend1.agentguard.io:8000;
    server backend2.agentguard.io:8000;
    server backend3.agentguard.io:8000;
}

server {
    listen 443 ssl;
    server_name api.agentguard.io;
    
    location / {
        proxy_pass http://agentguard_backend;
    }
}
```

## Backup and Disaster Recovery

### Database Backups

```bash
# Automated PostgreSQL backups
#!/bin/bash
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -h localhost -U agentguard_user agentguard | \
  gzip > $BACKUP_DIR/agentguard_$DATE.sql.gz

# Retain last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Upload to S3
aws s3 cp $BACKUP_DIR/agentguard_$DATE.sql.gz \
  s3://agentguard-backups/postgresql/
```

### Disaster Recohighly Plan

1. **Database Restore**:
   ```bash
   gunzip < backup.sql.gz | psql -h localhost -U agentguard_user agentguard
   ```

2. **Service Restoration**:
   ```bash
   kubectl apply -f k8s/
   kubectl rollout status deployment/agentguard
   ```

3. **Verification**:
   ```bash
   curl https://api.agentguard.io/health
   ```

## Performance Optimization

### 1. Caching Strategy

```python
# Redis caching for expensive operations
import redis
import json

redis_client = redis.from_url(os.getenv("REDIS_URL"))

def cache_result(key, data, ttl=3600):
    redis_client.setex(key, ttl, json.dumps(data))

def get_cached_result(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None
```

### 2. Database Optimization

```sql
-- Create indexes for common queries
CREATE INDEX idx_detection_results_agent_id ON detection_results(agent_id);
CREATE INDEX idx_detection_results_created_at ON detection_results(created_at);
CREATE INDEX idx_detection_results_risk_level ON detection_results(risk_level);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM detection_results WHERE agent_id = 'test';
```

### 3. Connection Pooling

```python
# PostgreSQL connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    os.getenv("DATABASE_URL"),
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

## Maintenance Procedures

### Rolling Updates

```bash
# Kubernetes rolling update
kubectl set image deployment/agentguard \
  agentguard=agentguard:v1.1.0 \
  --namespace=agentguard

# Monitor rollout
kubectl rollout status deployment/agentguard --namespace=agentguard

# Rollback if needed
kubectl rollout undo deployment/agentguard --namespace=agentguard
```

### Database Migrations

```bash
# Run migrations
python -m alembic upgrade head

# Rollback migration
python -m alembic downgrade -1
```

### Log Rotation

```bash
# logrotate config
/var/log/agentguard/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 agentguard agentguard
    sharedscripts
    postrotate
        systemctl reload agentguard
    endscript
}
```

## Troubleshooting

### High CPU Usage

```bash
# Check process usage
top -p $(pgrep -f agentguard)

# Profile application
py-spy record -o profile.svg -p $(pgrep -f agentguard)
```

### Memory Leaks

```bash
# Monitor memory usage
watch -n 1 'ps aux | grep agentguard'

# Use memory profiler
python -m memory_profiler app.py
```

### Database Connection Issues

```bash
# Check connections
psql -h localhost -U agentguard_user -c "SELECT count(*) FROM pg_stat_activity;"

# Kill idle connections
psql -h localhost -U agentguard_user -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"
```

## Compliance and Auditing

### Audit Logging

```python
# Enable audit logging
AUDIT_LOG_ENABLED=true
AUDIT_LOG_PATH=/var/log/agentguard/audit.log

# Log format
{
  "timestamp": "2025-10-25T12:00:00Z",
  "user_id": "user123",
  "action": "detect_hallucination",
  "resource": "agent_abc",
  "result": "success",
  "ip_address": "192.168.1.1"
}
```

### Compliance Reports

```bash
# Generate compliance report
curl -X POST https://api.agentguard.io/compliance/report \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"scope": ["EU_AI_ACT", "NIST_RMF", "GDPR"]}'
```

## Cost Optimization

### 1. Use Caching

```python
# Cache expensive API calls
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600
```

### 2. Optimize Model Selection

```python
# Use adaptive model selection
CONSENSUS_STRATEGY=ADAPTIVE
CONSENSUS_COST_OPTIMIZATION=true
```

### 3. Right-Size Resources

```bash
# Monitor actual usage
kubectl top nodes
kubectl top pods --namespace=agentguard

# Adjust resource requests/limits
kubectl set resources deployment/agentguard \
  --requests=cpu=500m,memory=1Gi \
  --limits=cpu=2000m,memory=4Gi
```

## Support and Escalation

### Support Channels
- **Email**: support@agentguard.io
- **Slack**: agentguard-support
- **Phone**: +1-800-AGENT-GUARD (critical issues only)

### Escalation Path
1. **Level 1**: Support team (response: 4 hours)
2. **Level 2**: Engineering team (response: 2 hours)
3. **Level 3**: Senior engineering (response: 1 hour)
4. **Level 4**: CTO (response: 30 minutes)

## Additional Resources

- API Documentation: https://api.agentguard.io/docs
- User Guides: https://docs.agentguard.io
- GitHub: https://github.com/agentguard/agentguard
- Status Page: https://status.agentguard.io

