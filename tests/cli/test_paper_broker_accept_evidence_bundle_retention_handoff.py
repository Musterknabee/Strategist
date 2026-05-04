from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_handoff_acceptance import _setup_handoff_verification


def test_cli_accept_evidence_bundle_retention_handoff_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_handoff_verification_path = _setup_handoff_verification(tmp_path)

    rc = main([
        "accept-evidence-bundle-retention-handoff",
        "--retention-handoff-verification-artifact",
        str(latest_handoff_verification_path),
        "--accepting-custodian-id",
        "archive-desk",
        "--custody-location",
        "vault-a",
        "--output-root",
        str(output_root),
    ])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["acceptance_status"] == "ACCEPTED_FOR_CUSTODY"
    assert out["retention_handoff_verification_artifact_hash_valid"] is True
    assert Path(out["artifact"]).exists()


def test_cli_accept_evidence_bundle_retention_handoff_returns_blocked_for_missing(capsys, tmp_path: Path) -> None:
    rc = main(["accept-evidence-bundle-retention-handoff", "--output-root", str(tmp_path / "paper_broker")])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["acceptance_status"] == "BLOCKED"
    assert out["blockers"]
