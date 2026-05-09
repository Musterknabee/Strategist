from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_semantic_validator_handoff_signoff_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_signoff.py")

    assert len(source.splitlines()) <= 100
    assert "def build_ui_semantic_validator_handoff_signoff_payload(" not in source
    assert "def _normalize_signoff(" not in source
    assert "def _signoff_row(" not in source
    assert "ui_semantic_validator_handoff_signoff_common" in source
    assert "ui_semantic_validator_handoff_signoff_artifacts" in source
    assert "ui_semantic_validator_handoff_signoff_rows" in source
    assert "ui_semantic_validator_handoff_signoff_payload" in source


def test_semantic_validator_handoff_signoff_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_signoff_common.py")
    artifacts = _function_names("ui_semantic_validator_handoff_signoff_artifacts.py")
    rows = _function_names("ui_semantic_validator_handoff_signoff_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_signoff_payload.py")

    assert {
        "_utc_now",
        "_s",
        "_norm",
        "_as_list",
        "_norm_set",
        "_contains",
        "_counts",
        "_digest",
        "_sha256",
        "_read_json",
        "_placeholder",
        "_packet_digest",
        "_authority_assertion_true",
        "_signoff_value",
        "_authority",
    } <= common
    assert artifacts == {"_is_signoff_candidate", "_normalize_signoff", "_signoff_artifacts"}
    assert rows == {
        "_match_signoffs",
        "_signoff_status",
        "_signoff_template",
        "_issue_codes",
        "_signoff_row",
        "_haystack",
        "_matches",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_signoff_payload",
        "build_ui_semantic_validator_handoff_signoff_latest_payload",
    }


def test_semantic_validator_handoff_signoff_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_signoff as facade
    from strategy_validator.application import ui_semantic_validator_handoff_signoff_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_semantic_validator_handoff_signoff_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_signoff import (
        _haystack,
        _is_signoff_candidate,
        _issue_codes,
        _match_signoffs,
        _matches,
        _normalize_signoff,
        _signoff_artifacts,
        _signoff_row,
        _signoff_status,
        _signoff_template,
    )

    assert callable(_is_signoff_candidate)
    assert callable(_normalize_signoff)
    assert callable(_signoff_artifacts)
    assert callable(_match_signoffs)
    assert callable(_signoff_status)
    assert callable(_signoff_template)
    assert callable(_issue_codes)
    assert callable(_signoff_row)
    assert callable(_haystack)
    assert callable(_matches)


def test_semantic_validator_handoff_signoff_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_signoff as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_decision_payload",
        lambda **_: {
            "schema_version": "synthetic-decision/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "summary": {"decision_count_total": 1, "ready_decision_count": 1},
            "decisions": [
                {
                    "decision_id": "decision-1",
                    "decision_status": "READY_FOR_OPERATOR_DECISION_DRAFT",
                    "decision_ready": True,
                    "decision_blocker_codes": [],
                    "review_id": "review-1",
                    "chain_id": "chain-1",
                    "chain_digest": "chain-digest-1",
                    "experiment_id": "EXP-SIGNOFF",
                    "trust_banner": "TRUST_RESTRICTED",
                    "decision_packet": {
                        "packet_digest": "packet-digest-1",
                        "source_evidence": {"decision_id": "decision-1"},
                    },
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_signoff_payload(issue_contains="missing")

    assert payload["source_schema_version"] == "synthetic-decision/v1"
    assert payload["search_root"] == "synthetic-root"
    assert payload["summary"]["signoff_gate_count_returned"] == 1
    assert payload["summary"]["awaiting_signoff_count"] == 1
    row = payload["signoffs"][0]
    assert row["signoff_status"] == "AWAITING_OPERATOR_SIGNOFF"
    assert row["signoff_template"]["human_reviewer_id"] == "<REQUIRED_EXTERNALLY>"
    assert row["validator_submission_allowed"] is False
    assert payload["signoff_write_authority"] == "none_read_plane"
    assert payload["validator_submission_authority"] == "none_read_plane"
