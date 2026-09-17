# CRM Health Doctor — Agent Readiness Edition

Status: offline implementation complete; live acceptance blocked by API credit balance. The key was loaded securely and `gpt-6-astra` model access was confirmed. Assessment requests returned HTTP 429 / `credit_balance_exhausted`. No successful real assessment or sanitized live example exists. Verified September 16, 2026 (America/Bogota).

## Protected V1 and concurrent work

- V1 commit: `75d972ff0d2a9fb25e24ac6bc91120c8c69c387b`.
- Checkpoint tag: `webmcp-v1-before-astra-2026-09-16` (created on September 16).
- Evolution branch: `astra-agent-readiness`, in a separate worktree.
- The original checkout remains on `challenge/webmcp-2026` at `e4686a8`; two remote documentation commits were fetched and inspected without advancing that checkout.
- The latest published branch changes only README relative to `e4686a8`. All existing rules, scoring, tests, and static artifacts are identical.
- There was one local worktree, no uncommitted work, and no existing Astra branch when inspected. This does not establish that another account is inactive. Recheck branch/worktree state before every implementation commit.
- Existing static deployment and `outputs/index.html` remain V1. No deployment configuration is checked into this repository; the previously validated Render configuration is external state.

## Minimal runtime architecture

Existing fixture and deterministic engine → structured evidence builder → server-side Responses API adapter (`gpt-6-astra`) → schema and evidence-reference validator → local readiness presentation.

Reuse `load_dataset`, `evaluate`, `build_queue`, `calculate_score`, `guidance_for`, and the V1 report. Keep new code in a separate `readiness/` package. Do not alter V1 rules or the three WebMCP tools. Serve the unchanged V1 report and a small readiness panel through a separate localhost-only server. Only fixed synthetic scenarios may be selected; do not accept arbitrary CRM payloads, URLs, or provider endpoints from the browser. A user-triggered assessment request may contact the fixed OpenAI Responses endpoint. The key stays in server-side `OPENAI_API_KEY` and is never logged, returned, or committed.

## Implemented input contract

Versioned JSON schema with required keys, `additionalProperties: false`, bounded lists and strings:

- `audit_id`: stable identifier derived from fixture, evaluation configuration, and record alias.
- `record`: alias and entity type; omit raw CRM ID, names, emails, owner IDs, and raw payload.
- `findings`: finding ID, issue type, original numeric severity points, original priority contribution (severity plus age bonus), controlled evidence, deterministic impact, and `human_review_required: true`.
- `observations`: identified, narrowly scoped check results for owner presence, name-format checks, and approved activity presence/age. Necessary to express positive evidence for a record with no findings. Passing a check does not establish business identity, consent, correct ownership, or complete engagement history.
- `audit_metadata`: finding count, record priority, source `fixture`, snapshot evaluation date, separately labeled generation time, and audit scope. Do not substitute today's date for the preserved fixture evaluation date.
- `scope_limits`: explicit scope limits. No supplied evidence establishes knowledge-base coverage, process design, enterprise governance, integration health, consent, or suitability for autonomous operation.

Every observation, finding, and scope limit receives a stable reference ID. Derive evidence from existing normalized fields and deterministic results; do not send arbitrary record text as instructions.

## Implemented output contract

Use Responses API Structured Outputs with a strict JSON Schema, then validate locally before presentation. Preserve the exact model `gpt-6-astra`; do not silently fall back to another model.

Required top-level keys:

- `overall_readiness_score`: integer 0–100 or null when overall readiness cannot be justified.
- `dimension_scores`: exactly `data`, `process`, `knowledge`, `governance`, `integrations`, each numeric or null. `dimension_assessments` contains a traceable claim explaining each dimension. Unknown dimensions have null scores and an explicit gap.
- `critical_blockers`, `viable_agent_opportunities`, `conditional_agent_opportunities`, `not_ready_agent_opportunities`, `remediation_priorities`, `recommended_next_actions`: bounded claim lists.
- `evidence_references`, `evidence_gaps`, `confidence`, `limitations`.

Every claim carries a concise statement, basis (`direct`, `inference`, `assumption`, or `evidence_gap`), valid supplied reference IDs, and `human_review_required: true`. Inferences must explain the connection. Assumptions and evidence gaps must be presented explicitly. Missing evidence cannot establish a factual blocker or justify a negative score. Unknown dimensions must have null scores and a description of the missing evidence. Do not aggregate only the known dimensions into an apparently comprehensive overall score; an overall null is valid and expected for limited CRM evidence.

Reject malformed JSON, extra fields, out-of-range values, unknown references, unsupported scored dimensions, or weakened human-review requirements. Schema/reference validation establishes structure and traceability, not complete semantic truth; inspect real model outputs for unsupported factual claims before accepting the slice.

## Comparison scenarios

