# REE_OpenClaw

REE_OpenClaw is a standalone, safety-first implementation testbed that applies Reflective Ethical Engine (REE) authority and commitment invariants to an OpenClaw-class agent shell.

## Purpose

This repository exists to make REE claims operational:

- turn typed authority boundaries into enforceable runtime behavior
- gate privileged/destructive actions through explicit verifier policy
- require explicit commitment before execution
- preserve accountability via append-only post-commit traces
- provide a practical local prototype for MacBook Air-class development

## Why This Project Is Unique

REE_OpenClaw combines capabilities that are usually split across separate prototypes:

1. Typed authority boundary (`OBS`/`INS`/`TRAJ` vs `POL`/`ID`/`CAPS`).
2. Manifest-driven verifier with provenance and consent enforcement.
3. Weighted RC conflict scoring plus hysteresis posture (`NORMAL`/`VERIFY`/`LOCKDOWN`).
4. Explicit commit token minting before action release.
5. Append-only hash-chained ledger with local durability flush.
6. Pre-commit rollout planning/ranking separated from execution.
7. Guarded multi-step autonomy demo with budget controls.
8. Protected offline consolidation from post-commit traces.

For contributors and users, this means you can work on autonomy features without losing safety/traceability primitives.

## Installation And Quick Start (macOS Native)

```bash
make setup
source .venv/bin/activate
make test
make run-plan-demo
make run-demo
make run-autonomy-demo
make offline-consolidate
```

## Usage

Run one full configurable proposal -> commit -> execute -> ledger cycle:

```bash
python3 -m ree_openclaw.cli run-cycle --command echo "hello from cycle"
```

Run with explicit RC conflict signals:

```bash
python3 -m ree_openclaw.cli run-cycle \
  --rc-signal-provenance-mismatch 0.7 \
  --rc-signal-identity-inconsistency 0.4 \
  --rc-signal-temporal-discontinuity 0.2 \
  --rc-signal-tool-output-inconsistency 0.1
```

Run safe built-in runtime demo:

```bash
python3 -m ree_openclaw.cli run-demo
```

Run rollout planning only (no commit, no execute, no ledger append):

```bash
python3 -m ree_openclaw.cli plan-demo
```

Run guarded multi-step autonomy demo:

```bash
python3 -m ree_openclaw.cli autonomy-demo --scenario safe
python3 -m ree_openclaw.cli autonomy-demo --scenario guarded
python3 -m ree_openclaw.cli autonomy-demo --scenario safe --max-command-count 2 --max-wall-clock-seconds 10
```

Run protected offline consolidation from ledger traces:

```bash
python3 -m ree_openclaw.cli offline-consolidate
```

Runtime state is written under `.ree_openclaw_state/` by default (ledger, sandbox root, verifier audit log, autonomy artifacts, offline summaries).

## Optional Docker Path

Docker is optional for sandbox parity:

```bash
make sandbox-test
```

This builds `sandbox/Dockerfile` and runs tests in-container.

## Make Targets

- `make setup`: create venv and install dev dependencies
- `make test`: run native test suite
- `make run-cycle`: run configurable runtime cycle
- `make run-demo`: run safe runtime demo
- `make run-plan-demo`: run planning-only demo
- `make run-autonomy-demo`: run guarded autonomy demo
- `make offline-consolidate`: run protected offline consolidation
- `make sandbox-test`: run containerized parity tests

## Licensing

- License: Apache-2.0 (`/Users/dgolden/Documents/GitHub/REE_OpenClaw/LICENSE`)
- Project notice and research/safety context: `/Users/dgolden/Documents/GitHub/REE_OpenClaw/NOTICE`
- Software is provided on an "AS IS" basis without warranties under Apache-2.0 terms.

## Citation

If you use REE_OpenClaw in research or derivative systems, cite:

- `/Users/dgolden/Documents/GitHub/REE_OpenClaw/CITATION.cff`

Example BibTeX:

```bibtex
@software{golden_ree_openclaw_2026,
  title = {REE_OpenClaw},
  author = {Golden, Daniel},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/Latent-Fields/REE_OpenClaw},
  license = {Apache-2.0}
}
```

## Contributor Entry Points

High-value contribution areas:

1. Autonomous loop hardening (session memory, retry/backoff, recovery policy).
2. Tool substrate expansion (filesystem/web adapters with provenance discipline).
3. Offline learning promotion gates from summaries to bounded playbooks.
4. Operator UX and observability for long-running autonomous sessions.

See:

- `/Users/dgolden/Documents/GitHub/REE_OpenClaw/docs/roadmap_autonomous_agent.md`
- `/Users/dgolden/Documents/GitHub/REE_OpenClaw/docs/architecture.md`
- `/Users/dgolden/Documents/GitHub/REE_OpenClaw/docs/milestones_m0_m5_audit.md`

## Status

Current branch represents a working v0 prototype with:

- native and optional Docker workflows
- explicit authority/commitment runtime pipeline
- guarded autonomy demo and roadmap toward fuller autonomous operation
