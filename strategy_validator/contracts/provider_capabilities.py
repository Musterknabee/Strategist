"""Optional external research/data provider capability registry.

No provider listed here is required for backend startup; connectors remain opt-in.

This module is the legacy public import path. Schema definitions and registry
entries are decomposed into focused submodules to keep the contract facade small.
"""
from __future__ import annotations

from strategy_validator.contracts.provider_capabilities_registry import (
    all_provider_capabilities,
    capability_by_provider_id,
    export_provider_capabilities_payload,
)
from strategy_validator.contracts.provider_capabilities_types import (
    SCHEMA_VERSION,
    DefaultTrustLevel,
    PitSuitability,
    ProviderAccessType,
    ProviderCapability,
    ProviderCategory,
    ResearchRole,
)

__all__ = (
    "SCHEMA_VERSION",
    "ProviderCategory",
    "ProviderAccessType",
    "DefaultTrustLevel",
    "PitSuitability",
    "ResearchRole",
    "ProviderCapability",
    "all_provider_capabilities",
    "export_provider_capabilities_payload",
    "capability_by_provider_id",
)
