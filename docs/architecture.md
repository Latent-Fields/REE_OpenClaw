# REE_OpenClaw Architecture (v0)

Date: 2026-02-18  
Status: Active prototype

## Intent

REE_OpenClaw upgrades an OpenClaw-class shell with explicit authority typing, layered commitment eligibility, and post-commit responsibility flow.

## Core Subsystems

1. Adapter Boundary (`src/ree_openclaw/adapter`)
- Intercepts user input, model outputs, and tool requests.
- Enforces typed boundary: external channels are `OBS`/`INS`/`TRAJ`.
- Blocks direct writes to trusted stores (`POL`/`ID`/`CAPS`).

2. Verifier (`src/ree_openclaw/verifier`)
- Loads and validates capability manifests.
- Enforces required verifier labels, provenance bindings, consent, and scope rules.
- Produces auditable verification decisions.

3. RC Conflict Lane (`src/ree_openclaw/rc`)
- Computes RC score via weighted structured signals, then applies hysteresis transitions (`NORMAL` -> `VERIFY` -> `LOCKDOWN`).
- Modulates verifier strictness and gate posture.

4. Commitment (`src/ree_openclaw/commit`)
- Mints explicit commit tokens with traceable provenance.
- Captures verifier and RC state snapshots at commit time.

5. Post-Commit Ledger (`src/ree_openclaw/ledger`)
- Append-only JSONL ledger for irreversible outcomes and accountability.
- Hash-chain linkage to detect tampering.

6. Sandboxed Runtime (`src/ree_openclaw/sandbox` + `sandbox/`)
- Constrained local executor and containerized test harness.
- Designed to stress irreversible action controls without touching host state.

7. Runtime Orchestrator (`src/ree_openclaw/runtime`)
- Runs one integrated cycle: typed boundary -> RC update -> verifier -> commit mint -> sandbox execute -> ledger append.
- Produces explicit rejection ledger entries when verifier denies action release.
- Exposed via local CLI (`src/ree_openclaw/cli.py`) for practical prototype execution on macOS.

## Milestone Map

1. M0 Integration Skeleton
- Boundary router implemented.
- Trusted store write restrictions implemented at typed-boundary layer.

2. M1 Verifier + Manifests
- Capability manifest schema and loader implemented.
- Verifier checks and audit logging implemented.
- `required_verifiers` and `provenance_bindings` are enforced at verification time.
- `LOCKDOWN` posture blocks privileged/destructive action release.

3. M2 Commit Token + Ledger
- Commit token model implemented.
- Append-only ledger and chain verification implemented.
- Runtime integration stamps commit tokens before execution and records post-commit outcomes.

4. M3 RC Conflict Hysteresis
- State transitions with high/low/lock thresholds implemented.
- Weighted RC signal scoring implemented.
- Runtime computes RC score and updates posture before verifier decision.

5. M4 Rollout Interface
- `TRAJ` typing and pre-commit separation are partially implemented.
- Dedicated rollout planner/scoring interface remains pending.

6. M5 Offline Consolidation
- Documented only; offline consolidation runtime is not implemented yet.

## Detailed Gap Tracking

- `docs/milestones_m0_m5_audit.md` is the source of exact M0-M5 gaps and implementation status.
