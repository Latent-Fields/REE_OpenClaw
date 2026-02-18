from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ree_openclaw.rc.hysteresis import RCState
from ree_openclaw.types import EffectClass
from ree_openclaw.verifier.capability_manifest import Capability


@dataclass(frozen=True)
class ConsentToken:
    action_class: str
    scope: str
    nonce: str
    issued_at: str
    expires_at: str | None = None

    def is_valid_for(self, action_class: str, scope: str) -> bool:
        if self.action_class != action_class:
            return False
        if self.scope != scope:
            return False
        if self.expires_at is None:
            return True
        expires = datetime.fromisoformat(self.expires_at)
        return expires > datetime.now(tz=timezone.utc)


@dataclass(frozen=True)
class VerificationRequest:
    action_class: str
    scope: str
    effect_class: EffectClass
    rc_state: RCState = RCState.NORMAL
    rc_conflict_score: float = 0.0
    consent_token: ConsentToken | None = None


@dataclass(frozen=True)
class VerificationDecision:
    allowed: bool
    reason: str
    requires_consent: bool
    strict_mode: bool


class CapabilityVerifier:
    def __init__(
        self,
        capabilities: dict[str, Capability],
        *,
        rc_high_threshold: float = 0.65,
        audit_log_path: Path | None = None,
    ) -> None:
        self.capabilities = capabilities
        self.rc_high_threshold = rc_high_threshold
        self.audit_log_path = audit_log_path

    def verify(self, request: VerificationRequest) -> VerificationDecision:
        capability = self.capabilities.get(request.action_class)
        if capability is None:
            decision = VerificationDecision(
                allowed=False,
                reason="unknown_action_class",
                requires_consent=False,
                strict_mode=False,
            )
            self._audit(request, decision)
            return decision

        if capability.effect_class != request.effect_class:
            decision = VerificationDecision(
                allowed=False,
                reason="effect_class_mismatch",
                requires_consent=False,
                strict_mode=False,
            )
            self._audit(request, decision)
            return decision

        if request.scope not in capability.allowed_scopes:
            decision = VerificationDecision(
                allowed=False,
                reason="scope_not_allowed",
                requires_consent=False,
                strict_mode=False,
            )
            self._audit(request, decision)
            return decision

        strict_mode = (
            request.rc_conflict_score >= self.rc_high_threshold
            or request.rc_state in {RCState.VERIFY, RCState.LOCKDOWN}
        )
        requires_consent = capability.requires_consent or (
            strict_mode and request.effect_class != EffectClass.NONE
        )

        if request.rc_state == RCState.LOCKDOWN and request.effect_class in {
            EffectClass.PRIVILEGED,
            EffectClass.DESTRUCTIVE,
        }:
            decision = VerificationDecision(
                allowed=False,
                reason="lockdown_posture_block",
                requires_consent=requires_consent,
                strict_mode=True,
            )
            self._audit(request, decision)
            return decision

        if requires_consent:
            token = request.consent_token
            if token is None or not token.is_valid_for(request.action_class, request.scope):
                decision = VerificationDecision(
                    allowed=False,
                    reason="consent_required",
                    requires_consent=True,
                    strict_mode=strict_mode,
                )
                self._audit(request, decision)
                return decision

        if strict_mode and request.effect_class == EffectClass.DESTRUCTIVE:
            decision = VerificationDecision(
                allowed=False,
                reason="destructive_blocked_in_strict_mode",
                requires_consent=requires_consent,
                strict_mode=True,
            )
            self._audit(request, decision)
            return decision

        decision = VerificationDecision(
            allowed=True,
            reason="allowed",
            requires_consent=requires_consent,
            strict_mode=strict_mode,
        )
        self._audit(request, decision)
        return decision

    def _audit(self, request: VerificationRequest, decision: VerificationDecision) -> None:
        if self.audit_log_path is None:
            return
        record = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "request": {
                "action_class": request.action_class,
                "scope": request.scope,
                "effect_class": request.effect_class.value,
                "rc_state": request.rc_state.value,
                "rc_conflict_score": request.rc_conflict_score,
            },
            "decision": asdict(decision),
        }
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
