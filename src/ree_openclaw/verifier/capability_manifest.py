from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ree_openclaw.types import EffectClass


@dataclass(frozen=True)
class Capability:
    action_class: str
    effect_class: EffectClass
    requires_consent: bool
    allowed_scopes: tuple[str, ...]
    required_verifiers: tuple[str, ...]
    provenance_bindings: tuple[str, ...]


def load_capabilities(path: Path) -> dict[str, Capability]:
    data = json.loads(path.read_text(encoding="utf-8"))
    capabilities: dict[str, Capability] = {}
    for item in data.get("capabilities", []):
        capability = Capability(
            action_class=item["action_class"],
            effect_class=EffectClass(item["effect_class"]),
            requires_consent=bool(item["requires_consent"]),
            allowed_scopes=tuple(item.get("allowed_scopes", [])),
            required_verifiers=tuple(item.get("required_verifiers", [])),
            provenance_bindings=tuple(item.get("provenance_bindings", [])),
        )
        capabilities[capability.action_class] = capability
    return capabilities

