# AgentGuard Kubernetes Deployment

## Overview

This directory contains production-ready Kubernetes manifests for deploying AgentGuard, an AI hallucination detection platform. The deployment includes auto-scaling, monitoring, security, and high availability configurations.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │     Ingress     │    │      NGINX      │
│   (External)    │───▶│   Controller    │───▶│   (2 replicas)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 ▼                                 │
                       │                    ┌─────────────────┐                           │
                       │                    │  AgentGuard API │                           │
                       │                    │  (3-20 replicas)│                           │
                       │                    └─────────────────┘                           │
                       │                             │                                     │
                       │        ┌────────────────────┼────────────────────┐               │
                       │        ▼                    ▼                    ▼               │
                       │ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐            │
                       │ │ PostgreSQL  │    │    Redis    │    │   MLflow    │            │
                       │ │(StatefulSet)│    │(StatefulSet)│    │(StatefulSet)│            │
                       │ └─────────────┘    └─────────────┘    └─────────────┘            │
                       └─────────────────────────────────────────────────────────────────┘
                                                        │
                       ┌─────────────────────────────────┼─────────────────────────────────┐
                       │                                 ▼                                 │
                       │                    ┌─────────────────┐                           │
                       │                    │   Prometheus    │                           │
                       │                    │   (Monitoring)  │                           │
                       │                    └─────────────────┘                           │
                       │                             │                                     │
                       │                             ▼                                     │
                       │                    ┌─────────────────┐                           │
                       │                    │     Grafana     │                           │
                       │                    │  (Dashboards)   │                           │
                       │                    └─────────────────┘                           │
                       └─────────────────────────────────────────────────────────────────┘
```

## Features

###  **Scalability**
- **Horizontal Pod Autoscaler (HPA)**: Auto-scales API pods from 3-20 replicas based on CPU, memory, and custom metrics
- **Vertical Pod Autoscaler (VPA)**: Automatically adjusts resource requests and limits
- **Load Balancing**: NGINX ingress with intelligent load balancing and session affinity

###  **Security**
- **RBAC**: Role-based access control with minimal required permissions
- **Pod Security Policies**: Enforces security constraints on pods
- **Network Policies**: Restricts network traffic between pods
- **Secret Management**: Kubernetes secrets with optional external secret management
- **Non-root Containers**: All containers run as non-root users
- **Read-only Root Filesystem**: Enhanced container security

###  **Monitoring & Observability**
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization dashboards
- **Custom Metrics**: Application-specific metrics for HPA
- **Health Checks**: Comprehensive liveness, readiness, and startup probes
- **Logging**: Structured logging with log aggregation

### 🏗 **High Availability**
- **Multi-replica Deployments**: Redundancy across availability zones
- **Pod Anti-affinity**: Spreads pods across different nodes
- **Persistent Storage**: Reliable data persistence with backup strategies
- **Rolling Updates**: Zero-downtime deployments
- **Circuit Breakers**: Fault tolerance and graceful degradation

###  **Performance**
- **Resource Optimization**: Tuned resource requests and limits
- **Caching**: Redis for high-performance caching
- **Connection Pooling**: Optimized database connections
- **Compression**: Gzip compression for API responses
- **CDN Integration**: Static asset optimization

## Prerequisites

### Required Tools
```bash
# Kubernetes CLI
kubectl version --client

# Docker (for building images)
docker --version

# Helm (optional, for package management)
helm version
```

### Cluster Requirements
- **Kubernetes Version**: 1.24+
- **Node Resources**: Minimum 4 CPU cores, 8GB RAM per node
- **Storage Classes**: 
  - `fast-ssd` for databases (SSD-backed)
  - `standard` for general storage
  - `nfs-client` for shared storage (optional)
- **Ingress Controller**: NGINX Ingress Controller
- **Cert Manager**: For TLS certificate management
- **Metrics Server**: For HPA functionality

### Network Requirements
- **Ingress**: External load balancer or NodePort access
- **DNS**: Proper DNS resolution for domain names
- **Firewall**: Allow traffic on ports 80, 443, and Kubernetes API

## Quick Start

### 1. Clone and Prepare
```bash
git clone <repository-url>
cd mars/k8s
```

### 2. Configure Secrets
```bash
# Create secrets file (DO NOT commit to version control)
cp secrets.yaml secrets-production.yaml

