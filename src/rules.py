"""Pure, deterministic CRM health rules."""

from dataclasses import dataclass
from datetime import datetime
import unicodedata

from .adapter import Contact, Dataset, Deal
from .config import Config


@dataclass(frozen=True)
class Issue:
    alias: str
    object_type: str
    display_name: str
    category: str
    issue_type: str
    explanation: str
    severity_points: int
    age_bonus: int = 0


@dataclass(frozen=True)
class Evaluation:
    issues: tuple[Issue, ...]
    applicable: dict[str, int]


def _age_days(evaluation_date: datetime, timestamp: datetime) -> int:
    return max(0, (evaluation_date - timestamp).days)


def _letters(value: str) -> list[str]:
    return [character for character in value if character.isalpha()]


def name_quality_reasons(contact: Contact) -> list[str]:
    reasons: list[str] = []
    for label, value in (("first name", contact.firstname), ("last name", contact.lastname)):
        if not value:
            continue
        if value != value.strip():
            reasons.append(f"{label} has leading or trailing whitespace")
        if any(first.isspace() and second.isspace() for first, second in zip(value, value[1:])):
            reasons.append(f"{label} has repeated internal whitespace")
        if any(character.isdigit() for character in value):
            reasons.append(f"{label} contains digits")
        letters = _letters(value)
        if len(letters) >= 2 and all(character.isupper() for character in letters):
            reasons.append(f"{label} is ALL CAPS")
        # Forces Unicode decoding during validation without restricting cultures.
        unicodedata.normalize("NFC", value)
    return reasons


def _owner_issues(dataset: Dataset) -> list[Issue]:
    issues: list[Issue] = []
    records = [("contact", record) for record in dataset.contacts]
    records += [("deal", record) for record in dataset.deals]
    for object_type, record in records:
        if record.owner_id is None:
            issues.append(Issue(
                alias=record.alias,
                object_type=object_type,
                display_name=record.display_name,
                category="missing_owner",
                issue_type="missing_owner",
                explanation="Owner is absent or blank.",
                severity_points=40,
            ))
    return issues


def _name_issues(contacts: tuple[Contact, ...]) -> list[Issue]:
    issues: list[Issue] = []
    for contact in contacts:
        reasons = name_quality_reasons(contact)
        if reasons:
            issues.append(Issue(
                alias=contact.alias,
                object_type="contact",
                display_name=contact.display_name,
                category="name_quality",
                issue_type="malformed_name",
                explanation="; ".join(reasons) + ".",
                severity_points=20,
            ))
    return issues


def _contact_activity_issues(contacts: tuple[Contact, ...], config: Config) -> list[Issue]:
    issues: list[Issue] = []
    for contact in contacts:
        signals = [
            value for value in (
                contact.notes_last_updated,
                contact.notes_last_contacted,
                contact.last_sales_activity,
            ) if value is not None
        ]
        if not signals:
            issues.append(Issue(
                alias=contact.alias,
                object_type="contact",
                display_name=contact.display_name,
                category="contact_activity",
                issue_type="weak_activity",
                explanation="No approved contact activity signal exists; creation time is not treated as engagement.",
                severity_points=35,
            ))
            continue
        latest = max(signals)
        age = _age_days(config.evaluation_date, latest)
        if age > config.stale_contact_days:
            over = age - config.stale_contact_days
            issues.append(Issue(
                alias=contact.alias,
                object_type="contact",
                display_name=contact.display_name,
                category="contact_activity",
                issue_type="stale_activity",
                explanation=(
                    f"Latest approved activity is {age} days old, exceeding the "
                    f"{config.stale_contact_days}-day threshold by {over} days."
                ),
                severity_points=30,
                age_bonus=min(over, 20),
            ))
    return issues


def _deal_activity_issues(deals: tuple[Deal, ...], config: Config) -> tuple[list[Issue], int]:
    issues: list[Issue] = []
    applicable = 0
    for deal in deals:
        if deal.is_closed_won or deal.is_closed_lost:
            continue
        applicable += 1
        activity = [
            value for value in (deal.notes_last_updated, deal.notes_last_contacted)
            if value is not None
        ]
        timestamp = max(activity) if activity else deal.created_at
        if timestamp is None:
            issues.append(Issue(
                alias=deal.alias,
                object_type="deal",
                display_name=deal.display_name,
                category="stale_open_deals",
                issue_type="unknown_deal_activity",
                explanation="Open deal has no approved activity timestamp and no creation-time fallback; staleness is unknown.",
                severity_points=40,
            ))
            continue
        age = _age_days(config.evaluation_date, timestamp)
        if age > config.stale_deal_days:
            over = age - config.stale_deal_days
            source = "latest activity" if activity else "creation-time fallback"
            issues.append(Issue(
                alias=deal.alias,
                object_type="deal",
                display_name=deal.display_name,
                category="stale_open_deals",
                issue_type="stale_open_deal",
                explanation=(
                    f"Open deal's {source} is {age} days old, exceeding the "
                    f"{config.stale_deal_days}-day threshold by {over} days."
                ),
                severity_points=45,
                age_bonus=min(over, 30),
            ))
    return issues, applicable


def evaluate(dataset: Dataset, config: Config) -> Evaluation:
    deal_issues, open_deals = _deal_activity_issues(dataset.deals, config)
    issues = (
        _owner_issues(dataset)
        + _name_issues(dataset.contacts)
        + _contact_activity_issues(dataset.contacts, config)
        + deal_issues
    )
    issues.sort(key=lambda issue: (issue.object_type, issue.alias, issue.issue_type))
    return Evaluation(
        issues=tuple(issues),
        applicable={
            "missing_owner": len(dataset.contacts) + len(dataset.deals),
            "stale_open_deals": open_deals,
            "name_quality": len(dataset.contacts),
            "contact_activity": len(dataset.contacts),
        },
    )
