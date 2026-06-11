# 🎓 Facilitator Guide

> 📊 **Status:** ████████████████████ 100% Complete | 🏷️ **Version:** 1.1.0 | 📅 **Updated:** 2026-03-10

**MSI Hands-on Lab: Azure Gov AI Assist Architecture & Deployment**

---

## 🎯 Lab Overview and Goals

This hands-on lab walks senior engineers through building an AI-powered SOP assistant on Azure, designed for eventual deployment to Azure Government with FedRAMP compliance. The lab is structured in five phases, each building on the previous one, and takes approximately **4 hours** to complete (including ~2.5 hours of hands-on exercises, breaks, introductions, and wrap-up discussion).

### 📚 What Participants Will Learn

1. **Infrastructure as Code** — Deploying Azure AI services with Terraform, using modules that work identically in Commercial and Gov
2. **Document Ingestion** — Chunking, embedding, and dual-indexing SOPs into pgvector and Azure AI Search
3. **RAG Architecture** — Building a retrieval-augmented generation pipeline with hybrid search and grounded responses
4. **Content Safety** — Implementing pre/post safety checks with Azure Content Safety, calibrated for government use
5. **Evaluation** — Testing and measuring system quality with golden questions and an evaluation harness

### 🚫 What Participants Will NOT Learn

See [Non-Goals](non-goals.md) for an explicit list of out-of-scope topics. Key non-goals: production hardening, security configuration, CI/CD pipelines, cost optimization.

---

## 📅 4-Hour Session Schedule

| Time | Duration | Activity |
|------|----------|----------|
| 0:00 – 0:15 | 15 min | 🎤 Welcome, introductions, lab overview |
| 0:15 – 1:00 | 45 min | 🏗️ Phase 1: Infrastructure Provisioning |
| 1:00 – 1:10 | 10 min | ☕ Break |
| 1:10 – 1:40 | 30 min | 📥 Phase 2: SOP Ingestion & Indexing |
| 1:40 – 2:10 | 30 min | 🔍 Phase 3: RAG Query Flow |
| 2:10 – 2:20 | 10 min | ☕ Break |
| 2:20 – 2:40 | 20 min | 🛡️ Phase 4: Safety Integration |
| 2:40 – 3:05 | 25 min | 🧪 Phase 5: Testing & Evaluation |
| 3:05 – 3:15 | 10 min | ☕ Break |
| 3:15 – 3:50 | 35 min | 💬 Discussion: Architecture review, Q&A, next steps |
| 3:50 – 4:00 | 10 min | 🎯 Wrap-up: Action items, FedRAMP timeline, follow-ups |

> **🗣️ Facilitator Tip:** The schedule is intentionally tight. If a phase runs long, steal time from the discussion block rather than cutting exercises short. The discussion can happen async via follow-up.

---

## 📋 Prerequisites Checklist

Ensure the following are ready **before** the lab begins:

### 💻 Participant Environment

- [ ] Azure subscription with Contributor access (or a shared lab subscription with pre-provisioned resource quotas)
- [ ] Azure CLI ≥ 2.50 installed and authenticated (`az login`)
- [ ] Terraform ≥ 1.5 installed
- [ ] Python 3.11+ with pip
- [ ] Git clone of `ai_assist_lab` repository
- [ ] VS Code or preferred editor
- [ ] Terminal access (bash/zsh)

### ☁️ Azure Quotas (verify in advance)

- [ ] Azure OpenAI: at least 2 deployments available (gpt-4o, text-embedding-ada-002)
- [ ] PostgreSQL Flexible Server: quota for at least 1 server
- [ ] Azure AI Search: quota for at least 1 Basic-tier service
- [ ] Content Safety: available in the target region

### 🤝 If Using a Shared Lab Subscription

- [ ] Pre-create resource groups (one per participant or team)
- [ ] Pre-approve Azure OpenAI access (can take 1–2 business days)
- [ ] Set resource naming convention (e.g., `rg-aiassist-lab-{team}`)
- [ ] Verify spending limits and budget alerts

---

## 🏠 Room Setup Suggestions

### 🏢 In-Person Lab

