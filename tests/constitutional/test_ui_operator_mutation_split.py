from __future__ import annotations

from pathlib import Path


def test_ui_views_no_longer_owns_operator_mutation_receipts() -> None:
    ui_views = Path('strategy_validator/application/ui_views.py').read_text(encoding='utf-8')
    operator_mutations = Path('strategy_validator/application/operator_mutations.py').read_text(encoding='utf-8')

    assert 'def build_ui_operator_command_receipt_payload(' not in ui_views
    assert 'def build_ui_operator_command_receipt_payload(' in operator_mutations
