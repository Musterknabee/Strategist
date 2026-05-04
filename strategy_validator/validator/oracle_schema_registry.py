from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from pydantic import BaseModel

from strategy_validator.contracts.oracle_core import OraclePolicyArtifact
from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchPriorityReport,
    OracleStrategicInterventionReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleStrategicArtifactEvidenceManifest,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicCampaignReport,
)


@dataclass(frozen=True)
class RegisteredSchema:
    schema_version: str
    family: str = "oracle"
    status: str = "REGISTERED_COMPATIBILITY"


def _family(schema_version: str) -> str:
    if schema_version.startswith(("oracle_", "strategy_health_")):
        return "oracle"
    if schema_version.startswith("single_tenant_"):
        return "deployment"
    return "unknown"


_ORACLE_MODELS: dict[str, type[BaseModel]] = {
    "oracle_policy_artifact/v1": OraclePolicyArtifact,
    "oracle_doctrine_adaptation_report/v1": OracleDoctrineAdaptationReport,
    "oracle_research_priority_report/v1": OracleResearchPriorityReport,
    "oracle_strategic_intervention_report/v1": OracleStrategicInterventionReport,
    "oracle_strategic_campaign_report/v1": OracleStrategicCampaignReport,
    "oracle_strategic_campaign_execution_report/v1": OracleStrategicCampaignExecutionReport,
    "oracle_strategic_artifact_evidence_manifest/v1": OracleStrategicArtifactEvidenceManifest,
}


class _LooseOracleArtifact:
    """Attribute bag for lineage/metadata when no typed model is registered (canonical shim)."""

    __slots__ = ("_data",)

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)


def validate_registered_schema(
    payload: dict[str, Any],
    expected_families: set[str] | frozenset[str] | None = None,
) -> RegisteredSchema:
    if not isinstance(payload, dict):
        raise ValueError("schema payload must be an object")
    version = str(payload.get("schema_version") or "")
    if not version:
        raise ValueError("payload missing schema_version")
    fam = _family(version)
    if expected_families and fam not in expected_families:
        raise ValueError(f"schema family {fam!r} not in {sorted(expected_families)!r}")
    return RegisteredSchema(schema_version=version, family=fam)


def load_artifact_payload(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("artifact payload must be a JSON object")
    return raw


def _coerce_model(schema_version: str, payload: dict[str, Any]) -> Any:
    model_cls = _ORACLE_MODELS.get(schema_version)
    if model_cls is not None:
        return model_cls.model_validate(payload)
    return _LooseOracleArtifact(payload)


def load_registered_artifact(
    path: str | Path,
    *,
    expected_schemas: set[str] | frozenset[str] | None = None,
    expected_families: set[str] | frozenset[str] | None = None,
) -> tuple[RegisteredSchema, None, Any]:
    payload = load_artifact_payload(path)
    reg = validate_registered_schema(payload, expected_families=expected_families)
    if expected_schemas is not None and reg.schema_version not in expected_schemas:
        raise ValueError(f"schema {reg.schema_version!r} not in expected {sorted(expected_schemas)!r}")
    model = _coerce_model(reg.schema_version, payload)
    return reg, None, model


def iter_registered_artifacts(
    *,
    roots: list[Path] | None = None,
    root: str | Path | None = None,
    expected_schemas: set[str] | frozenset[str] | None = None,
    expected_families: set[str] | frozenset[str] | None = None,
) -> Iterator[tuple[Path, None, None, Any]]:
    search_roots: list[Path] = []
    if roots:
        search_roots.extend(roots)
    if root is not None:
        search_roots.append(Path(root))
    for base in search_roots:
        if not base.exists():
            continue
        for candidate in base.rglob("*.json"):
            try:
                _reg, _pad, model = load_registered_artifact(
                    candidate,
                    expected_schemas=expected_schemas,
                    expected_families=expected_families,
                )
            except Exception:
                continue
            yield candidate, None, None, model
