from __future__ import annotations

from dataclasses import dataclass

from ree_openclaw.types import (
    EffectClass,
    Envelope,
    PayloadType,
    Provenance,
    TRUSTED_STORE_TYPES,
)


class TypedBoundaryError(ValueError):
    """Raised when an untrusted source tries to write a trusted store."""


@dataclass(frozen=True)
class LLMRoleMapping:
    role: str
    payload_type: PayloadType


_ROLE_TO_PAYLOAD = {
    "interpretation": PayloadType.OBS,
    "rollout": PayloadType.TRAJ,
    "execution_suggestion": PayloadType.INS,
    "policy_draft": PayloadType.INS,
}


class TypedBoundaryRouter:
    def __init__(self, trusted_sources: set[str] | None = None) -> None:
        self._trusted_sources = trusted_sources or {"trusted_internal"}

    def assert_may_write(self, source_class: str, payload_type: PayloadType) -> None:
        if source_class in self._trusted_sources:
            return
        if payload_type in TRUSTED_STORE_TYPES:
            raise TypedBoundaryError(
                f"source_class={source_class!r} cannot write trusted type={payload_type.value!r}"
            )

    def route_user_message(
        self,
        text: str,
        *,
        as_observation: bool = False,
        source_id: str = "user",
    ) -> Envelope:
        payload_type = PayloadType.OBS if as_observation else PayloadType.INS
        self.assert_may_write("USER", payload_type)
        return Envelope(
            payload_type=payload_type,
            payload={"text": text},
            provenance=Provenance(source_class="USER", source_id=source_id),
        )

    def route_llm_output(
        self,
        content: str,
        *,
        role: str,
        model_call_id: str,
        prompt_hash: str,
        input_provenance: tuple[str, ...],
        proposed_effect_class: EffectClass = EffectClass.NONE,
    ) -> Envelope:
        payload_type = _ROLE_TO_PAYLOAD.get(role)
        if payload_type is None:
            raise ValueError(f"unknown llm role: {role}")

        self.assert_may_write("MODEL_INTERNAL", payload_type)
        return Envelope(
            payload_type=payload_type,
            payload={"content": content, "role": role},
            provenance=Provenance(
                source_class="MODEL_INTERNAL",
                source_id="llm",
                model_call_id=model_call_id,
                prompt_hash=prompt_hash,
                input_provenance=input_provenance,
            ),
            effect_class=proposed_effect_class,
        )

