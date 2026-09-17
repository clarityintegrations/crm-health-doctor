# P0 — required before Friday launch

- Independent re-review closed claim-support enforcement (P0-1) and score admissibility (P0-2): PASS WITH P1 FIXES. The original FAIL is superseded. All 13 reported counterexamples still fail closed; both authentic artifacts remain unchanged and valid. Obtain independent confirmation of the P1 generator-alignment change before treating this pass as launch approval.
- Measure the narrated recording at 150 seconds or less, using clearly labeled previously generated real assessments. Timing is still unverified.
- If a public URL is required, obtain separate deployment authorization and protect the paid API endpoint; retain deployed WebMCP V1. The readiness server remains local-only.
- Superseded September 16 tasks: restore credits, verify real access, run both real assessments, and capture examples. These were completed; artifacts are committed in `3c6483d`. One traceability rejection and one timeout were subsequently observed alongside successful calls. Runtime variability remains a challenge-stage limitation, not a proven UI defect.

# P1 — useful if time permits

- Generator guidance now comes from the canonical support catalog, filtered by existing applicability/validation rules. The validator remains authoritative; no vocabulary, scoring or evidence rules were relaxed. Exact wording remains a bounded MVP tradeoff.
- P1 generator/validator alignment verified: exactly two fresh `gpt-6-astra`/medium calls passed unchanged production validation, C-008 in 28.90 seconds and C-001 in 20.22 seconds. No refinement was needed. All 72 Python tests and three JavaScript suites pass. This closes the identified mismatch, not historical runtime variability or broader repeatability measurement.
- Improve recording readability only if rehearsal demonstrates a concrete need; no UI redesign or broad replay/cache system.

# POST-LAUNCH — explicitly deferred

- P2: duplicate JSON-key rejection, whitespace-only limitations, duplicate claims/gaps, duplicate finding IDs, schema-version field, broader repeatability measurements, and richer provenance packaging. No dedicated P2 mechanisms were added; the P0 closed vocabulary incidentally rejects unsupported whitespace-only limitation text.
- Ads, AEO, YouSpot, HubSpot Agent Hub, Prospecting Agent, and Customer Agent integrations.
- CRM writes, authentication redesign, billing, multi-tenant architecture, large UI changes, analytics, and enterprise permission systems.
