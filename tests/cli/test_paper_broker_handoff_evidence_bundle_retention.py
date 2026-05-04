from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import write_paper_execution_evidence_bundle_retention_handoff_artifact
from strategy_validator.cli.paper_broker import main
from tests.application.test_paper_execution_evidence_bundle_retention_handoff import _setup_signoff_verification


def test_cli_handoff_evidence_bundle_retention_writes_artifact(capsys, tmp_path: Path) -> None:
    output_root, latest_signoff_verification_path = _setup_signoff_verification(tmp_path)

    rc = main([
        "handoff-evidence-bundle-retention",
        "--retention-signoff-verification-artifact",
        str(latest_signoff_verification_path),
        "--custodian-id",
        "archive-vault",
        "--handoff-note",
        "custody transfer approved",
        "--output-root",
        str(output_root),
    ])

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["ok"] is True
    assert out["handoff_status"] == "READY_FOR_HANDOFF"
    assert out["custodian_id"] == "archive-vault"
    assert Path(out["artifact"]).exists()


def test_cli_handoff_evidence_bundle_retention_returns_blocked_for_missing(capsys, tmp_path: Path) -> None:
    rc = main(["handoff-evidence-bundle-retention", "--output-root", str(tmp_path / "paper_broker")])

    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["ok"] is False
    assert out["handoff_status"] == "BLOCKED"
    assert out["blockers"]