# Edit with your actual secrets
vim secrets-production.yaml

# Apply secrets
kubectl apply -f secrets-production.yaml
```

### 3. Deploy Infrastructure
```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy everything
./scripts/deploy.sh
```

### 4. Verify Deployment
```bash
# Check pod status
kubectl get pods -n agentguard

# Check services
kubectl get services -n agentguard

# Check ingress
kubectl get ingress -n agentguard

# Test health endpoint
curl -f https://watcher.mothership-ai.com/health
```

## Configuration

### Environment Variables

#### Required Secrets
```yaml
CLAUDE_API_KEY: "your_claude_api_key"
JWT_SECRET_KEY: "your_64_character_jwt_secret"
ENCRYPTION_KEY: "your_32_character_encryption_key"
POSTGRES_PASSWORD: "your_postgres_password"
REDIS_PASSWORD: "your_redis_password"
```

#### Optional Configuration
```yaml
WEBHOOK_SECRET: "your_webhook_secret"
SLACK_WEBHOOK_URL: "your_slack_webhook"
SMTP_PASSWORD: "your_smtp_password"
```

### Resource Limits

#### API Pods
```yaml
requests:
  cpu: "1000m"
  memory: "2Gi"
limits:
  cpu: "2000m"
  memory: "4Gi"
```

#### Database Pods
```yaml
postgres:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "1000m"
    memory: "2Gi"

redis:
  requests:
    cpu: "200m"
    memory: "512Mi"
  limits:
    cpu: "500m"
    memory: "1Gi"
```

### Auto-scaling Configuration

#### HPA Metrics
- **CPU Utilization**: Target 70%
- **Memory Utilization**: Target 80%
- **Custom Metrics**:
  - HTTP requests per second: Target 100/pod
  - Queue length: Target 50/pod

#### Scaling Behavior
- **Scale Up**: Max 50% increase, 4 pods per minute
- **Scale Down**: Max 10% decrease, 2 pods per minute
- **Stabilization**: 60s up, 300s down

## Monitoring

### Prometheus Metrics

#### Application Metrics
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request duration histogram
- `hallucination_detections_total`: Hallucination detection counts
- `model_inference_duration_seconds`: Model inference time
- `cache_hits_total`: Cache hit/miss statistics

#### Infrastructure Metrics
- `container_cpu_usage_seconds_total`: CPU usage
- `container_memory_usage_bytes`: Memory usage
- `kube_pod_status_ready`: Pod readiness status
- `kube_deployment_status_replicas`: Deployment replica status

### Grafana Dashboards

#### AgentGuard Overview
- Request rate and error rate
- Response time percentiles
- Hallucination detection trends
- Resource utilization

#### Infrastructure Health
- Pod status and resource usage
- Database performance metrics
- Cache hit rates
- Network traffic

### Alerting Rules

#### Critical Alerts
- **High Error Rate**: >10% 5xx errors for 5 minutes
- **Database Down**: PostgreSQL unavailable for 2 minutes
- **High Memory Usage**: >90% memory usage for 5 minutes

#### Warning Alerts
- **High Response Time**: >1s 95th percentile for 5 minutes
- **High Hallucination Rate**: Unusual detection patterns
- **Pod Restart**: Frequent pod restarts

## Security

### Network Security
```yaml
# Network policy example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: agentguard-network-policy
spec:
  podSelector:
    matchLabels:
      app: agentguard
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS only
```

### Pod Security
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
```

