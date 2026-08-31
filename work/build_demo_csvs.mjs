import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const outputDir = path.resolve("../demo-data");
await fs.mkdir(outputDir, { recursive: true });

const contacts = [
  ["Email", "First Name", "Last Name", "Contact owner", "Demo Scenario"],
  ["healthy.contact@example.com", "Maya", "Chen", "ASSIGN_TEST_PORTAL_OWNER", "Healthy Contact"],
  ["unowned.contact@example.com", "Jonas", "Rivera", "", "Unowned Contact"],
  ["malformed.contact@example.com", "MARIA7", "LOPEZ", "ASSIGN_TEST_PORTAL_OWNER", "Malformed Contact"],
  ["no.activity.contact@example.com", "Noah", "Williams", "ASSIGN_TEST_PORTAL_OWNER", "No Activity Contact"],
  ["stale.contact@example.com", "Amina", "Diallo", "ASSIGN_TEST_PORTAL_OWNER", "Stale Contact"],
];

const deals = [
  ["Deal Name", "Deal Pipeline", "Deal Stage", "Deal owner", "Close date", "Demo Scenario"],
  ["DEMO - Healthy Open Deal", "MAP_TO_TEST_PIPELINE", "MAP_TO_OPEN_STAGE", "ASSIGN_TEST_PORTAL_OWNER", "", "Healthy Open Deal"],
  ["DEMO - Stale Open Deal", "MAP_TO_TEST_PIPELINE", "MAP_TO_OPEN_STAGE", "ASSIGN_TEST_PORTAL_OWNER", "", "Stale Open Deal"],
  ["DEMO - New No-Activity Deal", "MAP_TO_TEST_PIPELINE", "MAP_TO_OPEN_STAGE", "ASSIGN_TEST_PORTAL_OWNER", "", "New No-Activity Deal"],
  ["DEMO - Old Closed Deal", "MAP_TO_TEST_PIPELINE", "MAP_TO_CLOSED_WON_STAGE", "ASSIGN_TEST_PORTAL_OWNER", "2026-04-01", "Old Closed Deal"],
];

const workbook = Workbook.create();
const contactsSheet = workbook.worksheets.add("Contacts");
contactsSheet.getRange("A1:E6").values = contacts;
const dealsSheet = workbook.worksheets.add("Deals");
dealsSheet.getRange("A1:F5").values = deals;

function csvCell(value) {
  const text = value == null ? "" : String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function toCsv(rows) {
  return rows.map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n";
}

await fs.writeFile(path.join(outputDir, "contacts.csv"), toCsv(contacts), "utf8");
await fs.writeFile(path.join(outputDir, "deals.csv"), toCsv(deals), "utf8");

const contactsCheck = await Workbook.fromCSV(toCsv(contacts), { sheetName: "Contacts" });
const dealsCheck = await Workbook.fromCSV(toCsv(deals), { sheetName: "Deals" });
const contactsPreviewSheet = contactsCheck.worksheets.getItem("Contacts");
contactsPreviewSheet.getRange("A1:E1").format = { fill: "#DCEAF7", font: { bold: true, color: "#17213A" } };
contactsPreviewSheet.getRange("A:A").format.columnWidthPx = 250;
contactsPreviewSheet.getRange("B:B").format.columnWidthPx = 120;
contactsPreviewSheet.getRange("C:C").format.columnWidthPx = 140;
contactsPreviewSheet.getRange("D:D").format.columnWidthPx = 260;
contactsPreviewSheet.getRange("E:E").format.columnWidthPx = 190;
const dealsPreviewSheet = dealsCheck.worksheets.getItem("Deals");
dealsPreviewSheet.getRange("A1:F1").format = { fill: "#DCEAF7", font: { bold: true, color: "#17213A" } };
dealsPreviewSheet.getRange("A:A").format.columnWidthPx = 230;
dealsPreviewSheet.getRange("B:B").format.columnWidthPx = 190;
dealsPreviewSheet.getRange("C:C").format.columnWidthPx = 260;
dealsPreviewSheet.getRange("D:D").format.columnWidthPx = 260;
dealsPreviewSheet.getRange("E:E").format.columnWidthPx = 110;
dealsPreviewSheet.getRange("F:F").format.columnWidthPx = 180;
const contactInspect = await contactsCheck.inspect({
  kind: "table",
  range: "Contacts!A1:E6",
  include: "values,formulas",
  tableMaxRows: 6,
  tableMaxCols: 5,
});
const dealInspect = await dealsCheck.inspect({
  kind: "table",
  range: "Deals!A1:F5",
  include: "values,formulas",
  tableMaxRows: 5,
  tableMaxCols: 6,
});

const contactsPreview = await contactsCheck.render({ sheetName: "Contacts", autoCrop: "all", scale: 1, format: "png" });
const dealsPreview = await dealsCheck.render({ sheetName: "Deals", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile("contacts-preview.png", new Uint8Array(await contactsPreview.arrayBuffer()));
await fs.writeFile("deals-preview.png", new Uint8Array(await dealsPreview.arrayBuffer()));

console.log(contactInspect.ndjson);
console.log(dealInspect.ndjson);
