from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from strategy_validator.contracts import operational as operational_contracts
from strategy_validator.contracts import oracle as oracle_contracts
from strategy_validator.contracts import oracle_temporal as temporal_contracts
from strategy_validator.contracts.oracle import (
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
    OracleSensorRawSemanticInput,
)
from strategy_validator.contracts.oracle_temporal import (
    TemporalEvidenceRef,
    TemporalSemanticBatchManifest,
    TemporalSemanticDay,
)
from strategy_validator.core.config import (
    AppConfig,
    NvidiaNimConnectorSettings,
    OpenBBMarketDataConnectorSettings,
    RuntimePolicy,
)
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.validator.operator_checks import (
    validate_nvidia_nim_connector,
    validate_openbb_market_data_connector,
)
from strategy_validator.validator.oracle_schema_registry import list_artifact_schema_registrations
from strategy_validator.validator.oracle_temporal_materialization import materialize_temporal_semantic_sensor_inputs
from strategy_validator.validator.oracle_temporal_verification import verify_temporal_semantic_batch_manifest
from strategy_validator.validator.providers.factory import (
    build_nvidia_nim_semantic_provider,
    build_openbb_market_data_provider,
)


def _declared_schema_versions(module: object) -> set[str]:
    values: set[str] = set()
    for name in dir(module):
        attr = getattr(module, name)
        model_fields = getattr(attr, "model_fields", None)
        if not model_fields or "schema_version" not in model_fields:
            continue
        default = model_fields["schema_version"].default
        if isinstance(default, str):
            values.add(default)
    return values


@pytest.mark.constitutional
def test_temporal_schema_registry_covers_declared_temporal_contract_schemas() -> None:
    registered = {item.schema_version for item in list_artifact_schema_registrations()}
    declared = (
        _declared_schema_versions(oracle_contracts)
        | _declared_schema_versions(operational_contracts)
        | _declared_schema_versions(temporal_contracts)
    )
    assert declared <= registered


@pytest.mark.constitutional
def test_factory_builds_openbb_and_nvidia_nim_when_enabled() -> None:
    cfg = AppConfig(
        mode=RuntimeMode.DEV,
        runtime_policy=RuntimePolicy(),
        market_data_openbb_connector=OpenBBMarketDataConnectorSettings(
            enabled=True,
            provider_id="openbb-http",
            mode="http",
            base_url="https://openbb.internal",
            liquidity_url_template="/liquidity/{asset_id}",
        ),
        semantic_nvidia_nim_connector=NvidiaNimConnectorSettings(enabled=True, provider_id="nim-1"),
    )
    openbb = build_openbb_market_data_provider(cfg)
    nim = build_nvidia_nim_semantic_provider(cfg)
    assert openbb is not None and openbb.provider_id == "openbb-http"
    assert nim is not None and nim.provider_id == "nim-1"


@pytest.mark.constitutional
def test_operator_checks_flag_missing_openbb_and_nim_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENBB_TEST_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_NIM_TEST_KEY", raising=False)
    cfg = AppConfig(
        mode=RuntimeMode.DEV,
        runtime_policy=RuntimePolicy(),
        market_data_openbb_connector=OpenBBMarketDataConnectorSettings(
            enabled=True,
            mode="http",
            base_url="https://openbb.internal",
            api_key_env_var="OPENBB_TEST_KEY",
        ),
        semantic_nvidia_nim_connector=NvidiaNimConnectorSettings(
            enabled=True,
            api_key_env="NVIDIA_NIM_TEST_KEY",
        ),
    )
    openbb_codes = {code for code, _ in validate_openbb_market_data_connector(cfg)}
    nim_codes = {code for code, _ in validate_nvidia_nim_connector(cfg)}
    assert "OPENBB_SECRET_MISSING" in openbb_codes
    assert "NVIDIA_NIM_CREDENTIALS_MISSING" in nim_codes


@pytest.mark.constitutional
def test_temporal_verification_rejects_future_citation_and_materializes_daily_inputs() -> None:
    day_one = TemporalSemanticDay(
        point_in_time_date=date(2026, 1, 5),
        trading_session_id="XNYS:2026-01-05",
        semantic_raw=OracleSensorRawSemanticInput(
            hawkish_document_ratio=0.4,
            dovish_document_ratio=0.2,
            geopolitical_headline_share=0.1,
            contradiction_count=1,
            belief_conflict_score=0.25,
        ),
        allowed_prefix_digest_sha256="abc123",
        provider_response_sha256="resp-1",
        citations=[
            TemporalEvidenceRef(
                source_id="doc-1",
                source_timestamp_utc=datetime(2026, 1, 5, 12, tzinfo=timezone.utc),
                exact_quote="same-day evidence",
            )
        ],
    )
    day_two = TemporalSemanticDay(
        point_in_time_date=date(2026, 1, 6),
        trading_session_id="XNYS:2026-01-06",
        semantic_raw=OracleSensorRawSemanticInput(
            hawkish_document_ratio=0.3,
            dovish_document_ratio=0.3,
            geopolitical_headline_share=0.2,
            contradiction_count=0,
            belief_conflict_score=0.1,
        ),
        allowed_prefix_digest_sha256="def456",
        provider_response_sha256="resp-2",
        citations=[
            TemporalEvidenceRef(
                source_id="doc-2",
                source_timestamp_utc=datetime(2026, 1, 7, 0, 0, 1, tzinfo=timezone.utc),
                exact_quote="future evidence",
            )
        ],
    )
    manifest = TemporalSemanticBatchManifest(
        provider_kind="NVIDIA_NIM",
        provider_id="nim-1",
        model_name="minimaxai/minimax-m2.7",
        batch_start_date=date(2026, 1, 5),
        batch_end_date=date(2026, 1, 6),
        days=[day_one, day_two],
    )
    verification = verify_temporal_semantic_batch_manifest(
        manifest,
        expected_dates=[date(2026, 1, 5), date(2026, 1, 6)],
        allowed_prefix_digests_by_date={date(2026, 1, 5): "abc123", date(2026, 1, 6): "def456"},
    )
    assert verification.status == "REJECTED"
    assert any(f.code == "CITATION_AFTER_CUTOFF" for f in verification.findings)

    payloads = materialize_temporal_semantic_sensor_inputs(
        TemporalSemanticBatchManifest(
            provider_kind="NVIDIA_NIM",
            provider_id="nim-1",
            model_name="minimaxai/minimax-m2.7",
            batch_start_date=date(2026, 1, 5),
            batch_end_date=date(2026, 1, 5),
            days=[day_one],
        ),
        universe_label="US_EQ",
        macro_by_date={date(2026, 1, 5): OracleSensorRawMacroInput(
            yield_curve_slope_bps=-20.0,
            high_yield_credit_spread_bps=410.0,
            equity_bond_correlation_20d=-0.3,
            cross_asset_correlation_20d=0.4,
            realized_volatility_20d=0.22,
            realized_volatility_252d=0.18,
        )},
        microstructure_by_date={date(2026, 1, 5): OracleSensorRawMicrostructureInput(
            buy_volume=1_000.0,
            sell_volume=900.0,
            median_spread_bps=8.0,
            baseline_spread_bps=6.0,
            top_book_depth_usd=1_200_000.0,
            baseline_top_book_depth_usd=1_500_000.0,
            toxic_flow_ratio=0.3,
        )},
    )
    assert len(payloads) == 1
    assert payloads[0].semantic_raw.hawkish_document_ratio == 0.4