| Item | Details |
|---|---|
| **Room layout** | Classroom or U-shape; participants need power outlets and screen space |
| **Projector/screen** | For live demos and architecture diagrams |
| **Whiteboard** | For drawing RAG flow, chunking strategy, and architecture decisions |
| **Network** | Reliable internet; verify Azure portal and CLI work from the room |
| **Backup hotspot** | In case corporate WiFi has proxy/firewall issues with Azure |
| **Printed cheat sheets** | Azure CLI commands, Terraform commands, Python commands |

### 💻 Virtual Lab

| Item | Details |
|---|---|
| **Video platform** | Teams/Zoom with screen sharing |
| **Shared environment** | GitHub Codespaces or Azure Cloud Shell as a fallback |
| **Chat channel** | For async questions and sharing error messages |
| **Breakout rooms** | For team-based exercises (Phase 5 golden questions) |

---

## 🗣️ Phase-by-Phase Facilitator Talking Points

### 🔧 Phase 1: Infrastructure Provisioning (~45 min)

**Key Messages:**
- This is **not** a Terraform tutorial — the modules are pre-written. Focus on *what* we're deploying and *why*.
- The dual-mode (Gov/Commercial) architecture means we can develop locally on Commercial and deploy to Gov with only config changes.
- Managed Identity eliminates secrets management — call attention to the `identity/` module.

**Pacing:**
- Steps 1–2 (config + review): 10 min
- Steps 3–8 (deploy resources): 25 min
- Step 9 (verify): 5 min
- Decision callouts: 5 min

**Watch For:**
- Participants who rush `terraform apply` without reading the plan — ask them to `terraform plan` first
- Azure quota issues — have a pre-provisioned fallback resource group
- Slow provisioning — Azure OpenAI can take 3–5 min; use the wait time for discussion

**If Running Behind:**
- Skip targeted deploys; do a single `terraform apply` for all resources
- Have a pre-provisioned environment ready as a fallback

---

### 📄 Phase 2: SOP Ingestion and Indexing (~30 min)

**Key Messages:**
- Chunking is the most impactful design decision in a RAG system — chunk size directly affects retrieval quality
- We index into *two* stores intentionally — see ADR-002
- Embeddings are the "language" that enables semantic search

**Pacing:**
- Steps 1–3 (upload + ingest + review): 10 min
- Steps 4–5 (embed + search index): 10 min
- Steps 6–7 (pgvector + verify): 5 min
- Decision callouts: 5 min

**Watch For:**
- Participants confused about *why* we need embeddings — explain with a simple analogy: "Embeddings convert text into coordinates in meaning-space. Similar documents are nearby."
- Storage account authentication issues — ensure participants use `--auth-mode login`

**Interactive Moment:**
- After Step 3, ask participants to open a chunk file and explain what each field means

---

### 🔍 Phase 3: RAG Query Flow (~30 min)

**Key Messages:**
- RAG = "look it up, then answer" — the model is grounded by the retrieved context
- Prompt engineering is not optional in Gov — the system prompt enforces grounding, citations, and refusal
- Hybrid search gives better recall than pure vector search

**Pacing:**
- Step 1 (architecture review): 5 min
- Steps 2–4 (search + compose): 10 min
- Steps 5–6 (generate + review): 10 min
- Step 7 (compare backends): 5 min

**Watch For:**
- "It just works" syndrome — push participants to understand *why* the answer is good (trace it back to chunks)
- Participants who want to skip to Phase 5 — remind them that understanding the query flow is essential for debugging

**Interactive Moment:**
- Ask each participant to try a different query. Compare results as a group. Identify any queries that produce poor results — discuss why.

---

### 🛡️ Phase 4: Safety Integration (~20 min)

**Key Messages:**
- Content Safety is a **separate service**, not built into Azure OpenAI
- Pre + post checks provide defense-in-depth
- Threshold calibration is a policy decision, not a technical one — involve your security team
- **⚠️ Content Safety does NOT detect prompt injection** — this is the biggest surprise for most teams
- Filter profiles let you customize thresholds per deployment context (gov/enterprise/dev)

**Pacing:**
- Steps 1–2 (review + config): 5 min
- Steps 3–4 (pre + post check): 5 min
- Steps 5–7 (test safe + boundary + audit): 5 min
- Steps 8–10 (injection gap + profiles + shield): 5 min