### Secret Management

#### Kubernetes Secrets (Basic)
```bash
kubectl create secret generic agentguard-secrets \
  --from-literal=CLAUDE_API_KEY=your_key \
  --from-literal=JWT_SECRET_KEY=your_jwt_secret \
  -n agentguard
```

#### External Secrets (Advanced)
```yaml
# Using External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: agentguard-external-secrets
spec:
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: agentguard-secrets
  data:
  - secretKey: CLAUDE_API_KEY
    remoteRef:
      key: agentguard/claude
      property: api_key
```

## Backup and Disaster Recovery

### Database Backup
```bash
# PostgreSQL backup
kubectl exec -n agentguard agentguard-postgres-0 -- \
  pg_dump -U agentguard agentguard > backup.sql

# Restore
kubectl exec -i -n agentguard agentguard-postgres-0 -- \
  psql -U agentguard agentguard < backup.sql
```

### Persistent Volume Backup
```bash
# Create volume snapshot
kubectl apply -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot
  namespace: agentguard
spec:
  source:
    persistentVolumeClaimName: postgres-data-agentguard-postgres-0
EOF
```

## Troubleshooting

### Common Issues

#### Pod Startup Issues
```bash
# Check pod status
kubectl get pods -n agentguard

# Check pod logs
kubectl logs -n agentguard deployment/agentguard-api

# Describe pod for events
kubectl describe pod -n agentguard <pod-name>
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -n agentguard agentguard-postgres-0 -- \
  psql -U agentguard -c "SELECT 1"

# Check database logs
kubectl logs -n agentguard agentguard-postgres-0
```

#### Ingress Issues
```bash
# Check ingress status
kubectl get ingress -n agentguard

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Performance Tuning

#### Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE;
```

#### Cache Optimization
```bash
# Redis memory usage
kubectl exec -n agentguard agentguard-redis-0 -- redis-cli info memory

# Cache hit rate
kubectl exec -n agentguard agentguard-redis-0 -- redis-cli info stats
```

## Maintenance

### Rolling Updates
```bash
# Update image
kubectl set image deployment/agentguard-api \
  agentguard-api=agentguard/api:new-version \
  -n agentguard

# Check rollout status
kubectl rollout status deployment/agentguard-api -n agentguard

# Rollback if needed
kubectl rollout undo deployment/agentguard-api -n agentguard
```

### Scaling Operations
```bash
# Manual scaling
kubectl scale deployment agentguard-api --replicas=5 -n agentguard

# Check HPA status
kubectl get hpa -n agentguard

# Update HPA configuration
kubectl patch hpa agentguard-api-hpa -n agentguard -p \
  '{"spec":{"maxReplicas":30}}'
```

### Resource Cleanup
```bash
# Delete specific deployment
kubectl delete deployment agentguard-api -n agentguard

# Delete entire namespace (WARNING: This deletes everything)
kubectl delete namespace agentguard
```

## Support

### Monitoring Endpoints
- **Health Check**: `https://watcher.mothership-ai.com/health`
- **Metrics**: `https://watcher.mothership-ai.com/metrics` (internal only)
- **API Docs**: `https://api.agentguard.mothership-ai.com/docs`
- **Grafana**: `https://grafana.agentguard.mothership-ai.com`

### Log Aggregation
```bash
# View aggregated logs
kubectl logs -n agentguard -l app=agentguard --tail=100 -f

# Export logs for analysis
kubectl logs -n agentguard deployment/agentguard-api --since=1h > agentguard.log
```

### Contact Information
- **Technical Support**: info@mothership-ai.com
- **Documentation**: https://docs.agentguard.mothership-ai.com
- **Status Page**: https://status.agentguard.mothership-ai.com

---

## License

Copyright (c) 2025 Mothership AI. All rights reserved.

This deployment configuration is part of the AgentGuard platform and is subject to the terms and conditions of the AgentGuard license agreement.
