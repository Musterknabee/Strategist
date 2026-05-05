from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.repository_truth_check import run_repository_truth_check
from scripts.sample_secret_hygiene import (
    collect_sample_secret_hygiene_violations,
    scan_private_key_material,
    scan_sample_env_text,
)


def test_deployment_env_sample_has_required_contract_names() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "deployment.env.sample").read_text(encoding="utf-8")
    assert "STRATEGY_VALIDATOR_MODE=PRODUCTION" in text
    assert "STRATEGY_VALIDATOR_API_TOKEN=CHANGEME" in text
    assert (
        "STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read" in text
    )
    assert "STRATEGY_VALIDATOR_LEDGER_DB_PATH" in text
    assert "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR" in text
    assert "STRATEGY_VALIDATOR_ARTIFACT_ROOT" in text


def test_deployment_env_sample_passes_secret_hygiene_scan() -> None:
    root = Path(__file__).resolve().parents[2]
    assert collect_sample_secret_hygiene_violations(root) == ()


def test_gitignore_protects_private_env_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    lines = (root / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "deployment.env" in lines
    assert ".env" in lines
    assert any(line.strip() == ".keys/" for line in lines)


@pytest.mark.parametrize(
    ("sample_text", "expect_substring"),
    [
        (
            "# ALPACA_API_KEY=PK7DRQ3SHAR4MPKCRIFQ7Z7WAE\n",
            "Alpaca-style API key",
        ),
        (
            "# ALPACA_API_SECRET=EJK8tuY9Ahh39W6F3uHfcYaDBQBQdinJmTRKhtvWdBwg\n",
            "provider secret",
        ),
        (
            "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890\n",
            "opaque API token",
        ),
        (
            "STRATEGY_VALIDATOR_RESEARCH_API_TOKEN=ResearchAbcdefghijklmnopqrstuvwxyz123456\n",
            "opaque API token",
        ),
    ],
)
def test_scan_sample_env_text_flags_plausible_alpaca_material(sample_text: str, expect_substring: str) -> None:
    violations = scan_sample_env_text(sample_text, label="fixture")
    assert violations, "expected at least one violation"
    assert any(expect_substring in item for item in violations)


def test_scan_private_key_material_flags_embedded_pem() -> None:
    pem = "".join(
        (
            bytes.fromhex(
                "2d2d2d2d2d424547494e205253412050524956415445204b45592d2d2d2d2d",
            ).decode("ascii"),
            "\nMII\n",
        )
    )
    violations = scan_private_key_material(pem, label="fixture")
    assert violations and "RSA" in violations[0]


def test_collect_hygiene_scans_docs_markdown(tmp_path: Path) -> None:
    (tmp_path / "deployment.env.sample").write_text(
        "STRATEGY_VALIDATOR_API_TOKEN=CHANGEME__NOT_A_REAL_TOKEN__PLACEHOLDER\n",
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "snippet.md").write_text(
        "STRATEGY_VALIDATOR_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890\n",
        encoding="utf-8",
    )
    violations = collect_sample_secret_hygiene_violations(tmp_path)
    assert violations
    assert any("snippet.md" in v and "opaque API token" in v for v in violations)


def test_collect_hygiene_scans_scripts_python(tmp_path: Path) -> None:
    (tmp_path / "deployment.env.sample").write_text(
        "STRATEGY_VALIDATOR_API_TOKEN=CHANGEME__NOT_A_REAL_TOKEN__PLACEHOLDER\n",
        encoding="utf-8",
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "example_env_snippet.py").write_text(
        '# Demo only:\n# ALPACA_API_SECRET=EJK8tuY9Ahh39W6F3uHfcYaDBQBQdinJmTRKhtvWdBwg\n',
        encoding="utf-8",
    )
    violations = collect_sample_secret_hygiene_violations(tmp_path)
    assert violations
    assert any("example_env_snippet.py" in v and "provider secret" in v for v in violations)


def test_repository_truth_includes_sample_secret_hygiene_gate() -> None:
    root = Path(__file__).resolve().parents[2]
    report = run_repository_truth_check(root)
    names = {check.name for check in report.checks}
    assert "sample_secret_hygiene" in names
    secret_check = next(c for c in report.checks if c.name == "sample_secret_hygiene")
    assert secret_check.status == "PASS"


def test_repository_truth_payload_records_sample_secret_hygiene() -> None:
    root = Path(__file__).resolve().parents[2]
    report = run_repository_truth_check(root)
    payload = report.to_payload()
    encoded = json.dumps(payload)
    assert "sample_secret_hygiene" in encoded
