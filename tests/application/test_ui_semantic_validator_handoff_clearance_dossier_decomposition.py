from __future__ import annotations

import ast
from pathlib import Path

APP = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (APP / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_clearance_dossier_facade_remains_thin() -> None:
    source = _source("ui_semantic_validator_handoff_clearance_dossier.py")

    assert len(source.splitlines()) <= 90
    assert "def build_ui_semantic_validator_handoff_clearance_dossier_payload(" not in source
    assert "def _dossier_from_gate(" not in source
    assert "def _matches(" not in source
    assert "ui_semantic_validator_handoff_clearance_dossier_common" in source
    assert "ui_semantic_validator_handoff_clearance_dossier_rows" in source
    assert "ui_semantic_validator_handoff_clearance_dossier_payload" in source


def test_clearance_dossier_subphase_ownership() -> None:
    common = _function_names("ui_semantic_validator_handoff_clearance_dossier_common.py")
    rows = _function_names("ui_semantic_validator_handoff_clearance_dossier_rows.py")
    payload = _function_names("ui_semantic_validator_handoff_clearance_dossier_payload.py")

    assert {"_utc_now", "_s", "_norm", "_as_list", "_norm_set", "_contains", "_digest", "_counts", "_authority"} <= common
    assert rows == {
        "_review_posture",
        "_operator_brief",
        "_review_checks",
        "_dossier_from_gate",
        "_sort_dossier",
        "_haystack",
        "_matches",
        "_degraded",
    }
    assert payload == {
        "_source_builder",
        "build_ui_semantic_validator_handoff_clearance_dossier_payload",
        "build_ui_semantic_validator_handoff_clearance_dossier_latest_payload",
    }


def test_clearance_dossier_facade_exports_public_builders() -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_dossier as facade
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_dossier_payload as payload

    assert facade.__all__ == payload.__all__
    for name in facade.__all__:
        assert getattr(facade, name) is getattr(payload, name)


def test_clearance_dossier_legacy_private_imports_remain_available() -> None:
    from strategy_validator.application.ui_semantic_validator_handoff_clearance_dossier import (
        _dossier_from_gate,
        _matches,
        _review_checks,
        _review_posture,
        _sort_dossier,
    )

    assert callable(_review_posture)
    assert callable(_review_checks)
    assert callable(_dossier_from_gate)
    assert callable(_sort_dossier)
    assert callable(_matches)


def test_clearance_dossier_facade_source_monkeypatch_surface_is_preserved(monkeypatch) -> None:
    from strategy_validator.application import ui_semantic_validator_handoff_clearance_dossier as facade

    monkeypatch.setattr(
        facade,
        "build_ui_semantic_validator_handoff_clearance_gate_payload",
        lambda **_: {
            "schema_version": "synthetic-clearance-gate/v1",
            "search_root": "synthetic-root",
            "degraded": [],
            "clearance_gates": [
                {
                    "clearance_gate_id": "gate-monkeypatch",
                    "clearance_status": "WAITING_EXTERNAL_ARTIFACT",
                    "scope_key": "EXP-MONKEY",
                    "experiment_id": "EXP-MONKEY",
                    "priority": "P1",
                    "severity": "WARN",
                    "trust_banner": "TRUST_RESTRICTED",
                    "owner_hint": "human_operator_clearance_owner",
                    "handoff_clearance_blocked": True,
                    "candidate_for_operator_clearance_review": False,
                    "requires_external_artifact": True,
                    "requires_human_review": True,
                    "source_resolution_step_count": 1,
                    "issue_codes": ["EXTERNAL_ARTIFACT_REQUIRED"],
                    "phase_set": ["EXTERNAL_ARTIFACT_COLLECTION"],
                    "clearance_condition": "Collect external artifact.",
                    "safe_instruction": "Do not approve.",
                    "source_route": "/ui/semantic-validator-handoff/clearance-gate",
                    "resolution_plan_route": "/ui/semantic-validator-handoff/resolution-plan",
                    "clearance_route": "/ui/semantic-validator-handoff/clearance-gate",
                }
            ],
        },
    )

    payload = facade.build_ui_semantic_validator_handoff_clearance_dossier_payload()

    assert payload["source_schema_version"] == "synthetic-clearance-gate/v1"
    assert payload["summary"]["clearance_dossier_count_returned"] == 1
    assert payload["clearance_dossiers"][0]["review_posture"] == "WAITING_EXTERNAL_ARTIFACT"
    assert payload["clearance_dossiers"][0]["external_artifact_write_authority"] == "none_read_plane"
