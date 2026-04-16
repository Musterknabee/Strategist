from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.contracts import operational as operational_contracts
from strategy_validator.contracts import oracle as oracle_contracts
from strategy_validator.contracts import oracle_temporal as oracle_temporal_contracts


@dataclass(frozen=True)
class ArtifactSchemaRegistration:
    schema_version: str
    artifact_kind: str
    producer_family: str
    model_name: str
    model: type[Any]


_CONTRACT_MODULES: tuple[tuple[str, object], ...] = (
    ("operational", operational_contracts),
    ("oracle", oracle_contracts),
    ("oracle_temporal", oracle_temporal_contracts),
)


def _iter_schema_registrations() -> list[ArtifactSchemaRegistration]:
    registrations: list[ArtifactSchemaRegistration] = []
    for family, module in _CONTRACT_MODULES:
        for name in sorted(dir(module)):
            attr = getattr(module, name)
            model_fields = getattr(attr, "model_fields", None)
            if not model_fields or "schema_version" not in model_fields:
                continue
            default = model_fields["schema_version"].default
            if not isinstance(default, str):
                continue
            artifact_kind = default.split("/", 1)[0]
            registrations.append(
                ArtifactSchemaRegistration(
                    schema_version=default,
                    artifact_kind=artifact_kind,
                    producer_family=family,
                    model_name=f"{module.__name__}.{name}",
                    model=attr,
                )
            )
    return registrations


_SCHEMA_REGISTRY: dict[str, ArtifactSchemaRegistration] = {
    registration.schema_version: registration
    for registration in _iter_schema_registrations()
}


def list_artifact_schema_registrations() -> tuple[ArtifactSchemaRegistration, ...]:
    return tuple(_SCHEMA_REGISTRY[key] for key in sorted(_SCHEMA_REGISTRY))


def get_artifact_schema_registration(schema_version: str) -> ArtifactSchemaRegistration | None:
    return _SCHEMA_REGISTRY.get(schema_version)


def load_artifact_payload(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def validate_registered_schema(
    payload: dict[str, Any],
    *,
    expected_families: set[str] | None = None,
) -> ArtifactSchemaRegistration:
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError("artifact payload is missing a string schema_version")
    registration = get_artifact_schema_registration(schema_version)
    if registration is None:
        supported = ", ".join(sorted(_SCHEMA_REGISTRY))
        raise ValueError(f"unsupported schema_version `{schema_version}`; supported schemas: {supported}")
    if expected_families is not None and registration.producer_family not in expected_families:
        allowed = ", ".join(sorted(expected_families))
        raise ValueError(
            f"schema_version `{schema_version}` belongs to producer family `{registration.producer_family}`, expected one of: {allowed}"
        )
    return registration


def load_registered_artifact(
    path: Path,
    *,
    expected_schemas: set[str] | None = None,
    expected_families: set[str] | None = None,
) -> tuple[ArtifactSchemaRegistration, dict[str, Any], Any]:
    payload = load_artifact_payload(path)
    registration = validate_registered_schema(payload, expected_families=expected_families)
    if expected_schemas is not None and registration.schema_version not in expected_schemas:
        allowed = ", ".join(sorted(expected_schemas))
        raise ValueError(
            f"schema_version `{registration.schema_version}` is not one of the expected schemas: {allowed}"
        )
    return registration, payload, registration.model.model_validate(payload)


def iter_registered_artifacts(
    *,
    roots: Iterable[Path],
    expected_schemas: set[str] | None = None,
    expected_families: set[str] | None = None,
) -> Iterable[tuple[Path, ArtifactSchemaRegistration, dict[str, Any], Any]]:
    seen: set[Path] = set()
    for root in roots:
        resolved_root = root.resolve()
        if resolved_root in seen or not resolved_root.exists():
            continue
        seen.add(resolved_root)
        for path in resolved_root.rglob("*.json"):
            resolved_path = path.resolve()
            try:
                registration, payload, model = load_registered_artifact(
                    resolved_path,
                    expected_schemas=expected_schemas,
                    expected_families=expected_families,
                )
            except Exception:
                continue
            yield resolved_path, registration, payload, model
