# Incident Response Procedures

**Document ID:** SOP-IR-001
**Version:** 3.0
**Effective Date:** 2024-03-01
**Review Date:** 2025-03-01
**Owner:** Chief Information Security Officer (CISO)

---

## 1. Purpose

This Standard Operating Procedure (SOP) establishes the framework for detecting, responding to, and recovering from information security incidents affecting organisational systems and data.

## 2. Scope

This procedure applies to all personnel, contractors, and third-party partners who access organisational information systems. It covers incidents including but not limited to:

- Unauthorised access or privilege escalation
- Malware or ransomware infections
- Data breaches or data exfiltration
- Denial-of-service (DoS) attacks
- Insider threats
- Physical security breaches affecting IT assets

## 3. Incident Classification

### 3.1 Severity Levels

| Level | Description | Response Time |
|-------|------------|---------------|
| **Critical (P1)** | Active data breach, ransomware, or complete service outage | 15 minutes |
| **High (P2)** | Partial service degradation, suspected breach, privilege escalation | 1 hour |
| **Medium (P3)** | Malware detection on non-critical systems, policy violations | 4 hours |
| **Low (P4)** | Informational alerts, minor policy deviations | Next business day |

## 4. Incident Response Phases

### 4.1 Phase 1 — Detection and Identification

1. **Identify** the incident through monitoring alerts, user reports, or automated detection tools (Azure Sentinel, Microsoft Defender).
2. **Classify** the incident severity using the table in Section 3.1.
3. **Document** initial findings in the incident management system (ticket ID, timestamp, affected systems).
4. **Notify** the Incident Response Team (IRT) lead.

### 4.2 Phase 2 — Containment

1. **Short-term containment:** Isolate affected systems from the network to prevent lateral movement. This may include disabling network ports, blocking IP addresses, or suspending user accounts.
2. **Evidence preservation:** Capture forensic images, memory dumps, and log snapshots before remediation alters the evidence.
3. **Long-term containment:** Apply temporary patches, firewall rules, or access restrictions while a permanent fix is developed.

### 4.3 Phase 3 — Eradication

1. **Root cause analysis:** Determine how the incident occurred (vulnerability, misconfiguration, social engineering, etc.).
2. **Remove** the threat (malware, backdoors, compromised accounts).
3. **Patch** the underlying vulnerability or close the attack vector.
4. **Verify** that eradication is complete by re-scanning affected systems.

### 4.4 Phase 4 — Recovery

1. **Restore** affected systems from verified clean backups (see SOP-BKP-001).
2. **Validate** system functionality with smoke tests and integrity checks.
3. **Monitor** restored systems closely for 72 hours for signs of re-infection.
4. **Gradually restore** normal operations and remove temporary containment measures.

### 4.5 Phase 5 — Post-Incident Review

1. Conduct a **post-incident review meeting** within 5 business days of resolution.
2. Document **lessons learned**, including what worked well and what needs improvement.
3. Update security controls, procedures, and training materials as needed.
4. Produce a **formal incident report** for management and compliance records.
5. Track follow-up **remediation actions** to completion.

## 5. Communication Plan

| Audience | When | Method |
|----------|------|--------|
| IRT Lead | Immediately upon detection | Phone / Teams |
| CISO | Within 30 minutes of P1/P2 | Phone / Teams |
| Executive Leadership | Within 2 hours of P1 | Briefing |
| Affected Users | After containment confirmed | Email notification |
| Legal / Compliance | If data breach confirmed | Formal notification |

## 6. Roles and Responsibilities

| Role | Responsibility |
|------|---------------|
| CISO | Overall incident response authority |
| IRT Lead | Coordinate response activities |
| Security Analysts | Investigate and contain the incident |
| System Administrators | Execute containment and recovery actions |
| Communications Officer | Manage internal and external notifications |
| Legal Counsel | Advise on regulatory reporting obligations |

## 7. Tools and Resources

- **SIEM:** Azure Sentinel
- **EDR:** Microsoft Defender for Endpoint
- **Forensics:** Azure Security Centre, FTK Imager
- **Ticketing:** ServiceNow
- **Communication:** Microsoft Teams (dedicated Incident channel)

## 8. Training

All personnel must complete annual incident response awareness training. The IRT conducts tabletop exercises quarterly.

## 9. References

- NIST SP 800-61 Rev. 2: Computer Security Incident Handling Guide
- CISA Incident Response Playbooks
- Organisation Information Security Policy (ISP-001)
