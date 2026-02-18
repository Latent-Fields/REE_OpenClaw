# Contract: Proposal -> Commit -> Execute -> Ledger Cycle

Doc: `docs/contracts/proposal_commit_execution_cycle.md`  
Date: 2026-02-18  
Status: Active (v0 prototype)

## Purpose

Define the required runtime order for action release in `REE_OpenClaw`.

## Ordered Stages

1. Typed boundary routing
- User text enters as `WORLD:INS` or `WORLD:OBS`.
- LLM proposal output enters as untrusted `INS` or `TRAJ`.
- No user/LLM direct writes to `POL`/`ID`/`CAPS`.

2. RC hysteresis update
- Runtime computes `rc_conflict_score` from structured RC signals (or accepts explicit override) in `[0,1]`.
- RC lane updates posture (`NORMAL`, `VERIFY`, `LOCKDOWN`) before verification.

3. Verifier decision
- Verifier checks capability manifest action/effect/scope agreement.
- Verifier checks `required_verifiers` coverage and `provenance_bindings`.
- Consent is required per capability and strict posture rules.
- `LOCKDOWN` blocks privileged/destructive actions.

4. Commit token minting
- If and only if verifier allows action release, runtime mints `commit_id`.
- Commit token snapshots include verifier state and RC state.

5. Sandboxed action execution
- Actions execute only through sandbox harness command allowlist.
- Runtime never executes action directly outside sandbox harness path.

6. Append-only ledger write
- Allowed execution writes `commit_executed` with `commit_id` and outcome.
- Denied action writes `proposal_rejected` with denial reason.
- Ledger remains hash-chained and append-only.

## Invariants

- Rejections do not mint commit tokens.
- No privileged/destructive release in `LOCKDOWN`.
- Every released action has a corresponding commit token and ledger trace.
