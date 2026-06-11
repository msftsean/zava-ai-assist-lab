# 🧪 Phase 5: Testing, Evaluation & Next Steps

> 📊 **Status:** ████████████████████ 100% Ready | 🏷️ **Version:** 1.1.0 | 📅 **Updated:** 2026-03-10

**⏱ Time Box: ~25 minutes**

## 🎯 Objective

Validate the system through automated tests, evaluate response quality using a golden question dataset and evaluation harness, and discuss how to extend the platform with MSI-specific content and prepare for the March FedRAMP stage.

---

## ✅ Prerequisites

- 🔹 Phases 1–4 complete (infrastructure, ingestion, RAG, safety all working)
- 🔹 `pytest` installed (`pip install pytest`)
- 🔹 `evals/` directory contains datasets and harness code

---

## 📋 Step 1: Run Unit Tests

Unit tests validate individual components in isolation — no Azure resources required:

```bash
# Run all unit tests
python -m pytest tests/unit/ -v --tb=short
```

Expected output:

```
tests/unit/test_chunker.py::test_chunk_size_within_limit PASSED
tests/unit/test_chunker.py::test_chunk_overlap PASSED
tests/unit/test_composer.py::test_prompt_template PASSED
tests/unit/test_composer.py::test_context_injection PASSED
tests/unit/test_safety.py::test_threshold_config PASSED
tests/unit/test_safety.py::test_safe_content_passes PASSED
tests/unit/test_safety.py::test_blocked_content_returns_default PASSED
...

49 passed in 5.07s
```

### ✔️ Verification

All unit tests pass. If any fail, review the error output — these are deterministic tests that shouldn't be affected by environment differences.

> **🗣️ Facilitator Note:** If tests fail, this is a good teaching moment. Ask participants to read the error message and identify the root cause before jumping to fix it. Common issues: missing dependencies, Python version mismatches.

---

## 📋 Step 2: Run Integration Tests (Mock or Live)

Integration tests validate the full pipeline. They can run in two modes:

**Mock mode** (no Azure resources needed — uses recorded responses):

```bash
python -m pytest tests/integration/ -v --tb=short -m "not live"
```

**Live mode** (requires deployed Azure resources):

```bash
# Set environment variables for live testing
export AZURE_OPENAI_ENDPOINT="https://oai-aiassist-lab.openai.azure.com/"
export AZURE_SEARCH_ENDPOINT="https://srch-aiassist-lab.search.windows.net"
export AZURE_PG_HOST="psql-aiassist-lab.postgres.database.azure.com"

python -m pytest tests/integration/ -v --tb=short -m "live"
```

### ✔️ Verification

```
tests/integration/test_retrieval.py::test_vector_search_returns_results PASSED
tests/integration/test_retrieval.py::test_hybrid_search_returns_results PASSED
tests/integration/test_pipeline.py::test_end_to_end_query PASSED
tests/integration/test_pipeline.py::test_safety_pre_check_integration PASSED
tests/integration/test_pipeline.py::test_safety_post_check_integration PASSED
...

19 passed in 3.08s
```

> **🗣️ Facilitator Note:** If you're running without live Azure resources, use mock mode. The mock tests use recorded API responses to validate the pipeline logic without incurring Azure costs. In a real CI/CD pipeline, you'd run mock tests on every PR and live tests on a schedule (e.g., nightly).

---

## 📋 Step 3: Review Golden Questions Dataset

The evaluation framework uses a **golden questions dataset** — a curated set of question-answer pairs that represent expected behavior:

```bash
ls evals/datasets/
cat evals/datasets/golden_questions.yaml
```

A golden question looks like:

```yaml
- id: gq-001
  question: "What is the system backup SOP?"
  expected_topics:
    - backup procedures
    - system backup
    - SOP reference
  expected_source_count: 1
  category: backup_recovery
  difficulty: easy
  notes: "Direct SOP lookup — should return backup procedure with source citation"
```

