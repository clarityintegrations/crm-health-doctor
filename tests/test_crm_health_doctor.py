import json
from dataclasses import replace
from pathlib import Path
import re
import tempfile
import unittest

from src.adapter import Contact, Dataset, Deal, normalize_hubspot, normalize_fixture
from src.config import Config, HUBSPOT_READ_TOOL_ALLOWLIST, parse_datetime
from src.report import render_html
from src.rules import evaluate, name_quality_reasons
from src.scoring import build_queue, calculate_score


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DATE = parse_datetime("2026-08-20T12:00:00Z")
CONFIG = Config(evaluation_date=EVALUATION_DATE)


def load_fixture():
    with (ROOT / "fixtures" / "health_matrix.json").open(encoding="utf-8") as handle:
        return normalize_fixture(json.load(handle))


def contact(alias="C-X", firstname="Maya", lastname="Chen", owner="owner-a", activity="2026-08-01T12:00:00Z"):
    return Contact(
        alias=alias,
        firstname=firstname,
        lastname=lastname,
        owner_id=owner,
        created_at=parse_datetime("2026-01-01T12:00:00Z"),
        notes_last_updated=parse_datetime(activity),
        notes_last_contacted=None,
        last_sales_activity=None,
    )


def deal(alias="D-X", created="2026-01-01T12:00:00Z", activity="2026-08-01T12:00:00Z", won=False, lost=False):
    return Deal(
        alias=alias,
        name="Deal",
        owner_id="owner-a",
        created_at=parse_datetime(created) if created else None,
        notes_last_updated=parse_datetime(activity) if activity else None,
        notes_last_contacted=None,
        is_closed_won=won,
        is_closed_lost=lost,
    )


class FixtureMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = load_fixture()
        cls.evaluation = evaluate(cls.dataset, CONFIG)
        cls.by_alias = {}
        for issue in cls.evaluation.issues:
            cls.by_alias.setdefault(issue.alias, set()).add(issue.issue_type)

    def test_all_required_fixtures_exist(self):
        self.assertEqual([item.alias for item in self.dataset.contacts], [f"C-{n:03d}" for n in range(1, 9)])
        self.assertEqual([item.alias for item in self.dataset.deals], [f"D-{n:03d}" for n in range(1, 6)])

    def test_contact_expectations(self):
        self.assertNotIn("C-001", self.by_alias)
        self.assertEqual(self.by_alias["C-002"], {"missing_owner"})
        self.assertEqual(self.by_alias["C-003"], {"malformed_name"})
        self.assertNotIn("C-004", self.by_alias)
        self.assertEqual(self.by_alias["C-005"], {"malformed_name"})
        self.assertEqual(self.by_alias["C-006"], {"weak_activity"})
        self.assertEqual(self.by_alias["C-007"], {"stale_activity"})
        self.assertEqual(
            self.by_alias["C-008"],
            {"missing_owner", "malformed_name", "weak_activity"},
        )

    def test_deal_expectations_and_closed_exclusions(self):
        self.assertNotIn("D-001", self.by_alias)
        self.assertEqual(self.by_alias["D-002"], {"stale_open_deal"})
        self.assertEqual(self.by_alias["D-003"], {"stale_open_deal"})
        self.assertNotIn("D-004", self.by_alias)
        self.assertNotIn("D-005", self.by_alias)
        fallback = next(issue for issue in self.evaluation.issues if issue.alias == "D-003")
        self.assertIn("creation-time fallback", fallback.explanation)

    def test_fixture_score_is_auditable(self):
        score = calculate_score(self.evaluation)
        self.assertEqual(score.overall_score, 60.4)
        audit = {item.category: (item.flagged, item.applicable) for item in score.categories}
        self.assertEqual(audit["missing_owner"], (2, 13))
        self.assertEqual(audit["stale_open_deals"], (2, 3))
        self.assertEqual(audit["name_quality"], (3, 8))
        self.assertEqual(audit["contact_activity"], (3, 8))

    def test_queue_consolidation_and_ordering(self):
        queue = build_queue(self.evaluation, CONFIG)
        self.assertEqual(len(queue), 8)
        self.assertEqual([row.alias for row in queue[:3]], ["C-008", "D-002", "D-003"])
        self.assertEqual(queue[0].priority, 95)
        self.assertEqual(len(queue[0].issues), 3)


