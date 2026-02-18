from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ree_openclaw.ledger.append_only import AppendOnlyLedger


class OfflineTriggerError(PermissionError):
    """Raised when offline consolidation is requested from an untrusted trigger."""


@dataclass(frozen=True)
class ConsolidationResult:
    output_path: Path
    processed_entries: int
    generated_at: str


class OfflineConsolidator:
    _ALLOWED_TRIGGERS = {"scheduler", "operator_cli"}

    def __init__(self, ledger: AppendOnlyLedger, output_dir: Path) -> None:
        self.ledger = ledger
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def consolidate(self, *, trigger_source: str) -> ConsolidationResult:
        if trigger_source not in self._ALLOWED_TRIGGERS:
            raise OfflineTriggerError(
                f"offline consolidation blocked for trigger_source={trigger_source!r}"
            )

        entries = self.ledger.read_all()
        summary = self._build_summary(entries)
        generated_at = datetime.now(tz=timezone.utc).isoformat()
        artifact = {
            "generated_at": generated_at,
            "trigger_source": trigger_source,
            "processed_entries": len(entries),
            "action_reliability": summary,
        }
        output_path = self.output_dir / "skill_reliability.json"
        output_path.write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
        return ConsolidationResult(
            output_path=output_path,
            processed_entries=len(entries),
            generated_at=generated_at,
        )

    @staticmethod
    def _build_summary(entries: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
        summary: dict[str, dict[str, float | int]] = {}
        for entry in entries:
            payload = entry.get("payload", {})
            action_class = str(payload.get("action_class", "UNKNOWN_ACTION"))
            action_bucket = summary.setdefault(
                action_class,
                {"total_events": 0, "commit_events": 0, "success_events": 0, "success_rate": 0.0},
            )
            action_bucket["total_events"] += 1
            if payload.get("event") == "commit_executed":
                action_bucket["commit_events"] += 1
                execution = payload.get("execution", {})
                if isinstance(execution, dict) and execution.get("returncode") == 0:
                    action_bucket["success_events"] += 1

        for action_bucket in summary.values():
            commit_events = int(action_bucket["commit_events"])
            if commit_events == 0:
                action_bucket["success_rate"] = 0.0
            else:
                action_bucket["success_rate"] = round(
                    float(action_bucket["success_events"]) / commit_events,
                    4,
                )
        return summary
