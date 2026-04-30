from __future__ import annotations

from pathlib import Path


def test_no_legacy_top_level_ledger_package() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    assert not (repo_root / 'ledger').exists(), 'Use strategy_validator/ledger as the only canonical ledger package.'
