"""Deterministic, human-reviewed remediation guidance for diagnostic findings."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Guidance:
    impact: str
    recommended_steps: tuple[str, ...]
    requires_human_review: bool = True


GUIDANCE_BY_ISSUE_TYPE = {
    "missing_owner": Guidance(
        impact="Unowned records can miss routing, accountability, and follow-up.",
        recommended_steps=(
            "Review assignment rules and identify the intended owner.",
            "Confirm ownership with the responsible human.",
            "Assign or correct the owner only after confirmation.",
        ),
    ),
    "malformed_name": Guidance(
        impact="Suspicious formatting can reduce matching, personalization, and reporting reliability.",
        recommended_steps=(
            "Review the flagged formatting against an authoritative identity source.",
            "Verify the correct human or company identity.",
            "Normalize the value only after human confirmation.",
        ),
    ),
    "weak_activity": Guidance(
        impact="Missing approved engagement signals makes recency and follow-up decisions unreliable.",
        recommended_steps=(
            "Check approved engagement sources for missing synchronization or logging.",
            "Determine whether engagement is absent or the data is incomplete.",
            "Correct the source or workflow after review; do not manufacture activity.",
        ),
    ),
    "stale_activity": Guidance(
        impact="Stale engagement signals can drive outdated segmentation, prioritization, or outreach.",
        recommended_steps=(
            "Verify the latest legitimate engagement across approved sources.",
            "Confirm whether the contact should remain active in the current process.",
            "Update follow-up or lifecycle state only after human review; do not manufacture activity.",
        ),
    ),
    "stale_open_deal": Guidance(
        impact="An apparently stale open deal can distort pipeline reporting, forecasting, and automation.",
        recommended_steps=(
            "Verify the current deal stage and latest legitimate activity.",
            "Confirm the intended status with the responsible owner.",
            "Close, update, or re-engage only after human review.",
        ),
    ),
    "unknown_deal_activity": Guidance(
        impact="Without an approved activity or creation timestamp, deal recency cannot be assessed reliably.",
        recommended_steps=(
            "Inspect approved source systems for missing timestamps or synchronization gaps.",
            "Verify the current deal status with the responsible owner.",
            "Correct timestamps or status only from verified evidence after human review.",
        ),
    ),
}


def guidance_for(issue_type: str) -> Guidance:
    """Fail closed when a diagnostic issue lacks deterministic guidance."""
    try:
        return GUIDANCE_BY_ISSUE_TYPE[issue_type]
    except KeyError as error:
        raise ValueError(f"No deterministic guidance for issue type: {issue_type}") from error
