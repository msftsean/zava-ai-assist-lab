# Guardrails Demo

An interactive, browser-based demo that shows a layered AI safety pipeline running in front of Azure OpenAI: **Prompt Shields → Input Content Safety → Azure OpenAI → Output Content Safety**, with a live audit trail.

## Overview & Goals

This demo is built to support conversations with **Motorola Solutions** and customers operating under **FedRAMP**-style audit regimes. It exists to make abstract guardrail concepts concrete during an architecture review:

- **Show, not tell.** A presenter can drive an end-to-end safety pipeline live, in under a minute per scenario.
- **Demonstrate defense in depth.** Prompt injection, harmful input, harmful output, and custom blocklists are each handled by a distinct stage with its own verdict.
- **Illustrate auditability.** Every request lands in a structured audit entry — the same shape that would feed a FedRAMP `AU-2` / `AU-3` audit pipeline if persisted.
- **Make tuning visible.** Operators can flip between `strict`, `standard`, and `relaxed` filter profiles, edit thresholds, add blocklist terms, and toggle Prompt Shields without restarting the app.
- **Stay representative.** All scenarios use a public-safety dispatcher persona, matching the kind of workload Motorola Solutions cares about.

## Architecture

```
                                                         ┌──────────────────┐
                                                         │   Audit Buffer   │
                                                         │ (in-memory ring) │
                                                         └─────────▲────────┘
                                                                   │ append
                                                                   │
   ┌──────┐    ┌────────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────┐
   │ User │──▶ │ Prompt Shield  │──▶ │ Input Safety │──▶ │ Azure OpenAI │──▶ │ Output Safety  │──▶ │ Response │
   └──────┘    │ (Azure or      │    │ (profile +   │    │  (chat: pub. │    │ (profile)      │    └──────────┘
               │  regex fallback│    │  blocklist)  │    │  safety SOP) │    │                │
               └───────┬────────┘    └──────┬───────┘    └──────┬───────┘    └────────┬───────┘
                       │                    │                   │                     │
                       └────────────────────┴───────────────────┴─────────────────────┘
                                                   │
                                            verdicts + traces
                                                   │
                                                   ▼
                                          (fanout to Audit Buffer)
```

**Verdicts emitted by the pipeline:**

| Verdict              | Meaning                                                        |
|----------------------|----------------------------------------------------------------|
| `allowed`            | Passed all stages; response returned to user.                  |
| `blocked_input`      | Input Content Safety (or blocklist) blocked the prompt.        |
| `blocked_output`     | Model produced a response that failed Output Content Safety.   |
| `injection_flagged`  | Prompt Shields (or regex fallback) detected injection intent.  |
| `error_*`            | Stage-specific upstream failure (e.g., `error_openai`).        |

## Required Azure Resources

| Resource                       | Notes                                                                                          |
|--------------------------------|------------------------------------------------------------------------------------------------|
| **Azure OpenAI**               | Chat deployment whose name matches `AZURE_OPENAI_CHAT_DEPLOYMENT` (e.g., `gpt-4o`).            |
| **Azure AI Content Safety**    | Used for both input/output category analysis **and** Prompt Shields (`text:shieldPrompt`).     |

**Recommended roles** (when using Managed Identity instead of keys):

- `Cognitive Services OpenAI User` on the Azure OpenAI resource.
- `Cognitive Services User` on the Azure AI Content Safety resource.

> **Region note:** Prompt Shields availability differs from base Content Safety. Confirm the region supports `api-version=2024-09-01` of the `text:shieldPrompt` action before demoing — especially in Azure Government.

## Environment Variables

The demo reuses the standard repo configuration (`app/.env.example`). The keys it actually exercises:

```bash
# Azure OpenAI (chat completion)
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o

# Azure AI Content Safety + Prompt Shields
AZURE_CONTENT_SAFETY_ENDPOINT=https://<resource>.cognitiveservices.azure.com
# API key OR keyless (Entra ID) — leave key empty to use DefaultAzureCredential
AZURE_CONTENT_SAFETY_API_KEY=<key-or-leave-empty-for-entra-id>

# Guardrails demo flags
ENABLE_PROMPT_SHIELDS=true
PROMPT_SHIELDS_API_VERSION=2024-09-01
DEMO_AUDIT_MAX=200
```

