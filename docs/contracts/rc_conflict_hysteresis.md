# Contract: RC Conflict Hysteresis

Doc: `docs/contracts/rc_conflict_hysteresis.md`  
Date: 2026-02-18  
Status: Active (v0 prototype)

## Purpose

Specify how RC conflict is computed and how state transitions avoid threshold oscillation.

## Inputs

`RC_conflict_score` is computed from weighted evidence in `[0.0, 1.0]`:

- provenance mismatch
- identity or capability contradictions
- temporal discontinuity
- tool output inconsistency with declared effects

Default v0 weighted scoring (`src/ree_openclaw/rc/scoring.py`):

- provenance mismatch: `0.35`
- identity/capability inconsistency: `0.30`
- temporal discontinuity: `0.20`
- tool output inconsistency: `0.15`

Score equation:

`RC_conflict_score = sum(weight_i * signal_i) / sum(weight_i)`

## States

- `NORMAL`
- `VERIFY`
- `LOCKDOWN` (optional hard posture)

## Thresholds

- `T_high`: enter `VERIFY`
- `T_low`: exit `VERIFY`
- `T_lock`: enter `LOCKDOWN`

Constraint: `T_low < T_high < T_lock`

## Transition Rules

1. If score `>= T_lock`: state becomes `LOCKDOWN`.
2. If state is `NORMAL` and score `>= T_high`: state becomes `VERIFY`.
3. If state is `VERIFY` or `LOCKDOWN` and score `<= T_low`: state becomes `NORMAL`.
4. If state is `LOCKDOWN` and `T_low < score < T_lock`: state becomes `VERIFY`.

## State Effects

- `NORMAL`: baseline verifier policy.
- `VERIFY`: stricter verifier posture and broader consent requirements.
- `LOCKDOWN`: block privileged/destructive actions pending explicit recovery.

## Probe Expectations

- Spoof attempt should push score over `T_high`.
- Repeated borderline signals should not cause fast mode flapping.
- Recovery requires sustained drop below `T_low`.