**Watch For:**
- Participants who want to test with actual harmful content — redirect to the `--test-category` simulation flags
- Confusion about severity levels — use the table in the lab guide
- Surprise at the injection gap — use this as a teaching moment about defense-in-depth

**Interactive Moment:**
- Discuss as a group: "What threshold would you set for your organization? Why?"
- After Step 8: "Did you expect Content Safety to catch prompt injection? What does this tell us about layered security?"

---

### 🧪 Phase 5: Testing, Evaluation & Next Steps (~25 min)

**Key Messages:**
- Evaluation is how you measure quality — without it, you're guessing
- Golden questions are the foundation of your eval framework (YAML format, 10 questions across 3 difficulty levels)
- The path from lab to FedRAMP is real but requires significant additional work
- **Today's results: 88/88 tests passed** — 49 unit, 19 integration, 10 mock eval, 10 live eval
- Live eval achieved **92% average topic coverage** across all golden questions

**Pacing:**
- Steps 1–2 (unit + integration tests): 5 min
- Steps 3–5 (eval harness + interpret): 10 min
- Step 6 (MSI-specific questions): 5 min
- Step 7 (next steps + discussion): 5 min

**Watch For:**
- Participants fixating on eval scores — remind them that the golden questions are samples; real eval requires 50+ questions
- "We need to build all of this by March" panic — help prioritize P0 items
- The eval harness command is `python -m evals.harness.eval_runner` (not `evals.harness.run`). Use `--mock` for no-Azure environments.

**Interactive Moment:**
- Ask each participant to write 2–3 golden questions. Review them as a group. Vote on which are the best evaluation questions.

---

## 📊 Session Results & Learnings (2026-03-10 Live Session)

### 🏆 Test Results Summary

| Test Suite | Result | Duration |
|---|---|---|
| Unit Tests | **49/49 passed** | 5.07s |
| Integration Tests | **19/19 passed** | 3.08s |
| Golden Questions Eval (Mock) | **10/10 passed** | — |
| Golden Questions Eval (Live Azure) | **10/10 passed** | 3.06s avg latency |
| **TOTAL** | **88/88 passed, 0 failures** | |

### 🔑 Key Finding: Content Safety ≠ Prompt Injection Detection

The most important discovery from the live session: **Azure Content Safety does not detect prompt injection attacks.** All 3 injection test cases scored severity 0/0/0/0. Content Safety analyzes text *toxicity*, not injection *intent*.

**What this means for facilitators:**
- Don't present Content Safety as a complete safety solution
- Always mention the injection gap when discussing defense-in-depth
- Show the Prompt Shield (`app/safety/prompt_shield.py`) as the current mitigation
- Mention Azure AI Prompt Shields (preview) as the future solution

### 📋 Content Safety Test Battery Results

From the 18-test content safety battery:
- **14 tests passed safe** — legitimate content correctly allowed
- **4 tests correctly blocked** — profanity/threat-adjacent content at severity 2
- **3 injection tests scored 0** — Content Safety does not detect injection

### 💡 Tips Learned from the Live Session

1. **API response shape matters:** The Content Safety API returns `result.categories_analysis` (a list of dicts with `category` and `severity`), NOT `result.hate_result`. Several participants hit this error — see [Troubleshooting Guide](troubleshooting.md) for details.

2. **Golden questions use YAML, not JSON:** The dataset is at `evals/datasets/golden_questions.yaml`. Update any references to `.json` format.

3. **Eval harness command:** The correct command is `python -m evals.harness.eval_runner` (not `evals.harness.run`). Add `--mock` for environments without Azure credentials.

4. **Filter profiles are a great demo:** Showing how `strict` blocks content that `relaxed` allows is a powerful visual for the "why customize thresholds?" discussion.

5. **Interactive lab engagement:** `scripts/lab_content_safety.py` works well as a hands-on exercise. Give participants 5–10 minutes to explore the 5 exercises independently, then discuss as a group.

### 🆕 New Modules Built in This Session

