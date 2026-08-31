from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Union


# The orchestration layer may invoke only these HubSpot operations for a run.
# The application itself has no connector client and no CRM write path.
HUBSPOT_READ_TOOL_ALLOWLIST = (
    "get_user_details",
    "search_crm_objects",
)


@dataclass(frozen=True)
class Config:
    evaluation_date: datetime
    stale_deal_days: int = 30
    stale_contact_days: int = 90
    queue_limit: int = 20

    def __post_init__(self) -> None:
        if self.evaluation_date.tzinfo is None:
            raise ValueError("evaluation_date must be timezone-aware")
        if self.stale_deal_days < 0 or self.stale_contact_days < 0:
            raise ValueError("stale thresholds must be non-negative")


def parse_datetime(value: Optional[Union[str, datetime]]) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
