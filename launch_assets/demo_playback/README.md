# CRM Health Doctor — demo playback

Static launch support for **CRM Health Doctor — Agent Readiness Edition**.
These pages present previously generated real GPT-6 Astra assessments over
synthetic CRM evidence. Playback is not live inference. Human review is required.

## Run locally

From the repository root, run:

```sh
python3 -m http.server 8767 --bind 127.0.0.1
```

Open [the playback index](http://127.0.0.1:8767/launch_assets/demo_playback/index.html).
Keep the server running during recording; use Ctrl+C afterward. No install,
build step, API key, internet connection or product server is needed for playback.
Serve the repository root: the pages read the original artifacts two levels up.
Opening the HTML directly with `file:` will not reliably allow the JSON fetch.

## Three-screen recording

| Screen | Prepare | What to show |
| --- | --- | --- |
| 1 | Existing product UI, C-008 selected | Three deterministic findings and priority 95. This is not an Astra readiness score. |
| 2 | [C-008 playback](http://127.0.0.1:8767/launch_assets/demo_playback/c008.html) | Data estimate 40/100; overall and other dimensions Unknown; supervised review, conditional cleanup, unsupported autonomous recency decisions, ranked remediation and evidence gaps. |
| 3 | [C-001 playback](http://127.0.0.1:8767/launch_assets/demo_playback/c001.html) | Zero findings and priority 0; all readiness values Unknown; zero returned blockers/remediation; supervised observation review and missing evidence. |

Screen 1 is the unchanged product, not part of this static package. If its local
server is not already running, start the existing entry point in a separate terminal:

```sh
python3 -m readiness serve --port 8766
```

Open `http://127.0.0.1:8766/`, leave C-008 selected and wait for deterministic
evidence. **Do not click “Assess with GPT-6 Astra” during recording.** Switch to
the explicitly labeled playback tabs for Screens 2 and 3. This asset work did not
start that product server or make any live model call.

## Source fidelity

`script.js` performs one same-origin, credential-free GET for the selected record:

- `demo_artifacts/c008_real_astra_sanitized.json`
- `demo_artifacts/c001_real_astra_sanitized.json`

There is no copied assessment payload or manually rewritten assessment embedded
in the pages. Counts and priorities come from `evidence.audit_metadata`; readiness
comes from `readiness_result`; `null` renders as **Unknown**. Interpretation and
remediation excerpts use their original `statement` strings. Gap labels/details,
confidence and recorded provenance also come from the JSON. Dates display in UTC.
The response ID is a preserved provenance identifier, not an API credential.

The page deliberately selects a recording-sized subset rather than displaying the
entire assessment. The original artifacts retain all rationale, references and
limitations. Headings, disclosure text, the C-001 takeaway and the explicitly
labeled “Demo guardrail” are presentation copy. The authoritative-source guardrail
is a recording constraint, not an additional claim attributed to the model.

The viewer has no inference endpoint, SDK, external font, CDN, analytics or storage.
Text is inserted with `textContent`. A missing or unexpected capture shows an
explicit error with no fallback assessment. Presentation sanity checks do not
replace or modify the frozen product validators.

## Recording setup and readability

Use a 1920×1080 capture at **100% browser zoom**. Prefer a full-screen browser,
hide sidebars/bookmarks/developer tools, and keep only the three recording tabs
visible. Use a full browser window rather than a narrow app preview panel.
The main assessment copy is 22px; the disclosure heading is 34px. Metadata is
smaller and kept below the core story.

See `previews/` for 1920×1080 browser screenshots and `readability.json` for
viewport measurements and the JSON-binding/error-state checks. The images show
actual local page rendering, not design mockups. Smaller windows reflow and may
scroll; they are not the target recording context.

Verified in local Chrome 153 at 100% zoom, with manual screenshot review:

| Page | 1920×1080 viewport | 1920×950 viewport (browser-chrome allowance) |
| --- | --- | --- |
| Index | Fits; both playback links and disclosures visible | Fits |
| C-008 | Fits; scores, opportunities, remediation, gaps and provenance visible | Fits |
| C-001 | Fits; contrast statement, Unknown values, evidence needs and provenance visible | Fits |

No horizontal overflow or clipped text was detected. At a 1536×864 CSS viewport
(the effective full-screen space at 125% zoom on 1920×1080), both assessment
pages require scrolling. **Use 100%, not 125%, for this recording.**

The normal loading pass had no browser script/console errors and requested only
the local HTML, CSS, JavaScript and the two artifact files. A temporary intercepted
test response confirmed score binding; an intercepted missing-file response
confirmed the explicit error state. Neither check changed an artifact on disk.

Read [the recording checklist](recording_checklist.md), then rehearse
[the narration](narration_script.md) once with a timer. The script has a 150-second
budget; the actual spoken duration must be checked during rehearsal.

## Freeze boundary

Launch branch: `launch-demo-assets`, based on engineering freeze
`38c4042f5ff75f91c1b56d2d2d190252eb411174`.
Frozen V1 baseline: `75d972ff0d2a9fb25e24ac6bc91120c8c69c387b`, pointed to by
`webmcp-v1-before-astra-2026-09-16` (annotated tag dereferenced).
All launch changes are contained in `launch_assets/demo_playback/`.
Product code, schemas, validation, integration and support policy remain untouched.

Preserved source-file SHA-256 values, checked before and after asset creation:

| File in `demo_artifacts/` | SHA-256 |
| --- | --- |
| `c008_real_astra_sanitized.json` | `7d8bbeff8cf4b3bc302543d0b890401063645d74ef8c604e6706506fbc7d566e` |
| `c001_real_astra_sanitized.json` | `c7c9000f6a6b41ed13c1731a808025b2a24605ce65555fe37976abd3c2adddbe` |
| `README.md` | `f7c927769897d3c56adcd547632fedf564bb44551fe49c2c83174a894e323bf0` |
