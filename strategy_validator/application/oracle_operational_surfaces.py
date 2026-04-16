from __future__ import annotations

from pathlib import Path

from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    load_oracle_input,
    render_oracle_morning_attestation_markdown,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.oracle_briefing import (
    build_oracle_briefing_pack,
    emit_oracle_briefing_pack_projection_registry,
    materialize_oracle_briefing_pack,
    render_oracle_briefing_pack_html,
    render_oracle_briefing_pack_markdown,
)
from strategy_validator.validator.oracle_diagnostics import (
    build_oracle_incident_pack,
    build_oracle_operator_diagnostic_from_checkpoint,
    build_oracle_operator_diagnostic_from_report,
    build_oracle_status_pack,
    materialize_oracle_incident_pack,
    materialize_oracle_status_pack,
    render_oracle_incident_pack_html,
    render_oracle_incident_pack_markdown,
    render_oracle_operator_diagnostic_markdown,
    render_oracle_status_pack_html,
    render_oracle_status_pack_markdown,
)
from strategy_validator.validator.oracle_event_log import append_oracle_event_log
from strategy_validator.validator.oracle_replay import audit_oracle_replay, render_oracle_replay_audit_markdown
from strategy_validator.validator.oracle_signal_fusion import (
    build_oracle_strategic_fusion_report,
    render_oracle_strategic_fusion_markdown,
)
from strategy_validator.validator.oracle_sensors import (
    load_sensor_ingestion_input,
    normalize_sensor_input,
    render_sensor_ingestion_markdown,
)
from strategy_validator.validator.oracle_strategic_briefing import (
    build_oracle_strategic_briefing,
    load_fusion_report,
    render_oracle_strategic_briefing_markdown,
)


def build_briefing_pack_payload(**kwargs):
    return build_oracle_briefing_pack(**kwargs)


def materialize_briefing_pack_payload(pack_root: Path, report, *, markdown: str, html: str):
    return materialize_oracle_briefing_pack(pack_root, report, markdown=markdown, html=html)


def emit_briefing_pack_projection_registry_payload(**kwargs):
    return emit_oracle_briefing_pack_projection_registry(**kwargs)


def render_briefing_pack_markdown_payload(report) -> str:
    return render_oracle_briefing_pack_markdown(report)


def render_briefing_pack_html_payload(report) -> str:
    return render_oracle_briefing_pack_html(report)


def build_strategic_briefing_payload(**kwargs):
    return build_oracle_strategic_briefing(**kwargs)


def render_strategic_briefing_markdown_payload(report) -> str:
    return render_oracle_strategic_briefing_markdown(report)


def load_fusion_report_payload(*args, **kwargs):
    return load_fusion_report(*args, **kwargs)


def build_replay_audit_payload(*args, **kwargs):
    return audit_oracle_replay(*args, **kwargs)


def render_replay_audit_markdown_payload(report) -> str:
    return render_oracle_replay_audit_markdown(report)


def append_event_log_entry_payload(**kwargs):
    return append_oracle_event_log(**kwargs)


def build_morning_attestation_payload(**kwargs):
    return build_oracle_morning_attestation(**kwargs)


def render_morning_attestation_markdown_payload(report) -> str:
    return render_oracle_morning_attestation_markdown(report)


def load_oracle_input_payload(*args, **kwargs):
    return load_oracle_input(*args, **kwargs)


def build_oracle_evidence_bundle_payload(**kwargs):
    return build_oracle_evidence_bundle(**kwargs)


def verify_oracle_evidence_bundle_payload(**kwargs):
    return verify_oracle_evidence_bundle(**kwargs)


def load_sensor_ingestion_input_payload(*args, **kwargs):
    return load_sensor_ingestion_input(*args, **kwargs)


def normalize_sensor_ingestion_payload(*args, **kwargs):
    return normalize_sensor_input(*args, **kwargs)


def render_sensor_ingestion_markdown_payload(report) -> str:
    return render_sensor_ingestion_markdown(report)


def build_strategic_fusion_payload(**kwargs):
    return build_oracle_strategic_fusion_report(**kwargs)


def render_strategic_fusion_markdown_payload(report) -> str:
    return render_oracle_strategic_fusion_markdown(report)


def build_operator_diagnostic_from_checkpoint_payload(*args, **kwargs):
    return build_oracle_operator_diagnostic_from_checkpoint(*args, **kwargs)


def build_operator_diagnostic_from_report_payload(*args, **kwargs):
    return build_oracle_operator_diagnostic_from_report(*args, **kwargs)


def render_operator_diagnostic_markdown_payload(report) -> str:
    return render_oracle_operator_diagnostic_markdown(report)


def build_status_pack_payload(*args, **kwargs):
    return build_oracle_status_pack(*args, **kwargs)


def materialize_status_pack_payload(*args, **kwargs):
    return materialize_oracle_status_pack(*args, **kwargs)


def render_status_pack_markdown_payload(report) -> str:
    return render_oracle_status_pack_markdown(report)


def render_status_pack_html_payload(report) -> str:
    return render_oracle_status_pack_html(report)


def build_incident_pack_payload(*args, **kwargs):
    return build_oracle_incident_pack(*args, **kwargs)


def materialize_incident_pack_payload(*args, **kwargs):
    return materialize_oracle_incident_pack(*args, **kwargs)


def render_incident_pack_markdown_payload(report) -> str:
    return render_oracle_incident_pack_markdown(report)


def render_incident_pack_html_payload(report) -> str:
    return render_oracle_incident_pack_html(report)
