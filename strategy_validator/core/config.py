from __future__ import annotations
import os
from pathlib import Path
from collections.abc import MutableSequence
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from strategy_validator.contracts.market_data import SourceMode, VendorOutageCircuitPolicy
from strategy_validator.core.enums import RuntimeMode, PromotionState, EvidenceType
from strategy_validator.core.provider_url_policy import validate_provider_url, validate_provider_url_template



_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}
_FALSEY_ENV_VALUES = {"0", "false", "no", "off"}


def _record_invalid_env_override(errors: MutableSequence[str] | None, name: str, raw: str, expected: str) -> None:
    if errors is not None:
        errors.append(f"{name}={raw!r} expected {expected}")


def _env_bool_checked(name: str, default: bool, errors: MutableSequence[str] | None = None) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUTHY_ENV_VALUES:
        return True
    if normalized in _FALSEY_ENV_VALUES:
        return False
    _record_invalid_env_override(errors, name, raw, "one of 1/0,true/false,yes/no,on/off")
    return default


def _env_int_checked(name: str, default: int, errors: MutableSequence[str] | None = None) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        _record_invalid_env_override(errors, name, raw, "an integer")
        return default


def _env_float_checked(name: str, default: float, errors: MutableSequence[str] | None = None) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        _record_invalid_env_override(errors, name, raw, "a number")
        return default


def _env_literal_checked(
    name: str,
    default: str,
    allowed: set[str],
    errors: MutableSequence[str] | None = None,
    *,
    normalize_upper: bool = True,
) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().upper() if normalize_upper else raw.strip().lower()
    if normalized in allowed:
        return normalized
    _record_invalid_env_override(errors, name, raw, "one of " + ",".join(sorted(allowed)))
    return default


def _env_provider_url_checked(
    name: str,
    default: str | None,
    errors: MutableSequence[str] | None = None,
    *,
    field_name: str,
    allow_local: bool = False,
) -> str | None:
    raw = os.environ.get(name)
    if raw is None:
        return default
    candidate = raw.strip()
    if not candidate:
        return None
    try:
        return validate_provider_url(candidate, allow_local=allow_local, field_name=field_name)
    except ValueError as exc:
        _record_invalid_env_override(errors, name, raw, str(exc))
        return default


def _env_provider_url_template_checked(
    name: str,
    default: str,
    errors: MutableSequence[str] | None = None,
    *,
    field_name: str,
    allow_relative: bool = True,
) -> str:
    raw = os.environ.get(name)
    if raw is None:
        return default
    candidate = raw.strip()
    if not candidate:
        return ""
    try:
        return validate_provider_url_template(candidate, allow_relative=allow_relative, field_name=field_name)
    except ValueError as exc:
        _record_invalid_env_override(errors, name, raw, str(exc))
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


CapacityImpactModel = Literal["HEURISTIC", "CALIBRATED"]
LiveFreshnessMarketHoursProfile = Literal["DISABLED", "US_EQUITIES_RTH"]



OpenBBConnectorMode = Literal["http", "python"]


class OpenBBMarketDataConnectorSettings(BaseModel):
    """Optional OpenBB ingress connector.

    The connector can target an HTTP/JSON sidecar or a local Python OpenBB runtime.
    Credentials remain environment-driven.
    """
    enabled: bool = False
    provider_id: str = Field(default="openbb", min_length=1)
    mode: OpenBBConnectorMode = "http"
    base_url: Optional[str] = None
    liquidity_url_template: str = ""
    borrow_url_template: str = ""
    oracle_macro_url_template: str = ""
    oracle_microstructure_url_template: str = ""
    api_key_env_var: Optional[str] = None
    timeout_seconds: float = Field(default=10.0, gt=0.0, le=300.0)
    source_mode: SourceMode = "SNAPSHOT"
    default_equity_provider: Optional[str] = None
    default_macro_provider: Optional[str] = None


    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_provider_url(value, field_name="openbb.base_url")

    @field_validator("liquidity_url_template", "borrow_url_template", "oracle_macro_url_template", "oracle_microstructure_url_template")
    @classmethod
    def _validate_url_templates(cls, value: str) -> str:
        return validate_provider_url_template(value, field_name="openbb.url_template")

    model_config = {"extra": "forbid"}


