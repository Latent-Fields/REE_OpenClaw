from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class SessionMemorySummary:
    total_sessions: int
    total_step_records: int
    trajectory_bias: dict[str, float]


class AutonomousSessionMemoryStore:
    """Persistent autonomy memory store, separate from trusted POL/ID/CAPS stores."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def start_session(self, *, goal_text: str, policy_snapshot: dict[str, Any]) -> str:
        session_id = str(uuid4())
        self._append(
            {
                "event": "session_started",
                "session_id": session_id,
                "goal_text": goal_text,
                "policy_snapshot": policy_snapshot,
            }
        )
        return session_id

    def append_step_record(
        self,
        *,
        session_id: str,
        step_index: int,
        user_intent: str,
        selected_trajectory_reference: str,
        selected_ranking_score: float,
        memory_bias_applied: float,
        action_class: str,
        scope: str,
        effect_class: str,
        allowed: bool,
        reason: str,
        rc_state: str,
        rc_conflict_score: float,
        commit_id: str | None,
    ) -> None:
        self._append(
            {
                "event": "step_recorded",
                "session_id": session_id,
                "step_index": step_index,
                "user_intent": user_intent,
                "selected_trajectory_reference": selected_trajectory_reference,
                "selected_ranking_score": selected_ranking_score,
                "memory_bias_applied": memory_bias_applied,
                "action_class": action_class,
                "scope": scope,
                "effect_class": effect_class,
                "allowed": allowed,
                "reason": reason,
                "rc_state": rc_state,
                "rc_conflict_score": rc_conflict_score,
                "commit_id": commit_id,
            }
        )

    def finalize_session(
        self,
        *,
        session_id: str,
        stopped_reason: str,
        steps_executed: int,
    ) -> None:
        self._append(
            {
                "event": "session_finished",
                "session_id": session_id,
                "stopped_reason": stopped_reason,
                "steps_executed": steps_executed,
            }
        )

    def trajectory_bias(self, trajectory_reference: str) -> float:
        step_records = [
            entry
            for entry in self.read_all()
            if entry.get("event") == "step_recorded"
            and entry.get("selected_trajectory_reference") == trajectory_reference
        ]
        if not step_records:
            return 0.0
        successes = sum(1 for entry in step_records if bool(entry.get("allowed")))
        failures = len(step_records) - successes
        bias = (successes - failures) / len(step_records)
        return max(min(bias * 0.05, 0.05), -0.05)

    def summarize(self) -> SessionMemorySummary:
        entries = self.read_all()
        sessions = {
            entry["session_id"]
            for entry in entries
            if entry.get("event") in {"session_started", "session_finished"}
            and "session_id" in entry
        }
        step_records = [entry for entry in entries if entry.get("event") == "step_recorded"]
        trajectories = {
            str(entry["selected_trajectory_reference"])
            for entry in step_records
            if "selected_trajectory_reference" in entry
        }
        trajectory_bias = {
            trajectory: self.trajectory_bias(trajectory) for trajectory in sorted(trajectories)
        }
        return SessionMemorySummary(
            total_sessions=len(sessions),
            total_step_records=len(step_records),
            trajectory_bias=trajectory_bias,
        )

    def read_all(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def _append(self, payload: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            **payload,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
