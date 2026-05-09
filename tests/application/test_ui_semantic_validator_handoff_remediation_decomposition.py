from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_remediation_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_remediation.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_remediation_payload(" not in source
    assert "def _build_remediation_record(" not in source
    assert "def _issue_step(" not in source
    assert "ui_semantic_validator_handoff_remediation_common" in source
    assert "ui_semantic_validator_handoff_remediation_rows" in source
    assert "ui_semantic_validator_handoff_remediation_payload" in source


def test_semantic_validator_handoff_remediation_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_remediation_common.py")
    rows = _function_names("ui_semantic_validator_handoff_remediation_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_remediation_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_as_list",
        "_norm_set",
        "_contains",
        "_counts",
        "_link_digest",
        "_authority",
    } <= common
    assert rows == {
        "_step_template",
        "_issue_step",
        "_max_severity",
        "_missing_components",
        "_component_labels_for_missing",
        "_broken_link_codes",
        "_remediation_status",
        "_priority_score",
        "_chain_haystack",
        "_build_remediation_record",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_remediation_payload",
        "build_ui_semantic_validator_handoff_remediation_latest_payload",
    }


def test_semantic_validator_handoff_remediation_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_remediation as facade
    from strategy_validator.application import ui_semantic_validator_handoff_remediation_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_remediation_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_remediation import (
        _broken_link_codes,
        _build_remediation_record,
        _chain_haystack,
        _issue_step,
        _matches,
        _max_severity,
        _missing_components,
        _priority_score,
        _remediation_status,
        _step_template,
    )

    assert callable(_step_template)
    assert callable(_issue_step)
    assert callable(_max_severity)
    assert callable(_missing_components)
    assert callable(_broken_link_codes)
    assert callable(_remediation_status)
    assert callable(_priority_score)
    assert callable(_chain_haystack)
    assert callable(_build_remediation_record)
    assert callable(_matches)


def test_semantic_validator_handoff_remediation_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_remediation as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_lineage_payload",
        lambda **_: {
            "schema_version": "synthetic-lineage/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {
                "chain_count_total": 1,
                "ready_chain_count": 0,
                "broken_chain_count": 1,
                "incomplete_chain_count": 0,
            },
            "chains": [
                {
                    "chain_id": "chain-1",
                    "chain_digest": "digest-1",
                    "experiment_id": "EXP-REMEDIATE",
                    "status": "BROKEN",
                    "ready_for_operator_review": False,
                    "ready_for_validator_ingress": False,
                    "issue_codes": ["PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH"],
                    "warning_codes": [],
                    "component_blocker_codes": [],
                    "component_issue_codes": [],
                    "link_checks": [],
                    "components": {},
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_remediation_payload(issue_contains="checksum")

    assert payload["source_schema_version"] == "synthetic-lineage/v1"
    assert payload["summary"]["remediation_count_returned"] == 1
    assert payload["summary"]["action_required_count"] == 1
    row = payload["remediations"][0]
    assert row["remediation_status"] == "EVIDENCE_REPAIR_REQUIRED"
    assert row["severity"] == "CRITICAL"
    assert row["recommended_action"] == "EXECUTE_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_BEFORE_REVIEW"
    assert payload["mutation_authority"] == "none_read_plane"
    assert payload["validator_submission_authority"] == "none_read_plane"
