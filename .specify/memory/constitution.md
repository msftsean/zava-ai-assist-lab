<!--
Sync Impact Report
Version change: (template) -> 1.0.0
Modified principles: none (initial ratification)
Added sections:
  - Core Principles (5): Spec-Driven Delivery; Configuration Over Code; Static Site Integrity;
    Safe and Reversible Deployments; Test and Verify Before Done
  - Additional Constraints (hosting, tooling, content style)
  - Development Workflow (branching, checkpoints, reviews)
  - Governance
Removed sections: none
Templates requiring updates:
  - .specify/templates/plan-template.md (Constitution Check) - reviewed, compatible
  - .specify/templates/spec-template.md - reviewed, compatible
  - .specify/templates/tasks-template.md - reviewed, compatible
Deferred TODOs: none
-->

# AI Assist Lab Constitution

## Core Principles

### I. Spec-Driven Delivery
Every non-trivial change MUST flow through the Spec Kit sequence: constitution, then spec, then
plan, then tasks, then implementation. Specs describe the WHAT and WHY in business terms and MUST
avoid prescribing implementation detail. No code or infrastructure change begins until its spec and
plan exist and are approved. Rationale: a written, reviewable trail keeps human owners in control of
intent and lets the work be paused, audited, and resumed at any checkpoint.

### II. Configuration Over Code
Cloud and environment selection MUST be driven by configuration and environment variables, never by
hardcoded branches in application code. Application code reads settings through the centralized
`Settings` class in `app/config.py`; it MUST NOT read `os.environ` directly. The same codebase MUST
run unchanged against Azure Government and Azure Commercial. Rationale: one codebase serving multiple
clouds stays maintainable only when the cloud is a value, not a code path.

### III. Static Site Integrity
The `site/` directory is a pure static site with no build step. Generated routing and hosting
configuration MUST preserve the real multi-page structure (`index.html`, `pages/*.html`, `show/*`).
SPA-style catch-all rewrites to a single `index.html` are PROHIBITED because real `.html` pages exist
and must resolve directly. Asset paths and MIME types MUST remain correct after any hosting change.
Rationale: the lab site is documentation; broken links or swallowed pages erode trust in the demo.

### IV. Safe and Reversible Deployments
Deployment changes MUST be additive and reversible by default. Existing publish paths (for example
GitHub Pages) MUST NOT be removed or disabled without explicit owner approval; disabling a trigger is
preferred over deleting a workflow. Every deployment change MUST ship with documented rollback steps.
Secrets and deployment tokens MUST never be printed, logged, or committed. Rationale: a live demo
environment must always have a known-good state to fall back to.

### V. Test and Verify Before Done
A task is complete only when its outcome is verified and persistent. Existing linters, builds, and
tests MUST pass before and after a change; new tooling is added only when the task requires it. Unit
tests run with no live Azure services and MUST stay green. Deploy changes MUST be verified against a
real preview or endpoint (for example, confirming `index.html` and a known sub-page serve) before the
change is declared done. Rationale: "it should work" is not evidence; verification is.

## Additional Constraints

- Hosting: static content is served from `site/`. New hosting targets are created fresh and never
  silently reuse an existing resource.
- Tooling: Python 3.12 is the supported interpreter. On Windows, set `PYTHONUTF8=1` for Spec Kit and
  the eval harness to avoid `cp1252` encoding failures.
- Content style: generated content (docs, configs, commit messages, site copy) MUST NOT contain em
  dashes. Use hyphens, commas, or restructured sentences instead.
- Security: Azure authentication uses Entra identity where available; API keys and deployment tokens
  are treated as secrets and set only through secret stores or `gh secret set`.

## Development Workflow

- Branching: all work happens on a feature branch, never directly on `main`.
- Checkpoints: multi-phase work PAUSES at each defined checkpoint for owner approval before
  proceeding to the next phase.
- Reviews: changes that touch deployment, infrastructure, or hosting list every changed file before
  any push, and surface rollback steps in the summary.
- Verification gate: run the repository's existing tests and any relevant deploy verification before
  marking work done.

## Governance

This constitution supersedes ad hoc practice for the AI Assist Lab repository. Amendments MUST be made
by editing this file, bumping the version per the policy below, and recording the change in the Sync
Impact Report comment at the top of this file.

Versioning policy (semantic):
- MAJOR: backward-incompatible governance or principle removal or redefinition.
- MINOR: a new principle or section, or materially expanded guidance.
- PATCH: clarifications, wording, or non-semantic refinements.

Compliance: every plan MUST include a Constitution Check, and reviewers MUST verify that deployment
changes are additive and reversible, that configuration drives cloud selection, that the static site
structure is preserved, and that generated content contains no em dashes. Complexity that violates a
principle MUST be justified in the plan's Complexity Tracking section or the change MUST be revised.

**Version**: 1.0.0 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
