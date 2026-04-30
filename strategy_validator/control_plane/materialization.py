from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.control_plane_event_envelope import (
    ControlPlaneEventEnvelope,
    build_control_plane_event_envelope,
)


@dataclass(frozen=True)
class MaterializedArtifactPair:
    """Filesystem rendering result for a control-plane JSON/Markdown artifact pair."""

    summary_output_path: str
    markdown_output_path: str
    summary_size_bytes: int
    markdown_size_bytes: int

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class EventBackedMaterializedArtifactPair:
    """Filesystem rendering result for an event-first control-plane artifact pair.

    The event envelope is the canonical record shape; JSON/Markdown files are
    derived renderings that remain compatible with existing operator workflows.
    """

    summary_output_path: str
    markdown_output_path: str
    event_output_path: str
    event_id: str
    payload_digest: str
    summary_size_bytes: int
    markdown_size_bytes: int
    event_size_bytes: int
    journal_action_event_id: str | None = None
    journal_sequence_number: int | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


def render_markdown_lines(lines: list[str] | tuple[str, ...]) -> str:
    """Render markdown lines using the repo's trailing-newline convention."""

    rendered = "\n".join(lines)
    if not rendered.endswith("\n"):
        rendered += "\n"
    return rendered


def event_envelope_for_materialized_payload(
    *,
    event_type: str,
    producer: str,
    payload: dict[str, Any],
    actor_id: str | None = None,
    target: dict[str, Any] | None = None,
    policy_fingerprint: str | None = None,
    idempotency_key: str | None = None,
    evidence_refs: tuple[str, ...] | list[str] = (),
) -> ControlPlaneEventEnvelope:
    """Build the canonical event envelope for a materialized control-plane payload.

    This deliberately does not mutate the ledger. It gives filesystem-rendered
    control-plane artifacts an event-shaped identity that later event-backed
    projections can replay.
    """

    return build_control_plane_event_envelope(
        event_type=event_type,
        producer=producer,
        payload=payload,
        actor_id=actor_id,
        target=target,
        policy_fingerprint=policy_fingerprint,
        idempotency_key=idempotency_key,
        evidence_refs=evidence_refs,
    )


def write_json_markdown_artifacts(
    *,
    summary_output_path: Path,
    markdown_output_path: Path,
    payload: dict[str, Any],
    markdown: str | list[str] | tuple[str, ...],
) -> MaterializedArtifactPair:
    """Write the common control-plane JSON + Markdown artifact pair.

    This keeps the many operator/control-plane materializers on one rendering
    primitive while preserving their existing public payload contracts.
    """

    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown_text = render_markdown_lines(markdown) if not isinstance(markdown, str) else markdown
    if not markdown_text.endswith("\n"):
        markdown_text += "\n"
    markdown_output_path.write_text(markdown_text, encoding="utf-8")
    return MaterializedArtifactPair(
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        summary_size_bytes=summary_output_path.stat().st_size,
        markdown_size_bytes=markdown_output_path.stat().st_size,
    )


def write_event_backed_json_markdown_artifacts(
    *,
    summary_output_path: Path,
    markdown_output_path: Path,
    event_output_path: Path,
    event_type: str,
    producer: str,
    payload: dict[str, Any],
    markdown: str | list[str] | tuple[str, ...],
    actor_id: str | None = None,
    target: dict[str, Any] | None = None,
    policy_fingerprint: str | None = None,
    idempotency_key: str | None = None,
    evidence_refs: tuple[str, ...] | list[str] = (),
    append_to_operator_journal: bool = False,
) -> EventBackedMaterializedArtifactPair:
    """Write an event-first control-plane materialization.

    The canonical event envelope is built from the payload and written as a
    sidecar. JSON/Markdown outputs remain derived operator-facing renderings.
    """

    normalized_evidence_refs = tuple(
        str(ref)
        for ref in (
            tuple(evidence_refs)
            if evidence_refs
            else (str(summary_output_path), str(markdown_output_path))
        )
    )
    event_output_path.parent.mkdir(parents=True, exist_ok=True)
    envelope = event_envelope_for_materialized_payload(
        event_type=event_type,
        producer=producer,
        payload=payload,
        actor_id=actor_id,
        target=target,
        policy_fingerprint=policy_fingerprint,
        idempotency_key=idempotency_key,
        evidence_refs=normalized_evidence_refs,
    )
    event_output_path.write_text(json.dumps(envelope.to_payload(), indent=2) + "\n", encoding="utf-8")
    journal_event = None
    if append_to_operator_journal:
        from strategy_validator.ledger.operator_actions import append_control_plane_event_envelope

        journal_event = append_control_plane_event_envelope(
            envelope,
            operator_id=actor_id or "control-plane",
            summary_line=f"control-plane event materialized: {event_type}",
        )
    rendered = write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=payload,
        markdown=markdown,
    )
    return EventBackedMaterializedArtifactPair(
        summary_output_path=rendered.summary_output_path,
        markdown_output_path=rendered.markdown_output_path,
        event_output_path=str(event_output_path),
        event_id=envelope.event_id,
        payload_digest=envelope.payload_digest,
        summary_size_bytes=rendered.summary_size_bytes,
        markdown_size_bytes=rendered.markdown_size_bytes,
        event_size_bytes=event_output_path.stat().st_size,
        journal_action_event_id=None if journal_event is None else journal_event.action_event_id,
        journal_sequence_number=None if journal_event is None else journal_event.sequence_number,
    )


__all__ = [
    "ControlPlaneEventEnvelope",
    "EventBackedMaterializedArtifactPair",
    "MaterializedArtifactPair",
    "event_envelope_for_materialized_payload",
    "render_markdown_lines",
    "write_event_backed_json_markdown_artifacts",
    "write_json_markdown_artifacts",
]
