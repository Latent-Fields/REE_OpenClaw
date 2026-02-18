from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class CommitToken:
    action_class: str
    trajectory_reference: str
    verifier_state: str
    rc_state: str
    precision_snapshot: dict[str, float]
    commit_id: str = field(default_factory=lambda: str(uuid4()))
    issued_at: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


def mint_commit_token(
    *,
    action_class: str,
    trajectory_reference: str,
    verifier_state: str,
    rc_state: str,
    precision_snapshot: dict[str, float],
) -> CommitToken:
    return CommitToken(
        action_class=action_class,
        trajectory_reference=trajectory_reference,
        verifier_state=verifier_state,
        rc_state=rc_state,
        precision_snapshot=precision_snapshot,
    )

