from __future__ import annotations

import ast
from importlib import import_module
from pathlib import Path

from strategy_validator.api.routes import research_release as legacy_release


ROUTE_FAMILY_MODULES = (
    "strategy_validator.api.routes.research_release_bundle_routes",
    "strategy_validator.api.routes.research_release_capsule_routes",
    "strategy_validator.api.routes.research_release_decision_routes",
    "strategy_validator.api.routes.research_release_handoff_routes",
)


def _source(module_path: str) -> str:
    return Path(module_path).read_text(encoding="utf-8")


def test_research_release_facade_aggregates_family_routers_without_losing_routes() -> None:
    family_paths: set[str] = set()
    for module_name in ROUTE_FAMILY_MODULES:
        module = import_module(module_name)
        assert module.router.routes, module_name
        family_paths.update(route.path for route in module.router.routes)

    aggregate_paths = {route.path for route in legacy_release.router.routes}

    assert aggregate_paths == family_paths
    assert "/semantic-adjudication-bundle/release-index" in aggregate_paths
    assert "/semantic-adjudication-bundle/release-decision-record/verify" in aggregate_paths
    assert "/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary" in aggregate_paths


def test_research_release_facade_stays_small_and_route_free() -> None:
    source = _source("strategy_validator/api/routes/research_release.py")
    tree = ast.parse(source)

    assert len(source.splitlines()) <= 140
    assert not [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
    assert not [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert "router.include_router(bundle_router)" in source
    assert "router.include_router(capsule_router)" in source
    assert "router.include_router(decision_router)" in source
    assert "router.include_router(handoff_router)" in source


def test_research_release_family_modules_own_expected_route_groups() -> None:
    bundle = _source("strategy_validator/api/routes/research_release_bundle_routes.py")
    capsule = _source("strategy_validator/api/routes/research_release_capsule_routes.py")
    decision = _source("strategy_validator/api/routes/research_release_decision_routes.py")
    handoff = _source("strategy_validator/api/routes/research_release_handoff_routes.py")

    assert "SemanticAdjudicationBundleReleaseIndexRequest" in bundle
    assert "semantic_adjudication_bundle_release_preflight" in bundle
    assert "SemanticAdjudicationReleaseCapsuleRequest" in capsule
    assert "summarize_release_capsule_route" in capsule
    assert "SemanticAdjudicationReleaseDecisionRecordRequest" in decision
    assert "semantic_adjudication_release_decision_ledger_summary" in decision
    assert "SemanticAdjudicationReleaseHandoffCertificateRequest" in handoff
    assert "semantic_adjudication_release_handoff_certificate_evidence_summary" in handoff


def test_legacy_research_release_import_surface_remains_stable() -> None:
    assert legacy_release.SemanticAdjudicationBundleReleaseIndexRequest.__name__ == "SemanticAdjudicationBundleReleaseIndexRequest"
    assert legacy_release.SemanticAdjudicationReleaseCapsuleRequest.__name__ == "SemanticAdjudicationReleaseCapsuleRequest"
    assert legacy_release.SemanticAdjudicationReleaseDecisionRecordRequest.__name__ == "SemanticAdjudicationReleaseDecisionRecordRequest"
    assert legacy_release.SemanticReleaseHandoffCertificateEvidenceVerificationRequest.__name__ == "SemanticReleaseHandoffCertificateEvidenceVerificationRequest"
    assert callable(legacy_release.semantic_adjudication_bundle_release_index)
    assert callable(legacy_release.summarize_release_capsule_route)
    assert callable(legacy_release.semantic_adjudication_release_decision_record_verify)
    assert callable(legacy_release.semantic_adjudication_release_handoff_certificate_evidence_summary)
