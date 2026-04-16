"""
Sink-neutral runtime metrics export (Prometheus textfile / pushgateway-style).

Must never disturb adjudication — same contract as telemetry sinks.
"""
from __future__ import annotations

import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class MetricsSink(Protocol):
    def emit_metrics(self, lines: str) -> None: ...


class PrometheusTextfileSink:
    """Append Prometheus exposition text lines to a file (node_exporter textfile collector)."""

    def __init__(self, path: str):
        self._path = path

    def emit_metrics(self, lines: str) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(lines)
            if not lines.endswith("\n"):
                f.write("\n")


class PrometheusPushgatewaySink:
    """POST ``text/plain`` metrics body to a Pushgateway-compatible endpoint."""

    def __init__(self, url: str, *, job: str = "strategy_validator", timeout_seconds: float = 5.0):
        self._url = url.rstrip("/") + f"/metrics/job/{urllib.parse.quote(job, safe='')}"
        self._timeout = timeout_seconds

    def emit_metrics(self, lines: str) -> None:
        body = lines.encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=body,
            method="POST",
            headers={"Content-Type": "text/plain; version=0.0.4"},
        )
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            resp.read()


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def build_runtime_metrics_lines(labels: dict[str, str], gauges: dict[str, float]) -> str:
    """Build minimal Prometheus exposition lines (no timestamps)."""
    lb = ",".join(f'{k}="{_escape_label(str(v))}"' for k, v in sorted(labels.items()))
    lines = []
    for name, val in sorted(gauges.items()):
        lines.append(f"{name}{{{lb}}} {val}")
    return "\n".join(lines) + "\n"


def emit_runtime_metrics(*, readiness_status: str, blocker_count: int, schema_ok: bool) -> None:
    """
    Emit a small fixed-cardinality metric bundle to configured sinks.

    Swallows all failures.
    """
    labels = {
        "readiness": readiness_status,
    }
    gauges = {
        "strategy_validator_blocker_count": float(blocker_count),
        "strategy_validator_schema_ok": 1.0 if schema_ok else 0.0,
    }
    text = build_runtime_metrics_lines(labels, gauges)

    path = os.environ.get("STRATEGY_VALIDATOR_METRICS_TEXTFILE_PATH")
    if path:
        try:
            PrometheusTextfileSink(path).emit_metrics(text)
        except OSError as exc:
            logger.warning("METRICS_TEXTFILE_FAILED: %s", exc)

    push = os.environ.get("STRATEGY_VALIDATOR_METRICS_PUSHGATEWAY_URL")
    if push:
        try:
            job = os.environ.get("STRATEGY_VALIDATOR_METRICS_PUSH_JOB", "strategy_validator")
            PrometheusPushgatewaySink(push, job=job).emit_metrics(text)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            logger.warning("METRICS_PUSHGATEWAY_FAILED: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("METRICS_PUSHGATEWAY_FAILED: %s", exc)
