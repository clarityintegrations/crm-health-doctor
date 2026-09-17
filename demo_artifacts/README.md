# Authentic Astra demo captures

**Previously generated real GPT-6 Astra assessment**

These files are captured real inference results, not live inference during playback.
They are not mocks. No substantive assessment content was edited. `record_id` is
a synthetic record alias, not a raw CRM identifier. API credentials, request
headers, environment values, billing information and local source paths are excluded.

| Artifact | Source | Original completion (UTC) |
| --- | --- | --- |
| `c008_real_astra_sanitized.json` | Successful instrumented UI request, captured verbatim in the response envelope | 2026-09-17T14:03:19.282405+00:00 |
| `c001_real_astra_sanitized.json` | Exact earlier CLI response recovered from this task's recorded tool output | 2026-09-17T13:42:59.172410+00:00 |

Both stored evidence payloads and assessments passed the unchanged input schema,
output schema and traceability validator again during preparation. Each artifact
retains its response ID, completion time, audit ID, reasoning setting and duration.
`content_sha256` covers canonical JSON of the evidence and assessment (sorted keys,
compact separators). It establishes integrity from capture, not a provider signature.

C-008 has three findings, deterministic priority 95 and a qualitative Data estimate
of 40/100. Its overall readiness and other dimensions are unknown. C-001 has zero
findings and priority 0; overall readiness and every dimension remain unknown.
The model estimate is not the deterministic score or measured organizational readiness.

## Smallest honest recording path — 150-second target

No replay system is implemented. Open the local deterministic evidence page and
these JSON captures in a readable viewer. Keep the capture label visible when
showing model output. Do not click Assess and imply these captures are its result.

| Time | Show and say |
| --- | --- |
| 0–15s | Introduce the problem: agents depend on reliable CRM context. Deterministic checks supply facts; Astra reasons over them. |
| 15–40s | Show C-008's malformed name, missing owner, weak activity and priority 95 in the local evidence page. |
| 40–85s | Show the labeled C-008 capture: bounded Data estimate, unknown overall readiness, supervised review opportunity, conditional name cleanup, unsupported autonomous recency decisions, remediation and evidence gaps. |
| 85–125s | Show C-001's zero findings and priority 0, then its labeled real capture: no invented remediation, all dimensions unknown, supervised evidence summary and evidence-acquisition next steps. |
| 125–150s | Conclude: CRM Health Doctor identifies deterministic CRM health issues. GPT-6 Astra evaluates their implications for agent readiness while preserving uncertainty and human review. No detected CRM issue does not equal proven agent readiness. |

This is a narration budget, not a measured recording result. Rehearse once before
claiming the 150-second gate. Live runtime inference has been demonstrated separately;
latency and validation rejection make it unsuitable as the recording's only path.

## Diagnostic closeout

Confirmed: an instrumented C-008 UI reproduction received HTTP 200 and schema-valid
output but failed traceability validation (`invalid_assessment`, 38.39 seconds).
The specific rejecting rule was not retained for that reproduction. A separate CLI
attempt timed out at 60.17 seconds before an HTTP response was received. A bounded
UI verification succeeded with all validation intact at approximately 38 seconds.

The instrumented CLI and UI requests had identical normalized evidence, prompt and
schema hashes, medium reasoning and 6,500 maximum output tokens. Their only payload
variation was generation time. Both use the same service and adapter, with no retry
or caching. The server adds same-origin/body checks and an assessment lock; its
five-second inbound socket timeout does not replace the adapter's 60-second API timeout.

Inference variability and API/transport latency are plausible explanations. There
is no proven repeatable UI/server implementation defect, nor enough evidence to
assign the two older uninstrumented failures a specific cause. No product-code fix,
prompt tuning or validation weakening was justified or performed. The temporary
diagnostic server was stopped and its harness removed; the original server was retained.
