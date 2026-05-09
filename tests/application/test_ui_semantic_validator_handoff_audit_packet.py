from __future__ import annotations

from strategy_validator.application import ui_semantic_validator_handoff_audit_packet as audit_packet


def _continuity_payload(*, terminal_status: str = "AWAITING_EXTERNAL_CLOSURE_ATTESTATION", trust_banner: str = "TRUST_RESTRICTED") -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_continuity/v1",
        "search_root": "synthetic-test-root",
        "degraded": [],
        "continuity_rows": [
            {
                "continuity_id": "continuity-EXP-AUDIT-001",
                "experiment_id": "EXP-AUDIT-001",
                "chain_id": "chain-001",
                "chain_digest": "chain-digest-001",
                "terminal_status": terminal_status,
                "current_stage": "closure",
                "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION",
                "trust_banner": trust_banner,
                "open_action": terminal_status != "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION",
                "stage_count_expected": 5,
                "stage_count_present": 5,
                "ready_stage_count": 4 if terminal_status != "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION" else 5,
                "recommended_action": "CREATE_EXTERNAL_CLOSURE_ATTESTATION",
                "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"] if terminal_status != "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION" else [],
                "stage_path": [
                    {"stage": "decision", "record_id": "decision-1", "digest": "digest-decision", "ready": True},
                    {"stage": "signoff", "record_id": "signoff-1", "digest": "digest-signoff", "ready": True},
                    {"stage": "custody", "record_id": "custody-1", "digest": "digest-custody", "ready": True},
                    {"stage": "archive", "record_id": "archive-1", "digest": "digest-archive", "ready": True},
                    {"stage": "closure", "record_id": "closure-1", "digest": "digest-closure", "ready": terminal_status == "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION"},
                ],
                "continuity_route": "/ui/semantic-validator-handoff/continuity",
            }
        ],
    }


def _timeline_payload() -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_timeline/v1",
        "degraded": [],
        "timeline_events": [
            {
                "timeline_event_id": "event-closure",
                "continuity_id": "continuity-EXP-AUDIT-001",
                "experiment_id": "EXP-AUDIT-001",
                "chain_id": "chain-001",
                "stage": "closure",
                "stage_position": 5,
                "event_state": "AWAITING_EXTERNAL_ARTIFACT",
                "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
            }
        ],
    }


def _gaps_payload() -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_evidence_gaps/v1",
        "degraded": ["SEMANTIC_VALIDATOR_HANDOFF_EXTERNAL_ARTIFACT_GAP_PRESENT"],
        "gap_rows": [
            {
                "gap_id": "gap-closure",
                "continuity_id": "continuity-EXP-AUDIT-001",
                "experiment_id": "EXP-AUDIT-001",
                "chain_id": "chain-001",
                "gap_kind": "EXTERNAL_ARTIFACT_GAP",
                "gap_state": "AWAITING_EXTERNAL_ARTIFACT",
                "priority": "P1",
                "severity": "WARN",
                "blocking": False,
                "external_artifact_required": True,
                "operator_action": "CREATE_EXTERNAL_ARTIFACT_EXTERNALLY",
                "repair_route": "/ui/semantic-validator-handoff/closure",
                "issue_codes": ["EXTERNAL_CLOSURE_ATTESTATION_MISSING"],
            }
        ],
    }


def _exceptions_payload(*, blocked: bool = False) -> dict[str, object]:
    return {
        "schema_version": "ui_semantic_validator_handoff_exceptions/v1",
        "degraded": ["SEMANTIC_VALIDATOR_HANDOFF_EXCEPTIONS_BLOCKED_PRESENT"] if blocked else [],
        "exception_rows": [
            {
                "exception_id": "exception-blocked" if blocked else "exception-info",
                "continuity_id": "continuity-EXP-AUDIT-001",
                "experiment_id": "EXP-AUDIT-001",
                "chain_id": "chain-001",
                "exception_state": "BLOCKED" if blocked else "OPEN",
                "priority": "P0" if blocked else "P3",
                "severity": "HIGH" if blocked else "LOW",
                "blocked": blocked,
                "external_artifact_required": False,
                "operator_action": "RESOLVE_BLOCKING_EXCEPTION" if blocked else "RETAIN_AUDIT_NOTE",
                "next_route": "/ui/semantic-validator-handoff/exceptions",
                "issue_codes": ["BLOCKING_EXCEPTION"] if blocked else [],
            }
        ] if blocked else [],
    }


