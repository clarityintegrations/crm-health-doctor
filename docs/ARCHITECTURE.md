# Architecture

This document distinguishes the implemented MVP architecture from possible future product architecture.

## Confirmed facts: current MVP

```text
Governed HubSpot MCP search                 Synthetic fixture
             |                                    |
             +---------- JSON envelope -----------+
                              |
                       Source adapter
                 normalize + discard raw IDs
                              |
                    Internal records model
                              |
              Deterministic rule evaluation
                              |
          +-------------------+-------------------+
          |                                       |
  Weighted scorecard                    Prioritized review queue
          |                                       |
          +--------------- HTML renderer ---------+
                              |
                   Self-contained report
```

### Components

| Component | Responsibility | Evidence |
|---|---|---|
| Orchestration boundary | Permit governed user lookup and CRM search; exclude writes | `src/config.py` |
| Adapter | Load fixture/HubSpot envelopes, normalize fields, discard raw IDs | `src/adapter.py` |
| Rule engine | Evaluate owner, deal staleness, name quality, and contact activity | `src/rules.py` |
| Scoring | Calculate category and overall scores with applicable denominators | `src/scoring.py` |
| Prioritization | Consolidate issues and rank the top review records | `src/scoring.py` |
| Report renderer | Escape CRM values and create dependency-free HTML | `src/report.py` |
| Command entry point | Configure and run the pipeline | `src/main.py` |
| Verification | Exercise policy boundaries, security behavior, and fixture output | `tests/` |

### Trust boundaries

1. **HubSpot boundary:** Only approved read operations are in scope. The application contains no connector client and no write path.
2. **Normalization boundary:** Only selected properties enter the internal model. Raw CRM IDs are intentionally discarded.
3. **Decision boundary:** Rules, thresholds, weights, and severity points are explicit code, not model-generated judgments.
4. **Presentation boundary:** Dynamic values are HTML-escaped. The report has no external assets or telemetry.
5. **Human-action boundary:** The output recommends review; it does not remediate records.

### Data model used by the MVP

Contacts use first name, last name, owner, creation timestamp, and three approved activity-summary timestamps. Deals use name, owner, creation timestamp, two approved activity-summary timestamps, and closed-won/closed-lost flags.

The output issue model includes a run-local alias, object type, display name, category, issue type, human-readable explanation, base severity, and optional age bonus.

### Determinism contract

An identical normalized dataset, evaluation timestamp, and configuration produce identical issues, category scores, queue priorities, ordering, and HTML content. Any later introduction of probabilistic analysis should remain outside this deterministic control layer and be labeled separately.

## Observations

- The current separation between data access, normalization, decisions, and presentation makes the prototype easy to audit.
- Keeping connector invocation outside the engine simplified the trust model but left orchestration and deployment incomplete.
- The architecture demonstrates a useful safety pattern for an assessment: read, normalize, evaluate, explain, then require human review.

## Hypothesis: future architecture

The following is a design direction, not implemented functionality:

```text
HubSpot portal
      |
Governed read connector + scoped property manifest
      |
Snapshot/version layer ---- run metadata + policy version
      |
Reliability control engine ---- optional labeled AI analysis
      |                                  |
Findings store <---------------- confidence + evidence
      |
Assessment report + trend view + owner workflow
      |
Human approval gate
      |
Optional remediation plan or separately authorized write workflow
```

### Proposed boundaries for evolution

- Keep assessment reads and remediation writes as separately authorized capabilities.
- Version every control, threshold, weight, and property manifest.
- Preserve the evidence used for every finding without exposing unnecessary CRM data.
- Separate deterministic failures from probabilistic recommendations.
- Record scan completeness, permission gaps, unsupported objects, and unknown states.
- Make comparisons only between compatible policy versions and dataset scopes.
- Add tenant isolation, retention controls, secrets management, audit logs, retries, rate-limit handling, and observability before production use.

### Proposed control domains

The present four categories may become a small subset of a broader catalog:

- ownership and routing;
- engagement freshness;
- lifecycle and pipeline integrity;
- required-field completeness;
- duplicates and identity resolution;
- contact-company-deal association coverage;
- schema and property fitness for intended AI use cases;
- workflow and integration dependencies;
- consent, lawful-use, and governance signals;
- unsupported or unknowable conditions.

Each domain requires portal-specific validation. No complete AI readiness standard is claimed today.

## Architecture decision record for the next phase

Before adding automation, decide and document:

1. Who is the assessment buyer and who reviews findings?
2. What specific AI use case is being declared “ready” or “not ready”?
3. Which properties and objects are minimally necessary?
4. Which controls are universal versus portal-configurable?
5. How will false positives, exceptions, and accepted risks be recorded?
6. What evidence must be retained, and for how long?
7. Will remediation remain advisory or become a separately approved capability?
