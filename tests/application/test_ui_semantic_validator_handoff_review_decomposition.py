from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_review_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_review.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_review_payload(" not in source
    assert "def _review_row(" not in source
    assert "def _review_checklist(" not in source
    assert "ui_semantic_validator_handoff_review_common" in source
    assert "ui_semantic_validator_handoff_review_rows" in source
    assert "ui_semantic_validator_handoff_review_payload" in source


def test_semantic_validator_handoff_review_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_review_common.py")
    rows = _function_names("ui_semantic_validator_handoff_review_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_review_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_as_list",
        "_norm_set",
        "_contains",
        "_counts",
        "_digest",
        "_authority",
    } <= common
    assert rows == {
        "_component_paths",
        "_check_status",
        "_review_checklist",
        "_review_status",
        "_trust_banner",
        "_review_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_review_payload",
        "build_ui_semantic_validator_handoff_review_latest_payload",
    }


def test_semantic_validator_handoff_review_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_review as facade
    from strategy_validator.application import ui_semantic_validator_handoff_review_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_review_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_review import (
        _check_status,
        _component_paths,
        _haystack,
        _matches,
        _review_checklist,
        _review_row,
        _review_status,
        _trust_banner,
    )

    assert callable(_component_paths)
    assert callable(_check_status)
    assert callable(_review_checklist)
    assert callable(_review_status)
    assert callable(_trust_banner)
    assert callable(_review_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_review_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_review as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_remediation_payload",
        lambda **_: {
            "schema_version": "synthetic-remediation/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"remediation_count_total": 1, "action_required_count": 0},
            "remediations": [
                {
                    "remediation_id": "remediation-1",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest-1",
                    "experiment_id": "EXP-REVIEW",
                    "chain_status": "READY",
                    "remediation_status": "READY_NO_ACTION",
                    "severity": "NONE",
                    "operator_action_required": False,
                    "issue_codes": [],
                    "component_blocker_codes": [],
                    "component_issue_codes": [],
                    "broken_link_codes": [],
                    "missing_components": [],
                    "remediation_steps": [],
                    "remediation_step_count": 0,
                    "ready_for_validator_ingress": True,
                    "validator_ingress_blocked": False,
                    "components": {
                        "decision_ledger": {
                            "artifact_id": "decision-ledger-1",
                            "payload_checksum": "ledger-checksum",
                            "artifact_sha256": "ledger-sha",
                            "artifact_path": "decision_ledger.json",
                            "verified": True,
                            "handoff_allowed": True,
                        },
                        "handoff_certificate": {
                            "artifact_id": "handoff-certificate-1",
                            "payload_checksum": "certificate-checksum",
                            "artifact_sha256": "certificate-sha",
                            "artifact_path": "handoff_certificate.json",
                            "verified": True,
                            "handoff_allowed": True,
                        },
                        "validator_packet": {
                            "artifact_id": "validator-packet-1",
                            "payload_checksum": "packet-checksum",
                            "artifact_sha256": "packet-sha",
                            "artifact_path": "validator_packet.json",
                            "verified": True,
                            "handoff_allowed": True,
                        },
                        "ingress_certificate": {
                            "artifact_id": "ingress-certificate-1",
                            "payload_checksum": "ingress-checksum",
                            "artifact_sha256": "ingress-sha",
                            "artifact_path": "ingress_certificate.json",
                            "verified": True,
                            "handoff_allowed": True,
                            "ready_for_validator_ingress": True,
                        },
                    },
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_review_payload(issue_contains="component_chain_complete")

    assert payload["source_schema_version"] == "synthetic-remediation/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["review_count_returned"] == 1
    assert payload["summary"]["ready_for_operator_review_count"] == 1
    row = payload["reviews"][0]
    assert row["review_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert row["trust_banner"] == "TRUSTED"
    assert row["operator_review_allowed"] is True
    assert row["validator_submission_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["execution_allowed"] is False
    assert row["review_pass_count"] == row["review_check_count"]
    assert payload["validator_submission_authority"] == "none_read_plane"
