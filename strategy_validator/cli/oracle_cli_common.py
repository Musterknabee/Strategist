"""Shared CLI helpers for oracle/reporting command surfaces."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")



def write_markdown(path: Path, content: str, *, banner: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((banner + content) if banner else content, encoding="utf-8")



def print_or_write_payload(payload: dict, output: str = "") -> None:
    if output:
        write_json(Path(output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")



def parse_utc(raw: str) -> datetime:
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)



def emit_report(
    report: Any,
    *,
    output: str = "",
    markdown_output: str = "",
    render_markdown: Callable[[Any], str],
    banner: str = "",
) -> None:
    payload = report.model_dump(mode="json")
    print_or_write_payload(payload, output)
    if markdown_output:
        write_markdown(Path(markdown_output), render_markdown(report), banner=banner)
