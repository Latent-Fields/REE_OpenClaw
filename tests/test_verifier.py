from pathlib import Path

from ree_openclaw.rc.hysteresis import RCState
from ree_openclaw.types import EffectClass
from ree_openclaw.verifier.capability_manifest import load_capabilities
from ree_openclaw.verifier.verifier import (
    CapabilityVerifier,
    ConsentToken,
    VerificationRequest,
)


def _load_default_caps() -> dict:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "config" / "capabilities" / "default_manifest.json"
    return load_capabilities(manifest_path)


def _provenance() -> dict[str, object]:
    return {
        "model_call_id": "m1",
        "prompt_hash": "p1",
        "input_provenance": ("u1",),
    }


def _verifier_labels() -> tuple[str, ...]:
    return (
        "scope_verifier",
        "consent_verifier",
        "destructive_action_verifier",
        "provenance_verifier",
    )


def test_privileged_action_requires_consent() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="SEND_EMAIL",
            scope="mailbox:primary",
            effect_class=EffectClass.PRIVILEGED,
            provenance=_provenance(),
            provided_verifiers=_verifier_labels(),
        )
    )
    assert not decision.allowed
    assert decision.requires_consent


def test_consent_allows_scoped_privileged_action() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="SEND_EMAIL",
            scope="mailbox:primary",
            effect_class=EffectClass.PRIVILEGED,
            consent_token=ConsentToken(
                action_class="SEND_EMAIL",
                scope="mailbox:primary",
                nonce="n1",
                issued_at="2026-02-18T00:00:00+00:00",
            ),
            provenance=_provenance(),
            provided_verifiers=_verifier_labels(),
        )
    )
    assert decision.allowed


def test_rc_verify_state_increases_strictness() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="WRITE_FILE",
            scope="workspace:project",
            effect_class=EffectClass.REVERSIBLE,
            rc_state=RCState.VERIFY,
            rc_conflict_score=0.7,
            provenance=_provenance(),
            provided_verifiers=_verifier_labels(),
        )
    )
    assert not decision.allowed
    assert decision.strict_mode
    assert decision.requires_consent


def test_lockdown_blocks_privileged_even_with_valid_consent() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="SEND_EMAIL",
            scope="mailbox:primary",
            effect_class=EffectClass.PRIVILEGED,
            rc_state=RCState.LOCKDOWN,
            rc_conflict_score=0.95,
            consent_token=ConsentToken(
                action_class="SEND_EMAIL",
                scope="mailbox:primary",
                nonce="n1",
                issued_at="2026-02-18T00:00:00+00:00",
            ),
            provenance=_provenance(),
            provided_verifiers=_verifier_labels(),
        )
    )
    assert not decision.allowed
    assert decision.reason == "lockdown_posture_block"
    assert decision.strict_mode


def test_required_verifier_missing_is_blocked() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="SEND_EMAIL",
            scope="mailbox:primary",
            effect_class=EffectClass.PRIVILEGED,
            provenance=_provenance(),
            provided_verifiers=("scope_verifier",),
        )
    )
    assert not decision.allowed
    assert decision.reason == "required_verifier_missing"


def test_provenance_binding_missing_is_blocked() -> None:
    verifier = CapabilityVerifier(_load_default_caps())
    decision = verifier.verify(
        VerificationRequest(
            action_class="WRITE_FILE",
            scope="workspace:project",
            effect_class=EffectClass.REVERSIBLE,
            provenance={
                "model_call_id": "m1",
                "prompt_hash": "p1",
                "input_provenance": (),
            },
            provided_verifiers=_verifier_labels(),
        )
    )
    assert not decision.allowed
    assert decision.reason == "provenance_binding_missing"