| Variable                     | Default       | Purpose                                                     |
|------------------------------|---------------|-------------------------------------------------------------|
| `ENABLE_PROMPT_SHIELDS`      | `true`        | If `false`, skip Azure call and use regex fallback only.    |
| `PROMPT_SHIELDS_API_VERSION` | `2024-09-01`  | API version passed to `text:shieldPrompt`.                  |
| `DEMO_AUDIT_MAX`             | `200`         | Max entries retained in the in-memory audit ring buffer.    |

### Keyless (Entra ID) Auth for Content Safety

If your Content Safety / Foundry resource has **`disableLocalAuth=true`** (the
secure default Microsoft pushes — keys are turned off at the resource level),
leave `AZURE_CONTENT_SAFETY_API_KEY` empty and the app will authenticate via
`DefaultAzureCredential`:

```bash
# 1. Sign in
az login

# 2. Grant yourself the Cognitive Services User role on the resource
az role assignment create \
  --assignee $(az ad signed-in-user show --query id -o tsv) \
  --role "Cognitive Services User" \
  --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<name>"
```

The same path works for managed identities in production — assign the role to
the app's managed identity and `DefaultAzureCredential` will pick it up
automatically. No code change required.

See `app/.env.example` for the full list (Gov vs. Commercial endpoint suffixes, Search/Storage/Postgres, etc.).

## Run Locally

```bash
pip install -r app/requirements.txt
cp app/.env.example app/.env   # then edit values
uvicorn app.main:app --reload --port 8000
```

Open the demo UI:

```
http://localhost:8000/demo/
```

The root path `/` redirects to `/demo/`.

## Run in Docker

The existing `Dockerfile` and `docker-compose.yml` already build and serve `app.main:app`, so the demo is included automatically:

```bash
docker compose up -d
# then open http://localhost:8000/demo/
```

Make sure the `.env` file (or compose `environment:` block) has the Azure OpenAI and Content Safety values from above.

## Endpoint Reference

| Method | Path                  | Purpose                                                                 |
|--------|-----------------------|-------------------------------------------------------------------------|
| GET    | `/demo/`              | Static HTML UI (`app/demo/static/index.html`).                          |
| GET    | `/demo/scenarios`     | Returns the prebuilt scenario prompts.                                  |
| GET    | `/demo/profiles`      | Returns `strict` / `standard` / `relaxed` profiles + category metadata. |
| GET    | `/demo/config`        | Current runtime config (profile, thresholds, blocklist, shield flag).   |
| POST   | `/demo/config`        | Partial update — see body shape below.                                  |
| POST   | `/demo/chat`          | Run the full pipeline against a prompt; returns trace + `audit_id`.     |
| GET    | `/demo/audit?limit=N` | Newest-first slice of the audit ring buffer.                            |
| DELETE | `/demo/audit`         | Clear the audit ring buffer.                                            |

**`POST /demo/config`** body (all fields optional):

```json
{
  "profile_name": "standard",
  "custom_thresholds": { "Hate": 4, "Violence": 4, "SelfHarm": 2, "Sexual": 4 },
  "blocklist": ["operation-redshield"],
  "prompt_shield_enabled": true
}
```

**`POST /demo/chat`** body:

```json
{ "prompt": "Dispatch units to a 10-50 at 5th and Main." }
```

The response includes per-stage results (`prompt_shield`, `input_safety`, `model`, `output_safety`), a final `verdict`, and an `audit_id` you can correlate with `GET /demo/audit`.

**Available scenarios** (via `GET /demo/scenarios`):

- `valid_public_safety` — clean dispatcher request, should pass.
- `malicious` — harmful intent, should be blocked at input safety.
- `edge_case_report` — graphic-but-legitimate incident report; useful for false-positive demos.
- `prompt_injection` — classic "ignore previous instructions" attack.
- `output_risk` — prompt designed to coax unsafe model output.

## Demo Script

A presenter-friendly walkthrough. Each step is intentionally short so the whole demo runs in 5–7 minutes.

### Step 1 — Baseline on `standard`

> "Out of the box we ship a `standard` profile — moderate severity thresholds, Prompt Shields on, no custom blocklist. Let's run all four scenarios."