class BoundaryAndValidationTests(unittest.TestCase):
    def issue_types(self, dataset):
        return {issue.issue_type for issue in evaluate(dataset, CONFIG).issues}

    def test_contact_exactly_at_90_days_is_not_stale(self):
        dataset = Dataset("fixture", (contact(activity="2026-05-22T12:00:00Z"),), ())
        self.assertNotIn("stale_activity", self.issue_types(dataset))

    def test_contact_91_days_is_stale(self):
        dataset = Dataset("fixture", (contact(activity="2026-05-21T12:00:00Z"),), ())
        self.assertIn("stale_activity", self.issue_types(dataset))

    def test_deal_exactly_at_30_days_is_not_stale(self):
        dataset = Dataset("fixture", (), (deal(activity="2026-07-21T12:00:00Z"),))
        self.assertNotIn("stale_open_deal", self.issue_types(dataset))

    def test_deal_31_days_is_stale(self):
        dataset = Dataset("fixture", (), (deal(activity="2026-07-20T12:00:00Z"),))
        self.assertIn("stale_open_deal", self.issue_types(dataset))

    def test_no_deal_timestamp_returns_diagnostic(self):
        dataset = Dataset("fixture", (), (deal(created=None, activity=None),))
        self.assertIn("unknown_deal_activity", self.issue_types(dataset))

    def test_unicode_apostrophe_and_hyphen_are_allowed(self):
        self.assertEqual(name_quality_reasons(contact(firstname="Élodie", lastname="O'Connor-Sánchez")), [])

    def test_unicode_all_caps_is_detected(self):
        reasons = name_quality_reasons(contact(firstname="ÉLODIE", lastname="Sánchez"))
        self.assertIn("first name is ALL CAPS", reasons)

    def test_digits_and_whitespace_are_detected(self):
        reasons = name_quality_reasons(contact(firstname="  Agent7  Smith ", lastname="Jones"))
        self.assertIn("first name contains digits", reasons)
        self.assertIn("first name has leading or trailing whitespace", reasons)
        self.assertIn("first name has repeated internal whitespace", reasons)

    def test_zero_applicable_category_renormalizes_weights(self):
        dataset = Dataset("fixture", (contact(owner=None),), ())
        score = calculate_score(evaluate(dataset, CONFIG))
        self.assertEqual(score.overall_score, 57.1)
        stale_deals = next(item for item in score.categories if item.category == "stale_open_deals")
        self.assertIsNone(stale_deals.score)
        self.assertEqual(stale_deals.normalized_weight, 0.0)

    def test_empty_dataset_scores_100(self):
        score = calculate_score(evaluate(Dataset("fixture", (), ()), CONFIG))
        self.assertEqual(score.overall_score, 100.0)
        self.assertEqual(score.active_weight_total, 0)

    def test_missing_owner_applies_to_contacts_and_all_deals(self):
        dataset = Dataset(
            "fixture",
            (contact(owner="owner-a"),),
            (replace(deal(won=True), owner_id=None),),
        )
        evaluation = evaluate(dataset, CONFIG)
        owner_issues = [issue for issue in evaluation.issues if issue.issue_type == "missing_owner"]
        self.assertEqual([(issue.object_type, issue.alias) for issue in owner_issues], [("deal", "D-X")])
        self.assertEqual(evaluation.applicable["missing_owner"], 2)


