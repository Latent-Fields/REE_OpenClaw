from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from ree_openclaw.agent.memory import AutonomousSessionMemoryStore, SessionMemorySummary
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
    max_command_count: int | None = None
    max_wall_clock_seconds: float | None = None
    stop_on_reject: bool = True


@dataclass(frozen=True)
class AutonomousStepResult:
    step_index: int
    selected_trajectory_reference: str
    selected_ranking_score: float
    memory_bias_applied: float
    cycle_result: ProposalCycleResult


@dataclass(frozen=True)
class AutonomousSessionResult:
    session_id: str
    goal_text: str
    step_results: tuple[AutonomousStepResult, ...]
    stopped_reason: str
    memory_path: Path
    memory_summary: SessionMemorySummary

    @property
    def steps_executed(self) -> int:
        return len(self.step_results)


class AutonomousSessionRunner:
    def __init__(
        self,
        runtime: OpenClawRuntime,
        *,
        memory_store: AutonomousSessionMemoryStore | None = None,
    ) -> None:
        self.runtime = runtime
        default_memory_path = runtime.ledger.path.parent / "autonomy" / "session_memory.jsonl"
        self.memory = memory_store or AutonomousSessionMemoryStore(default_memory_path)

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
        command_count = 0
        start_time = time.monotonic()
        session_id = self.memory.start_session(
            goal_text=goal_text,
            policy_snapshot={
                "max_steps": active_policy.max_steps,
                "max_command_count": active_policy.max_command_count,
                "max_wall_clock_seconds": active_policy.max_wall_clock_seconds,
                "stop_on_reject": active_policy.stop_on_reject,
            },
        )

        for step_index in range(limit):
            if (
                active_policy.max_wall_clock_seconds is not None
                and time.monotonic() - start_time >= active_policy.max_wall_clock_seconds
            ):
                stopped_reason = "max_wall_clock_reached"
                break
            if (
                active_policy.max_command_count is not None
                and command_count >= active_policy.max_command_count
            ):
                stopped_reason = "max_command_count_reached"
                break

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
            ranked_with_memory = []
            for evaluation in ranked:
                memory_bias = self.memory.trajectory_bias(
                    evaluation.candidate.trajectory_reference
                )
                ranked_with_memory.append(
                    (evaluation.ranking_score + memory_bias, memory_bias, evaluation)
                )
            selected_adjusted_score, memory_bias_applied, selected = max(
                ranked_with_memory,
                key=lambda item: item[0],
            )
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
            command_count += 1
            step_results.append(
                AutonomousStepResult(
                    step_index=step_index,
                    selected_trajectory_reference=selected_plan.trajectory_reference,
                    selected_ranking_score=selected_adjusted_score,
                    memory_bias_applied=memory_bias_applied,
                    cycle_result=cycle,
                )
            )
            self.memory.append_step_record(
                session_id=session_id,
                step_index=step_index,
                user_intent=step.user_intent,
                selected_trajectory_reference=selected_plan.trajectory_reference,
                selected_ranking_score=selected_adjusted_score,
                memory_bias_applied=memory_bias_applied,
                action_class=selected_plan.action_class,
                scope=selected_plan.scope,
                effect_class=selected_plan.effect_class.value,
                allowed=cycle.verification.allowed,
                reason=cycle.verification.reason,
                rc_state=cycle.rc_state.value,
                rc_conflict_score=cycle.rc_conflict_score,
                commit_id=cycle.commit_token.commit_id if cycle.commit_token else None,
            )
            if not cycle.verification.allowed and active_policy.stop_on_reject:
                stopped_reason = "rejected_step"
                break
            if (
                active_policy.max_wall_clock_seconds is not None
                and time.monotonic() - start_time >= active_policy.max_wall_clock_seconds
            ):
                stopped_reason = "max_wall_clock_reached"
                break

        if (
            stopped_reason == "completed"
            and len(step_results) >= active_policy.max_steps
            and len(steps) > active_policy.max_steps
        ):
            stopped_reason = "max_steps_reached"

        self.memory.finalize_session(
            session_id=session_id,
            stopped_reason=stopped_reason,
            steps_executed=len(step_results),
        )
        memory_summary = self.memory.summarize()

        return AutonomousSessionResult(
            session_id=session_id,
            goal_text=goal_text,
            step_results=tuple(step_results),
            stopped_reason=stopped_reason,
            memory_path=self.memory.path,
            memory_summary=memory_summary,
        )

    @staticmethod
    def write_artifact(result: AutonomousSessionResult, output_path: Path) -> Path:
        payload = {
            "session_id": result.session_id,
            "goal_text": result.goal_text,
            "steps_executed": result.steps_executed,
            "stopped_reason": result.stopped_reason,
            "memory_path": str(result.memory_path),
            "memory_summary": {
                "total_sessions": result.memory_summary.total_sessions,
                "total_step_records": result.memory_summary.total_step_records,
                "trajectory_bias": result.memory_summary.trajectory_bias,
            },
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "steps": [
                {
                    "step_index": item.step_index,
                    "selected_trajectory_reference": item.selected_trajectory_reference,
                    "selected_ranking_score": round(item.selected_ranking_score, 4),
                    "memory_bias_applied": round(item.memory_bias_applied, 4),
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
