from pathlib import Path

from ree_openclaw.runtime.pipeline import OpenClawRuntime
from ree_openclaw.types import EffectClass
from ree_openclaw.verifier.verifier import ConsentToken


def _manifest_path() -> Path:
    return Path(__file__).resolve().parents[1] / "config" / "capabilities" / "default_manifest.json"


def test_happy_path_commit_execute_ledger(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
        audit_log_path=tmp_path / "audit.jsonl",
    )

    result = runtime.run_command_cycle(
        user_text="Please run a safe action.",
        proposal_text="Run a reversible tool action in sandbox.",
        action_class="WRITE_FILE",
        scope="workspace:project",
        effect_class=EffectClass.REVERSIBLE,
        command=("echo", "runtime_cycle_ok"),
        rc_conflict_score=0.2,
        input_provenance=("test-user-message",),
    )

    assert result.verification.allowed
    assert result.commit_token is not None
    assert result.execution_result is not None
    assert result.execution_result.returncode == 0
    assert "runtime_cycle_ok" in result.execution_result.stdout
    assert result.ledger_entry["payload"]["event"] == "commit_executed"
    assert result.ledger_entry["payload"]["commit_id"] == result.commit_token.commit_id
    assert runtime.ledger.verify_chain()


def test_privileged_action_blocked_without_consent(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )

    result = runtime.run_command_cycle(
        user_text="Send the email.",
        proposal_text="Use tool to send privileged email action.",
        action_class="SEND_EMAIL",
        scope="mailbox:primary",
        effect_class=EffectClass.PRIVILEGED,
        command=("echo", "should_not_run"),
        rc_conflict_score=0.1,
        input_provenance=("test-user-message",),
    )

    assert not result.verification.allowed
    assert result.verification.reason == "consent_required"
    assert result.commit_token is None
    assert result.execution_result is None
    assert result.ledger_entry["payload"]["event"] == "proposal_rejected"
    assert result.ledger_entry["payload"]["reason"] == "consent_required"


def test_lockdown_blocks_privileged_even_with_consent(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )
    consent = ConsentToken(
        action_class="SEND_EMAIL",
        scope="mailbox:primary",
        nonce="test-consent",
        issued_at="2026-02-18T00:00:00+00:00",
    )

    result = runtime.run_command_cycle(
        user_text="Send this email.",
        proposal_text="Execute privileged action with consent.",
        action_class="SEND_EMAIL",
        scope="mailbox:primary",
        effect_class=EffectClass.PRIVILEGED,
        command=("echo", "should_not_run"),
        rc_conflict_score=0.95,
        input_provenance=("test-user-message",),
        consent_token=consent,
    )

    assert not result.verification.allowed
    assert result.verification.reason == "lockdown_posture_block"
    assert result.rc_state.value == "LOCKDOWN"
    assert result.commit_token is None
    assert result.execution_result is None
    assert result.ledger_entry["payload"]["event"] == "proposal_rejected"


def test_runtime_rejects_when_provenance_binding_missing(tmp_path: Path) -> None:
    runtime = OpenClawRuntime.from_manifest(
        manifest_path=_manifest_path(),
        ledger_path=tmp_path / "ledger.jsonl",
        sandbox_root=tmp_path / "sandbox",
    )

    result = runtime.run_command_cycle(
        user_text="Run safe action.",
        proposal_text="Run write file action.",
        action_class="WRITE_FILE",
        scope="workspace:project",
        effect_class=EffectClass.REVERSIBLE,
        command=("echo", "should_not_run"),
        rc_conflict_score=0.2,
    )

    assert not result.verification.allowed
    assert result.verification.reason == "provenance_binding_missing"
    assert result.commit_token is None
    assert result.execution_result is None
