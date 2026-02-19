from pathlib import Path

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
