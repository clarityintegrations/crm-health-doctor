# Lessons Learned

This document separates the event record from interpretation and future bets. Observations describe audience response as perceived during the event; they are not quantitative research.

## Confirmed facts: what happened

- CRM Health Doctor was built as a compact MVP and demonstrated live at the HubSpot Building with AI Hackathon.
- The demonstration produced five visible outputs: an overall CRM health score, category results, a prioritized record review queue, an explanation for every flagged record, and an HTML report.
- The implementation used synthetic/test data and a sanitized test-portal snapshot.
- The analysis was deterministic: the same normalized input, configuration, and evaluation time produce the same result.
- HubSpot access was governed and read-only-first. The application contract allowed user-detail lookup and CRM search, while excluding create, update, merge, and delete operations.
- Raw HubSpot record IDs were discarded during normalization and replaced with run-local aliases.
- The fixture matrix and automated tests exercised rule behavior, thresholds, scoring, ordering, sanitization, and report escaping.

## Observations: what the event suggested

1. **Workflow context mattered.** HubSpot emphasized AI-assisted developer workflows, including tools such as Claude Code and Cursor. The implementation story therefore benefits from showing how governed data access, deterministic code, and AI-assisted delivery fit together.

2. **Commercial clarity appeared to travel farther than implementation depth.** A technically rigorous build was necessary, but audience impact appeared stronger when a project quickly connected a problem to a buyer, business consequence, and next action.

3. **Reliability is a stronger bridge to AI than generic hygiene.** “Clean the CRM” can sound operational and open-ended. “Establish whether the CRM is reliable enough for AI-driven workflows” connects the same underlying work to a timely business decision.

4. **Explanations increased credibility.** A score alone would have been difficult to act on. Category counts, record-level reasons, and a prioritized queue made the result inspectable.

5. **Safety constraints can be part of the product story.** Read-only access, synthetic data, explicit rules, and sanitized identifiers were not merely implementation details; together they formed a credible trust boundary.

6. **A demo is not validation.** The live demonstration showed that the workflow could run. It did not establish demand, willingness to pay, accuracy across varied portals, or operational ROI.

## Hypotheses: lessons to test commercially

- Buyers may respond more strongly to **CRM reliability before AI deployment** than to a general CRM data-quality audit.
- A fixed-scope assessment may be the lowest-risk entry offer for Clarity Integrations because it produces evidence without requiring write access.
- The assessment may create a natural path to remediation services, governance design, and recurring monitoring.
- Sales, RevOps, and CRM owners may need different views of the same findings: business risk, operating backlog, and technical evidence.
- Transparent deterministic controls may be preferable to opaque model judgment for the first version of a reliability assessment.

## Practical changes to the story

Lead with the decision the buyer needs to make: **Can we trust this HubSpot environment enough to automate decisions or deploy AI on top of it?**

Then show the evidence chain:

1. Inspect approved CRM signals through a governed read-only boundary.
2. Apply explicit, reviewable controls.
3. Quantify reliability gaps without hiding the denominators.
4. Prioritize records and explain why each one needs attention.
5. Convert findings into a remediation and governance plan.

The MVP currently proves steps 1–4 in a controlled demonstration. Step 5 and any recurring service remain future work.

## What not to claim

- Do not describe the hackathon as a customer deployment.
- Do not present the 60.4 fixture score or the sanitized test-portal score as a real company result.
- Do not claim improved conversion, productivity, AI accuracy, or revenue.
- Do not imply that the four current rule categories constitute a complete AI readiness standard.
- Do not claim adoption, production readiness, or market validation without new evidence.
