from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ree_openclaw.offline.consolidation import OfflineTriggerError
from ree_openclaw.rc.scoring import RCConflictSignals
from ree_openclaw.runtime import OpenClawRuntime, RolloutProposal, RolloutSignals
from ree_openclaw.types import EffectClass
from ree_openclaw.verifier.verifier import ConsentToken


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_manifest() -> Path:
    return _repo_root() / "config" / "capabilities" / "default_manifest.json"


def _runtime_paths(state_dir: Path) -> tuple[Path, Path, Path]:
    return (
        state_dir / "ledger.jsonl",
        state_dir / "sandbox",
        state_dir / "verifier_audit.jsonl",
    )


def _build_runtime(manifest: Path, state_dir: Path) -> OpenClawRuntime:
    ledger_path, sandbox_root, audit_path = _runtime_paths(state_dir)
    return OpenClawRuntime.from_manifest(
        manifest_path=manifest,
        ledger_path=ledger_path,
        sandbox_root=sandbox_root,
        audit_log_path=audit_path,
    )


def _maybe_consent(enabled: bool, action_class: str, scope: str) -> ConsentToken | None:
    if not enabled:
        return None
    return ConsentToken(
        action_class=action_class,
        scope=scope,
        nonce="cli-consent",
        issued_at=datetime.now(tz=timezone.utc).isoformat(),
    )


def _print_result(result: dict[str, object]) -> None:
    print(json.dumps(result, indent=2, sort_keys=True))


def _run_cycle(args: argparse.Namespace) -> int:
    state_dir = args.state_dir.resolve()
    runtime = _build_runtime(args.manifest.resolve(), state_dir)
    effect_class = EffectClass(args.effect_class)
    consent_token = _maybe_consent(args.consent, args.action_class, args.scope)
    rc_signals = RCConflictSignals(
        provenance_mismatch=args.rc_signal_provenance_mismatch,
        identity_capability_inconsistency=args.rc_signal_identity_inconsistency,
        temporal_discontinuity=args.rc_signal_temporal_discontinuity,
        tool_output_inconsistency=args.rc_signal_tool_output_inconsistency,
    )
    cycle = runtime.run_command_cycle(
        user_text=args.user_text,
        proposal_text=args.proposal_text,
        action_class=args.action_class,
        scope=args.scope,
        effect_class=effect_class,
        command=args.command,
        rc_conflict_score=args.rc_score,
        rc_signals=rc_signals,
        llm_role=args.llm_role,
        model_call_id=args.model_call_id,
        prompt_hash=args.prompt_hash,
        input_provenance=tuple(args.input_provenance),
        trajectory_reference=args.trajectory_reference,
        consent_token=consent_token,
    )
    response = {
        "allowed": cycle.verification.allowed,
        "reason": cycle.verification.reason,
        "strict_mode": cycle.verification.strict_mode,
        "rc_conflict_score": cycle.rc_conflict_score,
        "rc_state": cycle.rc_state.value,
        "commit_id": cycle.commit_token.commit_id if cycle.commit_token else None,
        "execution_returncode": (
            cycle.execution_result.returncode if cycle.execution_result else None
        ),
        "execution_stdout": cycle.execution_result.stdout if cycle.execution_result else None,
        "ledger_index": cycle.ledger_entry["index"],
        "ledger_event": cycle.ledger_entry["payload"]["event"],
        "ledger_path": str(runtime.ledger.path),
    }
    _print_result(response)
    return 0 if cycle.verification.allowed else 2


def _run_demo(args: argparse.Namespace) -> int:
    state_dir = args.state_dir.resolve()
    runtime = _build_runtime(args.manifest.resolve(), state_dir)
    cycle = runtime.run_command_cycle(
        user_text="Run the safe demo action.",
        proposal_text="Execute a reversible sandbox-safe demo command.",
        action_class="WRITE_FILE",
        scope="workspace:project",
        effect_class=EffectClass.REVERSIBLE,
        command=("echo", "ree_openclaw_demo_ok"),
        rc_signals=RCConflictSignals(
            provenance_mismatch=0.1,
            identity_capability_inconsistency=0.05,
            temporal_discontinuity=0.0,
            tool_output_inconsistency=0.0,
        ),
        llm_role="rollout",
        model_call_id="demo-model-call",
        prompt_hash="demo-prompt-hash",
        input_provenance=("demo-user-message",),
        trajectory_reference="demo/trajectory/001",
    )
    response = {
        "allowed": cycle.verification.allowed,
        "reason": cycle.verification.reason,
        "rc_conflict_score": cycle.rc_conflict_score,
        "rc_state": cycle.rc_state.value,
        "commit_id": cycle.commit_token.commit_id if cycle.commit_token else None,
        "execution_stdout": cycle.execution_result.stdout if cycle.execution_result else None,
        "ledger_index": cycle.ledger_entry["index"],
        "ledger_event": cycle.ledger_entry["payload"]["event"],
        "ledger_path": str(runtime.ledger.path),
    }
    _print_result(response)
    return 0 if cycle.verification.allowed else 2


