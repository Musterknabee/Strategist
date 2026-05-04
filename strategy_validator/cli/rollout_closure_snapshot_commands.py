"""Bounded snapshot/attestation command registration and handlers."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.application_rollout_surfaces import (
    build_closure_release_attestation_payload,
    build_closure_snapshot_payload,
    build_governed_exception_memo_payload,
    generate_snapshot_signing_keypair_payload,
    render_decision_reconciliation_markdown_payload,
    render_final_release_signoff_markdown_payload,
    render_governed_exception_markdown_payload,
    verify_closure_snapshot_payload,
    verify_governed_exception_memo_payload,
)
from strategy_validator.cli.oracle_cli_common import parse_utc as common_parse_utc
from strategy_validator.cli.oracle_cli_common import write_json
from strategy_validator.contracts.operational import ClosureSnapshotManifest
from strategy_validator.contracts.operational import GovernedExceptionMemo


def _parse_utc(raw: str):
    return common_parse_utc(raw)


def cmd_snapshot_keypair(ns: argparse.Namespace) -> int:
    generate_snapshot_signing_keypair_payload(
        private_key_path=Path(ns.private_key),
        public_key_path=Path(ns.public_key),
    )
    payload = {"private_key": ns.private_key, "public_key": ns.public_key}
    sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0


def cmd_closure_snapshot(ns: argparse.Namespace) -> int:
    manifest, envelope = build_closure_snapshot_payload(
        closure_dir=Path(ns.closure_dir),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        fingerprint_path=Path(ns.fingerprint) if ns.fingerprint else None,
        bundle_path=Path(ns.bundle) if ns.bundle else None,
        checklist_path=Path(ns.checklist) if ns.checklist else None,
        review_path=Path(ns.review) if ns.review else None,
        allow_incomplete=ns.allow_incomplete,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    payload = manifest.model_dump(mode="json")
    snapshot_output = Path(ns.output) if ns.output else Path(ns.closure_dir) / "CLOSURE_SNAPSHOT.json"
    write_json(snapshot_output, payload)
    if envelope is not None:
        envelope_output = Path(ns.dsse_output) if ns.dsse_output else snapshot_output.with_suffix(".dsse.json")
        write_json(envelope_output, envelope.model_dump(mode="json"))
    return 0


def cmd_verify_closure_snapshot_payload(ns: argparse.Namespace) -> int:
    verification = verify_closure_snapshot_payload(
        snapshot_path=Path(ns.snapshot),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_governed_exception(ns: argparse.Namespace) -> int:
    snapshot_path = Path(ns.snapshot)
    memo, envelope = build_governed_exception_memo_payload(
        snapshot_path=snapshot_path,
        verification_path=Path(ns.verification),
        exception_code=ns.exception_code,
        requested_by=ns.requested_by,
        approved_by=ns.approved_by,
        valid_until_utc=_parse_utc(ns.valid_until),
        rationale=ns.rationale,
        constraints=list(ns.constraint or []),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        review_path=Path(ns.review) if ns.review else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    memo_output = Path(ns.output) if ns.output else snapshot_path.with_name("GOVERNED_EXCEPTION_MEMO.json")
    write_json(memo_output, memo.model_dump(mode="json"))
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else memo_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_governed_exception_memo_payload(
        memo_path=memo_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse_output) if ns.dsse_output else (memo_output.with_suffix(".dsse.json") if envelope is not None else None),
        public_key_path=Path(ns.public_key) if ns.public_key else None,
        review_path=Path(ns.review) if ns.review else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else memo_output.with_name("GOVERNED_EXCEPTION.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else memo_output.with_name("GOVERNED_EXCEPTION_MEMO.md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(
        render_governed_exception_markdown_payload(memo=memo, verification=verification),
        encoding="utf-8",
    )
    sys.stdout.write(json.dumps(memo.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_verify_governed_exception(ns: argparse.Namespace) -> int:
    verification = verify_governed_exception_memo_payload(
        memo_path=Path(ns.memo),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
        review_path=Path(ns.review) if ns.review else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_closure_attestation(ns: argparse.Namespace) -> int:
    snapshot_path = Path(ns.snapshot)
    repo_root = Path(ns.repo_root) if ns.repo_root else None
    verification = verify_closure_snapshot_payload(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else snapshot_path.with_name("CLOSURE_SNAPSHOT.verification.json")
    if not (ns.governed_exception and verification_output.exists()):
        write_json(verification_output, verification.model_dump(mode="json"))

    governed_memo = None
    governed_verification = None
    if ns.governed_exception:
        governed_verification = verify_governed_exception_memo_payload(
            memo_path=Path(ns.governed_exception),
            repo_root=repo_root,
            dsse_path=Path(ns.governed_exception_dsse) if ns.governed_exception_dsse else None,
            public_key_path=Path(ns.governed_exception_public_key) if ns.governed_exception_public_key else None,
            review_path=Path(ns.review) if ns.review else None,
        )
        governed_output = Path(ns.governed_exception_verification_output) if ns.governed_exception_verification_output else snapshot_path.with_name("GOVERNED_EXCEPTION.verification.json")
        write_json(governed_output, governed_verification.model_dump(mode="json"))
        governed_memo = GovernedExceptionMemo.model_validate(json.loads(Path(ns.governed_exception).read_text(encoding="utf-8")))

    attestation, verification = build_closure_release_attestation_payload(
        snapshot_path=snapshot_path,
        repo_root=repo_root,
        verification=verification,
        verification_path=verification_output,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
        review_path=Path(ns.review) if ns.review else None,
        governed_exception_memo=governed_memo,
        governed_exception_verification=governed_verification,
    )
    attestation_output = Path(ns.output) if ns.output else snapshot_path.with_name("ATTESTED_RELEASE_DECISION.json")
    write_json(attestation_output, attestation.model_dump(mode="json"))

    manifest = ClosureSnapshotManifest.model_validate(json.loads(snapshot_path.read_text(encoding="utf-8")))
    signoff_output = Path(ns.signoff_output) if ns.signoff_output else snapshot_path.with_name("FINAL_RELEASE_SIGNOFF.md")
    reconciliation_output = Path(ns.reconciliation_output) if ns.reconciliation_output else snapshot_path.with_name("DECISION_RECONCILIATION.md")
    signoff_output.parent.mkdir(parents=True, exist_ok=True)
    reconciliation_output.parent.mkdir(parents=True, exist_ok=True)
    signoff_output.write_text(
        render_final_release_signoff_markdown_payload(
            manifest=manifest,
            verification=verification,
            attestation=attestation,
        ),
        encoding="utf-8",
    )
    reconciliation_output.write_text(
        render_decision_reconciliation_markdown_payload(
            manifest=manifest,
            verification=verification,
            attestation=attestation,
        ),
        encoding="utf-8",
    )
    sys.stdout.write(json.dumps(attestation.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if attestation.signoff_status == "APPROVED" else 2


def register_rollout_closure_snapshot_commands(sub: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    sk = sub.add_parser("snapshot-keypair", help="Generate local Ed25519 signing keys for closure snapshots")
    sk.add_argument("--private-key", required=True, help="PEM output path for private key")
    sk.add_argument("--public-key", required=True, help="PEM output path for public key")
    sk.set_defaults(_run=cmd_snapshot_keypair)

    cs = sub.add_parser("closure-snapshot", help="Build a canonical closure snapshot manifest and optional DSSE envelope")
    cs.add_argument("--closure-dir", required=True, help="Directory containing canonical closure artifacts")
    cs.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    cs.add_argument("--fingerprint", default="", help="Optional override path for KEYED_HOST_FINGERPRINT.json")
    cs.add_argument("--bundle", default="", help="Optional override path for ROLLOUT_BUNDLE.json")
    cs.add_argument("--checklist", default="", help="Optional override path for DAILY_CHECKLIST.json")
    cs.add_argument("--review", default="", help="Optional override path for RUNTIME_REVIEW.json")
    cs.add_argument("--allow-incomplete", action="store_true", help="Allow manifest emission even when referenced burn-in artifacts are missing")
    cs.add_argument("--signing-private-key", default="", help="Optional Ed25519 private key PEM for DSSE signing")
    cs.add_argument("--output", default="", help="Write snapshot JSON artifact path")
    cs.add_argument("--dsse-output", default="", help="Write DSSE envelope JSON artifact path")
    cs.set_defaults(_run=cmd_closure_snapshot)

    vs = sub.add_parser("verify-closure-snapshot", help="Verify closure snapshot digests and optional DSSE signature")
    vs.add_argument("snapshot", help="Closure snapshot manifest JSON path")
    vs.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    vs.add_argument("--dsse", default="", help="Optional DSSE envelope JSON path")
    vs.add_argument("--public-key", default="", help="Optional Ed25519 public key PEM")
    vs.add_argument("--output", default="", help="Write verification JSON artifact path")
    vs.set_defaults(_run=cmd_verify_closure_snapshot_payload)

    ge = sub.add_parser("governed-exception", help="Create a signed governed exception memo for verified environmental nonconformance")
    ge.add_argument("--snapshot", required=True, help="Verified closure snapshot JSON path")
    ge.add_argument("--verification", required=True, help="Closure snapshot verification JSON path")
    ge.add_argument("--exception-code", required=True, help="Governed exception code from the machine attestation")
    ge.add_argument("--requested-by", required=True, help="Human operator requesting the exception")
    ge.add_argument("--approved-by", required=True, help="Named release authority approving the exception")
    ge.add_argument("--valid-until", required=True, help="UTC timestamp when the exception expires (ISO-8601)")
    ge.add_argument("--rationale", required=True, help="Operator rationale for the exception")
    ge.add_argument("--constraint", action="append", default=[], help="Additional constraint (repeatable)")
    ge.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    ge.add_argument("--review", default="", help="Optional override path for RUNTIME_REVIEW.json")
    ge.add_argument("--signing-private-key", default="", help="Optional Ed25519 private key PEM for DSSE signing")
    ge.add_argument("--public-key", default="", help="Optional Ed25519 public key PEM used to verify the memo immediately")
    ge.add_argument("--output", default="", help="Write memo JSON artifact path")
    ge.add_argument("--dsse-output", default="", help="Write DSSE envelope JSON artifact path")
    ge.add_argument("--verification-output", default="", help="Write governed exception verification JSON path")
    ge.add_argument("--markdown-output", default="", help="Write governed exception memo markdown path")
    ge.set_defaults(_run=cmd_governed_exception)

    vg = sub.add_parser("verify-governed-exception", help="Verify a governed exception memo and optional DSSE signature")
    vg.add_argument("memo", help="Governed exception memo JSON path")
    vg.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    vg.add_argument("--dsse", default="", help="Optional governed exception DSSE envelope JSON path")
    vg.add_argument("--public-key", default="", help="Optional Ed25519 public key PEM")
    vg.add_argument("--review", default="", help="Optional override path for RUNTIME_REVIEW.json")
    vg.add_argument("--output", default="", help="Write governed exception verification JSON path")
    vg.set_defaults(_run=cmd_verify_governed_exception)

    ca = sub.add_parser("closure-attestation", help="Derive signoff documents and attestation JSON from a verified closure snapshot")
    ca.add_argument("snapshot", help="Closure snapshot manifest JSON path")
    ca.add_argument("--repo-root", default="", help="Optional repository root used for artifact path resolution")
    ca.add_argument("--review", default="", help="Optional override path for RUNTIME_REVIEW.json")
    ca.add_argument("--dsse", default="", help="Optional closure snapshot DSSE envelope JSON path")
    ca.add_argument("--public-key", default="", help="Optional closure snapshot Ed25519 public key PEM")
    ca.add_argument("--governed-exception", default="", help="Optional governed exception memo JSON path")
    ca.add_argument("--governed-exception-dsse", default="", help="Optional governed exception DSSE envelope JSON path")
    ca.add_argument("--governed-exception-public-key", default="", help="Optional governed exception Ed25519 public key PEM")
    ca.add_argument("--verification-output", default="", help="Write closure verification JSON artifact path")
    ca.add_argument("--governed-exception-verification-output", default="", help="Write governed exception verification JSON artifact path")
    ca.add_argument("--output", default="", help="Write release attestation JSON artifact path")
    ca.add_argument("--signoff-output", default="", help="Write FINAL_RELEASE_SIGNOFF.md path")
    ca.add_argument("--reconciliation-output", default="", help="Write DECISION_RECONCILIATION.md path")
    ca.set_defaults(_run=cmd_closure_attestation)
