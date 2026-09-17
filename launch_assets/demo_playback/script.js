"use strict";

// Presentation only: read the preserved artifacts directly. No product API, SDK,
// credentials, model call, or assessment fallback is used by this viewer.
const artifactFiles = {
  "C-008": "../../demo_artifacts/c008_real_astra_sanitized.json",
  "C-001": "../../demo_artifacts/c001_real_astra_sanitized.json",
};
const titleCase = text => text.charAt(0).toUpperCase() + text.slice(1);
const scoreText = score => score === null ? "Unknown" : `${score} / 100`;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function stat(label, value, className = "") {
  const node = element("div", className);
  node.append(element("span", "label", label), element("strong", "stat-value", value));
  return node;
}

function opportunity(parent, heading, entries) {
  for (const entry of entries) {
    const block = element("section", "opportunity");
    block.append(element("h3", "", heading), element("p", "", entry.statement));
    parent.append(block);
  }
}

function render(capture) {
  const result = capture.readiness_result;
  const evidence = capture.evidence;
  const root = document.createDocumentFragment();
  const strip = element("section", "record-strip");
  strip.setAttribute("aria-label", "Record and deterministic findings");
  const record = element("div");
  record.append(element("span", "label", "Record"), element("h2", "record-title", capture.record_id));
  const priority = stat("Deterministic priority", evidence.audit_metadata.highest_priority);
  priority.append(element("p", "priority-note", "Not an Astra readiness score"));
  strip.append(record, stat("Deterministic findings", evidence.audit_metadata.finding_count), priority,
    stat("Overall readiness", scoreText(result.overall_readiness_score), "overall"));
  root.append(strip);

  const scores = element("section", "score-grid");
  scores.setAttribute("aria-label", "Readiness dimensions");
  for (const [dimension, value] of Object.entries(result.dimension_scores)) {
    const card = element("div", `score${value === null ? "" : " estimated"}`);
    card.append(element("h3", "", titleCase(dimension)), element("strong", "", scoreText(value)));
    scores.append(card);
  }
  root.append(scores, element("p", "score-note", result.dimension_assessments.data.statement));

  // A presenter takeaway, explicitly separate from the verbatim model excerpts.
  if (capture.record_id === "C-001" && evidence.findings.length === 0 && result.overall_readiness_score === null) {
    root.append(element("aside", "contrast", "No detected CRM issue does not equal proven agent readiness."));
  }

  const grid = element("div", "story-grid");
  const interpretation = element("section", "panel");
  interpretation.append(element("h2", "", "What the evidence supports"));
  if (evidence.findings.length === 0) {
    const counts = element("div", "empty-counts");
    for (const [label, entries] of [["Critical blockers returned", result.critical_blockers], ["Remediation items returned", result.remediation_priorities]]) {
      const count = element("div");
      count.append(element("strong", "", entries.length), element("span", "", label));
      counts.append(count);
    }
    interpretation.append(counts);
  }
  opportunity(interpretation, "Viable · supervised review", result.viable_agent_opportunities);
  opportunity(interpretation, "Conditional · verify the intended name", result.conditional_agent_opportunities);
  opportunity(interpretation, "Not supported · autonomous recency decisions", result.not_ready_agent_opportunities);
  if (result.conditional_agent_opportunities.length) {
    interpretation.append(element("aside", "guardrail", "Demo guardrail: verify against an authoritative source and obtain human approval before any cleanup."));
  }
  if (evidence.findings.length === 0) {
    opportunity(interpretation, "Before broader reliance", result.recommended_next_actions.filter(action => action.basis === "inference"));
  }
  const actions = element("section", "panel");
  if (result.remediation_priorities.length) {
    actions.append(element("h2", "", "Evidence-ranked remediation"));
    const list = element("ol", "remediation-list");
    for (const item of result.remediation_priorities) list.append(element("li", "", item.statement));
    actions.append(list);
    actions.append(element("h2", "gap-heading", "Evidence gaps"));
    const gaps = element("ul", "gap-chips");
    for (const gap of result.evidence_gaps) gaps.append(element("li", "", titleCase(gap.dimension)));
    actions.append(gaps);
  } else {
    actions.append(element("h2", "", "Evidence needed for broader readiness"));
    const gaps = element("ul", "gap-list");
    for (const gap of result.evidence_gaps) {
      const item = element("li");
      item.append(element("strong", "", titleCase(gap.dimension)), element("p", "", gap.detail));
      gaps.append(item);
    }
    actions.append(gaps);
  }
  grid.append(interpretation, actions);
  root.append(grid);
  if (result.remediation_priorities.length) {
    for (const action of result.recommended_next_actions.filter(action => action.basis === "inference")) {
      root.append(element("p", "approval", action.statement));
    }
  }

  const provenance = element("footer", "provenance");
  const row = element("div", "provenance-row");
  for (const [label, value] of [
    ["Confidence", titleCase(result.confidence)],
    ["Model", capture.provenance.model],
    ["Reasoning", capture.provenance.reasoning_effort],
    ["Recorded duration", `${capture.provenance.duration_seconds} s`],
    ["Completed (UTC)", new Date(capture.provenance.completed_at).toISOString().replace("T", " ").replace(/\.\d+Z$/, "")],
  ]) row.append(element("span", "", `${label}: ${value}`));
  provenance.append(row, element("p", "response-id", `Response ID: ${capture.provenance.response_id}`),
    element("p", "", "Selected assessment statements are verbatim from the preserved capture. Headings, takeaway and demo guardrail are presentation labels."));
  root.append(provenance);
  return root;
}

async function load() {
  const target = document.querySelector("#assessment");
  try {
    const alias = document.body.dataset.record;
    if (!Object.hasOwn(artifactFiles, alias)) throw new Error("Unsupported capture");
    const response = await fetch(artifactFiles[alias], { cache: "no-store", credentials: "omit" });
    if (!response.ok) throw new Error("Capture unavailable");
    const capture = await response.json();
    // Presentation sanity checks only; unchanged engineering validation lives in
    // the frozen product. Reject an unexpected file rather than inventing data.
    if (capture.record_id !== alias || capture.evidence.record.alias !== alias ||
        capture.real_inference !== true || capture.sanitized !== true ||
        capture.playback_is_live_inference !== false || capture.evidence.audit_metadata.source !== "fixture" ||
        capture.display_label !== document.querySelector("h1").textContent) {
      throw new Error("Unexpected capture");
    }
    target.replaceChildren(render(capture));
    target.dataset.loaded = "true";
  } catch {
    target.replaceChildren(element("p", "error", "Playback unavailable. Serve the repository root over local HTTP and confirm the original demo_artifacts files are present. No fallback assessment is shown."));
    target.setAttribute("role", "alert");
  } finally {
    target.setAttribute("aria-busy", "false");
  }
}

load();
