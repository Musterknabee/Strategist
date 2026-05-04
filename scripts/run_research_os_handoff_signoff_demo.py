#!/usr/bin/env python3
"""Build demo Research OS handoff verification and reviewer signoff artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_handoff_signoff_ops import (
    build_and_write_research_os_handoff_reviewer_signoff,
    build_and_write_research_os_handoff_verification_result,
)
from strategy_validator.contracts.research_os_handoff_signoff import ResearchOsHandoffReviewerDecision


def main() -> int:
    p = argparse.ArgumentParser(description="Run Research OS handoff signoff demo")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--verification-id", default="handoff-signoff-demo-verification")
    p.add_argument("--signoff-id", default="handoff-signoff-demo")
    p.add_argument("--reviewer-id", default="local-reviewer")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    root = Path(args.artifact_root)
    verification, verification_path = build_and_write_research_os_handoff_verification_result(
        verification_id=args.verification_id,
        artifact_root=root,
        overwrite=bool(args.overwrite),
    )
    signoff, signoff_path = build_and_write_research_os_handoff_reviewer_signoff(
        signoff_id=args.signoff_id,
        reviewer_id=args.reviewer_id,
        decision=ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS,
        rationale="Demo reviewer signoff for single-tenant handoff review; not deployment approval.",
        constraints=["Demo signoff is restricted to paper-only release review."],
        artifact_root=root,
        overwrite=bool(args.overwrite),
    )
    payload = {
        "ok": signoff.decision.value != "BLOCKED",
        "verification_status": verification.status.value,
        "signoff_decision": signoff.decision.value,
        "source_handoff_id": verification.source_handoff_id,
        "verification_path": str(verification_path),
        "signoff_path": str(signoff_path),
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        print(payload, flush=True)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
