# Contract: User Interaction and Delegated Authority

Doc: `docs/contracts/user_interaction_and_delegation.md`  
Date: 2026-02-18  
Status: Draft (v0)

## Purpose

Define how user input enters the system and how delegated authority is granted without collapsing typed boundaries.

## Core Principle

User messages are always WORLD sensory payloads.  
Authority is granted only through explicit, typed delegation.

## Sensory Classification

All user input is one of:

- `WORLD:INS`
- `WORLD:OBS`

User text is never:

- `POL`
- `ID`
- `CAPS`
- commit token

## Delegated Authority

In tool mode, privileged actions require a consent token.

Consent token fields:

- `action_class`
- `scope`
- `duration`
- `constraints`
- `nonce`
- `issued_at`

Tokens must be scoped, logged, revocable, and non-replayable.

## Commitment Flow

1. User submits `INS`.
2. System generates proposals (`TRAJ`/`INS`).
3. RC conflict and verifier checks run.
4. If privileged, consent token is required.
5. E3 issues `commit_id`.
6. Action runs and post-commit ledger entry is appended.

## Non-Overridable Invariants

User text cannot:

- rewrite identity anchors
- disable RC conflict checks
- disable hard harm veto
- erase post-commit traces
- directly mutate `POL`/`ID`/`CAPS`

