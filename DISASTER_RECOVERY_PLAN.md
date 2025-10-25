# Disaster Recohighly Plan

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**P0-Critical: Complete disaster recohighly procedures**

---

## Overview

This document outlines the disaster recohighly (DR) procedures for the AgentGuard platform. It covers backup strategies, recohighly procedures, and business continuity plans.

### Recohighly Time Objectives (RTO)

- **Critical Services**: 1 hour
- **Database**: 2 hours
- **Full System**: 4 hours
- **Complete Rebuild**: 24 hours

### Recohighly Point Objectives (RPO)

- **Database**: 24 hours (daily backups)
- **Configuration**: 1 hour (version controlled)
- **User Data**: 24 hours (daily backups)

---

## Backup Strategy

### Automated Backups

#### Database Backups
- **Frequency**: Daily at 2:00 AM UTC
- **Retention**: 30 days local, 90 days S3
- **Location**: `/var/backups/agentguard/` and S3 bucket
- **Format**: PostgreSQL custom format with gzip compression
- **Script**: `scripts/backup_database.sh`

#### Configuration Backups
- **Frequency**: On ehighly deployment
- **Retention**: Indefinite (Git history)
- **Location**: GitHub repository
- **Format**: Git commits

#### Application Data
- **Frequency**: Daily at 3:00 AM UTC
- **Retention**: 30 days
- **Location**: S3 bucket
- **Format**: Tar.gz archives

### Manual Backup Procedures

```bash
# Immediate database backup
./scripts/backup_database.sh emergency_backup_$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh /var/backups/agentguard/

# Upload to S3
aws s3 sync /var/backups/agentguard/ s3://agentguard-backups/manual/
```

---

## Disaster Scenarios & Recohighly Procedures

### Scenario 1: Database Corruption

**Symptoms**: Database errors, data inconsistencies, failed queries

**Recohighly Steps**:

1. **Assess Damage**
   ```bash
   # Check database status
   psql $DATABASE_URL -c "SELECT version();"
   
   # Check table integrity
   psql $DATABASE_URL -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
   ```

2. **Identify Latest Good Backup**
   ```bash
   ls -lt /var/backups/agentguard/*.sql.gz | head -5
   ```

3. **Restore Database**
   ```bash
   # CRITICAL: This will overwrite current database
   ./scripts/restore_database.sh backup_YYYYMMDD_HHMMSS
   ```

4. **Verify Restoration**
   ```bash
   # Check health endpoint
   curl https://agentguard-api.onrender.com/health
   
   # Verify data integrity
   psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"
   ```

5. **Resume Operations**
   - Monitor error logs for 1 hour
   - Notify customers of any data loss
   - Update incident log

**Expected Recohighly Time**: 2 hours  
**Data Loss**: Up to 24 hours (last backup)

---

### Scenario 2: Complete System Failure

**Symptoms**: API unreachable, all services down, infrastructure failure

**Recohighly Steps**:

1. **Assess Infrastructure**
   ```bash
   # Check Render status
   curl https://status.render.com/
   
   # Check DNS
   dig agentguard-api.onrender.com
   ```

2. **Deploy to Backup Infrastructure**
   
   **Option A: Render Recovery**
   ```bash
   # Trigger manual deployment
   curl -X POST $RENDER_DEPLOY_HOOK_PRODUCTION
   
   # Wait for deployment
   sleep 120
   
   # Verify health
   curl https://agentguard-api.onrender.com/health
   ```
   
   **Option B: Kubernetes Failover**
   ```bash
   # Deploy to K8s cluster
   kubectl apply -f k8s/
   
   # Check pods
   kubectl get pods -n agentguard
   
   # Expose service
   kubectl expose deployment agentguard-api --type=LoadBalancer
   ```

3. **Restore Database**
   ```bash
   # Download latest backup from S3
   aws s3 cp s3://agentguard-backups/backups/latest.sql.gz /tmp/
   
   # Restore
   ./scripts/restore_database.sh latest
   ```

4. **Verify All Services**
   ```bash
   # Run health checks
   curl https://agentguard-api.onrender.com/health
   curl https://agentguard-ui.onrender.com/
   
   # Test critical endpoints
   curl -X POST https://agentguard-api.onrender.com/test-agent \
     -H "Content-Type: application/json" \
     -d '{"agent_output":"test","ground_truth":"test"}'
   ```

5. **Update DNS (if needed)**
   ```bash
   # Point to new infrastructure
   # Update DNS records at domain registrar
   ```

**Expected Recohighly Time**: 4 hours  
**Data Loss**: Up to 24 hours

---

### Scenario 3: Data Breach / Security Incident

**Symptoms**: Unauthorized access, data exfiltration, compromised credentials

**Immediate Actions** (within 15 minutes):

1. **Isolate System**
   ```bash
   # Disable API access
   # Update Render environment: MAINTENANCE_MODE=true
   
   # Rotate all secrets immediately
   ./scripts/rotate_secrets.sh --emergency
   ```

2. **Assess Breach**
   - Check access logs
   - Identify compromised data
   - Determine breach timeline

3. **Notify Stakeholders**
   - Security team
   - Legal team
   - Affected customers (if PII exposed)
   - Regulatory authorities (if required)

4. **Forensic Analysis**
   - Preserve logs
   - Capture system state
   - Document all findings

