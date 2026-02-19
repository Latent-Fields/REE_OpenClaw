# REE_OpenClaw

REE_OpenClaw is a standalone implementation testbed for applying Reflective Ethical Engine (REE) authority, commitment, and responsibility invariants to an OpenClaw-class shell.

## Goals

- Keep untrusted channels (`OBS`/`INS`/`TRAJ`) separated from trusted store types (`POL`/`ID`/`CAPS`).
- Gate privileged and destructive actions through verifier + RC posture checks.
- Mint explicit commit tokens before execution and persist append-only post-commit traces.
- Keep local execution lightweight for macOS development, with optional Docker parity.

## Quick Start (macOS / native Python)

```bash
make setup
source .venv/bin/activate
make test
make run-plan-demo
make run-demo
make run-autonomy-demo
make offline-consolidate
```

`make run-demo` runs a safe local prototype cycle:

1. Proposal is routed through typed boundary.
2. RC score is computed from structured conflict signals, then hysteresis updates posture.
3. Verifier decides action eligibility.
4. Commit token is minted if allowed.
5. Action executes inside the local sandbox harness.
6. Append-only ledger records the result.

## Prototype CLI

Run one full configurable cycle:

```bash
python3 -m ree_openclaw.cli run-cycle --command echo "hello from cycle"
```

Pass explicit RC signals (computed into one score):

```bash
python3 -m ree_openclaw.cli run-cycle \
  --rc-signal-provenance-mismatch 0.7 \
  --rc-signal-identity-inconsistency 0.4 \
  --rc-signal-temporal-discontinuity 0.2 \
  --rc-signal-tool-output-inconsistency 0.1
```

Run the built-in safe demo:

```bash
python3 -m ree_openclaw.cli run-demo
```

Run rollout planning only (no commit, no execute, no ledger append):

```bash
python3 -m ree_openclaw.cli plan-demo
```

Run protected offline consolidation from post-commit traces:

```bash
python3 -m ree_openclaw.cli offline-consolidate
```

Run guarded multi-step autonomy demo:

```bash
python3 -m ree_openclaw.cli autonomy-demo --scenario safe
python3 -m ree_openclaw.cli autonomy-demo --scenario guarded
```

Runtime state is written under `.ree_openclaw_state/` by default (ledger, sandbox root, verifier audit log).

## Optional Docker Path

Docker is optional and kept for sandbox parity:

```bash
make sandbox-test
```

This builds `sandbox/Dockerfile` and runs tests in-container.

## Milestone Audit (M0-M5)

Current status and milestone coverage are maintained in:

- `docs/milestones_m0_m5_audit.md`
- `docs/roadmap_autonomous_agent.md`

## Status

v0 now includes a practical local runtime cycle and prototype CLI for MacBook Air-class development, while keeping Docker-based testing optional.
