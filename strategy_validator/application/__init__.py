"""Application-layer service façades.

Transport-neutral API/CLI use-case surface with lazy symbol resolution.
The canonical export map lives in ``strategy_validator.application._exports``.
"""

from __future__ import annotations

from importlib import import_module

from strategy_validator.application._exports import _EXPORT_MAP
# semantic export marker strings for compatibility checks:
# build_semantic_adjudication_bundle_release_index, verify_semantic_adjudication_bundle_release_index,
# build_semantic_release_handoff_certificate_evidence, verify_semantic_release_handoff_certificate_evidence
# build_semantic_adjudication_release_capsule, summarize_semantic_adjudication_release_capsule, build_semantic_adjudication_release_decision_record
# verify_semantic_adjudication_release_capsule, verify_semantic_adjudication_release_decision_record
# summarize_semantic_adjudication_release_decision_record

__all__ = sorted(_EXPORT_MAP)


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(name)
    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
