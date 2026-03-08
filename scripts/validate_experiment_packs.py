#!/usr/bin/env python3
"""Validate REE_OpenClaw experiment packs against local v1 schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:
    Draft202012Validator = None


MANIFEST_SCHEMA_PATH = Path("contracts/experiment_pack/v1/manifest.schema.json")
METRICS_SCHEMA_PATH = Path("contracts/experiment_pack/v1/metrics.schema.json")
RUNS_ROOT = Path("evidence/experiments")


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_pack(
    manifest_path: Path,
    manifest_validator: Draft202012Validator | None,
    metrics_validator: Draft202012Validator | None,
) -> list[str]:
    errors: list[str] = []
    run_dir = manifest_path.parent

    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{manifest_path}: failed to parse manifest ({exc})"]

    if manifest_validator is not None:
        for err in manifest_validator.iter_errors(manifest):
            errors.append(f"{manifest_path}: schema error at {list(err.path)} -> {err.message}")

    experiment_type = run_dir.parent.parent.name
    run_id = run_dir.name
    if manifest.get("experiment_type") != experiment_type:
        errors.append(
            f"{manifest_path}: experiment_type mismatch (manifest={manifest.get('experiment_type')}, dir={experiment_type})"
        )
    if manifest.get("run_id") != run_id:
        errors.append(f"{manifest_path}: run_id mismatch (manifest={manifest.get('run_id')}, dir={run_id})")

    for required in ("claim_ids_tested", "evidence_class", "evidence_direction"):
        if required not in manifest:
            errors.append(f"{manifest_path}: missing required linkage field `{required}`")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append(f"{manifest_path}: artifacts must be an object")
        return errors

    metrics_rel = str(artifacts.get("metrics_path", "")).strip()
    summary_rel = str(artifacts.get("summary_path", "")).strip()
    if not metrics_rel:
        errors.append(f"{manifest_path}: artifacts.metrics_path missing or empty")
    if not summary_rel:
        errors.append(f"{manifest_path}: artifacts.summary_path missing or empty")

    metrics_path = run_dir / metrics_rel if metrics_rel else None
    summary_path = run_dir / summary_rel if summary_rel else None

    if metrics_path is not None and not metrics_path.exists():
        errors.append(f"{manifest_path}: missing metrics file at {metrics_path}")
    if summary_path is not None and not summary_path.exists():
        errors.append(f"{manifest_path}: missing summary file at {summary_path}")

    traces_rel = str(artifacts.get("traces_dir", "")).strip()
    if traces_rel and not (run_dir / traces_rel).exists():
        errors.append(f"{manifest_path}: traces_dir not found at {run_dir / traces_rel}")

    if metrics_path is not None and metrics_path.exists():
        try:
            metrics = _load_json(metrics_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{metrics_path}: failed to parse metrics ({exc})")
            return errors

        if metrics_validator is not None:
            for err in metrics_validator.iter_errors(metrics):
                errors.append(f"{metrics_path}: schema error at {list(err.path)} -> {err.message}")

        values = metrics.get("values")
        if not isinstance(values, dict):
            errors.append(f"{metrics_path}: values must be an object")
        else:
            for key, value in values.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    errors.append(
                        f"{metrics_path}: metrics.values.{key} must be numeric, got {type(value).__name__}"
                    )

    return errors


def main() -> int:
    if not MANIFEST_SCHEMA_PATH.exists() or not METRICS_SCHEMA_PATH.exists():
        print(
            "Validation failed: missing schema files at "
            f"{MANIFEST_SCHEMA_PATH} and/or {METRICS_SCHEMA_PATH}"
        )
        return 1

    manifest_schema = _load_json(MANIFEST_SCHEMA_PATH)
    metrics_schema = _load_json(METRICS_SCHEMA_PATH)

    manifest_validator = None
    metrics_validator = None
    if Draft202012Validator is not None:
        manifest_validator = Draft202012Validator(manifest_schema)
        metrics_validator = Draft202012Validator(metrics_schema)
    else:
        print("jsonschema not installed; running structural checks only.")

    manifests = sorted(RUNS_ROOT.glob("*/runs/*/manifest.json"))
    if not manifests:
        print(f"Validation failed: no manifests found under {RUNS_ROOT}")
        return 1

    all_errors: list[str] = []
    for manifest_path in manifests:
        all_errors.extend(
            _validate_pack(
                manifest_path=manifest_path,
                manifest_validator=manifest_validator,
                metrics_validator=metrics_validator,
            )
        )

    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):")
        for err in all_errors:
            print(f"- {err}")
        return 1

    print(f"Validation succeeded for {len(manifests)} run pack(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
