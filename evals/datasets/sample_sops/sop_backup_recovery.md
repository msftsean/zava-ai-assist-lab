# System Backup and Recovery Procedures

**Document ID:** SOP-BKP-001
**Version:** 2.1
**Effective Date:** 2024-01-15
**Review Date:** 2025-01-15
**Owner:** IT Operations Manager

---

## 1. Purpose

This Standard Operating Procedure (SOP) defines the processes and responsibilities for performing system backups and restoring data in the event of hardware failure, software corruption, or disaster recovery scenarios.

## 2. Scope

This procedure applies to all production and staging systems managed by the IT Operations team, including:

- Application servers
- Database servers (PostgreSQL, SQL Server)
- File storage systems
- Configuration management repositories

## 3. Backup Schedule

### 3.1 Full Backups

Full system backups are performed **every Sunday at 02:00 UTC**. Full backups capture the entire state of each system, including operating system files, application data, and database contents.

### 3.2 Incremental Backups

Incremental backups run **nightly at 02:00 UTC** on Monday through Saturday. Only data changed since the last backup (full or incremental) is captured.

### 3.3 Database-Specific Backups

PostgreSQL databases use `pg_dump` for logical backups and WAL archiving for continuous point-in-time recovery. Database backups run every **6 hours** (00:00, 06:00, 12:00, 18:00 UTC).

## 4. Backup Storage

- **Primary target:** Azure Blob Storage (geo-redundant, GRS)
- **Secondary target:** On-premises NAS for rapid restore
- **Retention period:** 30 days for incremental, 90 days for full backups
- **Encryption:** AES-256 at rest, TLS 1.2+ in transit

## 5. Recovery Objectives

| Metric | Target |
|--------|--------|
| Recovery Time Objective (RTO) | 4 hours for critical systems |
| Recovery Point Objective (RPO) | 1 hour for databases, 24 hours for file systems |

## 6. Backup Verification

1. **Automated integrity checks** run after every backup using SHA-256 checksums.
2. **Monthly restore drills** are conducted to verify backup recoverability.
3. **Quarterly full-system restore tests** are performed in an isolated environment.

## 7. Procedure

### 7.1 Pre-Backup Checks

1. Verify sufficient disk space on the backup target (minimum 20% free).
2. Confirm that no conflicting maintenance windows are scheduled.
3. Check the status of the previous backup job for errors.

### 7.2 Executing the Backup

1. Initiate the backup job via the central management console (Azure Backup or Veeam).
2. Monitor the backup progress dashboard for errors or warnings.
3. Validate backup integrity using automated checksum verification.
4. Record the backup status, duration, and size in the operations log.

### 7.3 Recovery Procedure

1. Identify the most recent valid backup for the affected system.
2. Notify stakeholders of the estimated recovery time.
3. Restore data to the target environment (production or staging).
4. Validate the restored system's functionality with smoke tests.
5. Update the incident ticket with recovery details.

## 8. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| IT Operations Manager | Approve backup policy changes |
| Backup Administrator | Execute and monitor backup jobs |
| Database Administrator | Manage database-specific backups |
| Security Officer | Verify encryption compliance |

## 9. Escalation

If a backup job fails:

1. Retry the job within 1 hour.
2. If retry fails, escalate to the Backup Administrator.
3. If unresolved within 4 hours, escalate to the IT Operations Manager.
4. Document the failure and resolution in the incident management system.

## 10. References

- Azure Backup documentation: https://learn.microsoft.com/azure/backup/
- NIST SP 800-34 Rev. 1: Contingency Planning Guide
- Organisation Disaster Recovery Plan (DRP-001)
