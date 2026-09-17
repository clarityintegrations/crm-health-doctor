# P0 — required for Friday launch

- Make `OPENAI_API_KEY` available securely to the server process and verify Responses API access to `gpt-6-astra`.
- Implement strict input/output schemas and the evidence builder over unchanged deterministic results for C-008 and C-001.
- Implement the isolated server-side Astra adapter, reference/unknown-dimension validation, and small local readiness presentation with safe unavailable behavior.
- Test timeout, malformed/schema-invalid output, API error, missing key, unsupported evidence, and V1 regressions.
- Complete and review two real Astra assessments; verify evidence-sensitive differences without inventing unsupported dimension scores.
- Validate the under-three-minute demonstration. Resolve any public hosting/security needs in a separately authorized deployment step before a public launch.

# P1 — valuable if time remains

- Repeat model evaluations to measure consistency of evidence citations and unknown-dimension behavior.
- Record concise model-call provenance and an evidence-backed demo script after live validation.

# POST-LAUNCH — explicitly deferred

- Ads, AEO, YouSpot, HubSpot Agent Hub, Prospecting Agent, and Customer Agent integrations.
- CRM writes, authentication redesign, billing, multi-tenant architecture, large UI changes, analytics, and enterprise permission systems.
