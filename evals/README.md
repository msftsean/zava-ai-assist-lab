# 🧪 AI Assist Lab — Evaluation Guide

> 📊 **Status:** ████████████████████ 100% Complete | 🏷️ **Version:** 1.0.0 | 📅 **Updated:** 2026-03-09

This directory contains the evaluation harness for measuring the quality
of the AI Assist RAG pipeline. Use it to validate that the system returns
accurate, well-sourced answers to operational questions.

---

## 🚀 Quick Start

```bash
# 1. Install dependencies (from project root)
pip install pyyaml

# 2. Run with mock pipeline (no Azure credentials needed)
python -m evals.harness.eval_runner --mock

# 3. View the JSON report
cat evals/reports/eval_report.json
```

## 🌐 Running Against Live Services

```bash
# Set up your Azure credentials (see app/.env.example)
source scripts/setup-env.sh

# Run evaluation against real Azure services
python -m evals.harness.eval_runner
```

---

## 📂 Directory Structure

```
evals/
├── datasets/
│   ├── golden_questions.yaml       # Golden questions dataset
│   └── sample_sops/                # Sample SOP documents for testing
│       ├── sop_backup_recovery.md
│       ├── sop_incident_response.md
│       └── sop_access_control.md
├── harness/
│   ├── eval_runner.py              # Main evaluation script
│   └── report_template.md         # Markdown report template
├── reports/                        # Generated reports (gitignored)
│   └── eval_report.json
└── README.md                       # This file
```

---

## 📝 Adding Custom Questions

1. Open `datasets/golden_questions.yaml` (or create a new YAML file).
2. Add questions using this format:

```yaml
questions:
  - id: custom-001
    question: "Your domain-specific question here"
    expected_topics: ["keyword1", "keyword2", "keyword3"]
    expected_min_sources: 1
    difficulty: "easy"   # easy | medium | hard
```

3. Run with your custom dataset:

```bash
python -m evals.harness.eval_runner --dataset path/to/your_questions.yaml --mock
```

### Tips for Writing Good Questions

- **Be specific:** "What is the RTO for critical systems?" is better than
  "Tell me about recovery."
- **Include expected topics:** These are keywords the answer should contain.
  The harness checks for case-insensitive substring matches.
- **Set realistic source counts:** `expected_min_sources: 1` means the
  answer should cite at least one SOP document.
- **Tag difficulty:** This helps you analyse results by complexity level.

---

## 📊 Interpreting Results

### Pass/Fail Criteria

A question **passes** when:
- **Topic coverage ≥ 50%** — at least half of the expected topics appear
  in the answer.
- **Source count met** — the answer cites at least `expected_min_sources`
  documents.

### Report Fields

| Field | Description |
|-------|------------|
| `topic_hits` | Which expected topics were found in the answer |
| `topic_coverage` | Fraction of expected topics found (0.0–1.0) |
| `source_count` | Number of source documents cited |
| `source_count_met` | Whether the minimum source threshold was met |
| `latency_ms` | Time to generate the answer (milliseconds) |
| `pass` | Overall pass/fail for this question |

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Low topic coverage | Poor retrieval quality | Increase `top_k`, adjust chunk size/overlap |
| Zero sources | Documents not ingested/indexed | Run `/ingest` and `/index` endpoints first |
| High latency | Large context window | Reduce `top_k` or chunk size |
| All failures | Service connectivity | Check Azure credentials and endpoints |

---

## 🏢 Plugging in MSI's Own Dataset

To evaluate with your organisation's actual SOPs and questions:

1. **Ingest your SOPs:** Upload your SOP documents to Azure Blob Storage
   and call the `/ingest` endpoint.

2. **Index the documents:** Call the `/index` endpoint to generate
   embeddings and populate the search index.

3. **Create a golden questions file:** Write questions that your end users
   would actually ask, along with expected answer topics.

4. **Run the evaluation:**
   ```bash
   python -m evals.harness.eval_runner \
       --dataset path/to/msi_golden_questions.yaml
   ```

5. **Review and iterate:** Use the report to identify weak areas and
   improve your chunking strategy, prompt template, or document coverage.

---

## 🔧 Extending the Harness

The evaluation harness is designed to be extended. Here are some ideas:

- **LLM-based scoring:** Use a judge LLM to score answer relevance
  instead of keyword matching.
- **ROUGE / BERTScore:** Add NLP metrics for answer quality.
- **Latency percentiles:** Track P50, P95, P99 latency.
- **A/B testing:** Compare different prompt templates or retrieval
  strategies side by side.
- **Regression tracking:** Save reports over time and flag regressions.

---

## 🔄 CI/CD Integration

Add the evaluation to your CI pipeline:

```yaml
# .github/workflows/eval.yml
- name: Run evaluation
  run: python -m evals.harness.eval_runner --mock
  continue-on-error: false
```

This ensures that code changes don't degrade answer quality.

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — evaluation harness with golden questions and mock pipeline |
