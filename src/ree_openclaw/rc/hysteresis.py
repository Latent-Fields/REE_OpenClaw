from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RCState(str, Enum):
    NORMAL = "NORMAL"
    VERIFY = "VERIFY"
    LOCKDOWN = "LOCKDOWN"


@dataclass(frozen=True)
class RCHysteresisConfig:
    t_low: float = 0.35
    t_high: float = 0.65
    t_lock: float = 0.9

    def validate(self) -> None:
        if not (0.0 <= self.t_low < self.t_high < self.t_lock <= 1.0):
            raise ValueError("thresholds must satisfy 0 <= t_low < t_high < t_lock <= 1")


class RCHysteresis:
    def __init__(self, config: RCHysteresisConfig | None = None) -> None:
        self.config = config or RCHysteresisConfig()
        self.config.validate()
        self.state = RCState.NORMAL

    def update(self, score: float) -> RCState:
        if score < 0.0 or score > 1.0:
            raise ValueError("score must be in [0, 1]")

        if score >= self.config.t_lock:
            self.state = RCState.LOCKDOWN
            return self.state

        if self.state == RCState.NORMAL and score >= self.config.t_high:
            self.state = RCState.VERIFY
            return self.state

        if self.state in {RCState.VERIFY, RCState.LOCKDOWN} and score <= self.config.t_low:
            self.state = RCState.NORMAL
            return self.state

        if self.state == RCState.LOCKDOWN and self.config.t_low < score < self.config.t_lock:
            self.state = RCState.VERIFY
            return self.state

        return self.state

