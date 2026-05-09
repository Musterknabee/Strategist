from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_lineage_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_lineage.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_lineage_payload(" not in source
    assert "def _build_chains(" not in source
    assert "def _chain_entry(" not in source
    assert "ui_semantic_validator_handoff_lineage_common" in source
    assert "ui_semantic_validator_handoff_lineage_rows" in source
    assert "ui_semantic_validator_handoff_lineage_payload" in source


def test_semantic_validator_handoff_lineage_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_lineage_common.py")
    rows = _function_names("ui_semantic_validator_handoff_lineage_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_lineage_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_contains",
        "_as_list",
        "_norm_set",
        "_counts",
        "_entry_ref",
        "_component_id",
        "_find_first",
        "_find_first_by_any",
        "_link_digest",
        "_authority",
    } <= common
    assert rows == {
        "_link_check",
        "_select_chain_from_anchor",
        "_chain_entry",
        "_chain_key",
        "_build_chains",
        "_issue_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_lineage_payload",
        "build_ui_semantic_validator_handoff_lineage_latest_payload",
    }


def test_semantic_validator_handoff_lineage_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_lineage as facade
    from strategy_validator.application import ui_semantic_validator_handoff_lineage_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_lineage_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_lineage import (
        _build_chains,
        _chain_entry,
        _chain_key,
        _entry_ref,
        _issue_haystack,
        _link_check,
        _matches,
        _select_chain_from_anchor,
    )

    assert callable(_entry_ref)
    assert callable(_link_check)
    assert callable(_select_chain_from_anchor)
    assert callable(_chain_entry)
    assert callable(_chain_key)
    assert callable(_build_chains)
    assert callable(_issue_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_lineage_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_lineage as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_payload",
        lambda **_: {
            "schema_version": "synthetic-handoff/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"artifact_count_total": 4, "invalid_artifact_count": 0},
            "artifacts": [
                {
                    "artifact_kind": "decision_ledger",
                    "artifact_id": "ledger-artifact",
                    "experiment_id": "EXP-LINEAGE",
                    "ledger_id": "ledger-1",
                    "payload_checksum": "ledger-checksum",
                    "artifact_sha256": "ledger-sha",
                    "verified": True,
                    "handoff_allowed": True,
                },
                {
                    "artifact_kind": "handoff_certificate",
                    "artifact_id": "certificate-artifact",
                    "experiment_id": "EXP-LINEAGE",
                    "ledger_id": "ledger-1",
                    "certificate_id": "certificate-1",
                    "ledger_payload_checksum": "ledger-checksum",
                    "payload_checksum": "certificate-checksum",
                    "artifact_sha256": "certificate-sha",
                    "verified": True,
                    "handoff_allowed": True,
                },
                {
                    "artifact_kind": "validator_packet",
                    "artifact_id": "packet-artifact",
                    "experiment_id": "EXP-LINEAGE",
                    "certificate_id": "certificate-1",
                    "packet_id": "packet-1",
                    "certificate_payload_checksum": "certificate-checksum",
                    "payload_checksum": "packet-checksum",
                    "artifact_sha256": "packet-sha",
                    "verified": True,
                    "handoff_allowed": True,
                },
                {
                    "artifact_kind": "ingress_certificate",
                    "artifact_id": "ingress-artifact",
                    "experiment_id": "EXP-LINEAGE",
                    "packet_id": "packet-1",
                    "certificate_id": "ingress-1",
                    "packet_payload_checksum": "packet-checksum",
                    "payload_checksum": "ingress-checksum",
                    "artifact_sha256": "ingress-sha",
                    "verified": True,
                    "handoff_allowed": True,
                    "ready_for_validator_ingress": True,
                },
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_lineage_payload()

    assert payload["source_schema_version"] == "synthetic-handoff/v1"
    assert payload["summary"]["chain_count_returned"] == 1
    assert payload["chains"][0]["status"] == "READY"
    assert payload["chains"][0]["ready_for_operator_review"] is True
    assert payload["mutation_authority"] == "none_read_plane"
    assert payload["validator_submission_authority"] == "none_read_plane"
