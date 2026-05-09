from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_release_capsule,
    build_semantic_adjudication_release_decision_record,
)
from strategy_validator.application.ui_semantic_release import build_ui_semantic_release_handoff_payload
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _release_chain(experiment_id: str = "EXP-UI-SEMANTIC-001"):
    proposal = build_strategy_proposal(
        experiment_id=experiment_id,
        strategy_name="UiSemanticReleaseSmoke",
        proposer_id="projection-test",
        evaluation_time_utc=datetime(2026, 5, 6, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
    )
    bundle = build_semantic_adjudication_bundle(proposal, require_gate_artifact=False)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    index = build_semantic_adjudication_bundle_release_index(bundle, manifest=manifest, proposal=proposal)
    capsule = build_semantic_adjudication_release_capsule(index, bundle=bundle, manifest=manifest, proposal=proposal)
    decision = build_semantic_adjudication_release_decision_record(
        capsule,
        decision="ACCEPT_FOR_ADJUDICATION",
        decided_by="projection-test",
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=True,
    )
    return index, capsule, decision


def test_ui_semantic_release_handoff_indexes_release_chain(tmp_path: Path) -> None:
    index, capsule, decision = _release_chain()
    _write_json(tmp_path / "index" / "semantic_release_index.json", index.model_dump(mode="json"))
    _write_json(tmp_path / "capsule" / "semantic_release_capsule.json", capsule.model_dump(mode="json"))
    _write_json(tmp_path / "decision" / "semantic_release_decision_record.json", decision.model_dump(mode="json"))

    payload = build_ui_semantic_release_handoff_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_release_handoff/v1"
    assert payload["read_plane_only"] is True
    assert payload["adjudication_authority"] == "none_read_plane"
    assert payload["summary"]["artifact_count_total"] == 3
    assert payload["summary"]["release_index_count"] == 1
    assert payload["summary"]["release_capsule_count"] == 1
    assert payload["summary"]["decision_record_count"] == 1
    assert payload["summary"]["decision_allowed_count"] == 1
    assert payload["artifact_kind_counts"] == {"decision_record": 1, "release_capsule": 1, "release_index": 1}
    assert any(entry["artifact_kind"] == "decision_record" and entry["decision_allowed"] for entry in payload["artifacts"])
    assert "no_adjudication_or_validator_authority" in payload["guardrails"]


def test_ui_semantic_release_handoff_filters_and_surfaces_checksum_failures(tmp_path: Path) -> None:
    index, capsule, decision = _release_chain("EXP-UI-SEMANTIC-BAD")
    bad_index = index.model_dump(mode="json")
    bad_index["payload_checksum"] = "0" * 64
    _write_json(tmp_path / "bad" / "semantic_release_index.json", bad_index)
    _write_json(tmp_path / "good" / "semantic_release_capsule.json", capsule.model_dump(mode="json"))
    _write_json(tmp_path / "good" / "semantic_release_decision_record.json", decision.model_dump(mode="json"))
    (tmp_path / "bad" / "semantic_release_broken.json").write_text("{", encoding="utf-8")

    payload = build_ui_semantic_release_handoff_payload(
        search_root=tmp_path,
        artifact_kind=("release_index",),
        verified=False,
        require_blockers=True,
        issue_contains="CHECKSUM",
    )

    assert payload["summary"]["artifact_count_total"] == 3
    assert payload["summary"]["artifact_count_filtered"] == 1
    assert payload["summary"]["artifact_count_returned"] == 1
    assert payload["summary"]["invalid_artifact_count"] == 1
    assert payload["artifacts"][0]["artifact_kind"] == "release_index"
    assert payload["artifacts"][0]["verified"] is False
    assert "SEMANTIC_RELEASE_INDEX_CHECKSUM_MISMATCH" in payload["artifacts"][0]["issue_codes"]
    assert "INVALID_SEMANTIC_RELEASE_ARTIFACTS_PRESENT" in payload["degraded"]
    assert "SEMANTIC_RELEASE_SELF_VERIFICATION_FAILURES_PRESENT" in payload["degraded"]
