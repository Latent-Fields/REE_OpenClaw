# Contract: Rollout Interface and Pre-Commit Separation

Doc: `docs/contracts/rollout_interface.md`  
Date: 2026-02-18  
Status: Active (v0 prototype)

## Purpose

Define a strict separation between rollout imagination and committed execution.

## Rollout Candidate Interface

Each rollout candidate contains:

- untrusted `TRAJ` envelope
- `action_class`
- `scope`
- `effect_class`
- sandbox `command`
- `trajectory_reference`

Rollout candidates are built by:

- `src/ree_openclaw/rollout/planner.py` (`RolloutPlanner.build_candidates`)

## Ranking Overlay

Candidates are ranked by viability/valence overlay:

- viability score in `[0,1]`
- valence score in `[0,1]`
- weighted ranking score:
  - viability weight `0.6`
  - valence weight `0.4`

`ranking_score = (viability * 0.6 + valence * 0.4) / 1.0`

## Separation Invariant

Planning APIs do not:

- mint commit tokens
- execute sandbox commands
- append to ledger

Execution happens only after explicit commitment flow through:

1. RC posture update
2. verifier decision
3. commit token minting
4. sandbox execution
5. append-only ledger write
