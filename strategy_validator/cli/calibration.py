"""Validate calibration artifacts and print sealed metadata / sample curve lookups."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.core.config import load_config
from strategy_validator.validator.calibration_curve import interpolate_impact_bps
from strategy_validator.validator.calibration_governance import calibration_governance_violations
from strategy_validator.validator.calibration_loader import load_calibration_artifact_from_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Load and validate a CalibrationArtifactV1 (empirical calibration workflow).",
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        required=True,
        help="Path to calibration_v1.json",
    )
    parser.add_argument(
        "--participation",
        action="append",
        type=float,
        metavar="RATE",
        help="Optional participation rates in [0,1] to sample impact_bps (repeatable).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON (metadata plus optional samples) instead of plain lines.",
    )
    parser.add_argument(
        "--check-governance",
        action="store_true",
        help="Evaluate artifact against runtime governance policy from load_config() (exit non-zero if rejected).",
    )
    ns = parser.parse_args(argv)

    art = load_calibration_artifact_from_path(ns.artifact)
    if art is None:
        sys.stderr.write("CALIBRATION_LOAD_FAILED: missing, unreadable, or invalid artifact\n")
        return 2

    meta = art.to_metadata()
    if ns.check_governance:
        pol = load_config().runtime_policy
        gov = calibration_governance_violations(art, pol)
        if gov:
            sys.stderr.write("CALIBRATION_GOVERNANCE_REJECTED:\n")
            for g in gov:
                sys.stderr.write(f"  {g}\n")
            return 5

    samples: list[dict[str, float]] = []
    if ns.participation:
        if not art.empirical_participation_curve:
            sys.stderr.write("CALIBRATION_SAMPLE_SKIPPED: artifact has no empirical_participation_curve\n")
            return 3
        for r in ns.participation:
            if r < 0.0 or r > 1.0:
                sys.stderr.write(f"CALIBRATION_SAMPLE_INVALID_RATE: {r}\n")
                return 4
            samples.append(
                {
                    "participation_rate": r,
                    "impact_bps": interpolate_impact_bps(r, art.empirical_participation_curve),
                }
            )

    if ns.json:
        out = {
            "metadata": json.loads(meta.model_dump_json()),
            "samples": samples,
        }
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
    else:
        sys.stdout.write(f"OK dataset_fingerprint={meta.dataset_fingerprint} kind={meta.impact_model_kind}\n")
        for s in samples:
            sys.stdout.write(
                f"  participation={s['participation_rate']:.6g} impact_bps={s['impact_bps']:.6g}\n"
            )
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
