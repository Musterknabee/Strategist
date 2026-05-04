"""Optional research/data provider utilities (never required for API startup)."""

from strategy_validator.providers.health import build_provider_health_snapshot

__all__ = ["build_provider_health_snapshot"]