| Module | Purpose |
|---|---|
| `app/safety/filter_profiles.py` | 3 built-in + custom filter profiles for Content Safety scores |
| `app/safety/prompt_shield.py` | Pattern-based prompt injection detector (12 patterns, confidence scoring) |
| `scripts/demo_content_safety.py` | Live demo of the full safety pipeline |
| `scripts/lab_content_safety.py` | Interactive 5-exercise content safety lab |

---

## ❓ Common Participant Questions and Answers

### 🏗️ Infrastructure & Architecture

**Q: Can we use ARM templates instead of Terraform?**
A: Yes, but we chose Terraform for readability and portability (see ADR-005). ARM templates are an equally valid choice. Bicep is also worth considering as a middle ground.

**Q: Why not use Azure OpenAI's built-in content filtering instead of Content Safety?**
A: Azure OpenAI does have built-in filters, but Content Safety gives us more granular control, independent logging, and the ability to check *before* calling the model (saving tokens and cost). In Gov, you want explicit, auditable safety controls.

**Q: Is Azure OpenAI available in Azure Gov?**
A: Yes, in `usgovvirginia` and `usgovarizona`. Model availability may lag behind Commercial. Always check the latest service availability matrix.

**Q: How much does this cost to run?**
A: For a lab environment with minimal usage: ~$5–10/day. The main cost drivers are Azure OpenAI (per-token) and Azure AI Search (per-hour). PostgreSQL Flexible Server burstable tier is economical for dev/test.

### 🔎 RAG & Search

**Q: How do we handle SOPs that change frequently?**
A: Re-run the ingestion pipeline when SOPs are updated. In production, you'd set up an event-driven pipeline (e.g., blob storage trigger → Azure Function → re-index).

**Q: What if the model gives wrong answers even with RAG?**
A: This is why evaluation matters. Common causes: wrong chunks retrieved (tune chunking/search), model ignores context (strengthen the system prompt), or the information genuinely isn't in the SOPs (add it).

**Q: Can we use a different model (GPT-4, GPT-3.5)?**
A: Yes. GPT-4o is the recommended default, but the pipeline is model-agnostic. GPT-3.5-turbo is cheaper but less capable at following complex grounding instructions. Evaluate with your golden questions to find the right balance.

### 🔒 Safety & Compliance

**Q: Does Content Safety work with classified data?**
A: Content Safety is a cloud service — data is sent to the API for analysis. For classified environments, consult your security team about approved AI services in your authorization boundary.

**Q: How do we get FedRAMP authorized?**
A: Azure services are individually FedRAMP authorized, but *your application* also needs an Authorization to Operate (ATO). This involves a System Security Plan (SSP), security assessment, and continuous monitoring. Start with the SSP.

---

## 🔧 What to Do If Something Breaks

### ⚡ Terraform Errors

| Symptom | Quick Fix |
|---|---|
| `Error: Quota exceeded` | Use a different region or request a quota increase |
| `Error: Resource already exists` | `terraform import` or change the resource name |
| `Error: Provider authentication failed` | Re-run `az login` |
| `Error: API version not supported` | Update the azurerm provider version |

### ⚡ Azure OpenAI Issues

| Symptom | Quick Fix |
|---|---|
| `429 Too Many Requests` | Wait 60 seconds; reduce batch size |
| `Model not found` | Verify the deployment name matches |
| `Access denied` | Check RBAC role assignment for the Managed Identity |

### ⚡ PostgreSQL Issues

| Symptom | Quick Fix |
|---|---|
| `Connection refused` | Check firewall rules; add your IP |
| `Extension "vector" not found` | Enable via `azure.extensions` server parameter |
| `Permission denied` | Verify AAD admin is configured |

### 🆘 General Fallback

If something is truly broken and can't be fixed in 5 minutes:
1. Have participants pair up with someone whose environment works
2. Use a pre-provisioned shared environment
3. Skip to the next phase using pre-built outputs (stored in `evals/datasets/`)

---

## 📬 Post-Lab Follow-Up Actions

### 📅 Within 1 Week

- [ ] Share lab recording/notes with participants who couldn't attend
- [ ] Collect feedback: what worked, what was confusing, what to improve
- [ ] Ensure all participants have access to the Git repository
- [ ] Assign owners for golden questions development (from Phase 5 exercise)

