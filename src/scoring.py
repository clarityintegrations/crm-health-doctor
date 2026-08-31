"""Auditable category scoring and deterministic review prioritization."""

from dataclasses import dataclass
from collections import defaultdict
from typing import Optional

from .config import Config
from .rules import Evaluation, Issue


CATEGORY_WEIGHTS = {
    "missing_owner": 0.30,
    "stale_open_deals": 0.30,
    "name_quality": 0.15,
    "contact_activity": 0.25,
}


@dataclass(frozen=True)
class CategoryScore:
    category: str
    flagged: int
    applicable: int
    raw_weight: float
    normalized_weight: float
    score: Optional[float]


@dataclass(frozen=True)
class Scorecard:
    overall_score: float
    categories: tuple[CategoryScore, ...]
    active_weight_total: float


@dataclass(frozen=True)
class QueueRow:
    alias: str
    object_type: str
    display_name: str
    priority: int
    issues: tuple[Issue, ...]


def calculate_score(evaluation: Evaluation) -> Scorecard:
    flagged_by_category: dict[str, set[str]] = defaultdict(set)
    for issue in evaluation.issues:
        flagged_by_category[issue.category].add(f"{issue.object_type}:{issue.alias}")

    active_weight_total = sum(
        weight for category, weight in CATEGORY_WEIGHTS.items()
        if evaluation.applicable.get(category, 0) > 0
    )
    categories: list[CategoryScore] = []
    weighted_total = 0.0
    for category, raw_weight in CATEGORY_WEIGHTS.items():
        applicable = evaluation.applicable.get(category, 0)
        flagged = len(flagged_by_category.get(category, set()))
        if applicable == 0:
            score = None
            normalized_weight = 0.0
        else:
            score = 100.0 * (1.0 - flagged / applicable)
            normalized_weight = raw_weight / active_weight_total
            weighted_total += score * normalized_weight
        categories.append(CategoryScore(
            category=category,
            flagged=flagged,
            applicable=applicable,
            raw_weight=raw_weight,
            normalized_weight=normalized_weight,
            score=score,
        ))
    return Scorecard(
        overall_score=round(weighted_total, 1) if active_weight_total else 100.0,
        categories=tuple(categories),
        active_weight_total=active_weight_total,
    )


def build_queue(evaluation: Evaluation, config: Config) -> tuple[QueueRow, ...]:
    grouped: dict[tuple[str, str], list[Issue]] = defaultdict(list)
    for issue in evaluation.issues:
        grouped[(issue.object_type, issue.alias)].append(issue)

    rows = []
    for (object_type, alias), issues in grouped.items():
        ordered = tuple(sorted(issues, key=lambda item: item.issue_type))
        priority = min(100, sum(issue.severity_points + issue.age_bonus for issue in ordered))
        rows.append(QueueRow(
            alias=alias,
            object_type=object_type,
            display_name=ordered[0].display_name,
            priority=priority,
            issues=ordered,
        ))
    rows.sort(key=lambda row: (-row.priority, row.object_type, row.alias))
    return tuple(rows[:config.queue_limit])
