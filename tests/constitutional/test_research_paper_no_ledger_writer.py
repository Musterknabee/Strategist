"""Research and paper paths must not import the ledger writer directly (authority boundary)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _py_files_under(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _assert_no_ledger_writer_reference(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    if "ledger.writer" in text or "ledger_writer" in lower:
        raise AssertionError(f"Forbidden ledger writer reference in {path.relative_to(ROOT)}")


def test_research_tree_has_no_ledger_writer_imports() -> None:
    for p in _py_files_under(ROOT / "strategy_validator" / "research"):
        _assert_no_ledger_writer_reference(p)


def test_paper_tracking_application_modules_have_no_ledger_writer_imports() -> None:
    root = ROOT / "strategy_validator" / "application"
    files = sorted(root.glob("paper_tracking*.py"))
    assert files
    for p in files:
        _assert_no_ledger_writer_reference(p)


def test_broker_packages_have_no_ledger_writer_imports() -> None:
    for p in _py_files_under(ROOT / "strategy_validator" / "brokers"):
        _assert_no_ledger_writer_reference(p)