Key fields:
- 🔹 **question** — the natural language query
- 🔹 **expected_topics** — topics the answer should cover (used for topic_coverage scoring)
- 🔹 **expected_source_count** — minimum number of source documents expected
- 🔹 **category** — for grouping evaluation results
- 🔹 **difficulty** — easy (fact lookup), medium (multi-step reasoning), hard (cross-document synthesis)

> **📝 Note:** The dataset uses **YAML format** (not JSON). YAML is more readable for hand-editing evaluation questions and supports comments for documenting expected behavior.

> **🗣️ Facilitator Note:** Ask participants: "What makes a good golden question?" Discuss: 1) It must have a verifiable answer in the SOPs, 2) The expected topics should be specific enough to evaluate programmatically, 3) Include a mix of difficulties. The current dataset has 10 questions: 3 easy, 4 medium, 3 hard.

---

## 📋 Step 4: Run Evaluation Harness

The evaluation harness runs all golden questions through the RAG pipeline and scores the results:

```bash
# Live mode (requires Azure credentials)
python -m evals.harness.eval_runner \
  --dataset evals/datasets/golden_questions.yaml \
  --backend ai_search \
  --model gpt-4o \
  --output evals/results/eval_report.json

# Mock mode (no Azure resources needed — uses recorded responses)
python -m evals.harness.eval_runner \
  --dataset evals/datasets/golden_questions.yaml \
  --mock \
  --output evals/results/eval_report.json
```

This process:
1. Iterates through each golden question
2. Runs the full RAG pipeline (retrieve → compose → generate)
3. Compares the generated answer against the expected answer
4. Scores each answer on multiple dimensions
5. Produces an evaluation report

### ✔️ Verification

```bash
# Check that the eval report was generated
ls -la evals/results/
```

---

## 📋 Step 5: Interpret Evaluation Report

Review the evaluation results:

```bash
python -m evals.harness.report \
  --input evals/results/eval_report.json
```

### 📊 Live Session Results (2026-03-10)

From today's live Azure evaluation run — **10/10 golden questions passed**:

| ID | Question | Topic Coverage | Latency | Pass |
|---|---|---|---|---|
| gq-001 | System backup SOP | 100% | 5781ms | ✅ |
| gq-002 | Incremental backup frequency | 100% | 2334ms | ✅ |
| gq-003 | First steps incident response | 75% | 2467ms | ✅ |
| gq-004 | Access control approval | 50% | 2447ms | ✅ |
| gq-005 | RTO for critical systems | 100% | 2319ms | ✅ |
| gq-006 | Revoking access after termination | 100% | 3253ms | ✅ |
| gq-007 | Approved MFA methods | 100% | 2391ms | ✅ |
| gq-008 | Post-incident review | 100% | 2836ms | ✅ |
| gq-009 | Backup verification procedures | 100% | 2426ms | ✅ |
| gq-010 | Privileged vs standard access | 80% | 4360ms | ✅ |

```
╔══════════════════════════════════════════════════╗
║         AI Assist Evaluation Report              ║
╠══════════════════════════════════════════════════╣
║ Total Questions:          10                     ║
║ Passed:                   10 (100%)              ║
║ Failed:                    0 (  0%)              ║
╠══════════════════════════════════════════════════╣
║ Scoring Criteria:                                ║
║   topic_coverage ≥ 0.5 AND source_count_met      ║
╠══════════════════════════════════════════════════╣
║ Metrics:                                         ║
║   Avg Topic Coverage:     92%                    ║
║   Avg Response Latency:   3.06s                  ║
║   Min Coverage:           50% (gq-004)           ║
║   Max Latency:            5.78s (gq-001)         ║
╚══════════════════════════════════════════════════╝
```

### 📈 Results by Difficulty

| Difficulty | Questions | Avg Coverage | Avg Latency |
|---|---|---|---|
| **Easy** (gq-001 to gq-003) | 3/3 passed | 92% | 3.53s |
| **Medium** (gq-004 to gq-007) | 4/4 passed | 88% | 2.60s |
| **Hard** (gq-008 to gq-010) | 3/3 passed | 93% | 3.21s |

