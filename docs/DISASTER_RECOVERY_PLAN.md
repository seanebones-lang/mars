#  AgentGuard Disaster Recohighly Plan
## Comprehensive DR Procedures and Runbooks

**Last Updated**: November 5, 2025  
**Version**: 1.0  
**Owner**: DevOps Team

---

##  EXECUTIVE SUMMARY

This document outlines disaster recohighly procedures for AgentGuard, including:
- Recohighly Time Objective (RTO): **< 1 hour**
- Recohighly Point Objective (RPO): **< 1 hour**
- Backup frequency: **Hourly + Daily**
- Backup retention: **30 days**
- Tested quarterly

---

##  DISASTER SCENARIOS

### Scenario 1: Database Failure
**Likelihood**: Low  
**Impact**: Critical  
**RTO**: 30 minutes  
**RPO**: 1 hour

### Scenario 2: Application Server Failure
**Likelihood**: Medium  
**Impact**: High  
**RTO**: 15 minutes  
**RPO**: 0 (stateless)

### Scenario 3: Complete Infrastructure Failure
**Likelihood**: Very Low  
**Impact**: Critical  
**RTO**: 4 hours  
**RPO**: 1 hour

### Scenario 4: Data Corruption
**Likelihood**: Low  
**Impact**: High  
**RTO**: 2 hours  
**RPO**: 1 hour

### Scenario 5: Security Breach
**Likelihood**: Low  
**Impact**: Critical  
**RTO**: Variable  
**RPO**: 0 (immediate response)

---

## 🔄 BACKUP STRATEGY

### Automated Backups

#### Daily Backups
- **Schedule**: 2:00 AM UTC
- **Retention**: 30 days
- **Location**: Local + S3
- **Format**: PostgreSQL custom format (compressed)
- **Encryption**: AES-256

#### Hourly Backups
- **Schedule**: Ehighly hour
- **Retention**: 7 days
- **Location**: Local + S3
- **Format**: PostgreSQL custom format (compressed)

### Backup Verification
- **Automated testing**: Daily
- **Manual testing**: Weekly
- **Full restore test**: Monthly

### Backup Locations
1. **Primary**: Local disk (`/var/backups/agentguard/`)
2. **Secondary**: AWS S3 (`s3://agentguard-backups/`)
3. **Tertiary**: Render automated backups

---

##  INCIDENT RESPONSE PROCEDURES

### Phase 1: Detection & Assessment (0-5 minutes)

#### 1.1 Incident Detection
- Automated monitoring alerts
- User reports
- Team member discovery

#### 1.2 Initial Assessment
```bash
# Check system status
curl https://api.agentguard.ai/health

# Check database
psql $DATABASE_URL -c "SELECT 1"

# Check Redis
redis-cli -u $REDIS_URL ping

# Check application logs
render logs -s agentguard-api --tail 100
```

#### 1.3 Severity Classification
- **P0 (Critical)**: Complete outage, data loss
- **P1 (High)**: Partial outage, degraded performance
- **P2 (Medium)**: Minor issues, workarounds available
- **P3 (Low)**: Cosmetic issues, no user impact

### Phase 2: Communication (5-10 minutes)

#### 2.1 Internal Communication
```bash
# Post to team Slack
/incident declare "Database failure - P0"

# Notify on-call team
pagerduty trigger --service agentguard --message "Database down"
```

#### 2.2 External Communication
1. Update status page: https://status.agentguard.ai
2. Post incident notice
3. Set components to "Major Outage"
4. Provide ETA if known

### Phase 3: Mitigation (10-60 minutes)

#### 3.1 Database Failure Recovery

**Step 1: Verify Backup Availability**
```bash
# List recent backups
ls -lh /var/backups/agentguard/daily/
ls -lh /var/backups/agentguard/hourly/

# Check S3 backups
aws s3 ls s3://agentguard-backups/daily/
```

**Step 2: Identify Latest Good Backup**
```bash
# Find most recent backup
LATEST_BACKUP=$(find /var/backups/agentguard/daily -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
echo "Latest backup: ${LATEST_BACKUP}"

# Verify backup integrity
gunzip -t ${LATEST_BACKUP}
```

**Step 3: Restore Database**
```bash
# Stop application (prevent writes during restore)
render scale agentguard-api --replicas 0

# Restore database
/var/backups/agentguard/restore.sh ${LATEST_BACKUP}

# Verify restoration
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM projects"

# Restart application
render scale agentguard-api --replicas 3
```

