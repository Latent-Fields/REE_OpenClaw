from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ree_openclaw.adapter.routing import TypedBoundaryRouter
from ree_openclaw.types import EffectClass, Envelope


@dataclass(frozen=True)
class RolloutProposal:
    proposal_text: str
    action_class: str
    scope: str
    effect_class: EffectClass
    command: tuple[str, ...]
    trajectory_reference: str
    model_call_id: str = "rollout-model-call"
    prompt_hash: str = "rollout-prompt-hash"
    input_provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class RolloutCandidate:
    envelope: Envelope
    action_class: str
    scope: str
    effect_class: EffectClass
    command: tuple[str, ...]
    trajectory_reference: str


@dataclass(frozen=True)
class RolloutSignals:
    viability: float = 0.5
    valence: float = 0.5

    def validate(self) -> None:
        if self.viability < 0.0 or self.viability > 1.0:
            raise ValueError("viability must be in [0, 1]")
        if self.valence < 0.0 or self.valence > 1.0:
            raise ValueError("valence must be in [0, 1]")


@dataclass(frozen=True)
class RolloutWeights:
    viability: float = 0.6
    valence: float = 0.4

    def validate(self) -> None:
        if self.viability < 0.0 or self.valence < 0.0:
            raise ValueError("rollout weights cannot be negative")
        if self.total <= 0.0:
            raise ValueError("rollout weights total must be positive")

    @property
    def total(self) -> float:
        return self.viability + self.valence


@dataclass(frozen=True)
class RolloutEvaluation:
    candidate: RolloutCandidate
    viability_score: float
    valence_score: float
    ranking_score: float


class RolloutPlanner:
    def __init__(
        self,
        *,
        router: TypedBoundaryRouter | None = None,
        weights: RolloutWeights | None = None,
    ) -> None:
        self.router = router or TypedBoundaryRouter()
        self.weights = weights or RolloutWeights()
        self.weights.validate()

    def build_candidates(
        self,
        proposals: Sequence[RolloutProposal],
    ) -> tuple[RolloutCandidate, ...]:
        candidates: list[RolloutCandidate] = []
        for proposal in proposals:
            envelope = self.router.route_llm_output(
                proposal.proposal_text,
                role="rollout",
                model_call_id=proposal.model_call_id,
                prompt_hash=proposal.prompt_hash,
                input_provenance=proposal.input_provenance,
                proposed_effect_class=proposal.effect_class,
            )
            candidates.append(
                RolloutCandidate(
                    envelope=envelope,
                    action_class=proposal.action_class,
                    scope=proposal.scope,
                    effect_class=proposal.effect_class,
                    command=proposal.command,
                    trajectory_reference=proposal.trajectory_reference,
                )
            )
        return tuple(candidates)

    def rank_candidates(
        self,
        candidates: Sequence[RolloutCandidate],
        *,
        signal_overrides: dict[str, RolloutSignals] | None = None,
    ) -> list[RolloutEvaluation]:
        signal_overrides = signal_overrides or {}
        ranked: list[RolloutEvaluation] = []
        for candidate in candidates:
            signals = signal_overrides.get(candidate.trajectory_reference, RolloutSignals())
            signals.validate()
            ranking_score = (
                signals.viability * self.weights.viability
                + signals.valence * self.weights.valence
            ) / self.weights.total
            ranked.append(
                RolloutEvaluation(
                    candidate=candidate,
                    viability_score=signals.viability,
                    valence_score=signals.valence,
                    ranking_score=ranking_score,
                )
            )
        ranked.sort(key=lambda item: item.ranking_score, reverse=True)
        return ranked
