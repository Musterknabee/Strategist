from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from strategy_validator.application import (
    canonicalize_temporal_semantic_batch_with_openbb_payload,
    fetch_openbb_temporal_sensor_inputs_payload,
)
from strategy_validator.contracts.oracle import OracleSensorRawSemanticInput
from strategy_validator.contracts.oracle_temporal import TemporalSemanticBatchManifest, TemporalSemanticDay
from strategy_validator.validator.oracle_openbb_ingress import fetch_openbb_temporal_sensor_inputs
from strategy_validator.validator.providers.openbb_provider import OpenBBMarketDataProvider


class _StubOpenBBProvider(OpenBBMarketDataProvider):
    def __init__(self) -> None:
        super().__init__(
            'openbb:test',
            mode='http',
            base_url='https://example.invalid',
            oracle_macro_url_template='/macro/{point_in_time_date}/{universe_label}',
            oracle_microstructure_url_template='/micro/{point_in_time_date}/{universe_label}',
        )

    def _get_json(self, url: str):  # type: ignore[override]
        if '/macro/' in url:
            if '2026-01-06' in url:
                return None
            return {
                'yield_curve_slope_bps': -22.5,
                'high_yield_credit_spread_bps': 405.0,
                'equity_bond_correlation_20d': -0.15,
                'cross_asset_correlation_20d': 0.30,
                'realized_volatility_20d': 0.19,
                'realized_volatility_252d': 0.17,
            }
        if '/micro/' in url:
            return {
                'buy_volume': 1200.0,
                'sell_volume': 900.0,
                'median_spread_bps': 7.0,
                'baseline_spread_bps': 5.0,
                'top_book_depth_usd': 1_500_000.0,
                'baseline_top_book_depth_usd': 2_000_000.0,
                'toxic_flow_ratio': 0.22,
            }
        raise AssertionError(url)


@pytest.mark.constitutional
def test_fetch_openbb_temporal_sensor_inputs_returns_maps_and_missing_day_report() -> None:
    provider = _StubOpenBBProvider()
    d1 = date(2026, 1, 5)
    d2 = date(2026, 1, 6)
    macro_by_date, micro_by_date, report = fetch_openbb_temporal_sensor_inputs(
        [d1, d2],
        provider=provider,
        universe_label='US_EQ',
    )

    assert sorted(macro_by_date) == [d1]
    assert sorted(micro_by_date) == [d1, d2]
    assert report.hydrated_dates == [d1]
    assert report.missing_macro_dates == [d2]
    assert report.missing_microstructure_dates == []
    assert report.results[1].notes == ['macro_raw missing from OpenBB ingress']


@pytest.mark.constitutional
def test_openbb_application_surfaces_fetch_and_canonicalize(tmp_path: Path) -> None:
    provider = _StubOpenBBProvider()
    pt_date = date(2026, 1, 5)
    manifest = TemporalSemanticBatchManifest(
        provider_kind='NVIDIA_NIM',
        provider_id='nim-1',
        model_name='minimaxai/minimax-m2.7',
        batch_start_date=pt_date,
        batch_end_date=pt_date,
        days=[
            TemporalSemanticDay(
                point_in_time_date=pt_date,
                trading_session_id='XNYS:2026-01-05',
                semantic_raw=OracleSensorRawSemanticInput(
                    hawkish_document_ratio=0.40,
                    dovish_document_ratio=0.20,
                    geopolitical_headline_share=0.15,
                    contradiction_count=1,
                    belief_conflict_score=0.10,
                ),
                allowed_prefix_digest_sha256='prefix-1',
                provider_response_sha256='resp-1',
                citations=[],
            )
        ],
    )

    ingress_payload = fetch_openbb_temporal_sensor_inputs_payload([pt_date], provider=provider, universe_label='US_EQ')
    assert ingress_payload['macro_by_date'][pt_date.isoformat()]['yield_curve_slope_bps'] == -22.5
    assert ingress_payload['ingress_report']['hydrated_dates'] == [pt_date.isoformat()]

    payload = canonicalize_temporal_semantic_batch_with_openbb_payload(
        manifest,
        provider=provider,
        universe_label='US_EQ',
        output_root=tmp_path / 'docs' / 'artifacts' / 'oracle_temporal',
        repo_root=tmp_path,
    )
    canonicalization = payload['canonicalization']
    assert payload['ingress_report']['hydrated_dates'] == [pt_date.isoformat()]
    assert canonicalization['verification_status'] == 'VERIFIED'
    assert canonicalization['canonicalized_dates'] == [pt_date.isoformat()]


@pytest.mark.constitutional
def test_fetch_openbb_temporal_sensor_inputs_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from strategy_validator.cli.oracle_temporal_runners import cmd_fetch_openbb_temporal_sensor_inputs

    provider = _StubOpenBBProvider()
    monkeypatch.setattr(
        'strategy_validator.cli.oracle_temporal_runners.build_openbb_market_data_provider',
        lambda cfg: provider,
    )

    dates_path = tmp_path / 'dates.json'
    output_path = tmp_path / 'ingress.json'
    dates_path.write_text(json.dumps(['2026-01-05', '2026-01-06']), encoding='utf-8')

    class NS:
        dates = str(dates_path)
        universe_label = 'US_EQ'
        config = ''
        output = str(output_path)

    rc = cmd_fetch_openbb_temporal_sensor_inputs(NS())
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['ingress_report']['hydrated_dates'] == ['2026-01-05']
    assert payload['microstructure_by_date']['2026-01-06']['median_spread_bps'] == 7.0
