# WebMCP Challenge Delta

This document separates the pre-existing CRM Health Doctor artifact from the WebMCP work completed during the challenge period. It is intentionally conservative and does not claim historical Git evidence that does not exist.

## Pre-existing work — August 20–21, 2026

Before the WebMCP Challenge, CRM Health Doctor already included:

- the Python application and command-line workflow;
- fixture and sanitized HubSpot-envelope adapters;
- deterministic diagnostic rules and scoring;
- deterministic queue prioritization and record-level explanations;
- synthetic/test data and generated HTML reports;
- the existing report UI;
- governed, read-only HubSpot/MCP capabilities outside the diagnostic engine;
- automated Python tests; and
- architecture, case-study, positioning, lessons, and roadmap documentation.

This baseline did not include WebMCP tool registration, browser-readable report state, WebMCP schemas, agent-triggered queue focus, or WebMCP contract tests.

## WebMCP Challenge work — August 31, 2026 onward

Challenge-period work added:

- an inert, safely escaped, bounded synthetic report snapshot;
- `document.modelContext.registerTool(...)` integration;
- the read-only `get_crm_health_summary` tool;
- the read-only `list_priority_issues` tool;
- the read-only `explain_priority_issue` tool;
- strict input validation and bounded structured outputs;
- deterministic impact and remediation mappings with mandatory human review;
- same-page scrolling, focus, highlighting, and accessible agent status;
- dependency-free JavaScript contract tests; and
- challenge provenance and public-submission documentation.

The challenge extension does not add live HubSpot access, CRM writes, authentication, persistence, backend services, or new scoring behavior.

## Commit boundary

| Commit | Period | What it represents |
| --- | --- | --- |
| `d5abc4c` | Baseline import on August 31 | Truthful import of the pre-existing CRM Health Doctor baseline. The imported work was created and last modified locally on August 20–21. This commit contains no WebMCP implementation and does not claim an earlier Git date. |
| `4e52c57` | Challenge provenance | Adds the conservative provenance statement and a SHA-256 manifest that establishes baseline integrity from August 31 forward. |
| `171118e` | First WebMCP vertical slice | Adds `list_priority_issues`, structured synthetic report state, strict filtering, and visible queue-row synchronization. |
| `3b204d3` | Complete minimal co-review | Adds `get_crm_health_summary`, `explain_priority_issue`, deterministic remediation guidance, and the complete three-tool contract tests. |

## Evidence limits

No pre-August-25 Git repository or commit history existed for this project. The initial Git commit was created on August 31 as an import; it was not backdated.

Original local filesystem metadata from August 20–21 is genuine supporting evidence, but it is not immutable historical proof. The August 31 checksum manifest proves integrity only from the time it was generated. The annotated tag `pre-webmcp-baseline-import-2026-08-31` marks the imported baseline boundary.

WebMCP functionality begins only after that tagged baseline, in the challenge-period commits listed above. Existing functionality and challenge-period additions remain separated in Git history and documentation.