- `C-008`: existing malformed-name, missing-owner, and weak-activity findings; record priority 95. Let Astra derive the business implications from supplied evidence.
- `C-001`: existing fixture record with owner present, no flagged name-format issue, and a recent approved activity signal at the fixed evaluation date. Confirm this through the existing engine before building its payload. No findings means only that the implemented checks found none.

Compare supported Data reasoning and opportunities, without requiring different scores on unsupported dimensions. Knowledge, Process, Governance, and Integrations may remain unknown in both. Do not hard-code opportunities or a negative/positive business conclusion.

## Failure and security contract

Missing key, timeout, provider error, refusal, incomplete response, malformed JSON, schema failure, or evidence-validation failure produces `AI readiness layer unavailable` with a bounded generic reason. Keep deterministic findings visible. Never fabricate an assessment or display a stale result for another alias. Escape model text and render it as text. No CRM writes or model-invoked tools. Bound request duration, response bytes, and output tokens. Disable storage in the Responses request and do not persist CRM or assessment content by default.

The local server must reject non-local origins/hosts and unknown aliases, and prevent overlapping uncontrolled model calls. Public deployment hardening is outside this slice; do not expose an unauthenticated paid API endpoint publicly.

## Acceptance and demo

Required tests: both fixture scenarios; evidence payload schema; strict output schema; invalid references; scored-unknown dimensions; timeout; malformed output; schema failure; missing key; API error; refusal/incomplete response; safe rendering; unchanged V1 regression suite.

Live acceptance requires actual Responses API calls to `gpt-6-astra` for both scenarios, validated outputs with traceable references, credible differences, and safe failure behavior. Mocks do not satisfy runtime acceptance. Retain only non-secret provenance such as model, response ID, timestamp, and payload hash when recording validation evidence.

Under-three-minute demonstration: show V1 deterministic C-008 findings; request Astra assessment and inspect cited implications plus unknown dimensions; compare C-001; demonstrate unavailable AI while deterministic evidence remains visible.

## Runtime, schemas, and tests

No third-party runtime dependency is required. `readiness/contracts.py` defines both JSON Schemas and validates the exact subset of schema keywords used. Export them for inspection with:

```bash
python3 -m readiness schema input
python3 -m readiness schema output
```

The production prompt lives in `readiness/astra.py`. The adapter uses the OpenAI Responses API with `model=gpt-6-astra`, strict `text.format` JSON Schema, `store=false`, a 60-second timeout, a bounded response size, and no tools. `ASTRA_REASONING_EFFORT` defaults to `medium`; `low`, `medium`, and `high` are accepted. Redirects are rejected. Error messages never include provider bodies, request headers, key values, or exception text; only fixed/allowlisted codes leave the boundary.

Provide `OPENAI_API_KEY` through the server process environment or a secure secret manager. Never put it in source, browser code, documentation, command-line arguments, or a tracked file. For an interactive zsh session, a silent prompt can populate the environment without placing the value in shell history:

```zsh
read -rs 'OPENAI_API_KEY?OpenAI API key: '
export OPENAI_API_KEY
```

Then verify access and start the local product:

```bash
python3 -m readiness check-access
python3 -m readiness serve
```

Open `http://127.0.0.1:8766`. Choose C-008 or C-001 and select **Assess with GPT-6 Astra**. `/v1` serves the unchanged V1 report; the new page links to it. The local server accepts only the fixed synthetic aliases, checks Host/Origin, and allows one model call at a time. It is a local demo server, not a public hosting architecture.

For a CLI assessment:

```bash
python3 -m readiness assess C-008
python3 -m readiness assess C-001
```

Optional `--output <file>` explicitly saves the sanitized envelope. Without that option, no model result is persisted by the application. After a session, `unset OPENAI_API_KEY` removes the shell variable. Secure or remove any plaintext file used to provision the key; the application does not read a key file itself.

All tests use synthetic mocks and need no key or external API access:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
node tests/test_webmcp_contract.mjs
node tests/test_readiness_ui.mjs
```

Server tests require permission to bind a loopback socket. Existing V1 tests are unmodified. New tests cover evidence construction, schema/reference rejection, unknown dimensions, mocks for both scenarios, missing key, timeout, malformed/partial/refused output, API/auth/model errors, quota failure, secret-safe errors/logs, same-origin HTTP behavior, text-only presentation, and failure retention of deterministic findings.

## Live validation status and next gate

Model discovery succeeded for exactly `gpt-6-astra`. Three assessment attempts (initial request, bounded-code retry, sanitized diagnostic) were rejected by the provider before any model output, with the final diagnostic confirming HTTP 429 / `credit_balance_exhausted`. No prompt refinement has been spent. No live result is represented by the test mocks.

Add API credits to the relevant OpenAI project/organization, then repeat the access check and both assessments through the production adapter. Validate schema and references, manually inspect factual/inference boundaries, and measure the full demo. A successful model-discovery request does not establish sufficient credits for inference. Live output quality and the under-three-minute live flow remain unverified until the billing blocker is resolved.

Official model reference: https://developers.openai.com/api/docs/models/gpt-6-astra
