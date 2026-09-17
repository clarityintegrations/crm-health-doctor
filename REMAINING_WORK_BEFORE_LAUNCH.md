# P0 — required before Friday launch

- Resolve the OpenAI API credit-balance blocker (`credit_balance_exhausted`). Key loading and model access succeeded; inference did not.
- Run and review real C-008 and C-001 assessments through the implemented production adapter. Validate references, factual claims, unknown dimensions, human-review requirements, and defensible differences. Permit at most one bounded prompt/schema refinement if needed.
- Capture sanitized successful examples and verify the complete live presentation fits under three minutes.
- If a public URL is required, authorize a separate deployment step that protects the paid API endpoint; retain deployed WebMCP V1. The current readiness server is local-only.

# P1 — useful if time permits

- Repeat model evaluations to measure consistency of evidence citations and unknown-dimension behavior.
- Record concise model-call provenance and an evidence-backed demo script after live validation.

# POST-LAUNCH — explicitly deferred

- Ads, AEO, YouSpot, HubSpot Agent Hub, Prospecting Agent, and Customer Agent integrations.
- CRM writes, authentication redesign, billing, multi-tenant architecture, large UI changes, analytics, and enterprise permission systems.
