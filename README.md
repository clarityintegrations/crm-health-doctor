# CRM Health Doctor

A deterministic CRM reliability assessment with a governed, read-only WebMCP human-agent co-review layer.

## Problem

Automation, reporting, routing, and AI agents all depend on sufficiently reliable CRM records. Missing ownership, stale activity, weak engagement signals, and malformed fields can make those systems operate on incomplete or misleading context. CRM Health Doctor demonstrates a narrow, auditable way to identify selected failures before expanding automation or deploying AI. It does not claim measured customer outcomes or production readiness.

## What It Does

The challenge demo follows one deterministic evidence chain:

1. Evaluate a synthetic contact-and-deal fixture with explicit Python rules.
2. Calculate category scores and an overall CRM health score.
3. Consolidate findings into a deterministic priority review queue.
4. Embed a bounded, safely escaped report snapshot in static HTML.
5. Expose three read-only WebMCP tools for structured agent access.
6. Keep the human on the same report page and visibly focus the record under review.

The diagnostic engine and remediation mappings do not call an LLM. The agent receives precomputed evidence and deterministic guidance; any remediation remains a human decision.

## WebMCP Challenge Extension

CRM Health Doctor existed before the WebMCP Challenge. The application, diagnostic engine, scoring logic, synthetic fixtures, report UI, and existing HubSpot/MCP adapter capabilities are pre-existing work.

During the challenge period, WebMCP added a browser-native, agent-facing layer over the synthetic report. This extension introduced structured report state, three read-only tools, strict tool inputs, bounded outputs, deterministic remediation guidance, and same-page visual synchronization. It did not add live HubSpot access, CRM writes, authentication, persistence, or backend services.

## Human + Agent Workflow

1. `get_crm_health_summary` gives the agent the precomputed overall score, evaluated scope, category state, and issue counts.
2. `list_priority_issues` applies structured filters to the deterministic review queue and focuses the highest returned row in the report.
3. `explain_priority_issue` returns the selected record's evidence, operational impact, recommended review steps, and human-review requirement while focusing the same row.

The visible synchronization connects the agent's structured selection to the evidence the human sees: when the agent selects or explains alias `C-008`, the page scrolls to and highlights the `C-008` queue row and updates an accessible status message.

## WebMCP Tools

| Tool | Purpose | Write capability |
| --- | --- | --- |
| `get_crm_health_summary` | Read overall health, scope, category scores, and bounded issue counts | None — read-only |
| `list_priority_issues` | Filter and rank queue findings, then focus the first matching row | None — read-only |
| `explain_priority_issue` | Explain one queue alias with deterministic impact and review steps | None — read-only |

## Architecture

```text
Synthetic CRM fixture
        ↓
Python deterministic diagnostic engine
        ↓
Precomputed safe report state
        ↓
Static HTML
        ↓
WebMCP tools
        ↓
Agent + human co-review
```

The Python layer owns normalization, rules, scoring, prioritization, and guidance selection. The browser layer reads precomputed state; it does not reimplement the diagnostic engine.

## Security & Privacy

- The public challenge demo uses synthetic data only.
- The page has no live CRM connection.
- Raw HubSpot record IDs are not exposed.
- The page makes no network calls.
- The application has no CRM write path.
- Tool inputs are strictly validated and outputs are bounded.
- CRM-derived strings are treated as untrusted evidence, not instructions.
- Remediation guidance is deterministic rather than LLM-generated.
- Every recommended remediation requires human review.

The repository also preserves a sanitized test-portal artifact as historical evidence. It is not used by the public challenge page and does not establish compatibility with arbitrary customer portals.

## Run Locally

Requirements: Python 3.9 or later. No third-party package installation is required.

Regenerate the synthetic challenge page from the repository root:

```bash
python3 -m src.main \
  --source fixture \
  --input fixtures/health_matrix.json \
  --output outputs/index.html \
  --evaluation-date 2026-08-20T12:00:00Z
```

Serve it with Python's standard-library HTTP server:

```bash
python3 -m http.server 8765
```

Then open `http://127.0.0.1:8765/outputs/index.html` in a WebMCP-capable browser. The normal report remains usable when WebMCP is unavailable.

## Test with ChatGPT

Open the deployed report in ChatGPT's in-app browser, then use this validated sequence:

1. **Summary:** “Using the open CRM Health Doctor page's `get_crm_health_summary` site tool, summarize the synthetic CRM's overall health, evaluated scope, and weakest category. Do not infer from the visible HTML.”
2. **Prioritization:** “Using the open page's `list_priority_issues` site tool, return one contact issue in the `missing_owner` category with minimum priority 40 and limit 1. Tell me which alias the page highlighted.”
3. **Explanation:** “Using the open page's `explain_priority_issue` site tool, explain alias `C-008`. Give the deterministic impact, recommended steps, and human-review requirement, and confirm which row the page is reviewing.”

The validated synthetic result selects `C-008` at priority 95 and visibly focuses that row.

## Test with Chrome

The Chrome gate was validated with WebMCP testing enabled:

1. Open `chrome://flags/#enable-webmcp-testing`, enable WebMCP testing, and relaunch Chrome.
2. Open the deployed report, or serve and open the local report URL shown above.
3. In DevTools, discover the registered tools:

```js
const tools = await document.modelContext.getTools();
tools.map(({ name }) => name);
```

The validated result contained exactly `explain_priority_issue`, `get_crm_health_summary`, and `list_priority_issues`.

To reproduce the tested priority execution in the validated Chrome build, pass the tool input as serialized JSON:

```js
const priorityTool = tools.find(({ name }) => name === "list_priority_issues");
const result = await document.modelContext.executeTool(
  priorityTool,
  JSON.stringify({
    category: "missing_owner",
    objectType: "contact",
    minPriority: 40,
    limit: 1,
  })
);
result;
```

The tested result returned two total matches, one bounded result, alias `C-008`, and priority 95; the report focused `C-008`. These instructions document that tested Chrome flow only and do not claim broader browser compatibility.

## Tests

Run the complete existing suites:

```bash
python3 -m unittest discover -s tests -v
node tests/test_webmcp_contract.mjs
```

At the feature freeze, all 26 Python tests and the dependency-free JavaScript WebMCP contract suite pass. Coverage includes deterministic scoring, threshold boundaries, stable queue ordering, safe embedded state, strict tool inputs, bounded outputs, privacy exclusions, graceful degradation, and row-focus synchronization.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `src/` | Deterministic normalization, rules, scoring, recommendations, reporting, and WebMCP layer |
| `fixtures/health_matrix.json` | Synthetic challenge fixture |
| `outputs/index.html` | Self-contained challenge demo page |
| `tests/` | Python and dependency-free JavaScript verification |
| `PROVENANCE.md` | Conservative provenance statement |
| `docs/WEBMCP_CHALLENGE_DELTA.md` | Pre-existing versus challenge-period work |

## Challenge Provenance

See [PROVENANCE.md](PROVENANCE.md), [the WebMCP challenge delta](docs/WEBMCP_CHALLENGE_DELTA.md), and the annotated tag `pre-webmcp-baseline-import-2026-08-31`.

No pre-August-25 Git repository existed. The baseline Git import was truthfully created on August 31, 2026, from work originally created and last modified locally on August 20–21. The import does not claim earlier Git history, and local filesystem dates are supporting rather than immutable historical proof. WebMCP functionality begins only in later challenge-period commits.

## License

Licensed under the [MIT License](LICENSE).

## Live Demo

https://crm-health-doctor-webmcp.onrender.com

## Demo Video

TBD — public YouTube demo
