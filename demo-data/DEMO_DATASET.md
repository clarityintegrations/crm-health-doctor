# CRM Health Doctor demo dataset

Evaluation reference: **2026-08-20 12:00 UTC**. Thresholds are strictly greater than 30 days for open deals and strictly greater than 90 days for contact activity.

These files contain synthetic data only. The CRM Health Doctor application must not create records or activities. Inspect and import the files manually into the confirmed Clarity Integrations test portal.

## Before importing

The CSVs contain readable placeholders because HubSpot owner, pipeline, and stage internal values are portal-specific. Do not import the placeholders unchanged.

- Replace `ASSIGN_TEST_PORTAL_OWNER` with the existing test-portal owner's email address if the import flow supports owner assignment by email. Otherwise, leave the owner field unmapped and assign the owner in the HubSpot UI after import.
- Replace or manually map `MAP_TO_TEST_PIPELINE` to the intended test deal pipeline.
- Replace or manually map `MAP_TO_OPEN_STAGE` to a genuinely open deal stage.
- Replace or manually map `MAP_TO_CLOSED_WON_STAGE` to the pipeline's closed-won stage.
- Keep the Unowned Contact's owner blank.
- Treat `Demo Scenario` as import context only. Select **Don't import column** unless the portal already has a harmless text property intended for demo labels.

Do not create new owners, pipelines, stages, or custom properties merely to satisfy these files.

## Import mapping

### `contacts.csv`

| CSV column | Intended HubSpot property/action | Mapping note |
|---|---|---|
| Email | Contact property: Email | Synthetic `example.com` address; safe record identifier for deduplication. |
| First Name | Contact property: First Name (`firstname`) | Import as text exactly as provided. |
| Last Name | Contact property: Last Name (`lastname`) | Import as text exactly as provided. |
| Contact owner | Contact property: Contact owner (`hubspot_owner_id`) | Placeholder must be replaced with a valid existing owner email, or leave unmapped and assign manually. Leave Unowned Contact blank. Never invent an owner ID. |
| Demo Scenario | No HubSpot mapping required | Select **Don't import column**. |

### `deals.csv`

| CSV column | Intended HubSpot property/action | Mapping note |
|---|---|---|
| Deal Name | Deal property: Deal Name (`dealname`) | Import as text. |
| Deal Pipeline | Deal property: Pipeline (`pipeline`) | Map the placeholder to an existing test pipeline; do not invent an internal value. |
| Deal Stage | Deal property: Deal Stage (`dealstage`) | Map open placeholders to an open stage and the closed placeholder to a closed-won stage in the selected pipeline. |
| Deal owner | Deal property: Deal owner (`hubspot_owner_id`) | Replace with a valid existing owner email or assign manually after import. Never invent an owner ID. |
| Close date | Deal property: Close date (`closedate`) | Only the closed control has a date. This is descriptive; the stale-open rule does not use close date. |
| Demo Scenario | No HubSpot mapping required | Select **Don't import column**. |

## Minimum post-import actions

Use manually logged **completed calls or meetings** with explicit activity dates. These activities are expected to populate approved HubSpot summary properties such as Last Activity Date or Last Contacted. Associate the activity directly with the intended contact or deal. Do not create activities through MCP or CRM Health Doctor.

For reproducibility against the fixed evaluation date:

| Record | Manual action | Activity date | Expected rule outcome |
|---|---|---:|---|
| Healthy Contact | Assign test owner; log completed call/meeting | 2026-08-15 | No issues. |
| Unowned Contact | Keep owner blank; log completed call/meeting | 2026-08-15 | `missing_owner` only. |
| Malformed Contact | Assign test owner; log completed call/meeting | 2026-08-15 | `malformed_name` only. |
| No Activity Contact | Assign test owner; add no activity | None | `weak_activity` only. |
| Stale Contact | Assign test owner; log completed call/meeting | 2026-04-22 | `stale_activity` only; activity is 120 days old. |
| Healthy Open Deal | Assign test owner; keep open; log completed call/meeting | 2026-08-15 | No stale-deal issue. |
| Stale Open Deal | Assign test owner; keep open; log completed call/meeting | 2026-06-21 | `stale_open_deal`; activity is 60 days old. |
| New No-Activity Deal | Assign test owner; keep open; add no activity | None | Creation-time fallback; not stale when newly created. |
| Old Closed Deal | Assign test owner; use closed-won stage | None required | Excluded from stale-open-deal evaluation even with an old close date. |

The dates above are relative to 2026-08-20. If the final run uses a later evaluation date, shift the three recent activities to approximately 5–7 days before that date, the stale contact activity to approximately 120 days before it, and the stale deal activity to approximately 60 days before it.

## Verification before the final scan

1. Confirm four contacts and all four deals have the intended valid owner; confirm Unowned Contact remains blank.
2. Confirm the three recent contacts and Healthy Open Deal show a recent activity summary date.
3. Confirm Stale Contact shows the historical date and Stale Open Deal shows its historical date.
4. Confirm No Activity Contact and New No-Activity Deal have no logged activities.
5. Confirm the closed control is in a genuinely closed-won stage.
6. Tell Codex that seeding is complete. The next step is a complete read-only MCP scan and expected-versus-actual comparison.

## Owner-rule applicability

The current deterministic engine intentionally evaluates Missing Owner across **all contacts and all deals, including closed deals**. The category denominator is therefore `contacts + deals`. This explains the fixture report's 13 applicable records from 8 contacts and 5 deals. No scoring behavior was changed during demo preparation.
