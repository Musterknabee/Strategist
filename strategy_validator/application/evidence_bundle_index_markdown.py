"""Markdown rendering for read-only evidence bundle index payloads."""
from __future__ import annotations

from collections import Counter
from typing import Any


def _markdown_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def _markdown_bool(value: object) -> str:
    return "yes" if bool(value) else "no"


def render_evidence_bundle_index_markdown(payload: dict[str, Any]) -> str:
    """Render an operator-readable Markdown summary for an evidence index payload.

    The Markdown view is derived from the JSON discovery payload. It does not add
    verification, deployment approval, operator signoff, live-trading authority,
    or profitability semantics.
    """
    entries = [entry for entry in payload.get("entries", []) if isinstance(entry, dict)]
    status_counts = Counter(str(entry.get("status") or "UNKNOWN").upper() for entry in entries)
    discovered = sum(1 for entry in entries if entry.get("exists") is True)
    verified = sum(1 for entry in entries if entry.get("verified_integrity") is True)

    lines = [
        "# Evidence Bundle Index Summary",
        "",
        "## Scope",
        "",
        "- Evidence discovery only.",
        "- Not production deployment approval.",
        "- Not operator signoff.",
        "- Not live trading authorization.",
        "- Not profitability evidence.",
        "- Artifact presence is not strategy quality.",
        "",
        "## Snapshot",
        "",
        f"- Schema version: `{_markdown_cell(payload.get('schema_version', 'UNKNOWN'))}`",
        f"- Generated at UTC: `{_markdown_cell(payload.get('generated_at_utc', 'UNKNOWN'))}`",
        f"- Repository head SHA: `{_markdown_cell(payload.get('repo_head_sha', 'UNKNOWN'))}`",
        f"- Artifact root: `{_markdown_cell(payload.get('artifact_root', 'UNKNOWN'))}`",
        f"- Discovered entries: `{discovered}/{len(entries)}`",
        f"- Verified integrity entries: `{verified}`",
        "",
        "## Status Summary",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    if status_counts:
        for status, count in sorted(status_counts.items()):
            lines.append(f"| {_markdown_cell(status)} | {count} |")
    else:
        lines.append("| UNKNOWN | 0 |")

    warnings = [str(item) for item in payload.get("warnings", []) if item]
    blockers = [str(item) for item in payload.get("blockers", []) if item]
    lines.extend(["", "## Warnings And Blockers", ""])
    lines.append(f"- Warnings: `{len(warnings)}`")
    for warning in warnings:
        lines.append(f"  - `{_markdown_cell(warning)}`")
    lines.append(f"- Blockers: `{len(blockers)}`")
    for blocker in blockers:
        lines.append(f"  - `{_markdown_cell(blocker)}`")

    lines.extend(
        [
            "",
            "## Entries",
            "",
            "| Kind | Status | Exists | Verified integrity | Path | Summary |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for entry in entries:
        lines.append(
            "| "
            + " | ".join(
                [
                    _markdown_cell(entry.get("kind", "UNKNOWN")),
                    _markdown_cell(entry.get("status", "UNKNOWN")),
                    _markdown_bool(entry.get("exists")),
                    _markdown_bool(entry.get("verified_integrity")),
                    f"`{_markdown_cell(entry.get('path', ''))}`",
                    _markdown_cell(entry.get("summary", "")),
                ]
            )
            + " |"
        )

    lines.extend(["", "## Next Safe Inspection Commands", ""])
    next_commands = []
    for entry in entries:
        if entry.get("exists") is True:
            continue
        command = str(entry.get("source_command") or "").strip()
        if command:
            next_commands.append(command)
    if next_commands:
        for command in next_commands[:10]:
            lines.append(f"- `{_markdown_cell(command)}`")
    else:
        lines.append("- No missing evidence producer commands were discovered.")

    lines.append("")
    return "\n".join(lines)


__all__ = ["render_evidence_bundle_index_markdown"]
