from __future__ import annotations

from strategy_validator.application.ui_views import build_ui_burnin_payload


def test_build_ui_burnin_payload_includes_deep_dive_metrics() -> None:
    payload = build_ui_burnin_payload()

    assert payload['schema_version'] == 'ui_burnin_dashboard/v1'
    metrics = payload['metrics']
    assert 'dsrPbo' in metrics
    assert 'pathStability' in metrics
    assert 'realismConstraints' in metrics
    assert 'forensicSummary' in metrics

    assert metrics['dsrPbo']['promotionPosture'] in {'PROMOTION_ELIGIBLE', 'REVIEW_REQUIRED'}
    assert metrics['dsrPbo']['overfitRisk'] in {'CONTROLLED', 'ELEVATED'}
    assert len(metrics['pathStability']) >= 1
    assert len(metrics['realismConstraints']) >= 1
    assert isinstance(metrics['forensicSummary']['forensic_notes'], list)

    assert 'metricProvenance' in metrics
    assert 'cpcvCoverage' in metrics['metricProvenance']
    assert metrics['metricProvenance']['providerPaths']['source_label'] == 'configured ingress providers'
