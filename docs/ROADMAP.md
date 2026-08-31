# Improvement Roadmap

The roadmap protects the hackathon evidence while moving through validation gates. Dates are intentionally omitted until ownership and capacity are assigned.

## Confirmed starting point

The current MVP has deterministic checks for four categories, a governed read-only access contract, synthetic fixtures, a sanitized test-portal input, automated tests, deterministic scoring and prioritization, record explanations, and local HTML reporting.

It does not have validated commercial demand, representative multi-portal evidence, a production runtime, recurring monitoring, or CRM remediation.

## Observations shaping the roadmap

- The next increment should improve commercial clarity as well as technical breadth.
- Reliability should be connected to a defined AI use case, not presented as generic cleanup.
- Trust features—read-only access, explainability, visible denominators, and human review—should remain product requirements.
- Product expansion should follow evidence gates rather than the name progression alone.

## Hypothesized evolution

`CRM Health Doctor → CRM Reliability Assessment → CRM Reliability Agent → AI Readiness Assessment for HubSpot`

This sequence is not a committed product plan. Each transition depends on evidence from the preceding stage.

## Phase 0: preserve and package the artifact

**Outcome:** professional, reproducible evidence of the hackathon MVP.

- Freeze the implemented scoring contract and fixed-date fixture as the hackathon baseline.
- Keep generated reports, sanitized fixtures, and tests together with clear data labels.
- Add a release tag or immutable archive when the project is placed under version control.
- Capture a short demo walkthrough and screenshots without exposing portal identifiers.
- Use the technical case study and claim guardrails in portfolio materials.

**Exit evidence:** a reviewer can reproduce the fixture report, run all tests, trace each claim to an artifact, and distinguish demo outputs from product proposals.

## Phase 1: validate the assessment offer

**Outcome:** determine whether a scoped CRM Reliability Assessment solves a paid or high-priority problem.

### Product work

- Conduct structured discovery with plausible buyers and delivery stakeholders.
- Select one or two concrete HubSpot AI use cases as assessment anchors.
- Define control objectives, evidence requirements, unknown states, and exception handling.
- Create an executive summary and a remediation-backlog format.
- Define what is standard, configurable, and out of scope.

### Technical work

- Add scan metadata, property manifests, completeness indicators, and policy versioning.
- Make stable non-sensitive cross-run identifiers possible.
- Expand fixtures for permission gaps, malformed payloads, pagination, empty objects, and mixed pipelines.
- Add integration-contract tests around the orchestration boundary.
- Separate “failed,” “passed,” “not applicable,” and “unknown/not observed.”

**Exit evidence:** repeated buyer interest, reviewer agreement on the findings, successful use on representative authorized test environments, and a delivery scope that Clarity Integrations can price and execute. The project currently has none of this evidence.

## Phase 2: deliver controlled pilots

**Outcome:** learn whether the assessment is useful across real portal configurations.

- Run explicitly authorized, read-only assessments with documented scope and retention.
- Compare automated findings with human review; log false positives, false negatives, exceptions, and missing evidence.
- Calibrate controls by portal type and intended AI use case without hiding customizations.
- Produce a remediation plan with owner, severity, dependency, and acceptance criteria.
- Measure delivery effort, time to review, finding acceptance, and remediation follow-through.
- Add tenant isolation, authentication, secrets management, audit logging, rate-limit handling, and operational error reporting before handling production data at scale.

**Exit evidence:** representative pilot results show that findings are understandable, sufficiently accurate for the stated purpose, and worth acting on. No target threshold should be claimed until pilot design is agreed.

## Phase 3: test a CRM Reliability Agent

**Outcome:** determine whether recurring monitoring creates value beyond a periodic assessment.

- Add scheduled read-only scans, trend history, control-version compatibility, and change detection.
- Route findings to accountable owners with deduplication, suppression, and exception expiry.
- Track remediation status without silently modifying HubSpot records.
- Add alert-quality metrics and guard against notification fatigue.
- Provide human approval for any downstream action.

**Exit evidence:** users return to the monitoring view, act on recurring findings, and prefer recurrence to periodic manual assessment. This is a future validation gate, not a current outcome.

## Phase 4: validate an AI Readiness Assessment

**Outcome:** expand from CRM reliability to evidence for a defined HubSpot AI deployment decision.

- Add schema fitness, workflow dependencies, integration health, consent/governance, human oversight, and monitoring readiness.
- Map every control to a named AI use case and a documented failure mode.
- Include residual risk, accepted exceptions, unavailable evidence, and reassessment conditions.
- Seek legal, security, privacy, and domain review where applicable.
- Avoid a universal certification; deliver a scoped decision record.

**Exit evidence:** stakeholders use the assessment in an actual go/no-go or remediation decision and find its scope and evidence credible. That behavior has not yet been observed.

## Cross-cutting backlog

| Priority | Improvement | Why it matters |
|---|---|---|
| Now | Evidence labels and claim discipline | Prevents prototype results from becoming inflated product claims |
| Now | Policy and scan versioning | Makes outputs reproducible and comparisons defensible |
| Now | Completeness and unknown states | Prevents missing access or data from looking healthy |
| Next | Representative fixtures and contract tests | Tests behavior beyond the happy path |
| Next | Stable privacy-preserving record references | Enables cross-run follow-up without publishing raw IDs |
| Next | Configurable, approved control profiles | Supports portal and use-case differences transparently |
| Next | Assessment deliverable templates | Connects technical findings to executive and operational action |
| Later | Secure run history and trend comparison | Enables recurring reliability monitoring |
| Later | Owner workflow and exception lifecycle | Turns findings into governed follow-through |
| Conditional | Separately authorized remediation | Should follow demand, safety design, and explicit approval |

## Measures to define before pilots

- scan coverage and inaccessible-signal rate;
- finding acceptance and exception rate;
- false-positive and known-miss review method;
- time required to scope, run, review, and present an assessment;
- percentage of findings assigned and resolved;
- buyer willingness to pay and purchase path;
- repeat-assessment or monitoring interest;
- effect on a named operational or AI deployment decision.

These are proposed measures, not current results.

## Explicit non-goals until validated

- autonomous CRM cleanup;
- opaque AI-generated health scores;
- an unqualified AI-ready certification;
- claims of ROI, compliance, improved AI accuracy, or revenue impact;
- broad production deployment before security and operational controls exist.
