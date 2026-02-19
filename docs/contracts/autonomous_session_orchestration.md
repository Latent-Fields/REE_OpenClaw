# Contract: Autonomous Session Orchestration

Doc: `docs/contracts/autonomous_session_orchestration.md`  
Date: 2026-02-18  
Status: Active (prototype)

## Purpose

Define bounded autonomous multi-step execution on top of REE runtime controls.

## Session Model

Autonomous sessions are composed of ordered steps, where each step includes one or more rollout candidates.

Per step flow:

1. Build `TRAJ` candidates.
2. Rank candidates using viability/valence overlay.
3. Select top-ranked trajectory.
4. Run normal runtime cycle:
   - typed boundary
   - RC posture
   - verifier
   - commit + execute + ledger (if allowed)

## Guards

Session policy requires:

- `max_steps` bound
- optional `max_command_count` bound
- optional `max_wall_clock_seconds` bound
- optional `stop_on_reject`

If a step is rejected and `stop_on_reject` is enabled, the session stops immediately.
If command-count or wall-clock budgets are exhausted, the session stops with guardrail reasons.

Prototype stop reasons:

- `completed`
- `max_steps_reached`
- `max_command_count_reached`
- `max_wall_clock_reached`
- `rejected_step`
- `no_candidates`

## Scope

This contract defines prototype orchestration only. It does not imply open-ended self-directed autonomy or production-grade autonomous planning.
