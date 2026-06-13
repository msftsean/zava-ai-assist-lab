# 🚫 Non-Goals

> 📊 **Status:** ████████████████████ 100% Complete | 🏷️ **Version:** 1.0.0 | 📅 **Updated:** 2026-03-09

This document explicitly states what the AI Assist lab is **not** trying to achieve. Being clear about non-goals prevents scope creep, sets expectations, and helps participants focus on what matters.

---

## 🚫 What This Lab Is NOT

### ❌ This Is NOT a Production Deployment

This lab provisions Azure resources for **learning and experimentation**. The resulting deployment is not suitable for production use without significant additional hardening.

What's missing for production:
- Private Endpoints and VNet isolation
- Web Application Firewall (WAF)
- Auto-scaling and load balancing
- Disaster recovery and failover
- Performance testing under load
- Formal security review

---

### ❌ This Is NOT a Security Hardening Guide

While we use Managed Identity (a security best practice) and integrate Content Safety, this lab does not cover:
- Network security configuration (NSGs, Private Endpoints, Azure Firewall)
- Penetration testing
- Vulnerability scanning
- Security Information and Event Management (SIEM) setup
- Compliance documentation (SSP, POA&M)
- Key management and rotation policies
- Data Loss Prevention (DLP) configuration

See the [Gov Compatibility Checklist](gov-compatibility-checklist.md) for security items that need to be addressed before production.

---

### ❌ No Custom Model Fine-Tuning

This lab uses Azure OpenAI models **as-is** (GPT-4.1, text-embedding-3-small). We do not:
- Fine-tune models on custom data
- Train custom embedding models
- Perform any model training or distillation
- Modify model weights or behavior beyond prompt engineering

RAG is the strategy here: we augment the model's responses with retrieved SOP content rather than training the model on SOP content.

---

### ❌ No Multi-Region High Availability

The lab deploys to a **single Azure region**. We do not:
- Configure geo-redundant deployments
- Set up active-active or active-passive failover
- Configure Traffic Manager or Front Door
- Test regional failover scenarios
- Design for 99.99% availability

For a production FedRAMP deployment, multi-region HA is likely required. This is a post-lab engineering effort.

---

### ❌ No Full CI/CD Pipeline

The lab uses manual `terraform apply` and manual script execution. We do not:
- Set up GitHub Actions workflows
- Configure automated testing pipelines
- Implement staged deployment (dev → staging → production)
- Create infrastructure drift detection
- Implement rollback procedures
- Configure branch protection or approval gates

CI/CD is an important part of production readiness but is outside the scope of this hands-on exercise.

---

### ❌ No Cost Optimization

The lab prioritizes **simplicity and learning** over cost efficiency. We do not:
- Use reserved capacity or savings plans
- Optimize SKU selection for cost
- Implement auto-shutdown for non-production hours
- Configure budget alerts
- Analyze cost per query or cost per document indexed
- Right-size compute resources

Participants should be aware that leaving lab resources running will incur costs. Tear down resources after the lab with `terraform destroy`.

---

### ❌ No Performance Benchmarking

The lab does not include:
- Load testing (concurrent queries)
- Latency profiling (P50, P95, P99)
- Throughput measurement (queries per second)
- Embedding generation throughput
- Index query performance tuning
- Database connection pooling optimization

Performance testing is important for production but requires a dedicated effort with realistic workloads.

---

### ❌ No Data Migration from Existing Systems

The lab uses **sample SOP documents** included in the repository. We do not:
- Migrate data from existing document management systems
- Import from SharePoint, ServiceNow, or Confluence
- Handle document format conversion at scale
- Implement incremental sync from source systems
- Address document versioning or change management

Integrating with real document sources is a post-lab engineering task specific to each organization's systems.

---

## ✅ What IS in Scope

To balance the non-goals, here's what the lab **does** cover:

| In Scope | Why It Matters |
|---|---|
| ✅ **Infrastructure as Code** | Reproducible deployment; same code works in Gov and Commercial |
| ✅ **Document ingestion pipeline** | Understand chunking, embedding, and indexing — the foundation of RAG |
| ✅ **Dual search strategy** | See the tradeoffs between pgvector and AI Search firsthand |
| ✅ **RAG query flow** | Build intuition for how retrieval + generation works together |
| ✅ **Content Safety integration** | Understand mandatory guardrails for Gov AI deployments |
| ✅ **Evaluation framework** | Learn how to measure quality and prevent regressions |
| ✅ **Architecture decisions** | Understand *why* the architecture looks this way |
| ✅ **Gov compatibility awareness** | Know what changes are needed for Azure Government |

The lab gives you a **working foundation** and **architectural understanding** that you can build on for production. It is deliberately scoped to fit in a half-day session without cutting corners on the concepts that matter most.

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — explicit non-goals and in-scope items |