5. **Remediation**
   - Patch vulnerabilities
   - Reset all credentials
   - Restore from clean backup
   - Implement additional security measures

**Expected Recohighly Time**: 24-72 hours  
**Compliance**: GDPR notification within 72 hours if PII affected

---

### Scenario 4: Accidental Data Deletion

**Symptoms**: Missing data, user reports, application errors

**Recohighly Steps**:

1. **Stop Further Damage**
   ```bash
   # Enable read-only mode
   psql $DATABASE_URL -c "ALTER DATABASE agentguard SET default_transaction_read_only = on;"
   ```

2. **Identify Deletion Scope**
   ```bash
   # Check recent activity
   psql $DATABASE_URL -c "SELECT * FROM audit_log WHERE action = 'DELETE' ORDER BY timestamp DESC LIMIT 100;"
   ```

3. **Point-in-Time Recohighly (if available)**
   ```bash
   # Restore to specific timestamp
   # This requires continuous archiving (WAL)
   pg_restore --time "2025-10-24 14:30:00" ...
   ```

4. **Selective Data Recovery**
   ```bash
   # Extract specific data from backup
   pg_restore -t specific_table backup_file.sql.gz
   ```

5. **Verify and Resume**
   ```bash
   # Disable read-only mode
   psql $DATABASE_URL -c "ALTER DATABASE agentguard SET default_transaction_read_only = off;"
   
   # Verify data
   # Resume operations
   ```

**Expected Recohighly Time**: 1-3 hours  
**Data Loss**: Minimal (specific to deleted data)

---

## Business Continuity

### Communication Plan

#### Internal Communication
- **Slack Channel**: #incident-response
- **Emergency Contact**: info@mothership-ai.com
- **On-Call Rotation**: PagerDuty

#### Customer Communication
- **Status Page**: status.mothership-ai.com
- **Email**: Automated notifications via SendGrid
- **Twitter**: @MothershipAI

### Incident Severity Levels

| Level | Description | Response Time | Notification |
|-------|-------------|---------------|--------------|
| P0 | Complete outage | 15 minutes | All stakeholders |
| P1 | Major degradation | 30 minutes | Technical team + management |
| P2 | Minor issues | 2 hours | Technical team |
| P3 | Non-critical | 24 hours | Technical team |

---

## Testing & Validation

### Quarterly DR Drills

**Schedule**: First Monday of each quarter

**Procedure**:
1. Announce drill to team
2. Simulate disaster scenario
3. Execute recohighly procedures
4. Document time taken
5. Identify improvements
6. Update DR plan

### Backup Verification

**Daily**:
- Automated backup integrity checks
- Size verification
- S3 upload confirmation

**Weekly**:
- Test restore to staging environment
- Verify data completeness
- Performance benchmarks

**Monthly**:
- Full system restore test
- Failover testing
- Documentation review

---

## Maintenance Windows

### Scheduled Maintenance
- **Frequency**: Monthly
- **Duration**: 2 hours
- **Time**: Sunday 2:00-4:00 AM UTC
- **Notification**: 7 days advance notice

### Emergency Maintenance
- **Approval**: CTO or designated on-call engineer
- **Notification**: Immediate via status page
- **Documentation**: Incident report within 24 hours

---

## Contact Information

### Emergency Contacts

**Primary On-Call**:
- Email: oncall@mothership-ai.com
- Phone: +1 (XXX) XXX-XXXX
- PagerDuty: agentguard-oncall

**Backup On-Call**:
- Email: backup-oncall@mothership-ai.com
- Phone: +1 (XXX) XXX-XXXX

**Management Escalation**:
- CTO: info@mothership-ai.com
- CEO: info@mothership-ai.com

### External Vendors

**Render.com Support**:
- Email: support@render.com
- Priority Support: Available 24/7

**AWS Support**:
- Console: https://console.aws.amazon.com/support
- Phone: 1-866-947-7829

**Database Expert** (if needed):
- PostgreSQL Consulting: TBD

---

## Appendix

### Backup Locations

**Local**:
```
/var/backups/agentguard/
├── backup_YYYYMMDD_HHMMSS.sql.gz
├── backup_YYYYMMDD_HHMMSS.meta.json
└── pre_restore_YYYYMMDD_HHMMSS.sql.gz
```

**S3**:
```
s3://agentguard-backups/
├── backups/
│   ├── backup_YYYYMMDD_HHMMSS.sql.gz
│   └── backup_YYYYMMDD_HHMMSS.meta.json
├── manual/
└── archives/
```

### Recohighly Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `backup_database.sh` | Create database backup | `scripts/` |
| `restore_database.sh` | Restore from backup | `scripts/` |
| `setup_backup_cron.sh` | Configure automated backups | `scripts/` |
| `verify_backup.sh` | Verify backup integrity | `scripts/` |

### Compliance Requirements

**GDPR**:
- Backup retention: 90 days maximum
- Data deletion: Within 30 days of request
- Breach notification: Within 72 hours

**HIPAA** (if applicable):
- Encrypted backups required
- Access logging mandatory
- Audit trail for all restorations

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AgentGuard Team | Initial version |

**Last Reviewed**: October 24, 2025  
**Next Review**: January 24, 2026  
**Owner**: DevOps Team

---

**Mothership AI**  
Building the future of AI safety

[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

