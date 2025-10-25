# Performance Benchmarks & Load Testing

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Performance validation and benchmarking**

---

## Performance Targets

### Response Time
- **P50 (Median)**: < 100ms
- **P95**: < 200ms
- **P99**: < 500ms
- **Max**: < 2000ms

### Throughput
- **Requests/second**: 1,000+
- **Concurrent Users**: 10,000+
- **WebSocket Connections**: 10,000+

### Reliability
- **Uptime**: 99.9%
- **Error Rate**: < 1%
- **Success Rate**: > 99%

### Resource Utilization
- **CPU**: < 80% average
- **Memory**: < 80% average
- **Database Connections**: < 80% pool size

---

## Load Testing Suite

### Test Types

#### 1. Baseline Performance Test
**Purpose**: Establish baseline metrics  
**Configuration**:
- Users: 100
- Duration: 2 minutes
- Spawn Rate: 10 users/second

**Expected Results**:
- P95 Response Time: < 150ms
- Requests/sec: 100-200
- Error Rate: < 0.1%

#### 2. Target Load Test
**Purpose**: Validate target performance  
**Configuration**:
- Users: 1,000
- Duration: 5 minutes
- Spawn Rate: 100 users/second

**Expected Results**:
- P95 Response Time: < 200ms
- Requests/sec: 1,000+
- Error Rate: < 1%

#### 3. Stress Test
**Purpose**: Find breaking point  
**Configuration**:
- Users: 5,000
- Duration: 3 minutes
- Spawn Rate: 500 users/second

**Expected Results**:
- Identify maximum capacity
- Graceful degradation
- No crashes or data loss

#### 4. Spike Test
**Purpose**: Handle sudden traffic spikes  
**Configuration**:
- Users: 0 → 2,000 → 0
- Duration: 2 minutes
- Spawn Rate: 1,000 users/second

**Expected Results**:
- Auto-scaling triggers
- No service disruption
- Recohighly within 30 seconds

#### 5. WebSocket Load Test
**Purpose**: Validate real-time monitoring scalability  
**Configuration**:
- Connections: 1,000 concurrent
- Duration: 2 minutes
- Message Rate: Variable

**Expected Results**:
- Connection Success Rate: > 95%
- Message Latency: < 100ms
- No connection drops

---

## Running Load Tests

### Prerequisites

```bash
# Install Locust
pip install locust

# Install WebSocket testing dependencies
pip install websockets
```

### Quick Start

```bash
# Run all tests for staging
./scripts/run_load_tests.sh staging

# Run all tests for production
./scripts/run_load_tests.sh production
```

### Individual Tests

```bash
# Baseline test
locust -f tests/load/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 2m \
    --host=https://agentguard-api.onrender.com

# Target load test
locust -f tests/load/locustfile.py \
    --headless \
    --users 1000 \
    --spawn-rate 100 \
    --run-time 5m \
    --host=https://agentguard-api.onrender.com

# WebSocket test
python tests/load/websocket_load_test.py \
    --url wss://agentguard-api.onrender.com/ws/monitor \
    --connections 1000 \
    --duration 120
```

### Interactive Mode

```bash
# Start Locust web UI
locust -f tests/load/locustfile.py --host=https://agentguard-api.onrender.com

# Open browser to http://localhost:8089
# Configure users and spawn rate in UI
```

---

## Endpoint Performance Targets

| Endpoint | P50 | P95 | P99 | RPS Target |
|----------|-----|-----|-----|------------|
| `/health` | 10ms | 20ms | 50ms | 500+ |
| `/metrics` | 20ms | 50ms | 100ms | 100+ |
| `/test-agent` | 100ms | 200ms | 500ms | 500+ |
| `/prompt-injection/detect` | 50ms | 150ms | 300ms | 200+ |
| `/multi-model/detect` | 200ms | 500ms | 1000ms | 100+ |
| `/pii-protection/detect` | 30ms | 100ms | 200ms | 300+ |
| `/bias-fairness/audit` | 100ms | 250ms | 500ms | 150+ |
| `/multimodal/detect-image` | 500ms | 1000ms | 2000ms | 50+ |

---

## Performance Optimization Checklist

### Backend Optimizations
- [ ] Database query optimization
- [ ] Connection pooling configured
- [ ] Redis caching implemented
- [ ] Async operations for I/O
- [ ] Rate limiting per customer
- [ ] Request batching where possible

