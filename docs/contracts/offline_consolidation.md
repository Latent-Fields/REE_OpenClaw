# Contract: Offline Consolidation

Doc: `docs/contracts/offline_consolidation.md`  
Date: 2026-02-18  
Status: Active (v0 prototype)

## Purpose

Define protected offline consolidation behavior over post-commit traces.

## Implementation Surface

- `src/ree_openclaw/offline/consolidation.py`
- `OpenClawRuntime.run_offline_consolidation(...)`
- CLI command: `offline-consolidate`

## Trigger Boundary

Allowed trigger sources:

- `operator_cli`
- `scheduler`

Any other trigger source is blocked.

## Output

Offline consolidation emits:

- `skill_reliability.json` artifact under runtime offline state directory
- per-action totals
- per-action commit counts
- per-action success counts and success rates

## Safety Invariant

Offline consolidation reads ledger traces and writes offline summaries only.
It does not execute tools and does not mint commits.
