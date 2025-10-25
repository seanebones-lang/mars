# Incident Response Plan

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Production incident response procedures**

---

## Table of Contents

1. [Overview](#overview)
2. [Incident Classification](#incident-classification)
3. [Response Team](#response-team)
4. [Incident Response Process](#incident-response-process)
5. [Incident Types & Procedures](#incident-types--procedures)
6. [Communication Templates](#communication-templates)
7. [Post-Incident Review](#post-incident-review)
8. [Appendices](#appendices)

---

## Overview

### Purpose

This Incident Response Plan (IRP) defines the procedures for detecting, responding to, and recovering from security and operational incidents affecting the AgentGuard platform.

### Scope

This plan covers:
- Security incidents (data breaches, unauthorized access, DDoS attacks)
- Operational incidents (service outages, performance degradation, data loss)
- Compliance incidents (regulatory violations, audit failures)

### Objectives

1. **Minimize Impact**: Reduce the duration and severity of incidents
2. **Protect Data**: Prevent data loss and unauthorized access
3. **Maintain Trust**: Communicate transparently with stakeholders
4. **Learn and Improve**: Conduct post-incident reviews to prevent recurrence

---

## Incident Classification

### Severity Levels

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0 - Critical** | Complete service outage, data breach, security compromise | 15 minutes | Immediate to management |
| **P1 - High** | Partial service outage, significant performance degradation | 30 minutes | After 1 hour |
| **P2 - Medium** | Minor service degradation, isolated issues | 2 hours | After 4 hours |
| **P3 - Low** | Cosmetic issues, feature requests | 24 hours | None |

### P0 - Critical Incidents

**Examples**:
- Complete API outage (all endpoints down)
- Data breach (PII exposed)
- Security compromise (unauthorized access to systems)
- Database corruption or loss
- Payment system failure
- DDoS attack causing service unavailability

**Response**: Immediate all-hands response, management notification, customer communication

### P1 - High Incidents

**Examples**:
- Partial API outage (some endpoints down)
- Significant performance degradation (P95 > 2 seconds)
- Database connection failures
- External API failures (Claude, Stripe)
- High error rate (> 5%)

**Response**: Immediate on-call engineer response, management notification if not resolved in 1 hour

### P2 - Medium Incidents

**Examples**:
- Minor performance issues (P95 > 500ms)
- Non-critical feature failures
- Monitoring alerts
- Backup failures
- Isolated user reports

**Response**: On-call engineer response within 2 hours

### P3 - Low Incidents

**Examples**:
- UI cosmetic issues
- Documentation errors
- Feature requests
- Non-urgent improvements

**Response**: Addressed during normal business hours

---

## Response Team

### Roles and Responsibilities

#### Incident Commander (IC)
**Responsibilities**:
- Overall incident coordination
- Decision-making authority
- Communication with stakeholders
- Post-incident review

**Contact**: oncall@mothership-ai.com

#### Technical Lead
**Responsibilities**:
- Technical investigation
- Root cause analysis
- Implementation of fixes
- Documentation

**Contact**: tech-lead@mothership-ai.com

#### Communications Lead
**Responsibilities**:
- Customer communication
- Status page updates
- Internal communication
- Media relations (if needed)

**Contact**: info@mothership-ai.com

#### Security Lead
**Responsibilities**:
- Security incident investigation
- Forensics and evidence collection
- Compliance reporting
- Security remediation

**Contact**: security@mothership-ai.com

### On-Call Rotation

**Primary On-Call**:
- Phone: +1 (XXX) XXX-XXXX
- Email: oncall@mothership-ai.com
- PagerDuty: agentguard-oncall

**Backup On-Call**:
- Phone: +1 (XXX) XXX-XXXX
- Email: backup-oncall@mothership-ai.com

**Schedule**: 7-day rotation, 24/7 coverage

---

## Incident Response Process

### Phase 1: Detection & Triage (0-15 minutes)

#### 1.1 Detection Sources
- Automated monitoring alerts (Sentry, Render)
- Customer reports
- Internal team reports
- Security scans
- Health check failures

#### 1.2 Initial Assessment
1. **Acknowledge Alert**
   - Respond to PagerDuty/Slack alert
   - Log into incident management system
   - Create incident ticket

2. **Assess Severity**
   - Determine impact (users affected, services down)
   - Classify severity (P0-P3)
   - Identify affected systems

3. **Assemble Team**
   - Page Incident Commander (P0/P1)
   - Page Technical Lead
   - Page Communications Lead (P0 only)
   - Create incident Slack channel: `#incident-YYYYMMDD-HHMM`

#### 1.3 Initial Communication
```
Incident: [Title]
Severity: P0/P1/P2/P3
Status: Investigating
Impact: [Description]
Started: [Timestamp]
IC: [Name]
```

### Phase 2: Investigation & Containment (15-60 minutes)

#### 2.1 Investigation
1. **Gather Information**
   ```bash
   # Check API health
   curl https://agentguard-api.onrender.com/health | jq
   
   # Check logs
   # In Render dashboard: Logs tab
   
   # Check Sentry errors
   # In Sentry dashboard: Issues
   
   # Check metrics
   curl https://agentguard-api.onrender.com/metrics
   ```

2. **Identify Root Cause**
   - Review recent deployments
   - Check infrastructure changes
   - Analyze error patterns
   - Review external dependencies

3. **Document Findings**
   - Update incident ticket
   - Log all actions taken
   - Note timestamps

#### 2.2 Containment
1. **Stop the Bleeding**
   - Rollback recent deployment if needed
   - Disable affected feature
   - Scale resources if needed
   - Block malicious traffic

2. **Prevent Spread**
   - Isolate affected systems
   - Rotate credentials if security incident
   - Enable maintenance mode if needed

3. **Communicate Status**
   ```
   Update: [Description of findings]
   Action: [What we're doing]
   ETA: [Expected resolution time]
   ```

### Phase 3: Resolution & Recovery (1-4 hours)

#### 3.1 Implement Fix
1. **Develop Solution**
   - Code fix
   - Configuration change
   - Infrastructure scaling
   - Security patch

2. **Test Fix**
   - Test in staging environment
   - Verify fix resolves issue
   - Check for side effects

3. **Deploy Fix**
   - Deploy to production
   - Monitor for issues
   - Verify resolution

#### 3.2 Verify Recovery
1. **Health Checks**
   ```bash
   # API health
   curl https://agentguard-api.onrender.com/health
   
   # Test critical endpoints
   curl -X POST https://agentguard-api.onrender.com/test-agent \
     -H "Content-Type: application/json" \
     -d '{"agent_output":"test","ground_truth":"test"}'
   ```

2. **Monitor Metrics**
   - Error rate < 1%
   - Response time normal
   - No new alerts

3. **Customer Verification**
   - Test from customer perspective
   - Verify reported issues resolved

#### 3.3 Communicate Resolution
```
RESOLVED: [Incident Title]

The incident has been resolved. All services are operating normally.

Root Cause: [Brief description]
Resolution: [What we did]
Duration: [Total time]

We apologize for any inconvenience. A full post-mortem will be published within 48 hours.
```

### Phase 4: Post-Incident Review (24-48 hours)

#### 4.1 Post-Mortem Meeting
**Attendees**: IC, Technical Lead, affected team members

**Agenda**:
1. Timeline review
2. Root cause analysis
3. What went well
4. What could be improved
5. Action items

#### 4.2 Post-Mortem Document
See [Post-Incident Review Template](#post-incident-review-template)

#### 4.3 Follow-Up Actions
- Implement preventive measures
- Update runbooks
- Improve monitoring
- Schedule follow-up review

---

## Incident Types & Procedures

### 1. Complete Service Outage (P0)

**Symptoms**:
- API returning 5xx errors
- Health check failing
- No response from service

**Immediate Actions**:
1. Check Render service status
2. Check recent deployments
3. Check database connectivity
4. Check external dependencies

**Resolution Steps**:
```bash
# 1. Check service logs
# In Render dashboard: Logs tab

# 2. Check health endpoint
curl https://agentguard-api.onrender.com/health

# 3. Restart service if hung
# In Render dashboard: Manual Deploy → Restart

# 4. Rollback if recent deployment
# In Render dashboard: Rollback to previous version

# 5. Scale up if resource exhaustion
# In Render dashboard: Scale → Increase instances
```

**Communication**:
- Update status page immediately
- Send email to all customers
- Post on social media if widespread

### 2. Data Breach (P0)

**Symptoms**:
- Unauthorized access detected
- Data exfiltration alerts
- Security scan findings
- Customer reports

**Immediate Actions**:
1. **Contain**
   - Isolate affected systems
   - Revoke compromised credentials
   - Enable maintenance mode

2. **Assess**
   - Determine scope of breach
   - Identify affected data
   - Identify attack vector

3. **Notify**
   - Management (immediate)
   - Legal team (immediate)
   - Affected customers (within 72 hours)
   - Regulatory authorities (as required)

**Resolution Steps**:
```bash
# 1. Rotate all secrets
./scripts/rotate_secrets.sh --emergency

# 2. Review access logs
# Check for unauthorized access patterns

# 3. Patch vulnerability
# Implement security fix

# 4. Verify no backdoors
# Security audit of all systems

# 5. Monitor for further attempts
# Enhanced logging and alerting
```

**Communication**:
```
SECURITY INCIDENT NOTIFICATION

We are writing to inform you of a security incident that may have affected your data.

What Happened: [Description]
What Data Was Affected: [PII types]
What We're Doing: [Response actions]
What You Should Do: [Customer actions]

We take security very seriously and are taking all necessary steps to prevent future incidents.

For questions: security@mothership-ai.com
```

### 3. DDoS Attack (P0)

**Symptoms**:
- Sudden spike in traffic
- Service degradation
- Cloudflare DDoS alerts
- Legitimate users unable to access

**Immediate Actions**:
1. **Verify Attack**
   - Check Cloudflare analytics
   - Analyze traffic patterns
   - Identify attack vectors

2. **Enable Protection**
   - Activate Cloudflare "Under Attack" mode
   - Enable additional rate limiting
   - Block malicious IPs

3. **Scale Infrastructure**
   - Increase server capacity
   - Enable auto-scaling
   - Distribute load

**Resolution Steps**:
```bash
# 1. Enable Cloudflare "Under Attack" mode
# In Cloudflare dashboard: Security → Settings → Under Attack Mode

# 2. Analyze attack pattern
# In Cloudflare dashboard: Analytics → Security

# 3. Create firewall rules to block attack
# In Cloudflare dashboard: Security → WAF → Firewall rules

# 4. Monitor for attack cessation
# Watch traffic patterns return to normal

# 5. Gradually relax protections
# Disable "Under Attack" mode when safe
```

### 4. Database Failure (P0)

**Symptoms**:
- Database connection errors
- Data corruption
- Slow queries
- Disk space full

**Immediate Actions**:
1. **Assess Damage**
   - Check database status
   - Verify data integrity
   - Check available space

2. **Restore Service**
   - Restart database if hung
   - Clear disk space if full
   - Failover to replica if available

3. **Restore Data**
   - Restore from backup if corrupted
   - Verify data integrity
   - Test critical queries

**Resolution Steps**:
```bash
# 1. Check database status
psql $DATABASE_URL -c "SELECT version();"

# 2. Check disk space
psql $DATABASE_URL -c "SELECT pg_database_size('agentguard');"

# 3. Restore from backup if needed
./scripts/restore_database.sh backup_YYYYMMDD_HHMMSS

# 4. Verify data integrity
psql $DATABASE_URL -c "SELECT count(*) FROM detection_results;"

# 5. Resume normal operations
# Restart API service
```

### 5. External API Failure (P1)

**Symptoms**:
- Claude API errors
- Stripe API errors
- Timeouts from external services

**Immediate Actions**:
1. **Verify Outage**
   - Check external service status pages
   - Test API directly
   - Check rate limits

2. **Enable Fallbacks**
   - Use cached responses if available
   - Switch to backup provider
   - Queue requests for retry

3. **Communicate**
   - Update customers on impact
   - Provide ETA based on external status

**Resolution Steps**:
```bash
# 1. Check external service status
curl https://status.anthropic.com
curl https://status.stripe.com

# 2. Test API directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_API_KEY" \
  -H "anthropic-version: 2023-06-01"

# 3. Monitor for restoration
# Watch external status pages

# 4. Resume normal operations
# Verify API calls succeeding
```

### 6. Performance Degradation (P1)

**Symptoms**:
- Slow response times (P95 > 500ms)
- High CPU/memory usage
- Database slow queries
- External API latency

**Immediate Actions**:
1. **Identify Bottleneck**
   - Check system metrics
   - Profile slow endpoints
   - Review database queries

2. **Quick Fixes**
   - Scale up resources
   - Clear cache
   - Kill long-running queries

3. **Monitor Impact**
   - Track response times
   - Monitor error rates
   - Check customer reports

**Resolution Steps**:
```bash
# 1. Check system metrics
# In Render dashboard: Metrics tab

# 2. Identify slow queries
psql $DATABASE_URL -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 3. Scale resources
# In Render dashboard: Scale → Increase plan

# 4. Optimize queries
# Add indexes, optimize code

# 5. Verify performance
# Run load tests to confirm improvement
```

---

## Communication Templates

### Internal Communication (Slack)

#### Incident Start
```
🚨 INCIDENT DECLARED 🚨

Severity: P0
Title: Complete API Outage
Impact: All API endpoints returning 503
Started: 2025-10-24 14:30 UTC
IC: @john-doe
Channel: #incident-20251024-1430

All hands on deck. Join the incident channel.
```

#### Status Update
```
📊 INCIDENT UPDATE

Status: Investigating
Findings: Database connection pool exhausted
Action: Increasing connection pool size and restarting service
ETA: 15 minutes

Next update in 15 minutes or when resolved.
```

#### Resolution
```
✅ INCIDENT RESOLVED

Duration: 45 minutes
Root Cause: Database connection pool exhaustion
Resolution: Increased pool size from 10 to 50 connections

Post-mortem will be published within 48 hours.
Thank you to everyone who helped resolve this quickly.
```

### Customer Communication (Email)

#### Incident Notification
```
Subject: Service Disruption - AgentGuard API

Dear AgentGuard Customer,

We are currently experiencing a service disruption affecting the AgentGuard API. Our team is actively working to resolve the issue.

Impact: All API endpoints are currently unavailable
Started: October 24, 2025 at 2:30 PM UTC
Status: Investigating

We will provide updates every 30 minutes until resolved.

For real-time updates, visit: https://status.mothership-ai.com

We apologize for the inconvenience.

Mothership AI Team
info@mothership-ai.com
```

#### Resolution Notification
```
Subject: Resolved - Service Disruption - AgentGuard API

Dear AgentGuard Customer,

The service disruption affecting the AgentGuard API has been resolved. All services are now operating normally.

Duration: 45 minutes (2:30 PM - 3:15 PM UTC)
Root Cause: Database connection pool exhaustion
Resolution: Increased connection pool capacity

We have implemented additional monitoring to prevent similar issues in the future. A detailed post-mortem will be published within 48 hours.

We sincerely apologize for the disruption and appreciate your patience.

Mothership AI Team
info@mothership-ai.com
```

### Status Page Updates

#### Investigating
```
🔍 Investigating

We are investigating reports of API unavailability. Our team is actively working to identify the root cause.

Last Updated: 2:35 PM UTC
```

#### Identified
```
🔎 Identified

We have identified the issue as database connection pool exhaustion. We are implementing a fix.

Last Updated: 2:45 PM UTC
```

#### Monitoring
```
👀 Monitoring

A fix has been deployed and we are monitoring the situation. Services appear to be recovering.

Last Updated: 3:10 PM UTC
```

#### Resolved
```
✅ Resolved

The incident has been resolved. All services are operating normally. We will publish a post-mortem within 48 hours.

Last Updated: 3:15 PM UTC
```

---

## Post-Incident Review

### Post-Incident Review Template

```markdown
# Post-Incident Review: [Incident Title]

**Date**: YYYY-MM-DD  
**Severity**: P0/P1/P2/P3  
**Duration**: X hours Y minutes  
**Incident Commander**: [Name]

## Summary

[Brief 2-3 sentence summary of what happened]

## Timeline

| Time (UTC) | Event |
|------------|-------|
| 14:30 | Incident detected via monitoring alert |
| 14:32 | IC paged, incident channel created |
| 14:35 | Root cause identified (database connection pool) |
| 14:45 | Fix implemented (increased pool size) |
| 14:50 | Service restarted |
| 15:00 | Monitoring shows recovery |
| 15:15 | Incident resolved |

## Root Cause

[Detailed explanation of what caused the incident]

Example:
The database connection pool was configured with a maximum of 10 connections. During a traffic spike, all connections were exhausted, causing new requests to fail with "connection pool timeout" errors.

## Impact

- **Users Affected**: 100% of API users
- **Duration**: 45 minutes
- **Failed Requests**: ~2,700 (estimated)
- **Revenue Impact**: $500 (estimated)

## What Went Well

1. Monitoring detected the issue immediately
2. IC responded within 2 minutes
3. Root cause identified quickly
4. Fix deployed rapidly
5. Communication was clear and timely

## What Could Be Improved

1. Connection pool size should have been higher from the start
2. Load testing should have caught this issue
3. Auto-scaling for database connections not configured
4. Status page update was delayed by 5 minutes

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| Increase connection pool to 50 | @tech-lead | P0 | Completed | ✅ |
| Implement connection pool monitoring | @tech-lead | P0 | 2025-10-25 | 🔄 |
| Add load test for high connection usage | @qa-lead | P1 | 2025-10-27 | 📋 |
| Configure auto-scaling for connections | @devops | P1 | 2025-10-30 | 📋 |
| Update runbook with connection pool troubleshooting | @tech-lead | P2 | 2025-11-01 | 📋 |

## Lessons Learned

1. **Capacity Planning**: Always plan for 3-5x expected load
2. **Load Testing**: Comprehensive load testing is critical
3. **Monitoring**: Monitor all resource pools (connections, memory, etc.)
4. **Documentation**: Keep runbooks up to date

## Follow-Up

- Post-mortem review meeting: 2025-10-25 at 10:00 AM
- Customer communication: Email sent, blog post published
- Preventive measures: Action items tracked in Jira
```

---

## Appendices

### Appendix A: Contact List

| Role | Name | Email | Phone | PagerDuty |
|------|------|-------|-------|-----------|
| Incident Commander | TBD | oncall@mothership-ai.com | +1-XXX-XXX-XXXX | agentguard-oncall |
| Technical Lead | TBD | tech-lead@mothership-ai.com | +1-XXX-XXX-XXXX | agentguard-tech |
| Security Lead | TBD | security@mothership-ai.com | +1-XXX-XXX-XXXX | agentguard-security |
| Communications | TBD | info@mothership-ai.com | +1-XXX-XXX-XXXX | N/A |
| Management | TBD | management@mothership-ai.com | +1-XXX-XXX-XXXX | N/A |

### Appendix B: Useful Commands

```bash
# Health check
curl https://agentguard-api.onrender.com/health | jq

# Metrics
curl https://agentguard-api.onrender.com/metrics

# Test critical endpoint
curl -X POST https://agentguard-api.onrender.com/test-agent \
  -H "Content-Type: application/json" \
  -d '{"agent_output":"test","ground_truth":"test"}'

# Database health
psql $DATABASE_URL -c "SELECT 1;"

# Redis health
redis-cli ping

# Check recent deployments
# In Render dashboard: Events tab

# Rollback deployment
# In Render dashboard: Rollback button

# Restart service
# In Render dashboard: Manual Deploy → Restart
```

### Appendix C: External Resources

- **Render Dashboard**: https://dashboard.render.com/
- **Sentry Dashboard**: https://sentry.io/organizations/mothership-ai/
- **Cloudflare Dashboard**: https://dash.cloudflare.com/
- **Stripe Dashboard**: https://dashboard.stripe.com/
- **Claude Status**: https://status.anthropic.com/
- **GitHub**: https://github.com/mothership-ai/agentguard

### Appendix D: Compliance Requirements

#### GDPR (Data Breach Notification)
- **Timeline**: Notify supervisory authority within 72 hours
- **Content**: Nature of breach, affected data, likely consequences, measures taken
- **Contact**: DPA in relevant EU member state

#### HIPAA (if applicable)
- **Timeline**: Notify HHS within 60 days
- **Content**: Description of breach, types of information, steps taken
- **Contact**: HHS Office for Civil Rights

#### SOC 2 (if certified)
- **Timeline**: Notify auditor immediately
- **Content**: Incident details, impact on controls
- **Contact**: SOC 2 auditor

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

