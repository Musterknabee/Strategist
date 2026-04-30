from __future__ import annotations

from strategy_validator.application.ui_views import build_ui_evidence_payload, build_ui_tribunal_payload


def test_build_ui_tribunal_payload_includes_doctrine_stats_and_provenance() -> None:
    payload = build_ui_tribunal_payload()

    assert payload['schema_version'] == 'ui_tribunal_workspace/v1'
    assert payload['doctrine_stats']['active_doctrine_count'] >= 1
    assert 'section_provenance' in payload
    assert payload['section_provenance']['thesis_graph']['projection_family'] == 'tribunal'
    assert payload['blindness']['quantitative_payloads_present'] is False


def test_build_ui_evidence_payload_includes_section_provenance() -> None:
    payload = build_ui_evidence_payload()

    assert payload['schema_version'] == 'ui_evidence_dashboard/v1'
    assert 'section_provenance' in payload
    assert payload['section_provenance']['registry']['verification_label']
    assert payload['section_provenance']['lineage']['projection_family'] == 'evidence'
