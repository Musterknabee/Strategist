from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.contracts.operator_control_plane_bundle import OracleOperatorControlPlaneBundle
from strategy_validator.control_plane.operator_control_plane_bundle_rendering import (
    render_operator_control_plane_bundle_markdown_lines,
)


def render_operator_control_plane_bundle_markdown_document(bundle: OracleOperatorControlPlaneBundle) -> str:
    return "\n".join(render_operator_control_plane_bundle_markdown_lines(bundle))


def persist_operator_control_plane_bundle(bundle: OracleOperatorControlPlaneBundle) -> OracleOperatorControlPlaneBundle:
    Path(bundle.summary_output_path).write_text(json.dumps(bundle.to_payload(), indent=2) + "\n", encoding="utf-8")
    Path(bundle.markdown_output_path).write_text(
        render_operator_control_plane_bundle_markdown_document(bundle),
        encoding="utf-8",
    )
    return bundle


__all__ = [
    "persist_operator_control_plane_bundle",
    "render_operator_control_plane_bundle_markdown_document",
]
