"""CLI for Research OS handoff verification and reviewer signoff."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_handoff_signoff_ops import (
    build_and_write_research_os_handoff_reviewer_signoff,
    build_and_write_research_os_handoff_verification_result,
    build_research_os_handoff_reviewer_signoff,
    build_research_os_handoff_verification_result,
    load_latest_research_os_handoff_reviewer_signoff,
    load_latest_research_os_handoff_verification_result,
)
from strategy_validator.contracts.research_os_handoff_signoff import ResearchOsHandoffReviewerDecision


def _print(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str), flush=True)
    else:
        print(payload, flush=True)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--json", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Research OS handoff packs and record reviewer signoff.")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="Verify latest handoff pack and source artifact digests")
    _add_common(verify)
    verify.add_argument("--verification-id", default="research-os-handoff-verification")
    verify.add_argument("--write", action="store_true")
    verify.add_argument("--overwrite", action="store_true")

    signoff = sub.add_parser("signoff", help="Record reviewer signoff using latest handoff verification")
    _add_common(signoff)
    signoff.add_argument("--signoff-id", default="research-os-handoff-reviewer-signoff")
    signoff.add_argument("--reviewer-id", default="local-reviewer")
    signoff.add_argument("--decision", choices=[x.value for x in ResearchOsHandoffReviewerDecision], default=ResearchOsHandoffReviewerDecision.ACCEPTED_WITH_RESTRICTIONS.value)
    signoff.add_argument("--rationale", default="Single-tenant handoff evidence reviewed; not deployment approval.")
    signoff.add_argument("--constraint", action="append", default=[])
    signoff.add_argument("--overwrite", action="store_true")

    latest = sub.add_parser("latest", help="Read latest handoff verification and reviewer signoff")
    _add_common(latest)

    args = parser.parse_args(argv)
    artifact_root = Path(args.artifact_root)

    if args.command == "verify":
        if args.write:
            result, path = build_and_write_research_os_handoff_verification_result(
                verification_id=args.verification_id,
                artifact_root=artifact_root,
                overwrite=bool(args.overwrite),
            )
            payload = result.model_dump(mode="json")
            payload["artifact_path"] = str(path)
        else:
            result = build_research_os_handoff_verification_result(verification_id=args.verification_id, artifact_root=artifact_root)
            payload = result.model_dump(mode="json")
        _print(payload, as_json=bool(args.json))
        return 0 if payload.get("status") in {"VERIFIED", "STALE"} else 2

    if args.command == "signoff":
        signoff_obj, path = build_and_write_research_os_handoff_reviewer_signoff(
            signoff_id=args.signoff_id,
            reviewer_id=args.reviewer_id,
            decision=ResearchOsHandoffReviewerDecision(args.decision),
            rationale=args.rationale,
            constraints=list(args.constraint or []),
            artifact_root=artifact_root,
            overwrite=bool(args.overwrite),
        )
        payload = signoff_obj.model_dump(mode="json")
        payload["artifact_path"] = str(path)
        _print(payload, as_json=bool(args.json))
        return 0 if payload.get("decision") not in {"BLOCKED"} else 2

    if args.command == "latest":
        verification = load_latest_research_os_handoff_verification_result(artifact_root=artifact_root)
        signoff_obj = load_latest_research_os_handoff_reviewer_signoff(artifact_root=artifact_root)
        payload = {
            "ok": verification is not None or signoff_obj is not None,
            "verification": verification.model_dump(mode="json") if verification is not None else None,
            "signoff": signoff_obj.model_dump(mode="json") if signoff_obj is not None else None,
        }
        _print(payload, as_json=bool(args.json))
        return 0 if payload["ok"] else 1

    parser.error("unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