class NvidiaNimConnectorSettings(BaseModel):
    """Optional NVIDIA NIM OpenAI-compatible semantic connector."""
    enabled: bool = False
    provider_id: str = Field(default="nvidia_nim", min_length=1)
    base_url: str = Field(default="https://integrate.api.nvidia.com/v1", min_length=8)
    api_key_env: str = Field(default="NVIDIA_NIM_API_KEY", min_length=1)
    model: str = Field(default="minimaxai/minimax-m2.7", min_length=1)
    timeout_seconds: float = Field(default=60.0, gt=0.0, le=600.0)
    max_retries: int = Field(default=2, ge=0, le=10)


    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        return validate_provider_url(value, field_name="nvidia_nim.base_url") or value

    model_config = {"extra": "forbid"}


class AlpacaMarketDataConnectorSettings(BaseModel):
    """
    Alpaca Market Data v2 (live US equities snapshot) + optional Trading API borrow/locate.

    API keys are read from named environment variables (never from YAML).

    Borrow path: when ``enable_borrow_from_trading_api`` is True, calls Trading API
    ``GET /v2/assets/{symbol}`` for ``shortable`` / ``easy_to_borrow``. Alpaca does not
    return an annualized borrow fee on that response; ``etb_borrow_cost_bps`` /
    ``htb_borrow_cost_bps`` are **explicit operator tier assumptions** (documented), not
    hidden heuristics — they must be set knowingly for production.
    """
    enabled: bool = False
    provider_id: str = Field(default="alpaca_data_v2", min_length=1)
    data_base_url: str = Field(default="https://data.alpaca.markets", min_length=8)
    api_key_id_env: str = Field(default="APCA_API_KEY_ID", min_length=1)
    api_secret_key_env: str = Field(default="APCA_API_SECRET_KEY", min_length=1)
    timeout_seconds: float = Field(default=10.0, gt=0.0, le=300.0)
    enable_borrow_from_trading_api: bool = False
    trading_base_url: str = Field(default="https://paper-api.alpaca.markets", min_length=8)
    etb_borrow_cost_bps: float = Field(default=20.0, gt=0.0, le=10_000.0)
    htb_borrow_cost_bps: float = Field(default=300.0, gt=0.0, le=10_000.0)


    @field_validator("data_base_url", "trading_base_url")
    @classmethod
    def _validate_alpaca_urls(cls, value: str) -> str:
        return validate_provider_url(value, field_name="alpaca.url") or value

    model_config = {"extra": "forbid"}


class HttpJsonMarketDataConnectorSettings(BaseModel):
    """
    Optional HTTP/JSON live connector configuration (operator-supplied URLs).

    Secrets are never stored here: use api_key_env_var to name an environment variable.
    """
    enabled: bool = False
    provider_id: str = Field(default="http_json_live", min_length=1)
    liquidity_url_template: str = ""
    borrow_url_template: str = ""
    oracle_macro_url_template: str = ""
    oracle_microstructure_url_template: str = ""
    api_key_env_var: Optional[str] = None
    timeout_seconds: float = Field(default=10.0, gt=0.0, le=300.0)


    @field_validator("liquidity_url_template", "borrow_url_template", "oracle_macro_url_template", "oracle_microstructure_url_template")
    @classmethod
    def _validate_http_json_templates(cls, value: str) -> str:
        return validate_provider_url_template(value, field_name="http_json.url_template")

    model_config = {"extra": "forbid"}


