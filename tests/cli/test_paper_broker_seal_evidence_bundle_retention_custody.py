from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_custody_seal import _setup_custody_register_verification


def test_cli_seal_evidence_bundle_retention_custody_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_register_verification_path = _setup_custody_register_verification(tmp_path)

    rc = main([
        "seal-evidence-bundle-retention-custody",
        "--retention-custody-register-verification-artifact",
        str(latest_register_verification_path),
        "--sealed-by",
        "operator-jp",
        "--custody-location",
        "vault-a",
        "--output-root",
        str(output_root),
    ])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["seal_status"] == "SEALED"
    assert out["retention_custody_register_verification_artifact_hash_valid"] is True
    assert Path(out["artifact"]).exists()


def test_cli_seal_evidence_bundle_retention_custody_returns_blocked_for_missing(capsys, tmp_path: Path) -> None:
    rc = main(["seal-evidence-bundle-retention-custody", "--output-root", str(tmp_path / "paper_broker")])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["seal_status"] == "BLOCKED"
    assert out["blockers"]
