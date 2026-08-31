# Technical Case Study: CRM Health Doctor MVP

## Executive summary

CRM Health Doctor was demonstrated live as a read-only, deterministic analyzer for selected HubSpot CRM reliability signals. It transformed approved contact and deal fields into an auditable health score, issue categories, a prioritized review queue, record-level explanations, and a self-contained HTML report.

The case study documents a controlled hackathon prototype. It does not describe a production deployment or customer outcome.

## Confirmed facts

### The problem framed for the MVP

CRM automation and AI workflows depend on records being sufficiently owned, current, and usable. The MVP focused on a narrower technical question: can selected reliability defects be detected and explained without allowing the analyzer to modify CRM data?

### Scope delivered

The demonstrated workflow supported:

- contacts and deals;
- missing-owner checks across both object types;
- stale-open-deal checks;
- explicit contact-name formatting checks;
- missing or stale contact-activity checks;
- weighted category scoring with denominator visibility;
- deterministic priority ranking and issue consolidation;
- escaped, dependency-free HTML report generation.

### Data and access controls

- Demonstration data was synthetic/test data.
- HubSpot orchestration was governed by a two-operation read allowlist: `get_user_details` and `search_crm_objects`.
- No create, update, merge, delete, note, or task operation was part of the application contract.
- The engine consumed local JSON envelopes rather than making connector calls itself.
- Raw HubSpot record IDs were discarded during normalization and replaced with run-local aliases.
- Reports loaded no external scripts, fonts, analytics, or CDN assets.

### Processing flow

1. A fixture or sanitized HubSpot search envelope is loaded.
2. Source fields are normalized into internal contact and deal records.
3. Pure rules emit structured issues with category, type, explanation, base severity, and optional age bonus.
4. Category scores are calculated from unique flagged records and applicable denominators.
5. Issues are consolidated by record and ranked deterministically.
6. An escaped HTML report renders the scorecard, counts, queue, explanations, and methodology.

### Reproducible fixture result

Using the preserved fixture and the evaluation time `2026-08-20T12:00:00Z`, the application produces:

| Measure | Result |
|---|---:|
| Contacts | 8 |
| Deals | 5 |
| Issue instances | 10 |
| Records in review queue | 8 |
| Overall health score | 60.4 |

Category audit:

| Category | Flagged | Applicable | Category score |
|---|---:|---:|---:|
| Missing owner | 2 | 13 | 84.6 |
| Stale open deals | 2 | 3 | 33.3 |
| Name quality | 3 | 8 | 62.5 |
| Contact activity | 3 | 8 | 62.5 |

These values are synthetic fixture outputs designed to exercise the rules. They are not organizational performance results.

### Verification evidence

The 20-test suite covers:

- fixed fixture expectations and the 60.4 score;
- exact 30/31-day and 90/91-day threshold boundaries;
- closed-deal exclusion from stale-open-deal evaluation;
- missing timestamps and creation-time fallback behavior;
- Unicode-aware name checks;
- zero-applicability weight renormalization;
- cross-object missing-owner applicability;
- read-only tool allowlisting;
- HubSpot ID removal;
- HTML escaping and absence of external assets;
- stable queue tie-breaking.

## Technical decisions and tradeoffs

### Deterministic rules over model inference

This made outputs reproducible and explanations auditable. The tradeoff is limited semantic coverage: the engine detects only encoded controls and cannot infer business-specific context.

### Read-only-first boundary

This reduced the blast radius and made the demo suitable for controlled inspection. The tradeoff is that remediation remains outside the product.

### Explicit denominators and weight renormalization

Each category exposes both flagged and applicable counts. Categories with no applicable records are excluded rather than treated as perfect. The tradeoff is that the overall score can change composition across datasets, so comparisons require category context.

### Local, self-contained reporting

The report is portable and avoids external dependencies. The tradeoff is the absence of collaborative workflows, historical trends, and live drill-down.

## Observations

- The visible evidence chain—score, categories, queue, and explanations—made the prototype easier to inspect than a single composite score would have.
- The read-only and deterministic design supported a credible governance story.
- Event response suggested that the technical evidence should be paired with a clearer buyer problem and business consequence.

These observations are qualitative and were not collected through formal research.

## Hypotheses for product evolution

- The same evidence engine could support a fixed-scope Clarity Integrations CRM Reliability Assessment after the control catalog and delivery workflow are validated.
- Historical runs and owner-facing workflows could evolve the analyzer into a recurring CRM Reliability Agent.
- Additional evidence domains—schema fitness, lifecycle integrity, association coverage, duplication, workflow dependencies, consent, and integration health—could contribute to an AI Readiness Assessment.

## Current limitations

- The HubSpot connector call is external to the application.
- The test-portal snapshot contains only two synthetic contacts and no deals.
- The score weights and thresholds are prototype policies, not externally validated standards.
- Aliases are stable only within a consistently ordered run.
- Activity coverage relies on three summary timestamps.
- There is no tenant model, scheduler, persistence, trend analysis, authentication, write-back, or operational monitoring.
- No accuracy, productivity, revenue, or adoption outcome was measured.
