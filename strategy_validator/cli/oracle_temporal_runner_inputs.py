from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.oracle_core import StrategyHealthSnapshot
from strategy_validator.contracts.oracle_strategic_fusion import (
    OracleSensorRawMacroInput,
    OracleSensorRawMicrostructureInput,
)
from strategy_validator.contracts.oracle_temporal_results import (
    TemporalCanonicalizationBatchResult,
    TemporalEventLogAppendBatchResult,
)
from strategy_validator.contracts.oracle_temporal_semantics import (
    TemporalSemanticBatchManifest,
    TemporalSemanticBatchVerification,
    TemporalSemanticExtractionBatchRequest,
)


def read_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_extraction_request(path: str) -> TemporalSemanticExtractionBatchRequest:
    return TemporalSemanticExtractionBatchRequest.model_validate(read_json(path))


def load_manifest(path: str) -> TemporalSemanticBatchManifest:
    return TemporalSemanticBatchManifest.model_validate(read_json(path))


def load_canonicalization(path: str) -> TemporalCanonicalizationBatchResult:
    return TemporalCanonicalizationBatchResult.model_validate(read_json(path))


def load_verification_report(path: str) -> TemporalSemanticBatchVerification:
    return TemporalSemanticBatchVerification.model_validate(read_json(path))


def load_append_report(path: str) -> TemporalEventLogAppendBatchResult:
    return TemporalEventLogAppendBatchResult.model_validate(read_json(path))


def load_macro_map(path: str) -> dict:
    raw = read_json(path)
    return {k: OracleSensorRawMacroInput.model_validate(v) for k, v in raw.items()}


def load_micro_map(path: str) -> dict:
    raw = read_json(path)
    return {k: OracleSensorRawMicrostructureInput.model_validate(v) for k, v in raw.items()}


def load_generated_for_map(path: str) -> dict:
    return read_json(path)


def load_strategies_map(path: str) -> dict:
    raw = read_json(path)
    return {k: [StrategyHealthSnapshot.model_validate(item) for item in v] for k, v in raw.items()}
