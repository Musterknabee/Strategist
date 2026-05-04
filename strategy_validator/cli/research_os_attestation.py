"""Research OS closure verification and operator attestation CLI.

Evidence/read-plane only: no live trading, no broker orders, no deployment approval.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.research_os_attestation_ops import (
    build_operator_attestation,
    build_ui_research_os_attestation_latest_payload,
    load_latest_attestation,
    load_latest_verification,
    verify_research_os_closure_manifest,
    write_operator_attestation,
    write_research_os_closure_verification,
)
from strategy_validator.contracts.research_os_attestation import ResearchOsOperatorDecision


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    sys.stdout.write(json.dumps(payload, indent=2 if as_json else None, sort_keys=True) + "\n")


def _artifact_root(raw: str) -> Path | None:
    return Path(raw) if raw else None


def _manifest_path(raw: str) -> Path | None:
    return Path(raw) if raw else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_verify = sub.add_parser("verify", help="Verify latest or specified Research OS closure manifest")
    p_verify.add_argument("--verification-id", default="research-os-closure-verification")
    p_verify.add_argument("--manifest-path", default="")
    p_verify.add_argument("--artifact-root", default="")
    p_verify.add_argument("--write", action="store_true")
    p_verify.add_argument("--overwrite", action="store_true")
    p_verify.add_argument("--json", action="store_true")

    p_attest = sub.add_parser("attest", help="Write operator attestation for verified closure evidence")
    p_attest.add_argument("--attestation-id", default="research-os-operator-attestation")
    p_attest.add_argument("--operator-id", required=True)
    p_attest.add_argument(
        "--decision",
        choices=[x.value for x in ResearchOsOperatorDecision],
        default=ResearchOsOperatorDecision.ACKNOWLEDGED.value,
    )
    p_attest.add_argument("--rationale", default="")
    p_attest.add_argument("--constraint", action="append", default=[])
    p_attest.add_argument("--manifest-path", default="")
    p_attest.add_argument("--artifact-root", default="")
    p_attest.add_argument("--overwrite", action="store_true")
    p_attest.add_argument("--json", action="store_true")

    p_latest = sub.add_parser("latest", help="Show latest closure verification/attestation read-plane payload")
    p_latest.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "verify":
            artifact_root = _artifact_root(ns.artifact_root)
            result = verify_research_os_closure_manifest(
                verification_id=ns.verification_id,
                manifest_path=_manifest_path(ns.manifest_path),
                artifact_root=artifact_root,
            )
            out_path: str | None = None
            if ns.write:
                out_path = str(write_research_os_closure_verification(result, artifact_root=artifact_root, overwrite=ns.overwrite))
            _emit(
                {
                    "ok": result.status.value == "VERIFIED",
                    "status": result.status.value,
                    "trust_banner": result.trust_banner.value,
                    "closure_id": result.closure_id,
                    "manifest_path": result.manifest_path,
                    "artifact_count": len(result.artifact_checks),
                    "digest_mismatches": result.digest_mismatches,
                    "missing_artifacts": result.missing_artifacts,
                    "warnings": result.warnings,
                    "blockers": result.blockers,
                    "result_sha256": result.result_sha256,
                    "written_path": out_path,
                    "no_live_trading": True,
                    "no_broker_orders": True,
                },
                as_json=ns.json,
            )
            return 0 if result.status.value == "VERIFIED" else 1
        if ns.cmd == "attest":
            artifact_root = _artifact_root(ns.artifact_root)
            verification = verify_research_os_closure_manifest(
                verification_id=f"{ns.attestation_id}-verification",
                manifest_path=_manifest_path(ns.manifest_path),
                artifact_root=artifact_root,
            )
            vpath = write_research_os_closure_verification(verification, artifact_root=artifact_root, overwrite=True)
            attestation = build_operator_attestation(
                attestation_id=ns.attestation_id,
                operator_id=ns.operator_id,
                decision=ns.decision,
                rationale=ns.rationale,
                constraints=ns.constraint,
                verification=verification,
                artifact_root=artifact_root,
            )
            apath = write_operator_attestation(attestation, artifact_root=artifact_root, overwrite=ns.overwrite)
            _emit(
                {
                    "ok": attestation.decision.value not in {"BLOCKED", "REJECTED"},
                    "attestation_path": str(apath),
                    "verification_path": str(vpath),
                    "attestation_id": attestation.attestation_id,
                    "closure_id": attestation.closure_id,
                    "decision": attestation.decision.value,
                    "verification_status": attestation.verification_status.value,
                    "closure_trust_banner": attestation.closure_trust_banner.value,
                    "warnings": attestation.warnings,
                    "blockers": attestation.blockers,
                    "attestation_sha256": attestation.attestation_sha256,
                    "no_live_trading": True,
                    "no_broker_orders": True,
                },
                as_json=ns.json,
            )
            return 0 if attestation.decision.value not in {"BLOCKED", "REJECTED"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_attestation_latest_payload(), as_json=ns.json)
            return 0
    except Exception as e:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
