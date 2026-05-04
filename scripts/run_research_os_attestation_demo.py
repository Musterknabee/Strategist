#!/usr/bin/env python3
"""Build Research OS closure verification + operator attestation artifacts.

This is a paper-only evidence helper. It does not trade, submit broker orders,
or approve deployment.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from strategy_validator.application.research_os_attestation_ops import (
    build_operator_attestation,
    verify_research_os_closure_manifest,
    write_operator_attestation,
    write_research_os_closure_verification,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--verification-id", default="research-os-attestation-demo-verification")
    parser.add_argument("--attestation-id", default="research-os-attestation-demo")
    parser.add_argument("--operator-id", default="local-operator")
    parser.add_argument("--decision", default="ACCEPTED_WITH_RESTRICTIONS")
    parser.add_argument("--rationale", default="Paper-only closure evidence acknowledged; not deployment approval.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)
    artifact_root = Path(ns.artifact_root)
    verification = verify_research_os_closure_manifest(
        verification_id=ns.verification_id,
        artifact_root=artifact_root,
    )
    vpath = write_research_os_closure_verification(verification, artifact_root=artifact_root, overwrite=ns.overwrite)
    attestation = build_operator_attestation(
        attestation_id=ns.attestation_id,
        operator_id=ns.operator_id,
        decision=ns.decision,
        rationale=ns.rationale,
        constraints=["No live trading", "No broker orders", "No deployment approval implied"],
        verification=verification,
        artifact_root=artifact_root,
    )
    apath = write_operator_attestation(attestation, artifact_root=artifact_root, overwrite=ns.overwrite)
    payload = {
        "ok": attestation.decision.value not in {"BLOCKED", "REJECTED"},
        "verification_path": str(vpath),
        "attestation_path": str(apath),
        "verification_status": verification.status.value,
        "attestation_decision": attestation.decision.value,
        "closure_id": attestation.closure_id,
        "warnings": sorted(set(verification.warnings + attestation.warnings)),
        "blockers": sorted(set(verification.blockers + attestation.blockers)),
        "no_live_trading": True,
        "no_broker_orders": True,
    }
    sys.stdout.write(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True) + "\n")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