def _patch_sources(monkeypatch, *, continuity=None, gaps=None, exceptions=None, timeline=None) -> None:
    monkeypatch.setattr(audit_packet, "build_ui_semantic_validator_handoff_continuity_payload", lambda **_: continuity or _continuity_payload())
    monkeypatch.setattr(audit_packet, "build_ui_semantic_validator_handoff_evidence_gaps_payload", lambda **_: gaps or _gaps_payload())
    monkeypatch.setattr(audit_packet, "build_ui_semantic_validator_handoff_exceptions_payload", lambda **_: exceptions or _exceptions_payload())
    monkeypatch.setattr(audit_packet, "build_ui_semantic_validator_handoff_timeline_payload", lambda **_: timeline or _timeline_payload())


def test_audit_packet_rolls_external_evidence_gap_into_attention_packet(monkeypatch) -> None:
    _patch_sources(monkeypatch)

    payload = audit_packet.build_ui_semantic_validator_handoff_audit_packet_payload()

    assert payload["schema_version"] == "ui_semantic_validator_handoff_audit_packet/v1"
    assert payload["read_plane_only"] is True
    assert payload["packet_materialization_authority"] == "none_read_plane"
    assert payload["summary"]["audit_packet_count_total"] == 1
    assert payload["summary"]["external_artifact_required_count"] == 1
    assert payload["summary"]["validator_submission_allowed_count"] == 0
    row = payload["audit_packets"][0]
    assert row["packet_status"] == "AWAITING_EXTERNAL_ARTIFACT"
    assert row["packet_lane"] == "external_artifact"
    assert row["audit_ready"] is False
    assert row["external_artifact_required"] is True
    assert row["required_action_count"] == 1
    assert row["required_actions"][0]["route"] == "/ui/semantic-validator-handoff/closure"
    assert row["authority"]["validator_submission_allowed"] is False
    assert row["authority"]["execution_allowed"] is False


def test_audit_packet_blocks_on_open_exception(monkeypatch) -> None:
    _patch_sources(monkeypatch, exceptions=_exceptions_payload(blocked=True))

    payload = audit_packet.build_ui_semantic_validator_handoff_audit_packet_payload(
        packet_status=("OPEN_EXCEPTIONS_BLOCKING",),
        trust_banner=("UNTRUSTED",),
        operator_attention_required=True,
    )

    assert payload["summary"]["audit_packet_count_filtered"] == 1
    assert payload["summary"]["untrusted_count"] == 1
    row = payload["audit_packets"][0]
    assert row["packet_status"] == "OPEN_EXCEPTIONS_BLOCKING"
    assert row["trust_banner"] == "UNTRUSTED"
    assert row["blocking_exception_count"] == 1
    assert "UNTRUSTED_SEMANTIC_VALIDATOR_HANDOFF_AUDIT_PACKET_PRESENT" in payload["degraded"]


def test_audit_packet_marks_closed_chain_ready_when_no_gaps_or_exceptions(monkeypatch) -> None:
    _patch_sources(
        monkeypatch,
        continuity=_continuity_payload(terminal_status="CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION", trust_banner="TRUSTED"),
        gaps={"schema_version": "ui_semantic_validator_handoff_evidence_gaps/v1", "degraded": [], "gap_rows": []},
        exceptions={"schema_version": "ui_semantic_validator_handoff_exceptions/v1", "degraded": [], "exception_rows": []},
    )

    payload = audit_packet.build_ui_semantic_validator_handoff_audit_packet_payload(audit_ready=True)

    row = payload["audit_packets"][0]
    assert row["packet_status"] == "CLOSED_AUDIT_READY"
    assert row["audit_ready"] is True
    assert row["operator_attention_required"] is False
    assert row["trust_banner"] == "TRUSTED"
    assert payload["summary"]["audit_ready_count"] == 1
    assert row["required_actions"] == []
