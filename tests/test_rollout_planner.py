from pathlib import Path

from ree_openclaw.runtime.pipeline import OpenClawRuntime
from ree_openclaw.rollout.planner import RolloutProposal, RolloutSignals
from ree_openclaw.types import EffectClass, PayloadType


def _manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "capabilities" / "default_manifest.json"


def test_rollout_planner_ranks_candidates_with_viability_valence_overlay(
    tmp_path: Path,
) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    proposals = (
        RolloutProposal(
            proposal_text="Plan A: safe write to project workspace.",
            action_class="WRITE_FILE",
            scope="workspace:project",
            effect_class=EffectClass.REVERSIBLE,
            command=("echo", "plan_a"),
            trajectory_reference="traj/a",
            input_provenance=("user-msg",),
        ),
        RolloutProposal(
            proposal_text="Plan B: alternate write path.",
            action_class="WRITE_FILE",
            scope="workspace:project",
            effect_class=EffectClass.REVERSIBLE,
            command=("echo", "plan_b"),
            trajectory_reference="traj/b",
            input_provenance=("user-msg",),
        ),
    )

    ranked = runtime.plan_rollouts(
        proposals,
        signal_overrides={
            "traj/a": RolloutSignals(viability=0.9, valence=0.7),
            "traj/b": RolloutSignals(viability=0.4, valence=0.9),
        },
    )

    assert len(ranked) == 2
    assert ranked[0].candidate.trajectory_reference == "traj/a"
    assert ranked[0].candidate.envelope.payload_type == PayloadType.TRAJ
    assert ranked[1].candidate.envelope.payload_type == PayloadType.TRAJ


def test_rollout_planning_does_not_write_ledger(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )

    runtime.plan_rollouts(
        (
            RolloutProposal(
                proposal_text="Plan only, no execute.",
                action_class="WRITE_FILE",
                scope="workspace:project",
                effect_class=EffectClass.REVERSIBLE,
                command=("echo", "no_execute"),
                trajectory_reference="traj/only",
                input_provenance=("user-msg",),
            ),
        )
    )

    assert runtime.ledger.read_all() == []
