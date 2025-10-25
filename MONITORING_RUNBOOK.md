# Monitoring & Alerting Runbook

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Production monitoring and incident response procedures**

---

## Overview

This runbook provides procedures for monitoring the AgentGuard platform and responding to alerts.

### Monitoring Stack

- **Error Tracking**: Sentry
- **Alerting**: Slack, PagerDuty, Email
- **Health Monitoring**: Custom health checks
- **Metrics**: System metrics via `/metrics` endpoint

---

## Alert Severity Levels

| Severity | Response Time | Escalation | Notification |
|----------|---------------|------------|--------------|
| **CRITICAL** | 15 minutes | Immediate PagerDuty | Slack + PagerDuty + Email |
| **ERROR** | 30 minutes | After 1 hour | Slack + Email |
| **WARNING** | 2 hours | After 4 hours | Slack |
| **INFO** | 24 hours | None | Slack |

---

## Common Alerts & Responses

###  CRITICAL: API Service Down

**Alert**: "API Service Down: agentguard-api"

**Symptoms**:
- Health check returning non-200 status
- API not responding to requests
- Multiple 5xx errors

**Immediate Actions** (within 15 minutes):

1. **Check Service Status**
   ```bash
   curl https://agentguard-api.onrender.com/health
   ```

2. **Check Render Dashboard**
   - Go to dashboard.render.com
   - Check service logs
   - Check deployment status

3. **Quick Fixes**:
   - Restart service if hung
   - Rollback if recent deployment
   - Scale up if resource exhaustion

4. **Escalate** if not resolved in 15 minutes

**Investigation**:
```bash
# Check logs
# In Render dashboard: Logs tab

# Check recent deployments
# In Render dashboard: Events tab

# Check health endpoint details
curl https://agentguard-api.onrender.com/health | jq
```

**Resolution**:
- Document root cause
- Update incident log
- Implement preventive measures

---

### ❌ ERROR: Database Error

**Alert**: "Database Error"

**Symptoms**:
- Database connection failures
- Query timeouts
- Data inconsistencies

**Immediate Actions** (within 30 minutes):

1. **Check Database Status**
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

2. **Check Connection Pool**
   ```bash
   psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
   ```

3. **Check Disk Space**
   ```bash
   # In Render dashboard: Metrics tab
   ```

4. **Quick Fixes**:
   - Kill long-running queries
   - Restart database connections
   - Scale database if needed

**Investigation**:
```bash
# Check slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# Check locks
psql $DATABASE_URL -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Check table sizes
psql $DATABASE_URL -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size FROM pg_tables ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

**Resolution**:
- Optimize slow queries
- Add indexes if needed
- Consider database upgrade

---

###  WARNING: High Error Rate

**Alert**: "High Error Rate Detected"

**Symptoms**:
- Error rate > 5%
- Multiple 4xx or 5xx responses
- User complaints

**Actions** (within 2 hours):

1. **Check Error Logs**
   ```bash
   # In Sentry dashboard
   # Filter by time range and error type
   ```

2. **Identify Pattern**
   - Specific endpoint?
   - Specific user?
   - Recent deployment?

3. **Quick Fixes**:
   - Rollback if deployment-related
   - Fix obvious bugs
   - Add rate limiting if abuse

**Investigation**:
```bash
# Check error distribution
# In Sentry: Issues → Group by endpoint

# Check recent changes
git log --since="2 hours ago" --oneline

# Check API metrics
curl https://agentguard-api.onrender.com/metrics
```

---

###  WARNING: Slow API Response

**Alert**: "Slow API Response"

**Symptoms**:
- Response time > 2 seconds
- Timeouts
- User complaints about slowness

**Actions** (within 2 hours):

1. **Identify Slow Endpoints**
   ```bash
   # Check Sentry performance monitoring
   # Look for slow transactions
   ```

2. **Check System Resources**
   ```bash
   # In Render dashboard: Metrics
   # CPU, Memory, Network usage
   ```

3. **Quick Fixes**:
   - Scale up workers
   - Clear cache if stale
   - Optimize database queries

**Investigation**:
```bash
# Check database query performance
psql $DATABASE_URL -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check Redis cache hit rate
redis-cli INFO stats | grep hit_rate

# Profile slow endpoints
# Use Sentry performance monitoring
```

---

###  CRITICAL: Security Incident

**Alert**: "SECURITY INCIDENT"

**Symptoms**:
- Unauthorized access attempts
- Data breach indicators
- Suspicious activity patterns

**Immediate Actions** (within 15 minutes):

1. **Isolate System**
   ```bash
   # Enable maintenance mode
   # Update Render environment: MAINTENANCE_MODE=true
   ```

2. **Assess Breach**
   - Check access logs
   - Identify compromised data
   - Determine timeline

3. **Rotate Credentials**
   ```bash
   ./scripts/rotate_secrets.sh --emergency
   ```

4. **Notify Stakeholders**
   - Security team
   - Legal team
   - Management
   - Affected customers (if PII exposed)

**Investigation**:
```bash
# Check access logs
# In Render dashboard: Logs tab
# Filter for suspicious IPs or patterns

