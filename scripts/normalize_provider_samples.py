#!/usr/bin/env python3
"""Normalize provider sample manifest + files into PIT-aware observation records (no network)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_dir, safe_input_file, safe_output_file

from strategy_validator.data_spine.normalize import normalize_sample_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize artifacts/provider_samples manifest into observations.")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to retrieve_provider_samples manifest.json",
    )
    parser.add_argument(
        "--samples-dir",
        type=Path,
        default=None,
        help="Directory containing sample files (default: manifest parent).",
    )
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output JSON path.")
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON.")
    ns = parser.parse_args(argv)
    try:
        manifest = safe_input_file(ns.manifest, label="NORMALIZE_PROVIDER_MANIFEST", required=True)
        samples_dir = safe_input_dir(ns.samples_dir or manifest.parent, label="NORMALIZE_PROVIDER_SAMPLES_DIR", required=True)
        output = safe_output_file(ns.output, label="NORMALIZE_PROVIDER_OUTPUT")
    except PathIntegrityError as exc:
        sys.stdout.write(json.dumps(path_error_payload(exc), sort_keys=True) + "\n")
        return 2
    records = normalize_sample_bundle(manifest_path=manifest, samples_dir=samples_dir)
    payload = {
        "schema_version": "normalized_provider_observations/v1",
        "manifest_path": manifest.as_posix(),
        "samples_dir": samples_dir.as_posix(),
        "record_count": len(records),
        "records": [r.model_dump(mode="json") for r in records],
    }
    indent = 2 if ns.json else None
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=indent, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