Key metrics explained:

| Metric | What It Measures | Target for Gov |
|---|---|---|
| **Retrieval Precision@3** | Of the top 3 retrieved chunks, how many were relevant? | ≥ 0.80 |
| **Answer Faithfulness** | Does the answer only use information from retrieved context? | ≥ 0.90 |
| **Source Attribution** | Does the answer cite the correct source documents? | ≥ 0.90 |
| **Avg Response Time** | End-to-end latency (retrieve + generate) | < 5s |

> **🗣️ Facilitator Note:** Walk through any questions that scored "Incorrect." Ask the group to diagnose why: Was it a retrieval failure (wrong chunks retrieved)? A generation failure (right chunks, wrong answer)? A chunking issue (answer split across chunks)?

---

## 📋 Step 6: Discuss How to Add MSI-Specific Questions

To extend the evaluation dataset with MSI-specific content:

### 🔧 6.1 Adding New SOPs

```bash
# 1. Place new SOP documents in the corpus
cp /path/to/msi-sop-*.md evals/datasets/

# 2. Re-run the ingestion pipeline (Phase 2)
python -m app.ingestion.run \
  --storage-account $STORAGE_ACCOUNT \
  --container sops

# 3. Re-index
python -m app.indexing.search_index \
  --search-service "srch-aiassist-lab" \
  --index-name "sops-index"
```

### 📝 6.2 Adding Golden Questions

Create new entries in the golden questions file:

```json
{
  "id": "msi-gq-001",
  "question": "What is MSI's process for handling classified spills?",
  "expected_answer": "Immediately isolate the affected system, notify the FSO within 1 hour, and follow the 10-step remediation process in MSI-SOP-SEC-005.",
  "source_documents": ["msi-sop-sec-005.md"],
  "category": "security",
  "difficulty": "medium",
  "notes": "MSI-specific procedure, not covered by generic SOPs"
}
```

### ⚡ 6.3 Tips for Writing Good Golden Questions

1. **Cover the full difficulty spectrum** — include easy lookups, multi-step reasoning, and cross-document synthesis
2. **Include negative cases** — questions the SOPs don't answer (expected: "I don't have enough information")
3. **Test terminology** — use acronyms and jargon that MSI personnel would actually use
4. **Be specific in expected answers** — "30 minutes" is better than "the SOP covers escalation timelines"
5. **Map to source documents** — every golden question should trace to specific SOPs

> **🗣️ Facilitator Note:** This is a collaborative exercise. Ask each participant to draft 2–3 golden questions based on SOPs they know well. Collect them and discuss which ones are good evaluation questions and why.

---

## 📋 Step 7: Discuss Next Steps Toward March FedRAMP Stage

### ✅ What We Built Today

```
✅ Infrastructure as Code (Terraform)
✅ Document ingestion + chunking + embedding
✅ Dual search strategy (pgvector + AI Search)
✅ RAG pipeline with grounding
✅ Content Safety guardrails (pre-check + post-check)
✅ Prompt injection gap analysis (Content Safety ≠ injection detection)
✅ Customizable filter profiles (strict/standard/relaxed/custom)
✅ Pattern-based Prompt Shield (12 patterns, confidence scoring)
✅ Interactive content safety lab (5 exercises)
✅ Evaluation framework with golden questions (YAML, 10 questions)
✅ Full test suite: 88/88 tests passed (49 unit + 19 integration + 10 mock eval + 10 live eval)
```

### 🔧 What's Needed for Production / FedRAMP

