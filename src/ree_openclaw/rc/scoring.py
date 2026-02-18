from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RCConflictSignals:
    provenance_mismatch: float = 0.0
    identity_capability_inconsistency: float = 0.0
    temporal_discontinuity: float = 0.0
    tool_output_inconsistency: float = 0.0

    def validate(self) -> None:
        for field_name, value in (
            ("provenance_mismatch", self.provenance_mismatch),
            ("identity_capability_inconsistency", self.identity_capability_inconsistency),
            ("temporal_discontinuity", self.temporal_discontinuity),
            ("tool_output_inconsistency", self.tool_output_inconsistency),
        ):
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{field_name} must be in [0, 1]")


@dataclass(frozen=True)
class RCConflictWeights:
    provenance_mismatch: float = 0.35
    identity_capability_inconsistency: float = 0.3
    temporal_discontinuity: float = 0.2
    tool_output_inconsistency: float = 0.15

    def validate(self) -> None:
        for field_name, value in (
            ("provenance_mismatch", self.provenance_mismatch),
            ("identity_capability_inconsistency", self.identity_capability_inconsistency),
            ("temporal_discontinuity", self.temporal_discontinuity),
            ("tool_output_inconsistency", self.tool_output_inconsistency),
        ):
            if value < 0.0:
                raise ValueError(f"{field_name} weight cannot be negative")
        if self.total_weight <= 0.0:
            raise ValueError("total RC conflict weight must be positive")

    @property
    def total_weight(self) -> float:
        return (
            self.provenance_mismatch
            + self.identity_capability_inconsistency
            + self.temporal_discontinuity
            + self.tool_output_inconsistency
        )


class RCConflictScorer:
    def __init__(self, weights: RCConflictWeights | None = None) -> None:
        self.weights = weights or RCConflictWeights()
        self.weights.validate()

    def score(self, signals: RCConflictSignals) -> float:
        signals.validate()
        weighted_sum = (
            signals.provenance_mismatch * self.weights.provenance_mismatch
            + signals.identity_capability_inconsistency
            * self.weights.identity_capability_inconsistency
            + signals.temporal_discontinuity * self.weights.temporal_discontinuity
            + signals.tool_output_inconsistency * self.weights.tool_output_inconsistency
        )
        score = weighted_sum / self.weights.total_weight
        return min(max(score, 0.0), 1.0)
