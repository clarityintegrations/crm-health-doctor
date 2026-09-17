# Agent Readiness challenge deployment

This deployment-only entry point wraps the frozen engineering release
`38c4042f5ff75f91c1b56d2d2d190252eb411174`. Product logic, support policy,
schemas, prompts, scoring, UI source and authentic captures remain unchanged.
The wrapper supplies Render host/origin checks, public port binding, an explicit
playback-file allowlist and launch navigation in served HTML. `/assess` executes
the existing handler and Astra adapter; it is not a simulated model endpoint.

## Separate Render service

- Name: `crm-health-doctor-agent-readiness`
- Type/runtime: Web Service / Python 3
- Repository: `clarityintegrations/crm-health-doctor`
- Branch: `launch-demo-assets`
- Root directory: empty (repository root)
- Build: `python3 -m launch_assets.deployment.verify`
- Start: `python3 -m launch_assets.deployment.server`
- Health check: `/`
- Instance: Free; do not select paid compute without user approval.
- Auto-deploy: Off after initial deployment; publish this reviewed launch commit.
- No environment groups, secret files, or OpenAI credential configured in this pass.
- Render provides `PORT` and `RENDER_EXTERNAL_HOSTNAME`.

Live inference is unavailable without server-side `OPENAI_API_KEY`. The UI
clearly states this and links directly to both preserved real assessments.
No deployment step creates or copies a credential. Do not put keys in source,
launch files, browser code, build commands, or request URLs.

## Routes

- `/`: existing product UI plus launch links and deployment disclosure
- `/evidence?alias=C-008` and `/evidence?alias=C-001`: frozen deterministic runtime
- `/launch_assets/demo_playback/c008.html`: preserved C-008 assessment
- `/launch_assets/demo_playback/c001.html`: preserved C-001 assessment
- `/launch_assets/demo_playback/index.html`: launch index (`/demo` also works)
- `/demo_artifacts/c008_real_astra_sanitized.json` and corresponding C-001 JSON:
  byte-identical original captures
- `/v1`: unchanged synthetic V1 HTML snapshot, not a change to the V1 service
- `/assess`: existing same-origin POST path; safe unavailable envelope without key

All other filesystem paths are unavailable. Synthetic fixtures are read internally;
no real CRM/customer records or CRM write functionality are added.

## V1 protection baseline, inspected September 17, 2026

Existing Render static site: `crm-health-doctor-webmcp`.
Service ID: `srv-dabji7m1egvs73b1han0`.
Project: `My project`; environment: `Production`.
Branch: `challenge/webmcp-2026`.
Deployed commit: `75d972ff0d2a9fb25e24ac6bc91120c8c69c387b`.
Build: `mkdir -p public && cp outputs/index.html public/index.html`.
Publish directory: `public`.
URL: https://crm-health-doctor-webmcp.onrender.com/

Do not edit, redeploy, suspend, replace, or attach this service to the new build.
Do not serve the whole repository with a general directory server.

Verification: `python3 -m launch_assets.deployment.verify` performs bounded local
HTTP tests with `OPENAI_API_KEY` explicitly blank; it spends no API credits.
Public verification must separately check browser rendering and capture hashes.
