from __future__ import annotations

from strategy_validator.api.routes.research_release import semantic_adjudication_bundle_release_preflight


def test_release_preflight_route_returns_report(valid_semantic_adjudication_bundle_payload, valid_semantic_adjudication_bundle_manifest_payload):
    request = type(
        "Request",
        (),
        {
            "bundle": valid_semantic_adjudication_bundle_payload,
            "manifest": valid_semantic_adjudication_bundle_manifest_payload,
            "proposal": None,
            "require_manifest": True,
        },
    )()

    payload = semantic_adjudication_bundle_release_preflight(request)

    assert payload["schema_version"] == "semantic_adjudication_bundle_release_preflight/v1"
    assert payload["bundle_id"] == valid_semantic_adjudication_bundle_payload["bundle_id"]
