from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from ree_openclaw.adapter.routing import TypedBoundaryRouter
from ree_openclaw.commit.token import CommitToken, mint_commit_token
from ree_openclaw.ledger.append_only import AppendOnlyLedger
from ree_openclaw.rc.hysteresis import RCHysteresis, RCHysteresisConfig, RCState
from ree_openclaw.sandbox.harness import SandboxPolicy, SandboxResult, SandboxedExecutor
from ree_openclaw.types import EffectClass, Envelope
from ree_openclaw.verifier.capability_manifest import load_capabilities
from ree_openclaw.verifier.verifier import (
    CapabilityVerifier,
    ConsentToken,
    VerificationDecision,
    VerificationRequest,
)


@dataclass(frozen=True)
class ProposalCycleInput:
    user_text: str
    proposal_text: str
    action_class: str
    scope: str
    effect_class: EffectClass
    command: tuple[str, ...]
    rc_conflict_score: float = 0.0
    llm_role: str = "rollout"
    model_call_id: str = "local-model-call"
    prompt_hash: str = "local-prompt-hash"
    input_provenance: tuple[str, ...] = ()
    trajectory_reference: str = "local-trajectory"
    consent_token: ConsentToken | None = None


@dataclass(frozen=True)
class ProposalCycleResult:
    user_envelope: Envelope
    proposal_envelope: Envelope
    rc_state: RCState
    verification: VerificationDecision
    commit_token: CommitToken | None
    execution_result: SandboxResult | None
    ledger_entry: dict[str, Any]


class OpenClawRuntime:
    def __init__(
        self,
        *,
        capabilities: dict[str, Any],
        ledger_path: Path,
        sandbox_root: Path,
        rc_config: RCHysteresisConfig | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        audit_log_path: Path | None = None,
    ) -> None:
        self.router = TypedBoundaryRouter()
        self.rc_lane = RCHysteresis(rc_config)
        self.verifier = CapabilityVerifier(capabilities, audit_log_path=audit_log_path)
        self.ledger = AppendOnlyLedger(ledger_path)
        self.executor = SandboxedExecutor(sandbox_root, policy=sandbox_policy)

    @classmethod
    def from_manifest(
        cls,
        *,
        manifest_path: Path,
        ledger_path: Path,
        sandbox_root: Path,
        rc_config: RCHysteresisConfig | None = None,
        sandbox_policy: SandboxPolicy | None = None,
        audit_log_path: Path | None = None,
    ) -> OpenClawRuntime:
        capabilities = load_capabilities(manifest_path)
        return cls(
            capabilities=capabilities,
            ledger_path=ledger_path,
            sandbox_root=sandbox_root,
            rc_config=rc_config,
            sandbox_policy=sandbox_policy,
            audit_log_path=audit_log_path,
        )

    def run_cycle(self, proposal: ProposalCycleInput) -> ProposalCycleResult:
        if not proposal.command:
            raise ValueError("command cannot be empty")

        user_envelope = self.router.route_user_message(proposal.user_text)
        proposal_envelope = self.router.route_llm_output(
            proposal.proposal_text,
            role=proposal.llm_role,
            model_call_id=proposal.model_call_id,
            prompt_hash=proposal.prompt_hash,
            input_provenance=proposal.input_provenance,
            proposed_effect_class=proposal.effect_class,
        )

        rc_state = self.rc_lane.update(proposal.rc_conflict_score)
        verification = self.verifier.verify(
            VerificationRequest(
                action_class=proposal.action_class,
                scope=proposal.scope,
                effect_class=proposal.effect_class,
                rc_state=rc_state,
                rc_conflict_score=proposal.rc_conflict_score,
                consent_token=proposal.consent_token,
            )
        )

        if not verification.allowed:
            ledger_entry = self.ledger.append(
                {
                    "event": "proposal_rejected",
                    "action_class": proposal.action_class,
                    "scope": proposal.scope,
                    "effect_class": proposal.effect_class.value,
                    "rc_state": rc_state.value,
                    "reason": verification.reason,
                    "proposal_type": proposal_envelope.payload_type.value,
                }
            )
            return ProposalCycleResult(
                user_envelope=user_envelope,
                proposal_envelope=proposal_envelope,
                rc_state=rc_state,
                verification=verification,
                commit_token=None,
                execution_result=None,
                ledger_entry=ledger_entry,
            )

        verifier_state = "strict" if verification.strict_mode else "baseline"
        commit_token = mint_commit_token(
            action_class=proposal.action_class,
            trajectory_reference=proposal.trajectory_reference,
            verifier_state=verifier_state,
            rc_state=rc_state.value,
            precision_snapshot={"rc_conflict_score": proposal.rc_conflict_score},
        )
        execution_result = self.executor.run(proposal.command)
        ledger_entry = self.ledger.append(
            {
                "event": "commit_executed",
                "commit_id": commit_token.commit_id,
                "action_class": proposal.action_class,
                "scope": proposal.scope,
                "effect_class": proposal.effect_class.value,
                "rc_state": rc_state.value,
                "verifier_state": verifier_state,
                "command": list(proposal.command),
                "execution": {
                    "returncode": execution_result.returncode,
                    "stdout": execution_result.stdout,
                    "stderr": execution_result.stderr,
                },
            }
        )
        return ProposalCycleResult(
            user_envelope=user_envelope,
            proposal_envelope=proposal_envelope,
            rc_state=rc_state,
            verification=verification,
            commit_token=commit_token,
            execution_result=execution_result,
            ledger_entry=ledger_entry,
        )

    def run_command_cycle(
        self,
        *,
        user_text: str,
        proposal_text: str,
        action_class: str,
        scope: str,
        effect_class: EffectClass,
        command: Sequence[str],
        rc_conflict_score: float = 0.0,
        llm_role: str = "rollout",
        model_call_id: str = "local-model-call",
        prompt_hash: str = "local-prompt-hash",
        input_provenance: tuple[str, ...] = (),
        trajectory_reference: str = "local-trajectory",
        consent_token: ConsentToken | None = None,
    ) -> ProposalCycleResult:
        return self.run_cycle(
            ProposalCycleInput(
                user_text=user_text,
                proposal_text=proposal_text,
                action_class=action_class,
                scope=scope,
                effect_class=effect_class,
                command=tuple(command),
                rc_conflict_score=rc_conflict_score,
                llm_role=llm_role,
                model_call_id=model_call_id,
                prompt_hash=prompt_hash,
                input_provenance=input_provenance,
                trajectory_reference=trajectory_reference,
                consent_token=consent_token,
            )
        )