def _plan_demo(args: argparse.Namespace) -> int:
    state_dir = args.state_dir.resolve()
    runtime = _build_runtime(args.manifest.resolve(), state_dir)
    ranked = runtime.plan_rollouts(
        (
            RolloutProposal(
                proposal_text="Plan A: write a safe status marker in sandbox.",
                action_class="WRITE_FILE",
                scope="workspace:project",
                effect_class=EffectClass.REVERSIBLE,
                command=("echo", "plan_a"),
                trajectory_reference="demo/plan/a",
                input_provenance=("demo-user-message",),
            ),
            RolloutProposal(
                proposal_text="Plan B: alternative safe status marker.",
                action_class="WRITE_FILE",
                scope="workspace:project",
                effect_class=EffectClass.REVERSIBLE,
                command=("echo", "plan_b"),
                trajectory_reference="demo/plan/b",
                input_provenance=("demo-user-message",),
            ),
        ),
        signal_overrides={
            "demo/plan/a": RolloutSignals(viability=0.85, valence=0.7),
            "demo/plan/b": RolloutSignals(viability=0.6, valence=0.8),
        },
    )
    response = {
        "ranked_rollouts": [
            {
                "trajectory_reference": item.candidate.trajectory_reference,
                "action_class": item.candidate.action_class,
                "scope": item.candidate.scope,
                "viability_score": item.viability_score,
                "valence_score": item.valence_score,
                "ranking_score": round(item.ranking_score, 4),
                "payload_type": item.candidate.envelope.payload_type.value,
            }
            for item in ranked
        ]
    }
    _print_result(response)
    return 0


def _run_offline_consolidate(args: argparse.Namespace) -> int:
    state_dir = args.state_dir.resolve()
    runtime = _build_runtime(args.manifest.resolve(), state_dir)
    try:
        result = runtime.run_offline_consolidation(trigger_source=args.trigger_source)
    except OfflineTriggerError as exc:
        _print_result({"allowed": False, "reason": str(exc)})
        return 2
    response = {
        "output_path": str(result.output_path),
        "processed_entries": result.processed_entries,
        "generated_at": result.generated_at,
    }
    _print_result(response)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="REE_OpenClaw local prototype CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_cycle = subparsers.add_parser(
        "run-cycle",
        help="Run one full proposal -> commit -> execute -> ledger cycle.",
    )
    run_cycle.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest(),
        help="Path to capability manifest JSON.",
    )
    run_cycle.add_argument(
        "--state-dir",
        type=Path,
        default=Path(".ree_openclaw_state"),
        help="Directory for runtime ledger/audit/sandbox state.",
    )
    run_cycle.add_argument("--user-text", default="Execute the requested sandbox action.")
    run_cycle.add_argument(
        "--proposal-text",
        default="Propose one tool execution under verifier gating.",
    )
    run_cycle.add_argument("--action-class", default="WRITE_FILE")
    run_cycle.add_argument("--scope", default="workspace:project")
    run_cycle.add_argument(
        "--effect-class",
        choices=[effect.value for effect in EffectClass],
        default=EffectClass.REVERSIBLE.value,
    )
    run_cycle.add_argument(
        "--rc-score",
        type=float,
        default=None,
        help="Optional direct RC score override (0-1). If omitted, score is computed from RC signals.",
    )
    run_cycle.add_argument("--rc-signal-provenance-mismatch", type=float, default=0.0)
    run_cycle.add_argument("--rc-signal-identity-inconsistency", type=float, default=0.0)
    run_cycle.add_argument("--rc-signal-temporal-discontinuity", type=float, default=0.0)
    run_cycle.add_argument("--rc-signal-tool-output-inconsistency", type=float, default=0.0)
    run_cycle.add_argument("--llm-role", default="rollout")
    run_cycle.add_argument("--model-call-id", default="cli-model-call")
    run_cycle.add_argument("--prompt-hash", default="cli-prompt-hash")
    run_cycle.add_argument(
        "--input-provenance",
        nargs="*",
        default=["cli-user-input"],
    )
    run_cycle.add_argument("--trajectory-reference", default="cli/trajectory/001")
    run_cycle.add_argument(
        "--consent",
        action="store_true",
        help="Attach a matching consent token for action/scope.",
    )
    run_cycle.add_argument(
        "--command",
        nargs="+",
        default=["echo", "ree_openclaw_cycle_ok"],
        help="Sandbox command to execute.",
    )
    run_cycle.set_defaults(handler=_run_cycle)

    run_demo = subparsers.add_parser(
        "run-demo",
        help="Run a safe built-in demo scenario.",
    )
    run_demo.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest(),
        help="Path to capability manifest JSON.",
    )
    run_demo.add_argument(
        "--state-dir",
        type=Path,
        default=Path(".ree_openclaw_state"),
        help="Directory for runtime ledger/audit/sandbox state.",
    )
    run_demo.set_defaults(handler=_run_demo)

    plan_demo = subparsers.add_parser(
        "plan-demo",
        help="Run a rollout-planning demo without committing or executing actions.",
    )
    plan_demo.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest(),
        help="Path to capability manifest JSON.",
    )
    plan_demo.add_argument(
        "--state-dir",
        type=Path,
        default=Path(".ree_openclaw_state"),
        help="Directory for runtime ledger/audit/sandbox state.",
    )
    plan_demo.set_defaults(handler=_plan_demo)

    offline = subparsers.add_parser(
        "offline-consolidate",
        help="Run protected offline consolidation from post-commit ledger traces.",
    )
    offline.add_argument(
        "--manifest",
        type=Path,
        default=_default_manifest(),
        help="Path to capability manifest JSON.",
    )
    offline.add_argument(
        "--state-dir",
        type=Path,
        default=Path(".ree_openclaw_state"),
        help="Directory for runtime ledger/audit/sandbox state.",
    )
    offline.add_argument(
        "--trigger-source",
        default="operator_cli",
        help="Offline trigger source label (allowed: operator_cli, scheduler).",
    )
    offline.set_defaults(handler=_run_offline_consolidate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
