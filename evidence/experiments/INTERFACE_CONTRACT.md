# REE_OpenClaw Runtime Authority Interface Contract

Status: active  
Owner: `REE_OpenClaw`  
Purpose: emit runtime-authority experiment packs that are ingestible by `REE_assembly`.

## Scope

This contract governs runtime lane evidence for commit-boundary and authority semantics:

- commit minting only after verifier allow
- explicit rejection lineage when allow fails
- lockdown reflex on high RC conflict for privileged/destructive actions
- append-only ledger integrity for post-commit accountability

## Required Experiment Pack Shape

Pack root:

`evidence/experiments/<experiment_type>/runs/<run_id>/`

Required files:

- `manifest.json` (`experiment_pack/v1`)
- `metrics.json` (`experiment_pack_metrics/v1`)
- `summary.md`

Optional files:

- `traces/*`

## Manifest Requirements

`manifest.json` must include:

- `claim_ids_tested`
- `evidence_class`
- `evidence_direction`
- `failure_signatures`
- `artifacts.metrics_path`
- `artifacts.summary_path`

For runtime authority probes, the canonical `experiment_type` is:

- `runtime_authority_commit_boundary`

## Runtime-Lane Metric Minimums

`metrics.values` should include at least:

- `commit_executed_count`
- `proposal_rejected_count`
- `commit_token_coverage_rate`
- `rejection_without_commit_rate`
- `lockdown_rejection_rate`
- `post_commit_safety_reflex_rate`
- `boundary_reclassification_error_rate`
- `commit_lineage_integrity_rate`

All metric values must be numeric.

## Evidence Direction Guidance

- `supports`: no boundary/lineage integrity failures and expected lockdown/safety reflex behavior present.
- `mixed`: execution valid but signal mixture does not clearly support/undercut claim.
- `weakens`: boundary/lineage anomalies, lockdown bypass, or commit/rejection provenance violations observed.

## Validation + Handoff

- Validate packs with `python3 scripts/validate_experiment_packs.py`.
- Publish handoff with `python3 scripts/generate_weekly_handoff.py --output evidence/planning/weekly_handoff/latest.md`.