class TribunalThresholds(BaseModel):
    # Semantic Gates
    min_evidence_density: float = 0.3
    neutral_novelty: float = 0.5
    neutral_polarity: float = 0.0
    neutral_tolerance: float = 0.05

    # Quantitative Gates
    max_nuisance_p_value: float = 0.05
    min_deflated_sharpe_ratio: float = 0.0
    min_path_coverage: float = 0.7
    max_path_stability: float = 1.0
    max_prob_overfit: float = 0.2
    min_decoy_coverage: float = 0.8
    min_delta_bps_post_cost: float = 0.0
    phantom_edge_buffer_multiplier: float = 2.0

class RuntimePolicy(BaseModel):
    """
    Typed runtime production safety policy.

    This is the single source of truth for production readiness constraints.
    All enforcement points read from this contract — no scattered policy checks.

    Fields:
        mode: RuntimeMode — DEV | TEST | PRODUCTION
        allow_provisional_market_data: Whether PROVISIONAL market-data inputs
            are acceptable for PROMOTABLE outcomes.  Production must set False.
        allow_snapshot_market_data: Whether SNAPSHOT (replayable, non-live)
            market-data is acceptable for PROMOTABLE outcomes.  When False,
            only LIVE feeds qualify.
        require_absolute_ledger_path: Whether the ledger database path must
            be absolute and non-default.  Production must set True.
        strict_production_mode: When True and mode==PRODUCTION, PROVISIONAL
            market_data blocks PROMOTABLE entirely (not just CONDITIONAL).
        live_market_data_freshness_threshold_seconds: Max acceptable age for LIVE
            market-data snapshots. Stale data blocks in production unless
            fallback is allowed.
        live_freshness_market_hours_profile: When US_EQUITIES_RTH, applies a longer
            off-hours max age for LIVE data (NYSE RTH simplification; no holidays).
        live_market_data_freshness_off_hours_threshold_seconds: Max LIVE snapshot age
            when evaluation time is outside US regular session (only if profile is set).
        allow_market_data_fallback: Whether falling back from LIVE to SNAPSHOT
            feeds is permitted when LIVE is stale or missing.
        market_data_provider_max_retries: Retry budget for provider-backed lookups.
        market_data_circuit_breaker_threshold: Consecutive failures before circuit opens.
        market_data_circuit_cooldown_seconds: Cooldown window for an open circuit.
        market_data_vendor_outage_circuit_policy: When LENIENT_TRANSIENT_5XX, HTTP 5xx class
            provider errors do not advance the circuit-breaker counter (vendor outage blips).
        capacity_impact_model: HEURISTIC (default sqrt law) vs CALIBRATED (artifact required).
        calibration_artifact_path: Filesystem path to a typed CalibrationArtifactV1 JSON file.
        calibration_minimum_validation_score: When >0, production CALIBRATED readiness requires
            artifact.validation_quality_score >= this threshold.
        calibration_reject_flat_curve_spread_bps_below: When >0 with an empirical curve, reject
            if max(impact_bps)-min(impact_bps) is below this spread (weak / flat calibration).
        calibration_require_training_run_id: Require non-empty training_run_id on the artifact.
        calibration_require_empirical_curve_in_production: When True, CALIBRATED production
            requires empirical_participation_curve (not multiplier-only).
    """
    mode: RuntimeMode = RuntimeMode.DEV
    allow_provisional_market_data: bool = True
    allow_snapshot_market_data: bool = True
    require_absolute_ledger_path: bool = False
    require_explicit_evaluation_time: bool = False
    require_explicit_market_data_subject_id: bool = False
    strict_production_mode: bool = False
    live_market_data_freshness_threshold_seconds: int = 120
    live_freshness_market_hours_profile: LiveFreshnessMarketHoursProfile = "DISABLED"
    live_market_data_freshness_off_hours_threshold_seconds: int = Field(default=86_400, ge=60, le=604_800)
    allow_market_data_fallback: bool = False
    market_data_provider_max_retries: int = 0
    market_data_circuit_breaker_threshold: int = 2
    market_data_circuit_cooldown_seconds: int = 300
    market_data_vendor_outage_circuit_policy: VendorOutageCircuitPolicy = "STANDARD"
    capacity_impact_model: CapacityImpactModel = "HEURISTIC"
    calibration_artifact_path: Optional[str] = None
    calibration_minimum_validation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    calibration_reject_flat_curve_spread_bps_below: float = Field(default=0.0, ge=0.0)
    calibration_require_training_run_id: bool = False
    calibration_require_empirical_curve_in_production: bool = False
    invalid_environment_overrides: tuple[str, ...] = Field(default_factory=tuple, exclude=True)

    @classmethod
    def get_default_for_mode(cls, mode: RuntimeMode) -> RuntimePolicy:
        if mode == RuntimeMode.PRODUCTION:
            return cls(
                mode=RuntimeMode.PRODUCTION,
                allow_provisional_market_data=False,
                allow_snapshot_market_data=False,
                require_absolute_ledger_path=True,
                require_explicit_evaluation_time=True,
                require_explicit_market_data_subject_id=True,
                strict_production_mode=True,
                live_market_data_freshness_threshold_seconds=60,
                live_freshness_market_hours_profile="DISABLED",
                live_market_data_freshness_off_hours_threshold_seconds=86_400,
                allow_market_data_fallback=False,
                market_data_provider_max_retries=1,
                market_data_circuit_breaker_threshold=2,
                market_data_circuit_cooldown_seconds=300,
                market_data_vendor_outage_circuit_policy="STANDARD",
            )
        return cls(mode=mode)

