from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_evidence_index_console_script_registered() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'strategy-validator-evidence-index = "strategy_validator.cli.evidence_bundle_index:main"' in text


def test_evidence_index_doc_disclaimers_present() -> None:
    text = (ROOT / "docs/operator/EVIDENCE_BUNDLE_INDEX.md").read_text(encoding="utf-8")
    assert "not deployment approval" in text.lower()
    assert "not operator signoff" in text.lower()
    assert "not live trading authorization" in text.lower()
    assert "not profitability evidence" in text.lower()
