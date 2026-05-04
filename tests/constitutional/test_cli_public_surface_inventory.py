from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.public_surface import build_cli_public_surface_inventory


def test_cli_public_surface_inventory_exposes_compatibility_and_runtime_counts() -> None:
    inventory = build_cli_public_surface_inventory(Path('.').resolve())
    payload = inventory.to_payload()

    assert payload['schema_version'] == 'cli_public_surface_inventory/v1'
    assert payload['cli_file_count'] >= payload['command_file_count'] > 0
    assert payload['compatibility_file_count'] == len(payload['compatibility_files'])
    assert payload['runtime_command_file_count'] == len(payload['runtime_command_files'])
    assert 'compatibility_files=' in payload['summary_line']
