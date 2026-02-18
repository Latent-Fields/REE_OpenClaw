from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PayloadType(str, Enum):
    OBS = "OBS"
    INS = "INS"
    TRAJ = "TRAJ"
    POL = "POL"
    ID = "ID"
    CAPS = "CAPS"


class EffectClass(str, Enum):
    NONE = "none"
    REVERSIBLE = "reversible"
    PRIVILEGED = "privileged"
    DESTRUCTIVE = "destructive"


TRUSTED_STORE_TYPES = {PayloadType.POL, PayloadType.ID, PayloadType.CAPS}


@dataclass(frozen=True)
class Provenance:
    source_class: str
    source_id: str
    model_call_id: str | None = None
    prompt_hash: str | None = None
    input_provenance: tuple[str, ...] = field(default_factory=tuple)
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )


@dataclass(frozen=True)
class Envelope:
    payload_type: PayloadType
    payload: dict[str, Any]
    provenance: Provenance
    effect_class: EffectClass = EffectClass.NONE

