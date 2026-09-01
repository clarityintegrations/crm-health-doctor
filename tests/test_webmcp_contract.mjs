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
  issues: [
    {
      alias: "C-008",
      displayName: "TEST USER 99",
      objectType: "contact",
      priority: 95,
      findings: [
        { issueType: "missing_owner", category: "missing_owner", evidence: "Owner is absent or blank." },
        { issueType: "weak_activity", category: "contact_activity", evidence: "No approved activity signal exists." },
      ],
    },
    {
      alias: "D-002",
      displayName: "Stale Renewal",
      objectType: "deal",
      priority: 75,
      findings: [
        { issueType: "stale_open_deal", category: "stale_open_deals", evidence: "Latest activity exceeds the threshold." },
      ],
    },
    {
      alias: "C-002",
      displayName: "Jonas Rivera",
      objectType: "contact",
      priority: 40,
      findings: [
        { issueType: "missing_owner", category: "missing_owner", evidence: "Owner is absent or blank." },
      ],
    },
  ],
};

function loadPage({ webmcp = true } = {}) {
  let registeredTool;
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
        registeredTool = tool;
        return Promise.resolve();
      },
    };
  }
  vm.runInNewContext(source, { document, console });
  return { registeredTool, rows, status };
}

const page = loadPage();
assert.equal(page.registeredTool.name, "list_priority_issues");
assert.equal(page.registeredTool.inputSchema.additionalProperties, false);
assert.deepEqual(
  Array.from(page.registeredTool.inputSchema.properties.objectType.enum),
  ["contact", "deal"],
);
assert.equal(page.registeredTool.annotations.readOnlyHint, true);
assert.equal(page.registeredTool.annotations.untrustedContentHint, true);

const filtered = await page.registeredTool.execute({
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

const dealResult = await page.registeredTool.execute({ objectType: "deal" });
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
    () => page.registeredTool.execute(invalidInput),
    (error) => error?.name === "TypeError" && error.message.length > 0,
  );
}

assert.equal(loadPage({ webmcp: false }).registeredTool, undefined);
assert.doesNotMatch(source, /\b(fetch|XMLHttpRequest|WebSocket|sendBeacon)\b/);
assert.doesNotMatch(JSON.stringify(filtered), /(owner-a|@|portalId|sourcePayload|credential)/i);

console.log("WebMCP contract tests passed");
