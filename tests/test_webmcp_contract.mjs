import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";

const source = fs.readFileSync(new URL("../src/webmcp.js", import.meta.url), "utf8");

function classList() {
  const values = new Set();
  return {
    add: (value) => values.add(value),
    remove: (value) => values.delete(value),
    contains: (value) => values.has(value),
  };
}

function row(alias) {
  const attributes = new Map();
  return {
    dataset: { alias },
    classList: classList(),
    focused: false,
    scrolled: false,
    setAttribute: (name, value) => attributes.set(name, value),
    removeAttribute: (name) => attributes.delete(name),
    getAttribute: (name) => attributes.get(name),
    focus() {
      this.focused = true;
    },
    scrollIntoView() {
      this.scrolled = true;
    },
  };
}

const snapshot = {
  version: 1,
  summary: {
    source: "fixture",
    demoMode: true,
    evaluationDate: "2026-08-20T12:00:00+00:00",
    overallScore: 60.4,
    scope: { contacts: 8, deals: 5 },
    categories: [
      { category: "missing_owner", flagged: 2, applicable: 13, score: 84.6, normalizedWeight: 0.3 },
      { category: "stale_open_deals", flagged: 2, applicable: 3, score: 33.3, normalizedWeight: 0.3 },
      { category: "name_quality", flagged: 3, applicable: 8, score: 62.5, normalizedWeight: 0.15 },
      { category: "contact_activity", flagged: 3, applicable: 8, score: 62.5, normalizedWeight: 0.25 },
    ],
    issueCounts: {
      malformedName: 3,
      missingOwner: 2,
      staleActivity: 1,
      staleOpenDeal: 2,
      weakActivity: 2,
    },
  },
  issues: [
    {
      alias: "C-008",
      displayName: "TEST USER 99",
      objectType: "contact",
      priority: 95,
      findings: [
        {
          issueType: "missing_owner",
          category: "missing_owner",
          evidence: "Owner is absent or blank.",
          impact: "Unowned records can miss routing, accountability, and follow-up.",
          recommendedSteps: ["Review assignment rules.", "Confirm the intended owner."],
          requiresHumanReview: true,
        },
        {
          issueType: "weak_activity",
          category: "contact_activity",
          evidence: "No approved activity signal exists.",
          impact: "Missing signals make recency unreliable.",
          recommendedSteps: ["Check approved sources.", "Do not manufacture activity."],
          requiresHumanReview: true,
        },
      ],
    },
    {
      alias: "D-002",
      displayName: "Stale Renewal",
      objectType: "deal",
      priority: 75,
      findings: [
        {
          issueType: "stale_open_deal",
          category: "stale_open_deals",
          evidence: "Latest activity exceeds the threshold.",
          impact: "A stale deal can distort pipeline reporting.",
          recommendedSteps: ["Verify the stage.", "Update only after human review."],
          requiresHumanReview: true,
        },
      ],
    },
    {
      alias: "C-002",
      displayName: "Jonas Rivera",
      objectType: "contact",
      priority: 40,
      findings: [
        {
          issueType: "missing_owner",
          category: "missing_owner",
          evidence: "Owner is absent or blank.",
          impact: "Unowned records can miss routing, accountability, and follow-up.",
          recommendedSteps: ["Review assignment rules.", "Confirm the intended owner."],
          requiresHumanReview: true,
        },
      ],
    },
  ],
  explanationDisclaimer: "Deterministic prototype guidance for synthetic data.",
};

function loadPage({ webmcp = true } = {}) {
  const registeredTools = [];
  const rows = [row("C-008"), row("D-002"), row("C-002")];
  const status = { hidden: true, textContent: "" };
  const document = {
    getElementById(id) {
      if (id === "crm-health-snapshot") return { textContent: JSON.stringify(snapshot) };
      if (id === "agent-focus-status") return status;
      return null;
    },
    querySelectorAll(selector) {
      assert.equal(selector, "tr[data-alias]");
      return rows;
    },
  };
  if (webmcp) {
    document.modelContext = {
      registerTool(tool) {
        registeredTools.push(tool);
        return Promise.resolve();
      },
    };
  }
  vm.runInNewContext(source, { document, console });
  return { registeredTools, rows, status };
}

const page = loadPage();
assert.deepEqual(
  Array.from(page.registeredTools, (tool) => tool.name),
  ["get_crm_health_summary", "list_priority_issues", "explain_priority_issue"],
);
for (const tool of page.registeredTools) {
  assert.equal(tool.inputSchema.additionalProperties, false);
  assert.equal(tool.annotations.readOnlyHint, true);
  assert.equal(tool.annotations.untrustedContentHint, true);
}
const healthSummaryTool = page.registeredTools[0];
const priorityIssuesTool = page.registeredTools[1];
const explainPriorityIssueTool = page.registeredTools[2];

