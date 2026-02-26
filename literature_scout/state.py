from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SeenRecord:
    identifier: str
    title: str
    last_seen_date: str


def load_seen(path: Path) -> dict[str, SeenRecord]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    records: dict[str, SeenRecord] = {}
    for identifier, item in raw.get("papers", {}).items():
        records[identifier] = SeenRecord(
            identifier=identifier,
            title=item.get("title", ""),
            last_seen_date=item.get("last_seen_date", ""),
        )
    return records


def save_seen(path: Path, records: dict[str, SeenRecord]) -> None:
    payload = {
        "papers": {
            key: {
                "title": record.title,
                "last_seen_date": record.last_seen_date,
            }
            for key, record in sorted(records.items())
        }
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def update_seen(
    records: dict[str, SeenRecord],
    entries: list[tuple[str, str]],
    seen_date: datetime | None = None,
) -> dict[str, SeenRecord]:
    stamp = (seen_date or datetime.utcnow()).date().isoformat()
    for identifier, title in entries:
        records[identifier] = SeenRecord(
            identifier=identifier,
            title=title,
            last_seen_date=stamp,
        )
    return records


def append_run_log(path: Path, run_entry: dict) -> None:
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = {"runs": []}

    payload.setdefault("runs", []).append(run_entry)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
