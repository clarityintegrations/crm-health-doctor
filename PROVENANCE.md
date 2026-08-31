# CRM Health Doctor provenance

CRM Health Doctor existed before the WebMCP Challenge. The application, diagnostic engine, scoring rules, synthetic/demo data, reports, tests, and product documentation in the tagged baseline were created locally before August 25, 2026.

No Git repository or pre-August-25 Git history existed for this project. The initial Git commit is a truthful import created on August 31, 2026. It does not claim an earlier commit date. Original local filesystem dates from August 20-21 are supporting evidence, not immutable proof of when the work was created.

The annotated tag `pre-webmcp-baseline-import-2026-08-31` marks the imported pre-WebMCP baseline. WebMCP challenge implementation begins only after that tag, on the `challenge/webmcp-2026` branch. Existing functionality and challenge-period additions must remain clearly separated in commits and documentation.

| PRE-EXISTING | NEW WEBMCP CHALLENGE WORK |
| --- | --- |
| CRM Health Doctor application and CLI | WebMCP browser integration |
| Diagnostic engine and deterministic scoring rules | Agent-facing tool definitions and schemas |
| Synthetic/demo data and generated reports | WebMCP-specific adapters and demo-safe behavior |
| HubSpot/MCP adapter capabilities already present | WebMCP testing and compatibility work |
| Existing tests, architecture, case study, positioning, and roadmap | Challenge documentation, deployment changes, and submission materials created after the baseline tag |

This record is intentionally conservative: it documents the import boundary and supporting local evidence without representing the August 31 Git history or checksum manifest as proof that existed before August 25.