# Check database audit logs
psql $DATABASE_URL -c "SELECT * FROM audit_log WHERE timestamp > NOW() - INTERVAL '24 hours' ORDER BY timestamp DESC;"

# Check failed authentication attempts
# In application logs
```

**Resolution**:
- Document incident timeline
- Implement security fixes
- Update security procedures
- File incident report

---

### ❌ ERROR: Backup Failed

**Alert**: "Backup Failed"

**Symptoms**:
- Backup script errors
- Missing backup files
- S3 upload failures

**Actions** (within 30 minutes):

1. **Check Backup Logs**
   ```bash
   tail -f /var/log/agentguard/backup.log
   ```

2. **Verify Database Access**
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```

3. **Check S3 Access**
   ```bash
   aws s3 ls s3://agentguard-backups/
   ```

4. **Manual Backup**
   ```bash
   ./scripts/backup_database.sh emergency_$(date +%Y%m%d_%H%M%S)
   ```

**Investigation**:
```bash
# Check disk space
df -h /var/backups/agentguard

# Check S3 permissions
aws s3api get-bucket-acl --bucket agentguard-backups

# Test backup script
./scripts/backup_database.sh test_backup
```

---

###  INFO: Deployment Successful

**Alert**: "Deployment Successful"

**Actions**:
- Monitor for 30 minutes
- Check error rates
- Verify key functionality

**Post-Deployment Checks**:
```bash
# Health check
curl https://agentguard-api.onrender.com/health

# Test critical endpoints
curl -X POST https://agentguard-api.onrender.com/test-agent \
  -H "Content-Type: application/json" \
  -d '{"agent_output":"test","ground_truth":"test"}'

# Check error rate in Sentry
# Should be < 1% for first 30 minutes
```

---

## Monitoring Dashboards

### Sentry Dashboard
- **URL**: https://sentry.io/organizations/mothership-ai/
- **Purpose**: Error tracking and performance monitoring
- **Key Metrics**:
  - Error rate
  - Response time
  - User impact
  - Release tracking

### Render Dashboard
- **URL**: https://dashboard.render.com/
- **Purpose**: Infrastructure monitoring
- **Key Metrics**:
  - CPU usage
  - Memory usage
  - Request count
  - Deployment status

### Health Endpoint
- **URL**: https://agentguard-api.onrender.com/health
- **Purpose**: Component health status
- **Returns**:
  - Overall status
  - Component statuses
  - Response times
  - Environment info

---

## Escalation Procedures

### Level 1: On-Call Engineer
- **Response Time**: 15 minutes
- **Responsibilities**:
  - Acknowledge alert
  - Initial investigation
  - Quick fixes
  - Escalate if needed

### Level 2: Senior Engineer
- **Response Time**: 30 minutes (after L1 escalation)
- **Responsibilities**:
  - Deep investigation
  - Complex fixes
  - Coordinate with team
  - Escalate to management if needed

### Level 3: Management
- **Response Time**: 1 hour (after L2 escalation)
- **Responsibilities**:
  - Customer communication
  - Resource allocation
  - External vendor coordination
  - Executive updates

---

## On-Call Contacts

**Primary On-Call**:
- Email: oncall@mothership-ai.com
- Phone: +1 (XXX) XXX-XXXX
- PagerDuty: agentguard-oncall

**Backup On-Call**:
- Email: backup-oncall@mothership-ai.com
- Phone: +1 (XXX) XXX-XXXX

**Management Escalation**:
- Email: info@mothership-ai.com

---

## Useful Commands

### Health Checks
```bash
# API health
curl https://agentguard-api.onrender.com/health | jq

# Database health
psql $DATABASE_URL -c "SELECT 1;"

# Redis health
redis-cli ping
```

### Logs
```bash
# Application logs (Render dashboard)
# Go to: dashboard.render.com → Service → Logs

# Backup logs
tail -f /var/log/agentguard/backup.log

# Deployment logs
tail -f /var/log/agentguard/deployments.log
```

### Deployments
```bash
# Deploy to staging
./scripts/deploy_blue_green.sh staging

# Deploy to production
./scripts/deploy_blue_green.sh production

# Rollback (manual in Render dashboard)
```

### Database
```bash
# Backup
./scripts/backup_database.sh

# Restore
./scripts/restore_database.sh backup_YYYYMMDD_HHMMSS

# Check connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Alert Configuration

### Slack Webhook
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### PagerDuty
```bash
export PAGERDUTY_API_KEY="..."
```

### Sentry
```bash
export SENTRY_DSN="https://...@sentry.io/..."
export SENTRY_ENVIRONMENT="production"
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AgentGuard Team | Initial version |

**Last Updated**: October 24, 2025  
**Next Review**: January 24, 2026

---

**Mothership AI**  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

