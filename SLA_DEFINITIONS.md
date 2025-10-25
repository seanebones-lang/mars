# Service Level Agreement (SLA)

**Mothership AI - AgentGuard**  
**Product:** watcher.mothership-ai.com  
**Contact:** info@mothership-ai.com

**Effective Date**: January 1, 2026

---

## Overview

This Service Level Agreement (SLA) defines the performance and availability commitments for the AgentGuard platform.

---

## Service Availability

### Uptime Commitment

| Tier | Monthly Uptime | Downtime/Month | Downtime/Year |
|------|----------------|----------------|---------------|
| **Standard** | 99.5% | 3.6 hours | 43.8 hours |
| **Professional** | 99.9% | 43.2 minutes | 8.76 hours |
| **Enterprise** | 99.95% | 21.6 minutes | 4.38 hours |

**Measurement Period**: Calendar month (UTC)

**Exclusions** (not counted as downtime):
- Scheduled maintenance (with 7 days notice)
- Customer-caused issues
- Force majeure events
- Third-party service failures (Claude API, Stripe, etc.)
- DDoS attacks (beyond reasonable mitigation)

### Availability Calculation

```
Availability % = (Total Minutes - Downtime Minutes) / Total Minutes × 100
```

**Example**:
- Total minutes in month: 43,200
- Downtime: 30 minutes
- Availability: (43,200 - 30) / 43,200 × 100 = 99.93%

---

## Performance Commitments

### Response Time

| Endpoint Type | P50 | P95 | P99 |
|---------------|-----|-----|-----|
| **Health Check** | < 10ms | < 20ms | < 50ms |
| **Simple Detection** | < 100ms | < 200ms | < 500ms |
| **Complex Detection** | < 500ms | < 1000ms | < 2000ms |
| **Multimodal Detection** | < 1000ms | < 2000ms | < 5000ms |

**Measurement**: Based on server-side processing time (excludes network latency)

### Throughput

| Tier | Requests/Second | Concurrent Users |
|------|-----------------|------------------|
| **Standard** | 100 | 1,000 |
| **Professional** | 1,000 | 10,000 |
| **Enterprise** | Custom | Custom |

### Error Rate

**Target**: < 1% of all requests

**Exclusions**:
- Client errors (4xx) caused by invalid requests
- Rate limiting (429) responses
- Intentional rejections (e.g., detected attacks)

---

## Support Response Times

### Incident Response

| Severity | First Response | Resolution Target |
|----------|----------------|-------------------|
| **P0 - Critical** | 15 minutes | 4 hours |
| **P1 - High** | 30 minutes | 8 hours |
| **P2 - Medium** | 2 hours | 24 hours |
| **P3 - Low** | 24 hours | 5 business days |

### Support Channels

| Tier | Email | Chat | Phone | Dedicated Support |
|------|-------|------|-------|-------------------|
| **Standard** | ✅ | ❌ | ❌ | ❌ |
| **Professional** | ✅ | ✅ | ✅ | ❌ |
| **Enterprise** | ✅ | ✅ | ✅ | ✅ |

**Support Hours**:
- Standard: Business hours (9 AM - 5 PM EST, Monday-Friday)
- Professional: 24/7 for P0/P1 incidents
- Enterprise: 24/7 for all incidents

---

## Data Protection

### Backup Frequency

- **Database**: Daily automated backups
- **Retention**: 30 days local, 90 days S3
- **Recovery Point Objective (RPO)**: 24 hours
- **Recovery Time Objective (RTO)**: 4 hours

### Data Security

- **Encryption at Rest**: AES-256
- **Encryption in Transit**: TLS 1.3
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: All access logged and retained for 1 year

---

## Service Credits

### Credit Calculation

If we fail to meet the uptime commitment, you are eligible for service credits:

| Monthly Uptime | Service Credit |
|----------------|----------------|
| 99.9% - 99.5% | 10% |
| 99.5% - 99.0% | 25% |
| < 99.0% | 50% |

**Example**:
- Monthly fee: $1,000
- Actual uptime: 99.3%
- Credit: $100 (10%)

### Credit Claim Process

1. Submit claim within 30 days of incident
2. Provide evidence of downtime
3. Credits applied to next month's invoice
4. Maximum credit: 50% of monthly fee

---

## Maintenance Windows

### Scheduled Maintenance

- **Frequency**: Monthly
- **Duration**: Maximum 2 hours
- **Notice**: 7 days advance notice
- **Window**: Sundays 2:00 AM - 4:00 AM UTC (lowest traffic period)

### Emergency Maintenance

- **Notice**: Best effort (minimum 1 hour if possible)
- **Reason**: Critical security patches, urgent bug fixes
- **Duration**: As short as possible

---

## Monitoring & Reporting

### Real-Time Status

- **Status Page**: https://status.mothership-ai.com
- **Updates**: Real-time during incidents
- **History**: 90-day incident history

### Monthly Reports

Professional and Enterprise tiers receive monthly reports including:
- Uptime percentage
- Performance metrics (P50, P95, P99)
- Error rates
- Incident summary
- Capacity utilization

---

## Limitations & Exclusions

### Not Covered by SLA

1. **Alpha/Beta Features**: Experimental features marked as "beta"
2. **Free Tier**: Free tier has no SLA guarantees
3. **Customer Issues**: Problems caused by customer code or configuration
4. **Third-Party Services**: Failures of external dependencies (Claude API, Stripe, etc.)
5. **Force Majeure**: Natural disasters, war, terrorism, etc.
6. **DDoS Attacks**: Beyond reasonable mitigation efforts
7. **Scheduled Maintenance**: With proper notice

### Customer Responsibilities

To qualify for SLA credits, customers must:
1. Use the service in accordance with documentation
2. Implement proper error handling and retries
3. Report issues promptly
4. Cooperate with troubleshooting
5. Maintain current contact information

---

## Changes to SLA

We may modify this SLA with 30 days notice. Changes will be posted on our website and communicated via email.

---

## Contact

For SLA-related questions or credit claims:
- **Email**: sla@mothership-ai.com
- **Support Portal**: https://support.mothership-ai.com
- **Phone**: +1 (XXX) XXX-XXXX (Professional/Enterprise only)

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-24 | Initial version |

**Last Updated**: October 24, 2025  
**Next Review**: January 24, 2026

---

**Mothership AI**  
[mothership-ai.com](https://mothership-ai.com) • [watcher.mothership-ai.com](https://watcher.mothership-ai.com) • [info@mothership-ai.com](mailto:info@mothership-ai.com)

