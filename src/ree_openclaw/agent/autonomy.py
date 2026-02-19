from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ree_openclaw.rc.scoring import RCConflictSignals
from ree_openclaw.rollout.planner import RolloutProposal, RolloutSignals
from ree_openclaw.runtime.pipeline import OpenClawRuntime, ProposalCycleResult
from ree_openclaw.types import EffectClass


@dataclass(frozen=True)
class AutonomousCandidatePlan:
    proposal_text: str
    action_class: str
    scope: str
    effect_class: EffectClass
    command: tuple[str, ...]
    trajectory_reference: str
    viability: float = 0.5
    valence: float = 0.5
    rc_signals: RCConflictSignals = field(default_factory=RCConflictSignals)


@dataclass(frozen=True)
class AutonomousStep:
    user_intent: str
    candidates: tuple[AutonomousCandidatePlan, ...]


@dataclass(frozen=True)
class AutonomousPolicy:
    max_steps: int = 5
    stop_on_reject: bool = True


@dataclass(frozen=True)
class AutonomousStepResult:
    step_index: int
    selected_trajectory_reference: str
    selected_ranking_score: float
    cycle_result: ProposalCycleResult


@dataclass(frozen=True)
class AutonomousSessionResult:
    goal_text: str
    step_results: tuple[AutonomousStepResult, ...]
    stopped_reason: str

    @property
    def steps_executed(self) -> int:
        return len(self.step_results)


class AutonomousSessionRunner:
    def __init__(self, runtime: OpenClawRuntime) -> None:
        self.runtime = runtime

    def run(
        self,
        *,
        goal_text: str,
        steps: tuple[AutonomousStep, ...],
        policy: AutonomousPolicy | None = None,
    ) -> AutonomousSessionResult:
        active_policy = policy or AutonomousPolicy()
        step_results: list[AutonomousStepResult] = []
        stopped_reason = "completed"
        limit = min(active_policy.max_steps, len(steps))

        for step_index in range(limit):
            step = steps[step_index]
            if not step.candidates:
                stopped_reason = "no_candidates"
                break

            ranked = self.runtime.plan_rollouts(
                tuple(
                    RolloutProposal(
                        proposal_text=item.proposal_text,
                        action_class=item.action_class,
                        scope=item.scope,
                        effect_class=item.effect_class,
                        command=item.command,
                        trajectory_reference=item.trajectory_reference,
                        input_provenance=(f"autonomy-step-{step_index}",),
                    )
                    for item in step.candidates
                ),
                signal_overrides={
                    item.trajectory_reference: RolloutSignals(
                        viability=item.viability,
                        valence=item.valence,
                    )
                    for item in step.candidates
                },
            )
            selected = ranked[0]
            selected_plan = next(
                item
                for item in step.candidates
                if item.trajectory_reference == selected.candidate.trajectory_reference
            )

            cycle = self.runtime.run_command_cycle(
                user_text=step.user_intent,
                proposal_text=selected_plan.proposal_text,
                action_class=selected_plan.action_class,
                scope=selected_plan.scope,
                effect_class=selected_plan.effect_class,
                command=selected_plan.command,
                rc_signals=selected_plan.rc_signals,
                input_provenance=(f"autonomy-step-{step_index}",),
                trajectory_reference=selected_plan.trajectory_reference,
            )
            step_results.append(
                AutonomousStepResult(
                    step_index=step_index,
                    selected_trajectory_reference=selected_plan.trajectory_reference,
                    selected_ranking_score=selected.ranking_score,
                    cycle_result=cycle,
                )
            )
            if not cycle.verification.allowed and active_policy.stop_on_reject:
                stopped_reason = "rejected_step"
                break

        if len(step_results) >= active_policy.max_steps and len(steps) > active_policy.max_steps:
            stopped_reason = "max_steps_reached"

        return AutonomousSessionResult(
            goal_text=goal_text,
            step_results=tuple(step_results),
            stopped_reason=stopped_reason,
        )

    @staticmethod
    def write_artifact(result: AutonomousSessionResult, output_path: Path) -> Path:
        payload = {
            "goal_text": result.goal_text,
            "steps_executed": result.steps_executed,
            "stopped_reason": result.stopped_reason,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "steps": [
                {
                    "step_index": item.step_index,
                    "selected_trajectory_reference": item.selected_trajectory_reference,
                    "selected_ranking_score": round(item.selected_ranking_score, 4),
                    "allowed": item.cycle_result.verification.allowed,
                    "reason": item.cycle_result.verification.reason,
                    "rc_state": item.cycle_result.rc_state.value,
                    "rc_conflict_score": item.cycle_result.rc_conflict_score,
                    "commit_id": (
                        item.cycle_result.commit_token.commit_id
                        if item.cycle_result.commit_token is not None
                        else None
                    ),
                }
                for item in result.step_results
            ],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return output_path
