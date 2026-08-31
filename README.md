# CRM Health Doctor

CRM Health Doctor is a completed hackathon MVP and an exploration platform for a possible Clarity Integrations CRM reliability offering.

The project is now in **portfolio and product evolution mode**. The original implementation, synthetic fixtures, tests, and generated reports remain preserved as evidence of what was built. Future-looking documents are explicitly separated from hackathon facts.

## Evidence status

### Confirmed facts

- The MVP was demonstrated live during the HubSpot Building with AI Hackathon.
- It generated a CRM health score, issue categories, a prioritized review queue, record-level explanations, and a self-contained HTML report.
- It used synthetic/test data, deterministic scoring rules, read-only-first design, and governed HubSpot MCP access.
- The application has no HubSpot write path. Its orchestration allowlist contains only `get_user_details` and `search_crm_objects`.
- The local fixture run is reproducible: 8 contacts, 5 deals, 10 issues, 8 queue rows, and an overall score of 60.4 for the fixed evaluation date.
- The sanitized test-portal snapshot demonstrates the HubSpot data boundary, not representative CRM performance or broad rule coverage.

### Observations

- HubSpot emphasized developer workflows using tools such as Claude Code and Cursor.
- Stronger commercial storytelling appeared to create more audience impact than technical depth alone.
- CRM reliability before AI deployment appeared to be a stronger positioning angle than a standalone data-quality score.

These are post-event interpretations, not measured market results.

### Hypotheses

- Clarity Integrations may be able to package the MVP as a scoped CRM reliability assessment.
- A recurring CRM Reliability Agent may be valuable after the assessment workflow is validated.
- An AI Readiness Assessment may provide a commercially clearer umbrella by connecting CRM reliability to the safe deployment of AI workflows.

These are opportunities to test. The project does not claim customers, adoption, revenue, production readiness, or validated demand.

## Portfolio documents

- [Lessons learned](docs/LESSONS_LEARNED.md)
- [Technical case study](docs/TECHNICAL_CASE_STUDY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Product positioning draft](docs/PRODUCT_POSITIONING.md)
- [Improvement roadmap](docs/ROADMAP.md)

## Preserved hackathon artifact

| Evidence | Location | What it supports |
|---|---|---|
| Deterministic implementation | `src/` | Normalization, rules, scoring, prioritization, and report generation |
| Automated verification | `tests/` | Boundary behavior, scoring, read-only allowlist, ID removal, and HTML escaping |
| Synthetic rule matrix | `fixtures/health_matrix.json` | Reproducible coverage of healthy and flagged scenarios |
| Sanitized integration snapshot | `fixtures/hubspot-integration-sanitized.json` | Test-portal input shape with raw record IDs removed |
| Generated fixture report | `outputs/fixture-report.html` | Auditable scorecard and review queue |
| Generated integration report | `outputs/hubspot-report.html` | Read-only test-portal workflow evidence |
| Demo import guidance | `demo-data/DEMO_DATASET.md` | Synthetic data preparation and manual seeding controls |

Generated output is evidence of a controlled demonstration. It is not a benchmark, customer result, or production assessment.

## Run the preserved MVP

Requirements: Python 3.9 or later; no third-party packages. Run these commands from this directory.

```bash
python3 -m src.main \
  --source fixture \
  --input fixtures/health_matrix.json \
  --output outputs/fixture-report.html \
  --evaluation-date 2026-08-20T12:00:00Z
```

Run the verification suite:

```bash
python3 -m unittest discover -s tests -v
```

Reproduce the sanitized test-portal report:

```bash
python3 -m src.main \
  --source hubspot \
  --input fixtures/hubspot-integration-sanitized.json \
  --output outputs/hubspot-report.html \
  --evaluation-date 2026-08-20T12:00:00Z
```

## Current scoring contract

For each applicable category:

`category score = 100 × (1 − unique flagged records ÷ applicable records)`

Weights are missing owner 30%, stale open deals 30%, name quality 15%, and contact activity 25%. Categories with no applicable records are excluded and the remaining weights are renormalized.

Missing Owner applies to all contacts and deals, including closed deals. Stale open deals use a 30-day threshold; contact activity uses a 90-day threshold. Queue priority combines explicit severity points and bounded age bonuses, consolidates issues by record, caps priority at 100, and renders the top 20 rows.

## MVP boundaries

- MCP invocation remains outside the deterministic engine; the application consumes read-only search-result envelopes.
- Rules and weights are prototype policy choices, not universal standards or customer-validated thresholds.
- Run-local aliases depend on result order and are not durable cross-run identifiers.
- Contact activity uses three approved summary fields and is not a complete engagement audit.
- Name checks identify explicit formatting defects only and do not judge cultural or subjective validity.
- The current test portal contains two synthetic contacts and no deals, so its report demonstrates connectivity rather than balanced coverage.
- There is no multi-portal deployment, authentication layer, scheduler, historical trend store, remediation workflow, or production monitoring.
