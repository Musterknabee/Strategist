from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.contracts import operational as operational_contracts
from strategy_validator.contracts import oracle as oracle_contracts
from strategy_validator.validator.oracle_event_log import query_oracle_event_log
from strategy_validator.validator.oracle_schema_registry import list_artifact_schema_registrations


def _declared_schema_versions(module: object) -> set[str]:
    values: set[str] = set()
    for name in dir(module):
        attr = getattr(module, name)
        model_fields = getattr(attr, "model_fields", None)
        if not model_fields or "schema_version" not in model_fields:
            continue
        default = model_fields["schema_version"].default
        if isinstance(default, str):
            values.add(default)
    return values


@pytest.mark.constitutional
def test_schema_registry_covers_declared_contract_schemas() -> None:
    registered = {item.schema_version for item in list_artifact_schema_registrations()}
    declared = _declared_schema_versions(oracle_contracts) | _declared_schema_versions(operational_contracts)
    assert declared <= registered


@pytest.mark.constitutional
def test_query_rejects_unsupported_checkpoint_schema(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "ORACLE_DERIVED_VIEW.checkpoint.metadata.json"
    checkpoint_path.write_text(json.dumps({
        "schema_version": "oracle_derived_view_checkpoint_metadata/v999",
        "lane_id": "ORACLE_EVENT_LOG",
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported schema_version"):
        query_oracle_event_log(
            lane_path=tmp_path / "ORACLE_EVENT_LOG.jsonl",
            checkpoint_metadata_path=checkpoint_path,
        )