### 📅 Within 2 Weeks

- [ ] Schedule follow-up office hours for questions
- [ ] Begin MSI-specific SOP ingestion (real documents, not samples)
- [ ] Start SSP documentation for FedRAMP
- [ ] Set up Azure Gov subscription (if not already done)

### 🔄 Ongoing

- [ ] Run evaluation harness weekly as content is added
- [ ] Track eval scores over time (should trend upward)
- [ ] Review and update golden questions as SOPs change
- [ ] Maintain architecture decision records (ADRs) for all significant changes

---

## 🎨 How to Customize for Different Audiences

### 👔 For Leadership / Non-Technical Stakeholders

- **Skip:** Phases 1–2 (infrastructure + ingestion)
- **Focus:** Phase 3 (demo the RAG pipeline live), Phase 4 (safety), Phase 5 (eval results)
- **Modify:** Replace code walkthroughs with architecture diagrams and live demos
- **Time:** ~60 minutes total

### 🔒 For Security / Compliance Teams

- **Emphasize:** Phase 4 (Content Safety deep dive), ADRs, Gov Compatibility Checklist
- **Add:** Discussion of network isolation, data flow diagrams, NIST 800-53 control mapping
- **Skip:** Phase 2 implementation details
- **Time:** ~90 minutes total

### 🔬 For Data Scientists / ML Engineers

- **Emphasize:** Phase 2 (chunking strategy, embedding models), Phase 3 (retrieval comparison), Phase 5 (evaluation methodology)
- **Add:** Discussion of fine-tuning vs. RAG, embedding model benchmarks, advanced chunking strategies
- **Skip:** Phase 1 Terraform details
- **Time:** ~2 hours total

### ⏱️ For a Shorter Workshop (90 minutes)

- **Phase 1:** Pre-provision infrastructure; spend 5 min reviewing what's deployed
- **Phase 2:** Use pre-indexed data; spend 5 min reviewing the index
- **Phase 3:** Full walkthrough (25 min)
- **Phase 4:** Demo only, no hands-on (10 min)
- **Phase 5:** Run eval harness, discuss results (15 min)
- **Discussion:** Next steps and Q&A (30 min)

---

## 📝 Facilitator Cheat Sheet

### ⌨️ Key Commands

```bash
# Verify Azure CLI
az account show

# Deploy everything at once
cd infra && terraform apply -auto-approve

# Run full ingestion pipeline
python -m app.ingestion.run --storage-account $STORAGE_ACCOUNT --container sops

# Run a single RAG query
python -m app.query.runner --query "your question here" --backend ai_search --safety enabled

# Run evaluations (live)
python -m evals.harness.eval_runner --dataset evals/datasets/golden_questions.yaml --output evals/results/eval_report.json

# Run evaluations (mock — no Azure needed)
python -m evals.harness.eval_runner --dataset evals/datasets/golden_questions.yaml --mock --output evals/results/eval_report.json

# Run all tests
python -m pytest tests/ -v

# Run content safety demo
python scripts/demo_content_safety.py

# Run interactive content safety lab
python scripts/lab_content_safety.py
```

### 📁 Key Files

| File | Purpose |
|---|---|
| `infra/main.tf` | Terraform entry point |
| `infra/terraform.tfvars` | Environment configuration |
| `app/query/runner.py` | Full RAG pipeline entry point |
| `app/safety/config.py` | Content Safety thresholds |
| `app/safety/filter_profiles.py` | Customizable filter profiles (strict/standard/relaxed/custom) |
| `app/safety/prompt_shield.py` | Pattern-based prompt injection detector |
| `evals/datasets/golden_questions.yaml` | Evaluation dataset (YAML format, 10 questions) |
| `scripts/demo_content_safety.py` | Live demo of full safety pipeline |
| `scripts/lab_content_safety.py` | Interactive 5-exercise content safety lab |
| `docs/architecture-decisions.md` | Architecture Decision Records |

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — complete facilitator guide with 5-phase walkthrough |
| 1.1.0 | 2026-03-10 | Squad (Beacon 🔦) | Added session results & learnings section, updated Phase 4 & 5 talking points with prompt injection gap, filter profiles, real test numbers, corrected eval commands and file references |