class AppConfig(BaseModel):
    mode: RuntimeMode = Field(default=RuntimeMode.DEV)
    runtime_policy: Optional[RuntimePolicy] = None
    tribunal_thresholds: TribunalThresholds = Field(default_factory=TribunalThresholds)
    market_data_http_connector: Optional[HttpJsonMarketDataConnectorSettings] = None
    market_data_alpaca_connector: Optional[AlpacaMarketDataConnectorSettings] = None
    market_data_openbb_connector: Optional[OpenBBMarketDataConnectorSettings] = None
    semantic_nvidia_nim_connector: Optional[NvidiaNimConnectorSettings] = None

    def model_post_init(self, __context) -> None:
        if self.runtime_policy is None:
            self.runtime_policy = RuntimePolicy.get_default_for_mode(self.mode)

def load_config(config_path: str | Path | None = None) -> AppConfig:
    if config_path is None:
        config_path = Path(__file__).parent.parent / "promotion_gates.yaml"

    path = Path(config_path)
    if not path.exists():
        data: dict = {}
    else:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}

    if "mode" not in data:
        data["mode"] = os.environ.get("STRATEGY_VALIDATOR_MODE", "DEV").upper()

    cfg = AppConfig.model_validate(data)
    invalid_environment_overrides: list[str] = []
    rp = cfg.runtime_policy or RuntimePolicy.get_default_for_mode(cfg.mode)
    rp.mode = cfg.mode
    rp.allow_provisional_market_data = _env_bool_checked("STRATEGY_VALIDATOR_ALLOW_PROVISIONAL_MARKET_DATA", rp.allow_provisional_market_data, invalid_environment_overrides)
    rp.allow_snapshot_market_data = _env_bool_checked("STRATEGY_VALIDATOR_ALLOW_SNAPSHOT_MARKET_DATA", rp.allow_snapshot_market_data, invalid_environment_overrides)
    rp.require_absolute_ledger_path = _env_bool_checked("STRATEGY_VALIDATOR_REQUIRE_ABSOLUTE_LEDGER_PATH", rp.require_absolute_ledger_path, invalid_environment_overrides)
    rp.require_explicit_evaluation_time = _env_bool_checked("STRATEGY_VALIDATOR_REQUIRE_EXPLICIT_EVALUATION_TIME", rp.require_explicit_evaluation_time, invalid_environment_overrides)
    rp.require_explicit_market_data_subject_id = _env_bool_checked("STRATEGY_VALIDATOR_REQUIRE_EXPLICIT_MARKET_DATA_SUBJECT_ID", rp.require_explicit_market_data_subject_id, invalid_environment_overrides)
    rp.strict_production_mode = _env_bool_checked("STRATEGY_VALIDATOR_STRICT_PRODUCTION_MODE", rp.strict_production_mode, invalid_environment_overrides)
    rp.live_market_data_freshness_threshold_seconds = _env_int_checked("STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS", rp.live_market_data_freshness_threshold_seconds, invalid_environment_overrides)
    rp.live_freshness_market_hours_profile = _env_literal_checked(
        "STRATEGY_VALIDATOR_LIVE_FRESHNESS_MARKET_HOURS_PROFILE",
        str(rp.live_freshness_market_hours_profile),
        {"DISABLED", "US_EQUITIES_RTH"},
        invalid_environment_overrides,
    )  # type: ignore[assignment]
    rp.live_market_data_freshness_off_hours_threshold_seconds = _env_int_checked(
        "STRATEGY_VALIDATOR_LIVE_FRESHNESS_OFF_HOURS_THRESHOLD_SECONDS",
        rp.live_market_data_freshness_off_hours_threshold_seconds,
        invalid_environment_overrides,
    )
    rp.allow_market_data_fallback = _env_bool_checked("STRATEGY_VALIDATOR_ALLOW_MARKET_DATA_FALLBACK", rp.allow_market_data_fallback, invalid_environment_overrides)
    rp.market_data_provider_max_retries = _env_int_checked("STRATEGY_VALIDATOR_MARKET_DATA_PROVIDER_MAX_RETRIES", rp.market_data_provider_max_retries, invalid_environment_overrides)
    rp.market_data_circuit_breaker_threshold = _env_int_checked("STRATEGY_VALIDATOR_MARKET_DATA_CIRCUIT_BREAKER_THRESHOLD", rp.market_data_circuit_breaker_threshold, invalid_environment_overrides)
    rp.market_data_circuit_cooldown_seconds = _env_int_checked("STRATEGY_VALIDATOR_MARKET_DATA_CIRCUIT_COOLDOWN_SECONDS", rp.market_data_circuit_cooldown_seconds, invalid_environment_overrides)
    rp.capacity_impact_model = _env_literal_checked(
        "STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL",
        str(rp.capacity_impact_model),
        {"HEURISTIC", "CALIBRATED"},
        invalid_environment_overrides,
    )  # type: ignore[assignment]
    cal_path = os.environ.get("STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH")
    if cal_path is not None:
        rp.calibration_artifact_path = cal_path.strip() or None
    rp.market_data_vendor_outage_circuit_policy = _env_literal_checked(
        "STRATEGY_VALIDATOR_MARKET_DATA_VENDOR_OUTAGE_CIRCUIT_POLICY",
        str(rp.market_data_vendor_outage_circuit_policy),
        {"STANDARD", "LENIENT_TRANSIENT_5XX"},
        invalid_environment_overrides,
    )  # type: ignore[assignment]
    rp.calibration_minimum_validation_score = _env_float_checked(
        "STRATEGY_VALIDATOR_CALIBRATION_MINIMUM_VALIDATION_SCORE",
        rp.calibration_minimum_validation_score,
        invalid_environment_overrides,
    )
    rp.calibration_reject_flat_curve_spread_bps_below = _env_float_checked(
        "STRATEGY_VALIDATOR_CALIBRATION_REJECT_FLAT_CURVE_SPREAD_BPS_BELOW",
        rp.calibration_reject_flat_curve_spread_bps_below,
        invalid_environment_overrides,
    )
    rp.calibration_require_training_run_id = _env_bool_checked(
        "STRATEGY_VALIDATOR_CALIBRATION_REQUIRE_TRAINING_RUN_ID",
        rp.calibration_require_training_run_id,
        invalid_environment_overrides,
    )
    rp.calibration_require_empirical_curve_in_production = _env_bool_checked(
        "STRATEGY_VALIDATOR_CALIBRATION_REQUIRE_EMPIRICAL_CURVE_IN_PRODUCTION",
        rp.calibration_require_empirical_curve_in_production,
        invalid_environment_overrides,
    )

    # HTTP JSON connector env overrides (optional)
    mdc = cfg.market_data_http_connector
    if mdc is None and any(
        os.environ.get(k)
        for k in (
            "STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED",
            "STRATEGY_VALIDATOR_HTTP_MARKET_DATA_LIQUIDITY_URL_TEMPLATE",
            "STRATEGY_VALIDATOR_HTTP_MARKET_DATA_BORROW_URL_TEMPLATE",
        )
    ):
        mdc = HttpJsonMarketDataConnectorSettings()
    if mdc is not None:
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED") is not None:
            mdc.enabled = _env_bool_checked("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_ENABLED", mdc.enabled, invalid_environment_overrides)
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_PROVIDER_ID"):
            mdc.provider_id = os.environ["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_PROVIDER_ID"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_LIQUIDITY_URL_TEMPLATE"):
            mdc.liquidity_url_template = _env_provider_url_template_checked("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_LIQUIDITY_URL_TEMPLATE", mdc.liquidity_url_template, invalid_environment_overrides, field_name="http_json.liquidity_url_template")
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_BORROW_URL_TEMPLATE"):
            mdc.borrow_url_template = _env_provider_url_template_checked("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_BORROW_URL_TEMPLATE", mdc.borrow_url_template, invalid_environment_overrides, field_name="http_json.borrow_url_template")
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_API_KEY_ENV_VAR"):
            mdc.api_key_env_var = os.environ["STRATEGY_VALIDATOR_HTTP_MARKET_DATA_API_KEY_ENV_VAR"].strip() or None
        if os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_TIMEOUT_SECONDS") is not None:
            raw_t = os.environ.get("STRATEGY_VALIDATOR_HTTP_MARKET_DATA_TIMEOUT_SECONDS", "10")
            try:
                mdc.timeout_seconds = float(raw_t)
            except ValueError:
                _record_invalid_env_override(invalid_environment_overrides, "STRATEGY_VALIDATOR_HTTP_MARKET_DATA_TIMEOUT_SECONDS", raw_t, "a number")
        cfg.market_data_http_connector = mdc

    # Alpaca Market Data connector (optional)
    alp = cfg.market_data_alpaca_connector
    if alp is None and os.environ.get("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED") is not None:
        alp = AlpacaMarketDataConnectorSettings()
    if alp is not None:
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED") is not None:
            alp.enabled = _env_bool_checked("STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED", alp.enabled, invalid_environment_overrides)
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_DATA_BASE_URL"):
            alp.data_base_url = _env_provider_url_checked("STRATEGY_VALIDATOR_ALPACA_DATA_BASE_URL", alp.data_base_url, invalid_environment_overrides, field_name="alpaca.data_base_url") or alp.data_base_url
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_PROVIDER_ID"):
            alp.provider_id = os.environ["STRATEGY_VALIDATOR_ALPACA_PROVIDER_ID"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_API_KEY_ID_ENV"):
            alp.api_key_id_env = os.environ["STRATEGY_VALIDATOR_ALPACA_API_KEY_ID_ENV"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_API_SECRET_KEY_ENV"):
            alp.api_secret_key_env = os.environ["STRATEGY_VALIDATOR_ALPACA_API_SECRET_KEY_ENV"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_TIMEOUT_SECONDS") is not None:
            raw_timeout = os.environ["STRATEGY_VALIDATOR_ALPACA_TIMEOUT_SECONDS"]
            try:
                alp.timeout_seconds = float(raw_timeout)
            except ValueError:
                _record_invalid_env_override(invalid_environment_overrides, "STRATEGY_VALIDATOR_ALPACA_TIMEOUT_SECONDS", raw_timeout, "a number")
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_ENABLE_BORROW_FROM_TRADING_API") is not None:
            alp.enable_borrow_from_trading_api = _env_bool_checked(
                "STRATEGY_VALIDATOR_ALPACA_ENABLE_BORROW_FROM_TRADING_API",
                alp.enable_borrow_from_trading_api,
                invalid_environment_overrides,
            )
        if os.environ.get("STRATEGY_VALIDATOR_ALPACA_TRADING_BASE_URL"):
            alp.trading_base_url = _env_provider_url_checked("STRATEGY_VALIDATOR_ALPACA_TRADING_BASE_URL", alp.trading_base_url, invalid_environment_overrides, field_name="alpaca.trading_base_url") or alp.trading_base_url
        alp.etb_borrow_cost_bps = _env_float_checked(
            "STRATEGY_VALIDATOR_ALPACA_ETB_BORROW_COST_BPS", alp.etb_borrow_cost_bps, invalid_environment_overrides
        )
        alp.htb_borrow_cost_bps = _env_float_checked(
            "STRATEGY_VALIDATOR_ALPACA_HTB_BORROW_COST_BPS", alp.htb_borrow_cost_bps, invalid_environment_overrides
        )

    cfg.market_data_alpaca_connector = alp

    # OpenBB connector (optional)
    openbb = cfg.market_data_openbb_connector
    if openbb is None and any(
        os.environ.get(k)
        for k in (
            "STRATEGY_VALIDATOR_OPENBB_ENABLED",
            "STRATEGY_VALIDATOR_OPENBB_MODE",
            "STRATEGY_VALIDATOR_OPENBB_LIQUIDITY_URL_TEMPLATE",
            "STRATEGY_VALIDATOR_OPENBB_BASE_URL",
        )
    ):
        openbb = OpenBBMarketDataConnectorSettings()
    if openbb is not None:
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_ENABLED") is not None:
            openbb.enabled = _env_bool_checked("STRATEGY_VALIDATOR_OPENBB_ENABLED", openbb.enabled, invalid_environment_overrides)
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_PROVIDER_ID"):
            openbb.provider_id = os.environ["STRATEGY_VALIDATOR_OPENBB_PROVIDER_ID"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_MODE"):
            openbb.mode = _env_literal_checked("STRATEGY_VALIDATOR_OPENBB_MODE", str(openbb.mode), {"http", "python"}, invalid_environment_overrides, normalize_upper=False)  # type: ignore[assignment]
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_BASE_URL"):
            openbb.base_url = _env_provider_url_checked("STRATEGY_VALIDATOR_OPENBB_BASE_URL", openbb.base_url, invalid_environment_overrides, field_name="openbb.base_url")
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_LIQUIDITY_URL_TEMPLATE"):
            openbb.liquidity_url_template = _env_provider_url_template_checked("STRATEGY_VALIDATOR_OPENBB_LIQUIDITY_URL_TEMPLATE", openbb.liquidity_url_template, invalid_environment_overrides, field_name="openbb.liquidity_url_template")
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_BORROW_URL_TEMPLATE"):
            openbb.borrow_url_template = _env_provider_url_template_checked("STRATEGY_VALIDATOR_OPENBB_BORROW_URL_TEMPLATE", openbb.borrow_url_template, invalid_environment_overrides, field_name="openbb.borrow_url_template")
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_API_KEY_ENV_VAR"):
            openbb.api_key_env_var = os.environ["STRATEGY_VALIDATOR_OPENBB_API_KEY_ENV_VAR"].strip() or None
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_TIMEOUT_SECONDS") is not None:
            raw_timeout = os.environ["STRATEGY_VALIDATOR_OPENBB_TIMEOUT_SECONDS"]
            try:
                openbb.timeout_seconds = float(raw_timeout)
            except ValueError:
                _record_invalid_env_override(invalid_environment_overrides, "STRATEGY_VALIDATOR_OPENBB_TIMEOUT_SECONDS", raw_timeout, "a number")
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_SOURCE_MODE"):
            openbb.source_mode = _env_literal_checked("STRATEGY_VALIDATOR_OPENBB_SOURCE_MODE", str(openbb.source_mode), {"LIVE", "SNAPSHOT", "PROVISIONAL"}, invalid_environment_overrides)  # type: ignore[assignment]
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_DEFAULT_EQUITY_PROVIDER"):
            openbb.default_equity_provider = os.environ["STRATEGY_VALIDATOR_OPENBB_DEFAULT_EQUITY_PROVIDER"].strip() or None
        if os.environ.get("STRATEGY_VALIDATOR_OPENBB_DEFAULT_MACRO_PROVIDER"):
            openbb.default_macro_provider = os.environ["STRATEGY_VALIDATOR_OPENBB_DEFAULT_MACRO_PROVIDER"].strip() or None
        cfg.market_data_openbb_connector = openbb

    # NVIDIA NIM semantic connector (optional)
    nim = cfg.semantic_nvidia_nim_connector
    if nim is None and any(
        os.environ.get(k)
        for k in (
            "STRATEGY_VALIDATOR_NVIDIA_NIM_ENABLED",
            "STRATEGY_VALIDATOR_NVIDIA_NIM_MODEL",
            "STRATEGY_VALIDATOR_NVIDIA_NIM_BASE_URL",
        )
    ):
        nim = NvidiaNimConnectorSettings()
    if nim is not None:
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_ENABLED") is not None:
            nim.enabled = _env_bool_checked("STRATEGY_VALIDATOR_NVIDIA_NIM_ENABLED", nim.enabled, invalid_environment_overrides)
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_PROVIDER_ID"):
            nim.provider_id = os.environ["STRATEGY_VALIDATOR_NVIDIA_NIM_PROVIDER_ID"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_BASE_URL"):
            nim.base_url = _env_provider_url_checked("STRATEGY_VALIDATOR_NVIDIA_NIM_BASE_URL", nim.base_url, invalid_environment_overrides, field_name="nvidia_nim.base_url") or nim.base_url
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_API_KEY_ENV"):
            nim.api_key_env = os.environ["STRATEGY_VALIDATOR_NVIDIA_NIM_API_KEY_ENV"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_MODEL"):
            nim.model = os.environ["STRATEGY_VALIDATOR_NVIDIA_NIM_MODEL"].strip()
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_TIMEOUT_SECONDS") is not None:
            raw_timeout = os.environ["STRATEGY_VALIDATOR_NVIDIA_NIM_TIMEOUT_SECONDS"]
            try:
                nim.timeout_seconds = float(raw_timeout)
            except ValueError:
                _record_invalid_env_override(invalid_environment_overrides, "STRATEGY_VALIDATOR_NVIDIA_NIM_TIMEOUT_SECONDS", raw_timeout, "a number")
        if os.environ.get("STRATEGY_VALIDATOR_NVIDIA_NIM_MAX_RETRIES") is not None:
            raw_retries = os.environ["STRATEGY_VALIDATOR_NVIDIA_NIM_MAX_RETRIES"]
            try:
                nim.max_retries = int(raw_retries)
            except ValueError:
                _record_invalid_env_override(invalid_environment_overrides, "STRATEGY_VALIDATOR_NVIDIA_NIM_MAX_RETRIES", raw_retries, "an integer")
        cfg.semantic_nvidia_nim_connector = nim
    rp.invalid_environment_overrides = tuple(invalid_environment_overrides)
    cfg.runtime_policy = rp
    return cfg

AppConfig.model_rebuild()
