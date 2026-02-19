# REE_OpenClaw Architecture (v0)

Date: 2026-02-18  
Status: Active prototype

## Intent

REE_OpenClaw upgrades an OpenClaw-class shell with explicit authority typing, layered commitment eligibility, and post-commit responsibility flow.

## Distinctive Functionality

REE_OpenClaw is designed to be contributor-friendly for autonomy work because it already provides:

1. Typed authority boundaries between untrusted and trusted channels.
2. Manifest-backed verifier policy (scope, provenance, consent, posture).
3. RC conflict lane with explicit posture transitions.
4. Explicit commitment and append-only accountability traces.
5. Guarded autonomy sessions with bounded stop conditions.

## Core Subsystems

1. Adapter Boundary (`src/ree_openclaw/adapter`)
- Intercepts user input, model outputs, and tool requests.
- Enforces typed boundary: external channels are `OBS`/`INS`/`TRAJ`.
- Blocks direct writes to trusted stores (`POL`/`ID`/`CAPS`).

2. Trusted Stores (`src/ree_openclaw/stores`)
- Provides dedicated trusted `POL`/`ID`/`CAPS` store interfaces.
- Enforces trusted-source write requirements on store mutation.

3. Verifier (`src/ree_openclaw/verifier`)
- Loads and validates capability manifests.
- Enforces required verifier labels, provenance bindings, consent, and scope rules.
- Produces auditable verification decisions.

4. RC Conflict Lane (`src/ree_openclaw/rc`)
- Computes RC score via weighted structured signals, then applies hysteresis transitions (`NORMAL` -> `VERIFY` -> `LOCKDOWN`).
- Modulates verifier strictness and gate posture.

5. Commitment (`src/ree_openclaw/commit`)
- Mints explicit commit tokens with traceable provenance.
- Captures verifier and RC state snapshots at commit time.

6. Post-Commit Ledger (`src/ree_openclaw/ledger`)
- Append-only JSONL ledger for irreversible outcomes and accountability.
- Hash-chain linkage to detect tampering.

7. Sandboxed Runtime (`src/ree_openclaw/sandbox` + `sandbox/`)
- Constrained local executor and containerized test harness.
- Designed to stress irreversible action controls without touching host state.

8. Runtime Orchestrator (`src/ree_openclaw/runtime`)
- Runs one integrated cycle: typed boundary -> RC update -> verifier -> commit mint -> sandbox execute -> ledger append.
- Produces explicit rejection ledger entries when verifier denies action release.
- Exposed via local CLI (`src/ree_openclaw/cli.py`) for practical prototype execution on macOS.

9. Rollout Planner (`src/ree_openclaw/rollout`)
- Builds pre-commit `TRAJ`-typed rollout candidates.
- Applies viability/valence scoring overlay for candidate ranking.
- Keeps imagination/planning separate from commitment and durable writes.

10. Offline Consolidation (`src/ree_openclaw/offline`)
- Consolidates post-commit traces into action reliability summaries.
- Allows only protected trigger sources (`operator_cli`, `scheduler`).

11. Autonomous Session Runner (`src/ree_openclaw/agent`)
- Runs bounded multi-step sessions using rollout ranking and runtime action release.
- Applies stop guards (`max_steps`, `max_command_count`, `max_wall_clock_seconds`, stop-on-reject) for safe autonomy prototyping.

## Milestone Map

1. M0 Integration Skeleton
- Boundary router implemented.
- Trusted store write restrictions implemented at typed-boundary layer.
- Dedicated trusted-store interfaces implemented.

2. M1 Verifier + Manifests
- Capability manifest schema and loader implemented.
- Verifier checks and audit logging implemented.
- `required_verifiers` and `provenance_bindings` are enforced at verification time.
- `LOCKDOWN` posture blocks privileged/destructive action release.

3. M2 Commit Token + Ledger
- Commit token model implemented.
- Append-only ledger and chain verification implemented.
- Append durability flush (`fsync`) implemented for local reliability.
- Runtime integration stamps commit tokens before execution and records post-commit outcomes.

4. M3 RC Conflict Hysteresis
- State transitions with high/low/lock thresholds implemented.
- Weighted RC signal scoring implemented.
- Runtime computes RC score and updates posture before verifier decision.

5. M4 Rollout Interface
- `TRAJ` typing and pre-commit separation are implemented.
- Rollout planner and viability/valence ranking overlay are implemented.

6. M5 Offline Consolidation
- Offline consolidation runtime is implemented with protected trigger boundaries.
- Reliability summaries are generated from post-commit traces.

## Detailed Gap Tracking

- `docs/milestones_m0_m5_audit.md` is the source of exact M0-M5 gaps and implementation status.