### Infrastructure Optimizations
- [ ] Auto-scaling configured
- [ ] CDN for static assets
- [ ] Load balancer configured
- [ ] Database read replicas
- [ ] Redis cluster for caching
- [ ] Multi-region deployment

### Code Optimizations
- [ ] Lazy loading of models
- [ ] Response compression
- [ ] Efficient serialization
- [ ] Memory pooling
- [ ] Background task processing
- [ ] Query result caching

---

## Monitoring During Load Tests

### Key Metrics to Watch

**Application Metrics**:
- Response time (P50, P95, P99)
- Requests per second
- Error rate
- Active connections
- Queue depth

**System Metrics**:
- CPU utilization
- Memory usage
- Disk I/O
- Network throughput
- Database connections

**External API Metrics**:
- Claude API latency
- Claude API rate limits
- OpenAI API latency (if used)
- Stripe API latency (if used)

### Monitoring Commands

```bash
# Watch API metrics
watch -n 1 'curl -s https://agentguard-api.onrender.com/metrics | jq'

# Monitor health status
watch -n 5 'curl -s https://agentguard-api.onrender.com/health | jq .status'

# Check Render metrics
# Go to dashboard.render.com → Service → Metrics
```

---

## Performance Regression Testing

### Automated Performance Tests

Add to CI/CD pipeline:

```yaml
# In .github/workflows/production-ci.yml
- name: Performance Regression Test
  run: |
    locust -f tests/load/locustfile.py \
      --headless \
      --users 100 \
      --spawn-rate 10 \
      --run-time 1m \
      --host=https://staging-api.mothership-ai.com \
      --csv=performance_results
    
    # Check if P95 < 200ms
    p95=$(cat performance_results_stats.csv | grep Aggregated | cut -d',' -f9)
    if [ $p95 -gt 200 ]; then
      echo "Performance regression detected: P95 = ${p95}ms"
      exit 1
    fi
```

### Performance Baseline

Establish baseline after each major release:

```bash
# Run baseline test
./scripts/run_load_tests.sh production

# Save results
cp load_test_results/target_load_*.csv performance_baselines/v1.0.0.csv

# Compare with previous baseline
diff performance_baselines/v1.0.0.csv performance_baselines/v0.9.0.csv
```

---

## Troubleshooting Performance Issues

### High Response Time

**Symptoms**: P95 > 200ms

**Investigation**:
1. Check database query performance
2. Check external API latency (Claude, OpenAI)
3. Check Redis cache hit rate
4. Check CPU/memory utilization
5. Check for N+1 queries

**Solutions**:
- Add database indexes
- Optimize slow queries
- Increase cache TTL
- Scale up resources
- Implement query batching

### Low Throughput

**Symptoms**: RPS < 1,000

**Investigation**:
1. Check worker count
2. Check connection pool size
3. Check rate limiting configuration
4. Check for bottlenecks (database, Redis)
5. Check network bandwidth

**Solutions**:
- Increase worker count
- Increase connection pool size
- Adjust rate limits
- Scale database
- Add load balancer

### High Error Rate

**Symptoms**: Error rate > 1%

**Investigation**:
1. Check error logs in Sentry
2. Check database connection errors
3. Check external API errors
4. Check timeout configurations
5. Check resource exhaustion

**Solutions**:
- Fix application errors
- Increase timeouts
- Add retry logic
- Scale resources
- Implement circuit breakers

---

## Load Test Results Archive

### Latest Results

**Date**: TBD  
**Environment**: Production  
**Version**: 1.0.0

| Test | Users | Duration | RPS | P95 | Error Rate | Status |
|------|-------|----------|-----|-----|------------|--------|
| Baseline | 100 | 2m | TBD | TBD | TBD |  |
| Target Load | 1,000 | 5m | TBD | TBD | TBD |  |
| Stress | 5,000 | 3m | TBD | TBD | TBD |  |
| Spike | 2,000 | 2m | TBD | TBD | TBD |  |
| WebSocket | 1,000 | 2m | TBD | TBD | TBD |  |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AgentGuard Team | Initial version |

**Last Updated**: October 24, 2025  
**Next Review**: November 24, 2025

---

**Mothership AI**  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

