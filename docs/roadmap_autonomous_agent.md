# Roadmap: Full Autonomous REE_OpenClaw

Date: 2026-02-18  
Status: Planning baseline after v0 completion

## Why Build Here

REE_OpenClaw is a strong contributor surface because it already combines:

- typed authority boundaries that block direct trust-store mutation from user/LLM channels
- explicit verifier + consent policy gates for privileged/destructive actions
- RC conflict posture control with weighted scoring and hysteresis
- commit-token and append-only ledger accountability
- guarded multi-step autonomy loops with safety stop conditions

This lets contributors add autonomous capabilities while preserving safety and auditability constraints.

## Current Baseline

Implemented now:

- strict typed authority boundary
- verifier and capability manifest enforcement
- RC conflict scoring + hysteresis posture
- commit token + sandbox execution + append-only ledger
- rollout planning/ranking interface
- protected offline consolidation
- bounded autonomous session demo runner

## Contributor Priorities

If you want high-impact entry points, start here:

1. Persistent autonomy memory that improves planning without bypassing verifier/commit gates.
2. Tool substrate expansion for practical local workflows (filesystem/web/operator approval).
3. Replay + observability tooling for debugging long autonomy traces.
4. Reliability tuning from offline summaries into guarded playbooks.

## Phase 1 - Autonomous Loop Hardening

Goal: make multi-step autonomy reliable and inspectable.

Work items:

1. Add per-session budget guards (token/time/tool-call limits). (Completed in prototype)
2. Add persistent session memory separate from trusted stores.
3. Add explicit retry/backoff policy for reversible actions.
4. Add action failure classification and recovery transitions.

Exit criteria:

- deterministic replay of autonomous sessions from artifact + ledger
- bounded sessions cannot exceed configured limits

## Phase 2 - Tool Substrate Expansion

Goal: move from demo commands to practical local tool use.

Work items:

1. Add filesystem read/write/edit adapters through manifest classes.
2. Add local web fetch/search adapters with explicit provenance.
3. Add operator-approval lane for privileged side effects.
4. Add sandbox profiles for safe/restricted/elevated modes.

Exit criteria:

- autonomous sessions can solve non-trivial local workflows end-to-end
- privileged side effects always require explicit approval tokens

## Phase 3 - Memory and Learning

Goal: improve long-horizon autonomous behavior without breaking invariants.

Work items:

1. Add episodic trace store for session context.
2. Add policy for converting offline summaries into bounded playbooks.
3. Add typed write path from offline artifacts to trusted/internal stores.
4. Add quality gates before promoting learned playbooks to runtime use.

Exit criteria:

- measurable session success improvement from offline learning
- no direct external channel to durable/trusted updates

## Phase 4 - Productionization

Goal: run continuous autonomous operations safely on a MacBook-class machine.

Work items:

1. Add lightweight supervisor process and health checks.
2. Add structured telemetry and red-team probe suite expansion.
3. Add signed release artifacts and migration scripts.
4. Add operator dashboard for session review and intervention.

Exit criteria:

- continuous operation with bounded resource usage
- clear intervention and rollback workflow for operators

## Immediate Next Engineering Slice

Proceed with Phase 1 item #2:

- add persistent session memory for autonomy runs (separate from trusted stores)
- store per-step context and prior outcomes for later candidate construction
- add replay test ensuring memory does not bypass verifier/commit gates
