"""Normalize fixture and HubSpot MCP payloads into source-independent records."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Optional, Union

from .config import parse_datetime


@dataclass(frozen=True)
class Contact:
    alias: str
    firstname: Optional[str]
    lastname: Optional[str]
    owner_id: Optional[str]
    created_at: Optional[object]
    notes_last_updated: Optional[object]
    notes_last_contacted: Optional[object]
    last_sales_activity: Optional[object]

    @property
    def display_name(self) -> str:
        name = " ".join(part for part in (self.firstname, self.lastname) if part)
        return name or self.alias


@dataclass(frozen=True)
class Deal:
    alias: str
    name: Optional[str]
    owner_id: Optional[str]
    created_at: Optional[object]
    notes_last_updated: Optional[object]
    notes_last_contacted: Optional[object]
    is_closed_won: bool
    is_closed_lost: bool

    @property
    def display_name(self) -> str:
        return self.name or self.alias


@dataclass(frozen=True)
class Dataset:
    source: str
    contacts: tuple[Contact, ...]
    deals: tuple[Deal, ...]


def _missing(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _contact(data: dict[str, Any], alias: str) -> Contact:
    return Contact(
        alias=alias,
        firstname=data.get("firstname"),
        lastname=data.get("lastname"),
        owner_id=_missing(data.get("hubspot_owner_id")),
        created_at=parse_datetime(data.get("createdate") or data.get("createdAt")),
        notes_last_updated=parse_datetime(data.get("notes_last_updated")),
        notes_last_contacted=parse_datetime(data.get("notes_last_contacted")),
        last_sales_activity=parse_datetime(data.get("hs_last_sales_activity_timestamp")),
    )


def _deal(data: dict[str, Any], alias: str) -> Deal:
    return Deal(
        alias=alias,
        name=data.get("dealname"),
        owner_id=_missing(data.get("hubspot_owner_id")),
        created_at=parse_datetime(data.get("createdate") or data.get("createdAt")),
        notes_last_updated=parse_datetime(data.get("notes_last_updated")),
        notes_last_contacted=parse_datetime(data.get("notes_last_contacted")),
        is_closed_won=_bool(data.get("hs_is_closed_won")),
        is_closed_lost=_bool(data.get("hs_is_closed_lost")),
    )


def normalize_fixture(payload: dict[str, Any]) -> Dataset:
    contacts = tuple(
        _contact(row, row["alias"]) for row in payload.get("contacts", [])
    )
    deals = tuple(_deal(row, row["alias"]) for row in payload.get("deals", []))
    return Dataset(source="fixture", contacts=contacts, deals=deals)


def _results(section: Any) -> list[dict[str, Any]]:
    if isinstance(section, dict):
        return section.get("results", [])
    return []


def normalize_hubspot(payload: dict[str, Any]) -> Dataset:
    """Normalize MCP search results while intentionally discarding raw record IDs."""
    contacts = []
    for index, row in enumerate(_results(payload.get("contacts")), start=1):
        properties = dict(row.get("properties", {}))
        properties["createdAt"] = row.get("createdAt") or properties.get("createdate")
        contacts.append(_contact(properties, f"C-{index:03d}"))

    deals = []
    for index, row in enumerate(_results(payload.get("deals")), start=1):
        properties = dict(row.get("properties", {}))
        properties["createdAt"] = row.get("createdAt") or properties.get("createdate")
        deals.append(_deal(properties, f"D-{index:03d}"))

    return Dataset(source="hubspot", contacts=tuple(contacts), deals=tuple(deals))


def load_dataset(path: Union[str, Path], source: str) -> Dataset:
    with Path(path).open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if source == "fixture":
        return normalize_fixture(payload)
    if source == "hubspot":
        return normalize_hubspot(payload)
    raise ValueError(f"unsupported source: {source}")
