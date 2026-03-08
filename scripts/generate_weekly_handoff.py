#!/usr/bin/env python3
"""Generate weekly handoff markdown from runtime-authority run packs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_OUTPUT = Path("evidence/planning/weekly_handoff/latest.md")
DEFAULT_RUNS_ROOT = Path("evidence/experiments")
ALLOWED_DIRECTIONS = {"supports", "weakens", "mixed", "unknown"}


@dataclass(frozen=True)
class RunRow:
    experiment_type: str
    run_id: str
    seed: int | str
    condition_or_scenario: str
    status: str
    evidence_direction: str
    claim_ids_tested: list[str]
    failure_signatures: list[str]
    execution_mode: str
    compute_backend: str
    runtime_minutes: str
    pack_path: str
    timestamp_utc: datetime
    commit_count: float
    reject_count: float


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _monday_of_week(ts: datetime) -> str:
    monday = (ts - timedelta(days=ts.weekday())).date()
    return monday.isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_value(args: list[str], fallback: str) -> str:
    try:
        result = subprocess.run(args, check=True, capture_output=True, text=True)
    except Exception:
        return fallback
    value = result.stdout.strip()
    return value or fallback


def _collect_rows(runs_root: Path) -> list[RunRow]:
    rows: list[RunRow] = []
    for manifest_path in sorted(runs_root.glob("*/runs/*/manifest.json")):
        try:
            manifest = _load_json(manifest_path)
        except Exception:
            continue

        run_dir = manifest_path.parent
        metrics_path = run_dir / "metrics.json"
        runtime_minutes = "N/A"
        commit_count = 0.0
        reject_count = 0.0
        if metrics_path.exists():
            try:
                metrics = _load_json(metrics_path)
                values = metrics.get("values", {})
                if isinstance(values, dict):
                    if "runtime_minutes" in values:
                        runtime_minutes = str(values["runtime_minutes"])
                    commit_count = float(values.get("commit_executed_count", 0.0))
                    reject_count = float(values.get("proposal_rejected_count", 0.0))
            except Exception:
                pass

        scenario = manifest.get("scenario", {}) if isinstance(manifest.get("scenario"), dict) else {}
        seed = scenario.get("seed", "unknown")
        condition = str(scenario.get("name") or scenario.get("condition") or "unknown")

        rows.append(
            RunRow(
                experiment_type=str(manifest.get("experiment_type", "")),
                run_id=str(manifest.get("run_id", "")),
                seed=seed,
                condition_or_scenario=condition,
                status=str(manifest.get("status", "FAIL")),
                evidence_direction=str(manifest.get("evidence_direction", "unknown")),
                claim_ids_tested=list(manifest.get("claim_ids_tested", []))
                if isinstance(manifest.get("claim_ids_tested"), list)
                else [],
                failure_signatures=list(manifest.get("failure_signatures", []))
                if isinstance(manifest.get("failure_signatures"), list)
                else [],
                execution_mode="local",
                compute_backend="local_cpu",
                runtime_minutes=runtime_minutes,
                pack_path=str(run_dir),
                timestamp_utc=_parse_timestamp(str(manifest.get("timestamp_utc", _utc_now()))),
                commit_count=commit_count,
                reject_count=reject_count,
            )
        )
    return rows


def _latest_cycle(rows: list[RunRow], window_minutes: int) -> list[RunRow]:
    if not rows:
        return []
    latest_ts = max(row.timestamp_utc for row in rows)
    cutoff = latest_ts - timedelta(minutes=window_minutes)
    selected = [row for row in rows if row.timestamp_utc >= cutoff]
    selected.sort(key=lambda row: (row.experiment_type, row.run_id))
    return selected


def _schema_validation_gate() -> tuple[str, str]:
    command = ["python3", "scripts/validate_experiment_packs.py"]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except Exception:
        return "FAIL", "python3 scripts/validate_experiment_packs.py (runner missing)"
    status = "PASS" if result.returncode == 0 else "FAIL"
    return status, "python3 scripts/validate_experiment_packs.py"


def _seed_determinism_gate(rows: list[RunRow]) -> tuple[str, str]:
    by_experiment: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        if isinstance(row.seed, bool) or not isinstance(row.seed, int):
            return "FAIL", f"non-integer seed in run {row.run_id}"
        by_experiment[row.experiment_type].add(row.seed)

    for experiment_type, seeds in sorted(by_experiment.items()):
        if len(seeds) < 2:
            return "FAIL", f"{experiment_type} has fewer than 2 distinct integer seeds"
    return "PASS", "all latest-cycle experiment groups include >=2 distinct integer seeds"


def _hook_surface_gate(rows: list[RunRow]) -> tuple[str, str]:
    commit_present = any(row.commit_count > 0 for row in rows)
    reject_present = any(row.reject_count > 0 for row in rows)
    if commit_present and reject_present:
        return "PASS", "latest cycle includes both commit-executed and proposal-rejected runtime paths"
    return "FAIL", "latest cycle missing either commit-executed or proposal-rejected runtime path"


def _claim_summary(rows: list[RunRow]) -> list[dict[str, str | int]]:
    by_claim: dict[str, list[RunRow]] = defaultdict(list)
    for row in rows:
        claim_ids = row.claim_ids_tested or ["unknown_claim"]
        for claim_id in claim_ids:
            by_claim[claim_id].append(row)

    summaries: list[dict[str, str | int]] = []
    for claim_id in sorted(by_claim):
        claim_rows = by_claim[claim_id]
        direction_counts = Counter(row.evidence_direction for row in claim_rows)
        signature_counts = Counter(sig for row in claim_rows for sig in row.failure_signatures)
        recurring = sorted(sig for sig, count in signature_counts.items() if count >= 2)
        summaries.append(
            {
                "claim_id": claim_id,
                "runs_added": len(claim_rows),
                "supports": direction_counts.get("supports", 0),
                "weakens": direction_counts.get("weakens", 0),
                "mixed": direction_counts.get("mixed", 0),
                "unknown": direction_counts.get("unknown", 0),
                "recurring_failure_signatures": ", ".join(recurring) if recurring else "none",
            }
        )
    return summaries


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate weekly handoff markdown from run packs.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output markdown path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=DEFAULT_RUNS_ROOT,
        help=f"Runs root (default: {DEFAULT_RUNS_ROOT})",
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=240,
        help="Latest-cycle selection window in minutes (default: 240)",
    )
    args = parser.parse_args()

    rows = _collect_rows(args.runs_root)
    latest_rows = _latest_cycle(rows, args.window_minutes)
    if not latest_rows:
        print(f"FAIL: no run packs found under {args.runs_root}")
        return 1

    schema_status, schema_evidence = _schema_validation_gate()
    seed_status, seed_evidence = _seed_determinism_gate(latest_rows)
    hook_status, hook_evidence = _hook_surface_gate(latest_rows)
    remote_status, remote_evidence = (
        "N/A",
        "N/A for local runtime-authority lane (imports handled by REE_assembly sync).",
    )

    blockers: list[str] = []
    if schema_status != "PASS":
        blockers.append("schema_validation is FAIL; fix schema or manifest drift.")
    if seed_status != "PASS":
        blockers.append("seed_determinism is FAIL; emit at least two distinct seeds.")
    if hook_status != "PASS":
        blockers.append("hook_surface_coverage is FAIL; ensure both allow and reject runtime paths.")
    if any(row.evidence_direction not in ALLOWED_DIRECTIONS for row in latest_rows):
        blockers.append("one or more run rows has invalid evidence_direction.")
    if not blockers:
        blockers.append("none")

    latest_ts = max(row.timestamp_utc for row in latest_rows)
    week_of_utc = _monday_of_week(latest_ts)
    producer_repo = "ree-openclaw"
    producer_commit = _git_value(["git", "rev-parse", "HEAD"], "unknown")
    generated_utc = _utc_now()
    contract_lock_path = Path("contracts/experiment_pack/v1/manifest.schema.json")
    contract_lock_hash = (
        _sha256_file(contract_lock_path) if contract_lock_path.exists() else "missing-contract-lock"
    )
    summaries = _claim_summary(latest_rows)

    lines = [
        f"# Weekly Handoff - {producer_repo} - {week_of_utc}",
        "",
        "## Metadata",
        f"- week_of_utc: `{week_of_utc}`",
        f"- producer_repo: `{producer_repo}`",
        f"- producer_commit: `{producer_commit}`",
        f"- generated_utc: `{generated_utc}`",
        "",
        "## Contract Sync",
        "- ree_assembly_repo: `REE_assembly`",
        "- ree_assembly_commit: `N/A (resolved by REE_assembly sync job)`",
        f"- contract_lock_path: `{contract_lock_path}`",
        f"- contract_lock_hash: `{contract_lock_hash}`",
        "- schema_version_set: `experiment_pack/v1, experiment_pack_metrics/v1`",
        "",
        "## CI Gates",
        "| gate | status | evidence |",
        "| --- | --- | --- |",
        f"| schema_validation | {schema_status} | `{schema_evidence}` |",
        f"| seed_determinism | {seed_status} | `{seed_evidence}` |",
        f"| hook_surface_coverage | {hook_status} | `{hook_evidence}` |",
        f"| remote_export_import | {remote_status} | `{remote_evidence}` |",
        "",
        "## Run-Pack Inventory",
        "| experiment_type | run_id | seed | condition_or_scenario | status | evidence_direction | claim_ids_tested | failure_signatures | execution_mode | compute_backend | runtime_minutes | pack_path |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in latest_rows:
        claim_ids = ", ".join(row.claim_ids_tested) if row.claim_ids_tested else "none"
        signatures = ", ".join(row.failure_signatures) if row.failure_signatures else "none"
        lines.append(
            "| "
            f"{row.experiment_type} | {row.run_id} | {row.seed} | "
            f"{row.condition_or_scenario} | {row.status} | {row.evidence_direction} | "
            f"{claim_ids} | {signatures} | {row.execution_mode} | "
            f"{row.compute_backend} | {row.runtime_minutes} | {row.pack_path} |"
        )

    lines.extend(
        [
            "",
            "## Claim Summary",
            "| claim_id | runs_added | supports | weakens | mixed | unknown | recurring_failure_signatures |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for summary in summaries:
        lines.append(
            "| "
            f"{summary['claim_id']} | {summary['runs_added']} | {summary['supports']} | "
            f"{summary['weakens']} | {summary['mixed']} | {summary['unknown']} | "
            f"{summary['recurring_failure_signatures']} |"
        )

    lines.extend(["", "## Open Blockers"])
    for blocker in blockers:
        lines.append(f"- {blocker}")

    lines.extend(
        [
            "",
            "## Local Compute Options Watch",
            "- local_options_last_updated_utc: `N/A`",
            "- rolling_3mo_cloud_spend_eur: `N/A`",
            "- local_blocked_sessions_this_week: `N/A`",
            "- recommended_local_action: `N/A`",
            "- rationale: `N/A for REE_OpenClaw runtime lane unless compute planning is explicitly in scope.`",
        ]
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"PASS: generated weekly handoff at {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
