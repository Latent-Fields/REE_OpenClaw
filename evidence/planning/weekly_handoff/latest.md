# Weekly Handoff - ree-openclaw - 2026-02-23

## Metadata
- week_of_utc: `2026-02-23`
- producer_repo: `ree-openclaw`
- producer_commit: `a7a26c120ac93fab0decdb9e85ec08976bfd3725`
- generated_utc: `2026-02-25T19:50:51.093791Z`

## Contract Sync
- ree_assembly_repo: `REE_assembly`
- ree_assembly_commit: `N/A (resolved by REE_assembly sync job)`
- contract_lock_path: `contracts/experiment_pack/v1/manifest.schema.json`
- contract_lock_hash: `ddbfeac9f4c75e8153f7c4c1bcfeebb46b5da1877ab0ffc6b548e020d4a220d3`
- schema_version_set: `experiment_pack/v1, experiment_pack_metrics/v1`

## CI Gates
| gate | status | evidence |
| --- | --- | --- |
| schema_validation | PASS | `python3 scripts/validate_experiment_packs.py` |
| seed_determinism | PASS | `all latest-cycle experiment groups include >=2 distinct integer seeds` |
| hook_surface_coverage | PASS | `latest cycle includes both commit-executed and proposal-rejected runtime paths` |
| remote_export_import | N/A | `N/A for local runtime-authority lane (imports handled by REE_assembly sync).` |

## Run-Pack Inventory
| experiment_type | run_id | seed | condition_or_scenario | status | evidence_direction | claim_ids_tested | failure_signatures | execution_mode | compute_backend | runtime_minutes | pack_path |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_authority_commit_boundary | runtime_authority_commit_boundary_seed11_20260225T195039888432Z | 11 | runtime_authority_commit_boundary_probe | PASS | supports | MECH-056, MECH-057, MECH-060, MECH-061, Q-013, Q-014, Q-017 | none | local | local_cpu | N/A | evidence/experiments/runtime_authority_commit_boundary/runs/runtime_authority_commit_boundary_seed11_20260225T195039888432Z |
| runtime_authority_commit_boundary | runtime_authority_commit_boundary_seed29_20260225T195039901451Z | 29 | runtime_authority_commit_boundary_probe | PASS | supports | MECH-056, MECH-057, MECH-060, MECH-061, Q-013, Q-014, Q-017 | none | local | local_cpu | N/A | evidence/experiments/runtime_authority_commit_boundary/runs/runtime_authority_commit_boundary_seed29_20260225T195039901451Z |

## Claim Summary
| claim_id | runs_added | supports | weakens | mixed | unknown | recurring_failure_signatures |
| --- | --- | --- | --- | --- | --- | --- |
| MECH-056 | 2 | 2 | 0 | 0 | 0 | none |
| MECH-057 | 2 | 2 | 0 | 0 | 0 | none |
| MECH-060 | 2 | 2 | 0 | 0 | 0 | none |
| MECH-061 | 2 | 2 | 0 | 0 | 0 | none |
| Q-013 | 2 | 2 | 0 | 0 | 0 | none |
| Q-014 | 2 | 2 | 0 | 0 | 0 | none |
| Q-017 | 2 | 2 | 0 | 0 | 0 | none |

## Open Blockers
- none

## Local Compute Options Watch
- local_options_last_updated_utc: `N/A`
- rolling_3mo_cloud_spend_eur: `N/A`
- local_blocked_sessions_this_week: `N/A`
- recommended_local_action: `N/A`
- rationale: `N/A for REE_OpenClaw runtime lane unless compute planning is explicitly in scope.`