1. Confirm the profile selector reads `standard` and Prompt Shields is **on**.
2. Run each scenario in order:
   - `valid_public_safety` → expect **`allowed`**, model returns a dispatcher-style answer.
   - `malicious` → expect **`blocked_input`** (harmful category trips input safety).
   - `prompt_injection` → expect **`injection_flagged`** (Prompt Shields fires).
   - `output_risk` → expect either **`blocked_output`** or **`allowed`** with a refusal — point at the output-safety stage in the trace either way.

### Step 2 — Switch to `strict` to surface a false positive

> "Compliance teams often ask for the strictest setting. Let's see the trade-off."

1. Set profile to **`strict`**.
2. Re-run **`edge_case_report`**. Expect **`blocked_input`** even though the content is a legitimate incident report.
3. Open the trace for that request and point at the elevated severity score that crossed the strict threshold. This is the moment to discuss "tunable thresholds, not binary on/off."

### Step 3 — `relaxed` + custom blocklist precedence

> "Now imagine a customer-specific term we *must* block regardless of profile."

1. Set profile to **`relaxed`** so generic categories are very permissive.
2. Add a blocklist term that appears in your demo prompt — e.g., `operation-redshield`.
3. Send a prompt that includes that term, e.g.:

   ```
   Brief me on operation-redshield deployment status.
   ```

4. Expect **`blocked_input`** with a `Blocklist` category in the input-safety trace.
5. Talking point: "Even with categories dialed down, the blocklist still wins — this is how customers express organization-specific policy."

### Step 4 — Toggle Prompt Shields off, fall back to regex

> "What happens if Prompt Shields is unavailable, or the customer hasn't licensed it yet?"

1. Toggle **Prompt Shields off** (`prompt_shield_enabled: false`).
2. Re-run **`prompt_injection`**.
3. Show in the trace that the `prompt_shield` stage now reports the **regex fallback detector** rather than the Azure call. Verdict should still be **`injection_flagged`**.
4. Talking point: "We never depend on a single control — every stage has a degraded mode."

### Step 5 — Audit panel = FedRAMP audit trail

> "Every request you just saw produced one of these."

1. Open the **Audit** panel (`GET /demo/audit?limit=20`).
2. Walk through one entry: prompt, per-stage verdicts, profile in effect, blocklist hits, model output, final verdict.
3. Talking point: "In production, this same record shape is what we'd ship to an immutable store — Log Analytics, Event Hubs, or a SIEM — to satisfy FedRAMP `AU-2` (auditable events) and `AU-3` (content of audit records). Today it's an in-memory ring buffer so you can see it without infrastructure."
4. (Optional) `DELETE /demo/audit` to reset before the next demo.

## Limitations

- **In-memory only.** The audit ring buffer lives in process memory. Restarting the app clears it.
- **Single-process.** No coordination between workers — do not run with multiple Uvicorn workers if you need consistent audit and config state.
- **No persistence.** Runtime config changes (profile, thresholds, blocklist, shield toggle) are not written to disk; they reset on restart to defaults from `app/config.py`.
- **Region availability.** Prompt Shields is not GA in every Azure region, especially in Azure Government. Verify before demoing on Gov.
- **Demo-grade auth.** The `/demo/*` routes are unauthenticated by design for live presentations. Do not expose them publicly without adding auth.

## Troubleshooting

| Symptom                                                         | Likely cause / fix                                                                                          |
|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Prompt Shields returns **404**                                  | Region doesn't support `text:shieldPrompt` at this api-version. Check `PROMPT_SHIELDS_API_VERSION` and region. |
| Prompt Shields returns **401 / 403**                            | `AZURE_CONTENT_SAFETY_API_KEY` missing or wrong; or Managed Identity lacks `Cognitive Services User`.       |
| `error_openai` verdict on every request                         | Deployment name mismatch — `AZURE_OPENAI_CHAT_DEPLOYMENT` must equal the *deployment* name, not the model.  |
| `prompt_shield` always reports regex fallback                   | `ENABLE_PROMPT_SHIELDS=false`, missing Content Safety creds, or upstream Azure error — check app logs.      |
| `/demo/` returns 404                                            | The router isn't mounted; confirm `app/main.py` calls `include_router(demo_router)` and reload the app.     |
| Audit endpoint returns empty list after restart                 | Expected — the ring buffer is in-memory and resets every restart (`DEMO_AUDIT_MAX` controls capacity).      |
| Blocklist term doesn't trigger                                  | Matching is performed against the raw prompt; confirm casing/whitespace and that the term is in `GET /demo/config`. |