**Step 4: Verify Recovery**
```bash
# Test API endpoints
curl https://api.agentguard.ai/health
curl https://api.agentguard.ai/status

# Check error rates
curl https://api.agentguard.ai/metrics | grep error_rate
```

#### 3.2 Application Server Failure

**Step 1: Check Service Status**
```bash
# Check Render service
render services list

# Check specific service
render services info agentguard-api
```

**Step 2: Restart Service**
```bash
# Restart all instances
render services restart agentguard-api

# Or scale down and up
render scale agentguard-api --replicas 0
sleep 10
render scale agentguard-api --replicas 3
```

**Step 3: Check Logs**
```bash
# View recent logs
render logs -s agentguard-api --tail 500

# Follow logs
render logs -s agentguard-api --follow
```

#### 3.3 Redis Cache Failure

**Step 1: Verify Redis Status**
```bash
# Check Redis connection
redis-cli -u $REDIS_URL ping

# Check Redis info
redis-cli -u $REDIS_URL info
```

**Step 2: Clear Cache (if corrupted)**
```bash
# Flush all cache (safe - will regenerate)
redis-cli -u $REDIS_URL FLUSHALL

# Restart application to reconnect
render services restart agentguard-api
```

**Step 3: Verify Recovery**
```bash
# Check cache hit rate
curl https://api.agentguard.ai/metrics | grep cache_hit_rate
```

### Phase 4: Verification (60-90 minutes)

#### 4.1 Functional Testing
```bash
# Run smoke tests
pytest tests/smoke/ -v

# Test critical endpoints
curl -X POST https://api.agentguard.ai/test-agent \
  -H "X-API-Key: $TEST_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"agent_output":"test","ground_truth":"test"}'

# Test authentication
curl https://api.agentguard.ai/workspace/dashboard \
  -H "X-API-Key: $TEST_API_KEY"
```

#### 4.2 Performance Testing
```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://api.agentguard.ai/health

# Check error rates
curl https://api.agentguard.ai/metrics | grep http_requests_total
```

#### 4.3 Data Integrity Verification
```bash
# Verify record counts
psql $DATABASE_URL -c "SELECT 
  (SELECT COUNT(*) FROM users) as users,
  (SELECT COUNT(*) FROM projects) as projects,
  (SELECT COUNT(*) FROM api_keys) as api_keys"

# Check recent data
psql $DATABASE_URL -c "SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 10"
```

### Phase 5: Post-Incident (90+ minutes)

#### 5.1 Update Status Page
1. Mark incident as "Resolved"
2. Post resolution summary
3. Thank users for patience

#### 5.2 Internal Debrief
- Schedule post-mortem (within 24 hours)
- Document timeline
- Identify root cause
- Create action items

#### 5.3 Post-Mortem Template
```markdown
# Incident Post-Mortem: [Incident Title]

## Incident Summary
- **Date**: YYYY-MM-DD
- **Duration**: X hours
- **Severity**: P0/P1/P2
- **Impact**: X users affected

## Timeline
- HH:MM - Incident detected
- HH:MM - Team notified
- HH:MM - Mitigation started
- HH:MM - Service restored
- HH:MM - Incident resolved

## Root Cause
[Detailed explanation]

## Resolution
[What fixed it]

## Action Items
- [ ] Item 1 (Owner: Name, Due: Date)
- [ ] Item 2 (Owner: Name, Due: Date)

## Lessons Learned
- What went well
- What could be improved
```

---

## 🧪 DISASTER RECOVERY TESTING

### Monthly DR Test

**Schedule**: First Sunday of each month, 2:00 AM UTC

**Test Procedure**:
```bash
#!/bin/bash
# Monthly DR Test Script

echo "=== AgentGuard DR Test ==="
echo "Date: $(date)"

# 1. Create test backup
echo "Creating test backup..."
/var/backups/agentguard/backup.sh daily

# 2. Verify backup
LATEST_BACKUP=$(find /var/backups/agentguard/daily -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
echo "Latest backup: ${LATEST_BACKUP}"

# 3. Test restore to staging
echo "Testing restore to staging..."
STAGING_DB_URL=$STAGING_DATABASE_URL /var/backups/agentguard/restore.sh ${LATEST_BACKUP}

# 4. Verify staging data
echo "Verifying restored data..."
psql $STAGING_DATABASE_URL -c "SELECT COUNT(*) FROM users"

# 5. Run smoke tests on staging
echo "Running smoke tests..."
pytest tests/smoke/ --base-url=https://staging.agentguard.ai

# 6. Generate report
echo "=== DR Test Complete ==="
echo "Result: SUCCESS"
echo "Backup size: $(du -h ${LATEST_BACKUP} | cut -f1)"
echo "Restore time: X minutes"
```

