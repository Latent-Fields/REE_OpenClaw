from pathlib import Path

import pytest

from ree_openclaw.agent.autonomy import (
    AutonomousCandidatePlan,
    AutonomousPolicy,
    AutonomousSessionRunner,
    AutonomousStep,
)
from ree_openclaw.runtime.pipeline import OpenClawRuntime
from ree_openclaw.types import EffectClass


def _manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "capabilities" / "default_manifest.json"


def test_autonomy_safe_session_executes_multiple_steps(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    runner = AutonomousSessionRunner(runtime)

    result = runner.run(
        goal_text="Complete two safe autonomous updates.",
        steps=(
            AutonomousStep(
                user_intent="Step one",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate A",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "auto_a"),
                        trajectory_reference="auto/step1/a",
                        viability=0.9,
                        valence=0.8,
                    ),
                    AutonomousCandidatePlan(
                        proposal_text="Candidate B",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "auto_b"),
                        trajectory_reference="auto/step1/b",
                        viability=0.4,
                        valence=0.4,
                    ),
                ),
            ),
            AutonomousStep(
                user_intent="Step two",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate C",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "auto_c"),
                        trajectory_reference="auto/step2/a",
                    ),
                ),
            ),
        ),
        policy=AutonomousPolicy(max_steps=3, stop_on_reject=True),
    )

    assert result.steps_executed == 2
    assert result.stopped_reason == "completed"
    assert result.step_results[0].selected_trajectory_reference == "auto/step1/a"
    assert result.step_results[0].cycle_result.verification.allowed
    assert result.step_results[1].cycle_result.verification.allowed


def test_autonomy_stops_on_rejected_step(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    runner = AutonomousSessionRunner(runtime)

    result = runner.run(
        goal_text="Trigger guarded stop.",
        steps=(
            AutonomousStep(
                user_intent="Safe first step",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Safe write",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "safe"),
                        trajectory_reference="guard/step1",
                    ),
                ),
            ),
            AutonomousStep(
                user_intent="Privileged step without consent",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Send privileged message",
                        action_class="SEND_EMAIL",
                        scope="mailbox:primary",
                        effect_class=EffectClass.PRIVILEGED,
                        command=("echo", "blocked"),
                        trajectory_reference="guard/step2",
                    ),
                ),
            ),
            AutonomousStep(
                user_intent="Should not execute",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Extra step",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "never"),
                        trajectory_reference="guard/step3",
                    ),
                ),
            ),
        ),
        policy=AutonomousPolicy(max_steps=5, stop_on_reject=True),
    )

    assert result.steps_executed == 2
    assert result.stopped_reason == "rejected_step"
    assert result.step_results[1].cycle_result.verification.allowed is False
    assert result.step_results[1].cycle_result.verification.reason == "consent_required"


def test_autonomy_stops_at_max_command_count(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    runner = AutonomousSessionRunner(runtime)

    result = runner.run(
        goal_text="Respect command budget.",
        steps=(
            AutonomousStep(
                user_intent="Step one",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate one",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "budget_one"),
                        trajectory_reference="budget/step1",
                    ),
                ),
            ),
            AutonomousStep(
                user_intent="Step two",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate two",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "budget_two"),
                        trajectory_reference="budget/step2",
                    ),
                ),
            ),
        ),
        policy=AutonomousPolicy(max_steps=5, max_command_count=1, stop_on_reject=True),
    )

    assert result.steps_executed == 1
    assert result.stopped_reason == "max_command_count_reached"
    assert result.step_results[0].cycle_result.verification.allowed


def test_autonomy_stops_at_max_wall_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    runner = AutonomousSessionRunner(runtime)

    ticks = iter((0.0, 0.0, 2.0))

    def _fake_monotonic() -> float:
        return next(ticks)

    monkeypatch.setattr("ree_openclaw.agent.autonomy.time.monotonic", _fake_monotonic)

    result = runner.run(
        goal_text="Respect wall clock budget.",
        steps=(
            AutonomousStep(
                user_intent="Step one",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate one",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "time_one"),
                        trajectory_reference="time/step1",
                    ),
                ),
            ),
            AutonomousStep(
                user_intent="Step two",
                candidates=(
                    AutonomousCandidatePlan(
                        proposal_text="Candidate two",
                        action_class="WRITE_FILE",
                        scope="workspace:project",
                        effect_class=EffectClass.REVERSIBLE,
                        command=("echo", "time_two"),
                        trajectory_reference="time/step2",
                    ),
                ),
            ),
        ),
        policy=AutonomousPolicy(max_steps=5, max_wall_clock_seconds=1.0, stop_on_reject=True),
    )

    assert result.steps_executed == 1
    assert result.stopped_reason == "max_wall_clock_reached"