class AdapterAndReportTests(unittest.TestCase):
    def test_hubspot_tool_allowlist_is_read_only(self):
        self.assertEqual(
            HUBSPOT_READ_TOOL_ALLOWLIST,
            ("get_user_details", "search_crm_objects"),
        )
        self.assertFalse(any(word in tool for tool in HUBSPOT_READ_TOOL_ALLOWLIST for word in ("manage", "create", "update", "delete", "merge")))

    def test_hubspot_adapter_discards_ids(self):
        raw_id = "sensitive-record-id"
        payload = {
            "contacts": {"results": [{"id": raw_id, "properties": {"firstname": "Maya", "lastname": "Chen"}}]},
            "deals": {"results": [{"id": raw_id, "properties": {"dealname": "Example"}}]},
        }
        dataset = normalize_hubspot(payload)
        self.assertEqual(dataset.contacts[0].alias, "C-001")
        self.assertEqual(dataset.deals[0].alias, "D-001")
        self.assertNotIn(raw_id, repr(dataset))

    def test_html_escapes_crm_values_and_has_no_external_assets(self):
        malicious = contact(firstname="<script>alert('x')</script>", owner=None)
        dataset = Dataset("fixture", (malicious,), ())
        evaluation = evaluate(dataset, CONFIG)
        html = render_html(dataset, CONFIG, evaluation, calculate_score(evaluation), build_queue(evaluation, CONFIG))
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_queue_tie_breaking_is_stable(self):
        dataset = Dataset(
            "fixture",
            (contact(alias="C-002", owner=None), contact(alias="C-001", owner=None)),
            (),
        )
        queue = build_queue(evaluate(dataset, CONFIG), CONFIG)
        self.assertEqual([row.alias for row in queue], ["C-001", "C-002"])

    def test_fixture_report_embeds_safe_bounded_webmcp_state(self):
        malicious = contact(
            alias="C-SAFE",
            firstname="</script><script>alert(1)</script>",
            owner=None,
        )
        dataset = Dataset("fixture", (malicious,), ())
        evaluation = evaluate(dataset, CONFIG)
        html = render_html(
            dataset,
            CONFIG,
            evaluation,
            calculate_score(evaluation),
            build_queue(evaluation, CONFIG),
        )
        match = re.search(
            r'<script type="application/json" id="crm-health-snapshot">(.*?)</script>',
            html,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        serialized = match.group(1)
        self.assertNotIn("<", serialized)
        self.assertIn(r"\u003c/script\u003e", serialized)
        snapshot = json.loads(serialized)
        self.assertEqual(snapshot["version"], 1)
        self.assertLessEqual(len(snapshot["issues"]), 20)
        self.assertNotIn("owner-a", serialized)
        self.assertNotIn("hubspot_owner_id", serialized)

    def test_snapshot_aliases_match_rendered_rows_and_queue_order(self):
        dataset = load_fixture()
        evaluation = evaluate(dataset, CONFIG)
        queue = build_queue(evaluation, CONFIG)
        html = render_html(
            dataset,
            CONFIG,
            evaluation,
            calculate_score(evaluation),
            queue,
        )
        serialized = re.search(
            r'<script type="application/json" id="crm-health-snapshot">(.*?)</script>',
            html,
            re.DOTALL,
        ).group(1)
        snapshot_aliases = [item["alias"] for item in json.loads(serialized)["issues"]]
        rendered_aliases = re.findall(r'<tr data-alias="([^"]+)">', html)
        self.assertEqual(snapshot_aliases, [row.alias for row in queue])
        self.assertEqual(rendered_aliases, snapshot_aliases)

    def test_only_fixture_reports_register_webmcp(self):
        dataset = Dataset("hubspot", (contact(owner=None),), ())
        evaluation = evaluate(dataset, CONFIG)
        html = render_html(
            dataset,
            CONFIG,
            evaluation,
            calculate_score(evaluation),
            build_queue(evaluation, CONFIG),
        )
        self.assertNotIn("crm-health-snapshot", html)
        self.assertNotIn("list_priority_issues", html)
        self.assertNotIn("Synthetic WebMCP Challenge Demo", html)


if __name__ == "__main__":
    unittest.main()
