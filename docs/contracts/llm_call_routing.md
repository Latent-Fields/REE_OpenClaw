# Contract: LLM Call Routing and Authority Typing

Doc: `docs/contracts/llm_call_routing.md`  
Date: 2026-02-18  
Status: Draft (v0)

## Purpose

Define where LLM calls sit in REE_OpenClaw and how outputs are typed and routed.

## Payload Types

- `OBS`: untrusted observation
- `INS`: untrusted instruction/request
- `TRAJ`: untrusted rollout candidate
- `POL`: trusted policy store type
- `ID`: trusted identity store type
- `CAPS`: trusted capability store type

## Rule 1: LLM Is Not a Privileged Channel

LLM outputs are untrusted by default.

- Allowed LLM outputs: `OBS`, `INS`, `TRAJ`
- Disallowed direct emissions: `POL`, `ID`, `CAPS`

Any text that claims policy/identity/capabilities is still `INS`.

## Role Routing

1. Interpretation role
- Input: WORLD stream
- Output: `OBS`

2. Rollout role
- Input: WORLD + internal state
- Output: `TRAJ`

3. Execution suggestion role
- Output: `INS` or `TRAJ`
- Must pass verifier and commitment eligibility before action.

4. Policy draft role
- Output: `INS` only
- Never direct trusted-store write.

## Provenance Requirements

Each LLM output envelope must include:

- `model_call_id`
- `timestamp`
- `input_provenance`
- `prompt_hash`
- `role`
- `proposed_tool_effect_class`

## Elevation to Action

LLM output can influence action only through:

1. RC conflict check
2. Verifier checks
3. Eligibility gates
4. E3 commit token issuance

No direct path exists from LLM output to privileged action.