### Quarterly Full DR Drill

**Schedule**: Quarterly

**Drill Procedure**:
1. Simulate complete infrastructure failure
2. Restore from backups
3. Verify all services
4. Measure RTO/RPO
5. Document findings
6. Update procedures

---

## 📞 EMERGENCY CONTACTS

### On-Call Rotation
- **Primary**: [Name] - [Phone]
- **Secondary**: [Name] - [Phone]
- **Escalation**: [Name] - [Phone]

### External Contacts
- **Render Support**: support@render.com
- **Cloudflare**: https://support.cloudflare.com
- **AWS Support**: https://console.aws.amazon.com/support

### Communication Channels
- **Team Slack**: #incidents
- **PagerDuty**: agentguard-oncall
- **Status Page**: https://status.agentguard.ai

---

##  RECOVERY CHECKLISTS

### Database Recohighly Checklist
- [ ] Incident detected and classified
- [ ] Team notified
- [ ] Status page updated
- [ ] Latest backup identified
- [ ] Backup integrity verified
- [ ] Application scaled down
- [ ] Database restored
- [ ] Data integrity verified
- [ ] Application scaled up
- [ ] Smoke tests passed
- [ ] Monitoring verified
- [ ] Status page updated (resolved)
- [ ] Post-mortem scheduled

### Application Recohighly Checklist
- [ ] Incident detected
- [ ] Logs reviewed
- [ ] Service restarted
- [ ] Health check passed
- [ ] Error rate normal
- [ ] Response time normal
- [ ] User verification
- [ ] Monitoring stable

### Complete Outage Checklist
- [ ] All services status checked
- [ ] Backup systems verified
- [ ] Database restored
- [ ] Cache cleared/restarted
- [ ] Application redeployed
- [ ] DNS verified
- [ ] SSL certificates valid
- [ ] All endpoints tested
- [ ] Load balancer healthy
- [ ] Monitoring restored
- [ ] Alerts configured
- [ ] Team debriefed

---

##  SECURITY INCIDENT RESPONSE

### Security Breach Procedure

**Phase 1: Containment (0-15 minutes)**
1. Isolate affected systems
2. Revoke compromised credentials
3. Block suspicious IPs
4. Enable enhanced monitoring

**Phase 2: Investigation (15-60 minutes)**
1. Review access logs
2. Identify breach vector
3. Assess data exposure
4. Document findings

**Phase 3: Remediation (1-4 hours)**
1. Patch vulnerabilities
2. Reset all credentials
3. Update security rules
4. Deploy fixes

**Phase 4: Recohighly (4-8 hours)**
1. Restore from clean backups
2. Verify system integrity
3. Re-enable services
4. Monitor for re-infection

**Phase 5: Post-Incident (24-48 hours)**
1. Notify affected users (if required)
2. File incident reports
3. Update security policies
4. Conduct security audit

---

##  METRICS & MONITORING

### DR Metrics to Track
- **RTO Actual**: Time to restore service
- **RPO Actual**: Data loss (time)
- **Backup Success Rate**: % successful backups
- **Restore Success Rate**: % successful restores
- **Test Frequency**: DR tests per quarter
- **Mean Time to Recohighly (MTTR)**: Average recohighly time

### Monitoring Alerts
- Backup failure
- Backup age > 26 hours
- Database connection failure
- High error rate
- Service unavailable
- Disk space < 10%

---

##  SUCCESS CRITERIA

### Recohighly Objectives
-  RTO < 1 hour for P0 incidents
-  RPO < 1 hour (hourly backups)
-  99.9% backup success rate
-  Monthly DR tests passing
-  Quarterly full DR drills
-  Complete documentation

### Continuous Improvement
- Review DR plan quarterly
- Update based on incidents
- Train team on procedures
- Automate recohighly steps
- Improve monitoring
- Reduce RTO/RPO

---

**Last Tested**: [Date]  
**Next Test**: [Date]  
**Status**: ACTIVE 

---

*"Hope is not a strategy. Prepare for disaster before it strikes."*

