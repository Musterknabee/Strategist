from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.ui_promotion_review import build_ui_promotion_review_payload


def _write_packet(root: Path, tracking_id: str, *, strategy_id: str, recommendation: str, state: str, blockers: list[str] | None = None, warnings: list[str] | None = None) -> None:
    path = root / tracking_id / "promotion_review_packet.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "promotion_review_packet/v1",
        "packet_id": f"prp-{tracking_id}",
        "tracking_id": tracking_id,
        "strategy_id": strategy_id,
        "batch_id": "batch-1",
        "run_id": "run-1",
        "generated_at_utc": "2026-05-05T10:00:00+00:00",
        "candidate_lifecycle_state": state,
        "gauntlet_summary": {"promotion_eligible_at_enrollment": True},
        "paper_tracking_summary": {"days_of_signals": 31, "cumulative_paper_return": 0.08, "kill_state": "CLEAR"},
        "kill_rule_summary": {"posture": "NONE", "triggered": []},
        "execution_realism_summary": {"decay_level": "NONE"},
        "robustness_summary": {},
        "portfolio_correlation_summary": {"gate": "UNIQUE", "warnings": []},
        "provider_data_summary": {"status": "NOT_APPLICABLE"},
        "known_risks": ["Paper research evidence only"],
        "blockers": blockers or [],
        "warnings": warnings or [],
        "evidence_refs": [{"ref_kind": "paper_tracking_manifest", "artifact_path": "manifest.json", "sha256": "abc"}],
        "checklist": {
            "has_manifest": True,
            "has_scorecard": True,
            "has_lifecycle_assessment": True,
            "has_gauntlet_scorecard_ref": True,
            "has_evidence_manifest_ref": True,
        },
        "recommendation": {"recommendation": recommendation, "rationale": f"{recommendation} rationale"},
        "packet_sha256": f"sha-{tracking_id}",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_promotion_review_projection_indexes_packets_and_counts(tmp_path: Path) -> None:
    root = tmp_path / "paper_tracking"
    _write_packet(root, "trk-ready", strategy_id="alpha", recommendation="READY_FOR_HUMAN_REVIEW", state="PROMOTION_REVIEW_READY")
    _write_packet(root, "trk-blocked", strategy_id="beta", recommendation="DO_NOT_PROMOTE", state="REJECTED", blockers=["SYNTHETIC_DEMO_DO_NOT_PROMOTE"])
    (root / "bad" / "promotion_review_packet.json").parent.mkdir(parents=True)
    (root / "bad" / "promotion_review_packet.json").write_text("{bad json", encoding="utf-8")

    payload = build_ui_promotion_review_payload(paper_tracking_root=root)

    assert payload["schema_version"] == "ui_promotion_review/v1"
    assert payload["read_plane_only"] is True
    assert payload["promotion_authority"] == "none_read_plane_human_review_only"
    assert payload["summary"]["packet_count_total"] == 2
    assert payload["summary"]["invalid_artifact_count"] == 1
    assert payload["summary"]["ready_for_human_review_count"] == 1
    assert payload["summary"]["do_not_promote_count"] == 1
    assert payload["summary"]["blocked_packet_count"] == 1
    assert payload["recommendation_counts"]["READY_FOR_HUMAN_REVIEW"] == 1
    assert payload["recommendation_counts"]["DO_NOT_PROMOTE"] == 1
    assert payload["latest"]["tracking_id"] in {"trk-ready", "trk-blocked"}
    assert any("Human review only" in line for line in payload["guardrails"])


def test_promotion_review_projection_filters_issue_and_blocker(tmp_path: Path) -> None:
    root = tmp_path / "paper_tracking"
    _write_packet(root, "trk-ready", strategy_id="alpha-mean-reversion", recommendation="READY_FOR_HUMAN_REVIEW", state="PROMOTION_REVIEW_READY")
    _write_packet(root, "trk-blocked", strategy_id="beta-breakout", recommendation="DO_NOT_PROMOTE", state="REJECTED", blockers=["SYNTHETIC_DEMO_DO_NOT_PROMOTE"])

    payload = build_ui_promotion_review_payload(
        paper_tracking_root=root,
        recommendation=("DO_NOT_PROMOTE",),
        issue_contains="synthetic",
        require_blockers=True,
    )

    assert payload["summary"]["packet_count_filtered"] == 1
    assert payload["summary"]["packet_count_returned"] == 1
    assert payload["packets"][0]["tracking_id"] == "trk-blocked"
    assert payload["packets"][0]["blocker_count"] == 1
    assert payload["filters"]["recommendation"] == ["DO_NOT_PROMOTE"]
