# CRM Health Doctor — Agent Readiness Edition

Status updated September 17, 2026: real `gpt-6-astra` access and successful C-008/C-001 assessments are verified. Authentic sanitized captures were committed in `3c6483d`. Independent adversarial QA subsequently found P0 claim-support and score-admissibility defects. This remediation adds a fail-closed support policy and offline production-path counterexamples; independent re-review remains the launch gate. The under-150-second narrated recording has not yet been measured.

Historical September 16 status (superseded, retained for provenance): API requests returned HTTP 429 / `credit_balance_exhausted`; no successful real assessment or sanitized example existed at that time. Credits were subsequently restored. This is no longer the current blocker.

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

Strict JSON schema with required keys, `additionalProperties: false`, bounded lists and strings (no schema-version field yet):

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

Every claim carries a concise statement, basis (`direct`, `inference`, `assumption`, or `evidence_gap` in the existing schema), valid supplied reference IDs, and `human_review_required: true`. The launch support policy is narrower than that schema: unconstrained assumptions are rejected. Missing evidence cannot establish a factual blocker or justify a score. Unknown dimensions must have null scores and an explicit gap. Overall readiness remains null for this limited contract.

Reject malformed JSON, extra fields, out-of-range values, unknown references, unsupported scored dimensions, weakened human-review requirements, or claims outside the supported vocabulary. Schema/reference validity alone is insufficient.

### P0 deterministic support policy

`readiness/support_policy.py` enforces reviewed claim classes from
`readiness/support_catalog.json`. This is a closed controlled-language policy, not
arbitrary natural-language entailment, keyword matching, or a second LLM judge.
Every statement/rationale pair must exactly match approved wording and satisfy
evidence-type and placement predicates. Gap details and limitations are also
constrained; they cannot carry invented facts around the claim validator.

| Evidence | Permitted implications |
| --- | --- |
| Malformed name | Conditional human-verified cleanup; no invented replacement identity/name |
| Missing owner | Accountability/routing risk and human assignment verification; no asserted routing workflow or correct owner |
| Weak activity | Incomplete signal/recency confidence and no autonomous recency decision from that snapshot; not proof of inactivity |
| Bounded observations with no findings | Supervised evidence summary and verification; not readiness certification |
| Scope limits | Unknown dimensions and evidence acquisition; never factual defects, numeric scores or authorization |

Direct claims require an exact concrete evidence quote AND a fixed safe rationale.
Inferences require applicable concrete evidence, an approved claim class and the
correct output section. There is no approved wording granting consent, permissions,
write access, execution, autonomous deployment, or exemption from human review.
Numbers and ordering asserted in the reviewed remediation wording are checked
against actual finding priorities. Rules operate on finding types, not record aliases.

Numeric Data estimates require a cited, approved concrete finding combination
and the explicit `data_risk` scoring claim. Scope-only references, clean observations,
direct quotes and unscored/gap claims cannot justify a number. Thus C-001 remains
all-null; C-008's authentic 40 estimate remains admissible. The score must match
the number in the reviewed scoring statement, remains in coarse steps of five,
and is not a new deterministic formula. All other dimensions and overall readiness
remain null. The authentic artifacts remain byte-for-byte unchanged and validate.

The phrase catalog incorporates independently reviewed wording from the authentic
captures, but production never reads or trusts demo artifacts as validation policy.
This deliberate safety/availability tradeoff rejects novel safe paraphrases too.
The existing prompt and provider schema were not changed to force catalog wording;
fresh inference may therefore fail closed more often. Do not weaken the validator
or claim live reliability based on preserved examples. Vocabulary expansion or
provider guidance requires separate review, not automatic acceptance of new output.

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

Recording path: show deterministic C-008 evidence, its explicitly labeled previously generated real Astra capture, then C-001's evidence and capture. Keep human-review and unknown-dimension boundaries visible. Use the 150-second narration plan in `demo_artifacts/README.md`; do not present playback as live inference. The timing still needs a measured rehearsal.

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
node tests/test_readiness_adversarial_ui.mjs
```

Server tests require permission to bind a loopback socket. Existing V1 tests are unmodified. New tests cover evidence construction, schema/reference rejection, unknown dimensions, mocks for both scenarios, missing key, timeout, malformed/partial/refused output, API/auth/model errors, quota failure, secret-safe errors/logs, same-origin HTTP behavior, text-only presentation, and failure retention of deterministic findings.

## Live validation status and next gate

Real access for exactly `gpt-6-astra` was verified after credits were restored.
Both real C-008 and C-001 assessments passed their original semantic review and
were preserved under `demo_artifacts/` in commit `3c6483d`. These are not mocks.

Later diagnostic testing observed one HTTP-200/schema-valid response rejected by
traceability, a separate approximately 60-second timeout, and a subsequent successful
C-008 UI assessment. The first rejecting rule was not retained. This demonstrates
runtime variability, not a proven deterministic UI/server defect. No new live calls
are part of this P0 remediation.

The independent audit's current blockers were unsupported claims accepted with valid
references (P0-1) and scope-only/contradictory Data scores (P0-2). They are addressed
by the bounded support and score-admissibility policy above, with all 13 reported
counterexample classes rejected through adapter, service, HTTP and unchanged UI tests.
Independent review of the patch and a measured under-150-second recording remain.

Official model reference: https://developers.openai.com/api/docs/models/gpt-6-astra
