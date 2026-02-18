from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AppendOnlyLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        entries = self.read_all()
        previous_hash = entries[-1]["entry_hash"] if entries else "GENESIS"
        index = len(entries)
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        material = json.dumps(
            {"index": index, "payload": payload, "previous_hash": previous_hash},
            sort_keys=True,
            separators=(",", ":"),
        )
        entry_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()

        entry = {
            "index": index,
            "timestamp": timestamp,
            "payload": payload,
            "previous_hash": previous_hash,
            "entry_hash": entry_hash,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def read_all(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def verify_chain(self) -> bool:
        entries = self.read_all()
        previous_hash = "GENESIS"
        for index, entry in enumerate(entries):
            if entry.get("index") != index:
                return False
            if entry.get("previous_hash") != previous_hash:
                return False
            material = json.dumps(
                {
                    "index": index,
                    "payload": entry.get("payload"),
                    "previous_hash": previous_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            expected_hash = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if entry.get("entry_hash") != expected_hash:
                return False
            previous_hash = entry["entry_hash"]
        return True

