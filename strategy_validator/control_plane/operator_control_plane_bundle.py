from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.contracts.operator_control_plane_bundle import (
    OracleOperatorControlPlaneBundle,
    OracleOperatorControlPlaneBundleRequest,
)
from strategy_validator.control_plane.operator_control_plane_bundle_output import (
    persist_operator_control_plane_bundle,
)
from strategy_validator.control_plane.operator_control_plane_bundle_rendering import (
    render_operator_control_plane_bundle_markdown_lines,
)
from strategy_validator.control_plane.operator_control_plane_bundle_sections import (
    materialize_operator_control_plane_bundle_sections,
)
from strategy_validator.control_plane.operator_queue_query import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    run_operator_queue_query,
)


def build_operator_control_plane_bundle_request(**kwargs: Any) -> OracleOperatorControlPlaneBundleRequest:
    kwargs["bundle_root"] = Path(kwargs["bundle_root"]).resolve()
    return OracleOperatorControlPlaneBundleRequest(**kwargs)


def materialize_operator_control_plane_bundle(
    request: OracleOperatorControlPlaneBundleRequest,
    *,
    operator_queue_query_result: OracleOperatorQueueQueryResult | None = None,
    operator_queue_query_request: OracleOperatorQueueQueryRequest | None = None,
    **kwargs: Any,
) -> OracleOperatorControlPlaneBundle:
    if operator_queue_query_result is None:
        operator_queue_query_result = run_operator_queue_query(request=operator_queue_query_request, **kwargs)
    bundle = materialize_operator_control_plane_bundle_sections(
        request=request,
        operator_queue_query_result=operator_queue_query_result,
        operator_queue_query_request=operator_queue_query_request,
        **kwargs,
    )
    return persist_operator_control_plane_bundle(bundle)


__all__ = [
    "OracleOperatorControlPlaneBundle",
    "OracleOperatorControlPlaneBundleRequest",
    "build_operator_control_plane_bundle_request",
    "materialize_operator_control_plane_bundle",
    "render_operator_control_plane_bundle_markdown_lines",
]
