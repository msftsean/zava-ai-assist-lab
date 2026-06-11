#!/usr/bin/env python3
"""
Evaluation Harness for AI Assist Lab
=====================================
Runs golden questions through the RAG pipeline and produces a JSON report
with per-question pass/fail, latency, answer relevance, and source counts.

Usage::

    # With mocks (no live Azure services required):
    python -m evals.harness.eval_runner --mock

    # Against live services (requires valid Azure credentials):
    python -m evals.harness.eval_runner

    # Custom dataset:
    python -m evals.harness.eval_runner --dataset path/to/questions.yaml

    # Write report to a specific file:
    python -m evals.harness.eval_runner --mock --output results.json

Zava Lab guidance
----------------
This harness is intentionally simple so you can extend it with your own
metrics (e.g., LLM-based relevance scoring, ROUGE, BERTScore).

To plug in your own dataset:
  1. Copy ``evals/datasets/golden_questions.yaml`` as a template.
  2. Add your domain-specific questions, expected topics, and difficulty.
  3. Run: ``python -m evals.harness.eval_runner --dataset your_file.yaml``
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_DATASET = Path(__file__).resolve().parent.parent / "datasets" / "golden_questions.yaml"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "reports" / "eval_report.json"


# ---------------------------------------------------------------------------
# Dataset loader
# ---------------------------------------------------------------------------
def load_questions(path: Path) -> List[Dict[str, Any]]:
    """Load the golden-questions YAML file and return the list of questions."""
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    questions = data.get("questions", [])
    if not questions:
        print(f"⚠️  No questions found in {path}")
    return questions


# ---------------------------------------------------------------------------
# Mock RAG pipeline (for offline testing)
# ---------------------------------------------------------------------------
def _mock_rag_query(question: str, **kwargs) -> Dict[str, Any]:
    """Simulate a RAG response with deterministic mock data.

    This lets you validate the evaluation harness itself without
    needing live Azure services.
    """
    # Deterministic mock covering all golden-question expected topics
    mock_answer = (
        f"Based on the SOPs, the answer to '{question}' involves the following: "
        "backup schedules are defined in SOP-BKP-001, incident response steps "
        "are in SOP-IR-001, and access control policies are in SOP-AC-001. "
        "Backups run every Sunday. Incremental backups run nightly. "
        "Identify and classify the incident. Contain affected systems. "
        "Access is controlled via MFA, multi-factor authentication, and least privilege. "
        "The manager must provide approval before changes are authorised. "
        "Recovery time objective (RTO) is 4 hours for critical systems. "
        "Accounts are disabled and access revoked within 1 hour of termination. "
        "FIDO2 security keys (token) are required for privileged accounts. "
        "Standard accounts follow least privilege access control policies. "
        "Post-incident reviews include a lessons-learned report within 5 business days. "
        "Backup verification uses checksum-based integrity checks to verify and restore data."
    )
    return {
        "answer": mock_answer,
        "sources": ["sop_backup_recovery.md", "sop_incident_response.md", "sop_access_control.md"],
        "search_results_count": 3,
        "pgvector_results_count": 0,
    }


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------
def evaluate_answer(
    question_data: Dict[str, Any],
    answer: str,
    sources: List[str],
    latency_ms: float,
) -> Dict[str, Any]:
    """Score a single RAG answer against expected criteria.

    Scoring:
      • **topic_hits**: how many expected_topics appear in the answer (case-insensitive)
      • **topic_coverage**: fraction of expected topics found (0.0–1.0)
      • **source_count_met**: whether the answer cites enough sources
      • **pass**: True if topic_coverage ≥ 0.5 AND source_count_met
    """
    expected_topics = question_data.get("expected_topics", [])
    expected_min_sources = question_data.get("expected_min_sources", 1)

    answer_lower = answer.lower()
    topic_hits = [t for t in expected_topics if t.lower() in answer_lower]
    topic_coverage = len(topic_hits) / len(expected_topics) if expected_topics else 1.0
    source_count_met = len(sources) >= expected_min_sources

    passed = topic_coverage >= 0.5 and source_count_met

    return {
        "id": question_data["id"],
        "question": question_data["question"],
        "difficulty": question_data.get("difficulty", "unknown"),
        "expected_topics": expected_topics,
        "topic_hits": topic_hits,
        "topic_coverage": round(topic_coverage, 2),
        "source_count": len(sources),
        "source_count_met": source_count_met,
        "latency_ms": round(latency_ms, 1),
        "pass": passed,
    }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_evaluation(
    questions: List[Dict[str, Any]],
    use_mock: bool = False,
) -> List[Dict[str, Any]]:
    """Run every golden question through the RAG pipeline and score it."""
    results: List[Dict[str, Any]] = []

    # Choose the query function
    if use_mock:
        query_fn = _mock_rag_query
    else:
        # Import the real RAG pipeline (requires Azure services)
        from app.query.rag import rag_query as _real_rag_query

        def query_fn(question: str, **kw):
            resp = _real_rag_query(question, **kw)
            return {
                "answer": resp.answer,
                "sources": resp.sources,
                "search_results_count": resp.search_results_count,
                "pgvector_results_count": resp.pgvector_results_count,
            }

    total = len(questions)
    for idx, q in enumerate(questions, 1):
        qid = q["id"]
        question_text = q["question"]
        print(f"  [{idx}/{total}] {qid}: {question_text[:60]}...")

        start = time.perf_counter()
        try:
            response = query_fn(question_text)
            latency_ms = (time.perf_counter() - start) * 1000
            result = evaluate_answer(
                q,
                answer=response["answer"],
                sources=response["sources"],
                latency_ms=latency_ms,
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            result = {
                "id": qid,
                "question": question_text,
                "difficulty": q.get("difficulty", "unknown"),
                "error": str(exc),
                "latency_ms": round(latency_ms, 1),
                "pass": False,
            }

        status = "✅ PASS" if result["pass"] else "❌ FAIL"
        print(f"         {status}  (latency={result['latency_ms']}ms)")
        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def build_report(results: List[Dict[str, Any]], use_mock: bool) -> Dict[str, Any]:
    """Produce a summary report from individual question results."""
    passed = sum(1 for r in results if r.get("pass"))
    failed = len(results) - passed
    avg_latency = sum(r.get("latency_ms", 0) for r in results) / len(results) if results else 0

    return {
        "summary": {
            "total_questions": len(results),
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / len(results), 2) if results else 0,
            "avg_latency_ms": round(avg_latency, 1),
            "mode": "mock" if use_mock else "live",
        },
        "results": results,
    }


def print_summary_table(report: Dict[str, Any]) -> None:
    """Print a human-readable summary table to stdout."""
    summary = report["summary"]
    results = report["results"]

    print("\n" + "=" * 72)
    print("  AI Assist Lab — Evaluation Report")
    print("=" * 72)
    print(f"  Mode:            {summary['mode']}")
    print(f"  Total questions:  {summary['total_questions']}")
    print(f"  Passed:           {summary['passed']}")
    print(f"  Failed:           {summary['failed']}")
    print(f"  Pass rate:        {summary['pass_rate'] * 100:.0f}%")
    print(f"  Avg latency:      {summary['avg_latency_ms']:.1f} ms")
    print("-" * 72)
    print(f"  {'ID':<10} {'Difficulty':<10} {'Topics':<10} {'Sources':<10} {'Latency':<12} {'Result'}")
    print("-" * 72)

    for r in results:
        if "error" in r:
            print(f"  {r['id']:<10} {r.get('difficulty', '-'):<10} {'ERROR':<10} {'-':<10} {r['latency_ms']:<12.1f} ❌ FAIL")
            continue
        topics = f"{len(r['topic_hits'])}/{len(r['expected_topics'])}"
        sources = f"{r['source_count']}"
        status = "✅ PASS" if r["pass"] else "❌ FAIL"
        print(f"  {r['id']:<10} {r['difficulty']:<10} {topics:<10} {sources:<10} {r['latency_ms']:<12.1f} {status}")

    print("=" * 72)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="AI Assist Lab — Evaluation Harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=f"Path to the golden questions YAML file (default: {DEFAULT_DATASET})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path to write the JSON report (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run with mock RAG pipeline (no live Azure services needed)",
    )
    args = parser.parse_args()

    print(f"\n📂 Loading questions from: {args.dataset}")
    questions = load_questions(args.dataset)
    if not questions:
        sys.exit(1)

    print(f"🔬 Running evaluation ({len(questions)} questions, mode={'mock' if args.mock else 'live'})...\n")
    results = run_evaluation(questions, use_mock=args.mock)
    report = build_report(results, use_mock=args.mock)

    # Write JSON report
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 Report written to: {args.output}")

    print_summary_table(report)

    # Exit with non-zero if any failures
    if report["summary"]["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