assert.deepEqual(Object.keys(healthSummaryTool.inputSchema.properties), []);
const summary = await healthSummaryTool.execute({});
assert.deepEqual(
  Object.keys(summary),
  ["source", "demoMode", "evaluationDate", "overallScore", "scope", "categories", "issueCounts"],
);
assert.equal(summary.source, "fixture");
assert.equal(summary.demoMode, true);
assert.equal(summary.evaluationDate, "2026-08-20T12:00:00+00:00");
assert.equal(summary.overallScore, 60.4);
assert.deepEqual({ ...summary.scope }, { contacts: 8, deals: 5 });
assert.equal(summary.categories.length, 4);
assert.deepEqual(Array.from(summary.categories, (category) => category.score), [84.6, 33.3, 62.5, 62.5]);
assert.deepEqual(
  Object.keys(summary.categories[0]),
  ["category", "flagged", "applicable", "score", "normalizedWeight"],
);
assert.deepEqual(
  { ...summary.issueCounts },
  { malformedName: 3, missingOwner: 2, staleActivity: 1, staleOpenDeal: 2, weakActivity: 2 },
);
for (const invalidInput of [null, [], { extra: true }]) {
  await assert.rejects(
    () => healthSummaryTool.execute(invalidInput),
    (error) => error?.name === "TypeError" && error.message.length > 0,
  );
}

assert.deepEqual(
  Array.from(priorityIssuesTool.inputSchema.properties.objectType.enum),
  ["contact", "deal"],
);

const filtered = await priorityIssuesTool.execute({
  category: "missing_owner",
  objectType: "contact",
  minPriority: 40,
  limit: 1,
});
assert.equal(filtered.total, 2);
assert.equal(filtered.returned, 1);
assert.equal(filtered.issues[0].alias, "C-008");
assert.deepEqual(
  Array.from(filtered.issues[0].findings, (finding) => finding.category),
  ["missing_owner"],
);
assert.equal(page.rows[0].classList.contains("agent-focused"), true);
assert.equal(page.rows[0].focused, true);
assert.equal(page.rows[0].scrolled, true);
assert.equal(page.rows[0].getAttribute("aria-current"), "true");
assert.match(page.status.textContent, /Agent selected C-008/);

const dealResult = await priorityIssuesTool.execute({ objectType: "deal" });
assert.deepEqual(Array.from(dealResult.issues, (issue) => issue.alias), ["D-002"]);
assert.equal(page.rows[0].classList.contains("agent-focused"), false);
assert.equal(page.rows[1].classList.contains("agent-focused"), true);

for (const invalidInput of [
  null,
  [],
  { unknown: true },
  { objectType: "company" },
  { category: "not_a_category" },
  { minPriority: -1 },
  { minPriority: 101 },
  { minPriority: 10.5 },
  { limit: 0 },
  { limit: 21 },
  { limit: 1.5 },
]) {
  await assert.rejects(
    () => priorityIssuesTool.execute(invalidInput),
    (error) => error?.name === "TypeError" && error.message.length > 0,
  );
}

const explanation = await explainPriorityIssueTool.execute({ alias: "C-008" });
assert.deepEqual(
  Object.keys(explanation),
  ["alias", "displayName", "objectType", "priority", "findings", "disclaimer"],
);
assert.equal(explanation.alias, "C-008");
assert.equal(explanation.priority, 95);
assert.equal(explanation.findings.length, 2);
for (const finding of explanation.findings) {
  assert.deepEqual(
    Object.keys(finding),
    ["issueType", "category", "evidence", "impact", "recommendedSteps", "requiresHumanReview"],
  );
  assert.equal(finding.requiresHumanReview, true);
  assert.ok(finding.impact.length > 0);
  assert.ok(finding.recommendedSteps.length > 0);
  assert.ok(finding.recommendedSteps.length <= 5);
}
assert.equal(page.rows[0].classList.contains("agent-focused"), true);
assert.match(page.status.textContent, /Agent reviewing C-008/);
for (const invalidInput of [
  {},
  { alias: 8 },
  { alias: "" },
  { alias: "C-008", extra: true },
  { alias: "C-999" },
]) {
  await assert.rejects(
    () => explainPriorityIssueTool.execute(invalidInput),
    (error) => ["TypeError", "RangeError"].includes(error?.name),
  );
}

assert.deepEqual(loadPage({ webmcp: false }).registeredTools, []);
assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|WebSocket|sendBeacon)\b/);
assert.doesNotMatch(JSON.stringify(filtered), /(owner-a|@|portalId|sourcePayload|credential)/i);
assert.doesNotMatch(JSON.stringify(summary), /(owner-a|@|portalId|sourcePayload|credential)/i);
assert.doesNotMatch(JSON.stringify(explanation), /(owner-a|@|portalId|sourcePayload|credential)/i);

console.log("WebMCP contract tests passed");