| Gap | What's Needed | Priority |
|---|---|---|
| **Network isolation** | VNet integration, Private Endpoints for all services | P0 |
| **Data encryption** | CMK for data at rest, TLS 1.2+ in transit | P0 |
| **Audit logging** | Azure Monitor, Log Analytics, SIEM integration | P0 |
| **Identity governance** | Conditional Access, PIM for admin roles | P0 |
| **CI/CD pipeline** | GitHub Actions → Terraform → staged deployment | P1 |
| **Multi-region HA** | Secondary region, failover, backup strategy | P1 |
| **Monitoring & alerting** | Application Insights, availability tests, SLOs | P1 |
| **Cost management** | Reserved capacity, auto-scaling policies | P2 |
| **Penetration testing** | Third-party pen test of the deployed application | P1 |
| **SSP documentation** | System Security Plan for FedRAMP authorization | P0 |

### 📅 Recommended Timeline to March

```
January:
  ├── Finalize SOP corpus (MSI-specific documents)
  ├── Complete golden questions dataset (50+ questions)
  ├── Deploy to Azure Gov subscription
  └── Begin SSP documentation

February:
  ├── Network hardening (Private Endpoints, NSGs)
  ├── Integrate with MSI identity provider
  ├── CI/CD pipeline with gated deployments
  ├── Pen test and remediation
  └── Evaluation target: 90%+ faithfulness

March:
  ├── Final security review
  ├── FedRAMP readiness assessment
  ├── Stakeholder demo with real MSI SOPs
  └── Go/no-go decision for ATO package submission
```

> **🗣️ Facilitator Note:** This is the wrap-up discussion. Key messages:
> 1. **Today was a foundation** — the architecture is sound, but production readiness requires hardening.
> 2. **The eval framework is your compass** — as you add MSI content and tune the system, the eval scores tell you if you're improving or regressing.
> 3. **FedRAMP is a process, not a switch** — start the SSP documentation now, not in March.
>
> End with action items: each participant should leave with 1–2 specific tasks they own for the next sprint.

---

## 💡 Architecture Decision: What Makes a Good Eval Question?

A good evaluation question has these properties:

| Property | Good Example | Bad Example |
|---|---|---|
| **Specific** | "What is the max time to report a P1 incident?" | "Tell me about incidents" |
| **Verifiable** | Expected: "30 minutes" (checkable) | Expected: "A reasonable time" (subjective) |
| **Traceable** | Sources: `sop-001.md` section 4.2 | Sources: "somewhere in the SOPs" |
| **Realistic** | Uses language real users would use | Uses artificial/academic phrasing |
| **Categorized** | Category: incident_response | Category: general |

---

## 💡 Architecture Decision: Evaluation Metrics That Matter for Gov

Not all eval metrics are equally important. For a government SOP assistant:

**Critical metrics (must meet target):**
- **Answer Faithfulness ≥ 0.90** — the model must not hallucinate. Every claim must trace to a source.
- **Source Attribution ≥ 0.90** — users must be able to verify answers against official documents.

**Important metrics (should meet target):**
- **Retrieval Precision@3 ≥ 0.80** — retrieving the right context is the foundation of a good answer.
- **Negative Rejection ≥ 0.95** — when the SOPs don't contain the answer, the model must say so (not guess).

**Nice-to-have metrics:**
- **Response Time < 5s** — important for user experience but not a compliance requirement.
- **Answer Completeness** — does the answer cover all relevant information? Harder to measure automatically.

---

## 🎉 Wrap-Up

Congratulations — you've completed the full hands-on lab! You've:

- [x] Provisioned Azure infrastructure with Terraform
- [x] Ingested and indexed SOPs with embeddings
- [x] Built a RAG pipeline with hybrid search
- [x] Integrated content safety guardrails
- [x] Validated the system with tests and evaluations
- [x] Discussed the path from lab to production FedRAMP deployment

**Further reading:**
- [Architecture Decision Records](architecture-decisions.md)
- [Gov Compatibility Checklist](gov-compatibility-checklist.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Non-Goals](non-goals.md)
- [Facilitator Guide](facilitator-guide.md)

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — full lab guide |
| 1.1.0 | 2026-03-10 | Squad (Beacon 🔦) | Updated with live session results: 49 unit tests, 19 integration tests, 10/10 golden questions (YAML format), fixed eval_runner command, added --mock flag, real eval report with 92% avg coverage. |
