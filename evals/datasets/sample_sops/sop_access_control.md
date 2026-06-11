# Access Control and Identity Management

**Document ID:** SOP-AC-001
**Version:** 2.0
**Effective Date:** 2024-02-01
**Review Date:** 2025-02-01
**Owner:** Identity and Access Management (IAM) Team Lead

---

## 1. Purpose

This Standard Operating Procedure (SOP) defines the policies and procedures for managing user identities, authentication, and authorisation across all organisational information systems. It ensures compliance with the principle of least privilege and separation of duties.

## 2. Scope

Applies to:

- All employees, contractors, and third-party users
- All production, staging, and development environments
- Azure Government cloud resources and on-premises systems
- Service accounts and automated processes

## 3. Account Types

### 3.1 Standard User Accounts

- Assigned to all employees upon onboarding.
- Provide access to email, collaboration tools, and role-specific applications.
- Enforced with Multi-Factor Authentication (MFA).

### 3.2 Privileged Accounts (Admin)

- Assigned only to personnel who require elevated access for system administration.
- Subject to enhanced monitoring, session recording, and time-limited access.
- Must use Privileged Access Workstations (PAWs) for administrative tasks.
- Require approval from the IAM Team Lead and the user's line manager.

### 3.3 Service Accounts

- Used by applications and automated processes (not interactive human logins).
- Must have documented owners and be reviewed quarterly.
- Passwords or certificates must be rotated every 90 days.

## 4. Authentication Requirements

### 4.1 Multi-Factor Authentication (MFA)

All user accounts must be protected with MFA. Approved MFA methods include:

| Method | Use Case |
|--------|----------|
| **Microsoft Authenticator app** (push notification) | Primary method for all users |
| **FIDO2 security keys** (hardware token) | Required for privileged accounts |
| **SMS one-time passcode** | Permitted as fallback only; not for privileged accounts |

### 4.2 Password Policy

- Minimum length: 14 characters
- Complexity: at least one uppercase, one lowercase, one digit, one special character
- Expiry: 90 days for standard accounts, 60 days for privileged accounts
- History: last 12 passwords cannot be reused

### 4.3 Session Management

- Idle sessions time out after 15 minutes for privileged accounts, 30 minutes for standard accounts.
- Maximum session duration: 8 hours.
- Concurrent session limit: 2 per user.

## 5. Access Provisioning

### 5.1 New User Onboarding

1. HR submits a **New User Access Request** via ServiceNow.
2. The user's **line manager** approves the request and specifies the required roles.
3. The IAM team creates the account in Azure Active Directory (AAD).
4. Role-Based Access Control (RBAC) group memberships are assigned.
5. The user completes **security awareness training** before access is activated.

### 5.2 Role Changes

1. The line manager submits a **Role Change Request** when an employee changes position.
2. Previous role permissions are **revoked** before new ones are granted.
3. Changes are logged in the IAM audit trail.

### 5.3 Access Reviews

- **Quarterly access reviews** are conducted for all user accounts.
- **Monthly access reviews** for privileged accounts.
- Accounts not validated during review are automatically disabled.

## 6. Access Revocation

### 6.1 Voluntary Separation

1. HR notifies the IAM team **at least 3 business days** before the employee's last day.
2. The IAM team prepares account disablement scripts.
3. On the termination date, all accounts are **disabled within 4 hours**.
4. Mailbox and data are retained for 90 days per the data retention policy.

### 6.2 Involuntary Termination

1. HR and Security notify the IAM team **immediately**.
2. All accounts are **disabled within 1 hour** of notification.
3. Active sessions are terminated.
4. Physical access badges are revoked simultaneously.

### 6.3 Contractor / Third-Party Offboarding

1. The sponsoring manager submits a **Contractor Offboarding Request**.
2. Access is revoked on or before the contract end date.
3. Shared credentials (if any) are rotated immediately.

## 7. Least Privilege and Separation of Duties

- Users are granted the **minimum permissions** necessary to perform their job functions.
- No single individual may both **approve and execute** privileged operations (e.g., firewall changes, database schema modifications).
- Exceptions require documented approval from the CISO.

## 8. Monitoring and Auditing

- All authentication events are logged in Azure Active Directory and forwarded to Azure Sentinel.
- Failed login attempts exceeding 5 within 10 minutes trigger an automatic account lockout and alert.
- Privileged account activity is subject to real-time monitoring and quarterly audit reports.

## 9. Compliance

This SOP aligns with:

- NIST SP 800-53 AC (Access Control) family
- CISA Zero Trust Maturity Model
- FedRAMP Moderate baseline (applicable to Azure Government)

## 10. References

- Azure Active Directory documentation: https://learn.microsoft.com/azure/active-directory/
- NIST SP 800-63B: Digital Identity Guidelines — Authentication and Lifecycle Management
- Organisation Information Security Policy (ISP-001)
