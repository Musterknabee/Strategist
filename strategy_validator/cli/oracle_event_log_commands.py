from __future__ import annotations

import argparse
from collections.abc import Callable

from strategy_validator.cli.command_registry import CommandSpec, register_commands


RunnerMap = dict[str, Callable[..., int]]


def register_oracle_event_log_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: RunnerMap,
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-event-log-append', 'Append verified daily oracle evidence into a canonical append-only Oracle Event Log', _configure_oracle_event_log_append, runners['oracle-event-log-append']),
            CommandSpec('oracle-derived-view', 'Build a rolling derived doctrine view from the canonical Oracle Event Log', _configure_oracle_derived_view, runners['oracle-derived-view']),
            CommandSpec('oracle-horizon-view', 'Preferred converged oracle view: derive weekly/monthly/quarterly/semiannual/annual/constitutional posture directly from the canonical Oracle Event Log', _configure_oracle_horizon_view, runners['oracle-horizon-view']),
            CommandSpec('oracle-rolling-review', 'Preferred converged rolling review: derive weekly/monthly/quarterly/semiannual/annual/constitutional posture from the canonical Oracle Event Log', _configure_oracle_rolling_review, runners['oracle-rolling-review']),
            CommandSpec('oracle-rolling-review-checkpoint', 'Preferred converged checkpoint: freeze a named rolling review directly from the canonical Oracle Event Log', _configure_oracle_rolling_review_checkpoint, runners['oracle-rolling-review-checkpoint']),
            CommandSpec('oracle-event-checkpoint', 'Freeze a rolling derived view and event-log window into a signed checkpoint bundle', _configure_oracle_event_checkpoint, runners['oracle-event-checkpoint']),
            CommandSpec('oracle-horizon-checkpoint', 'Preferred converged checkpoint: freeze a named horizon view from the canonical Oracle Event Log into signed checkpoint evidence', _configure_oracle_horizon_checkpoint, runners['oracle-horizon-checkpoint']),
            CommandSpec('verify-oracle-event-checkpoint', 'Verify signed oracle event checkpoint evidence', _configure_verify_oracle_event_checkpoint, runners['verify-oracle-event-checkpoint']),
        ],
    )


def _configure_oracle_event_log_append(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('manifest', help='ORACLE_EVIDENCE.json path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--dsse', default='', help='Optional DSSE envelope path')
    parser.add_argument('--public-key', default='', help='Optional Ed25519 public key PEM used to verify DSSE')
    parser.add_argument('--log-path', required=True, help='Append-only JSONL oracle event log path')
    parser.add_argument('--verification-output', default='', help='Write verification JSON path')
    parser.add_argument('--output', default='', help='Write ORACLE_EVENT_LOG_ENTRY.json path')


def _configure_oracle_derived_view(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--log-path', required=True, help='Append-only JSONL oracle event log path')
    parser.add_argument('--view-label', default='rolling', help='Label for the derived view window')
    parser.add_argument('--window-size', type=int, default=7, help='Rolling window size in event-log entries')
    parser.add_argument('--output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')


def _configure_oracle_horizon_view(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--log-path', default='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl', help='Append-only JSONL oracle event log path')
    parser.add_argument('--horizon', default='weekly', help='Named horizon preset for the derived view')
    parser.add_argument('--window-size', type=int, default=0, help='Override the default window size for the selected horizon; 0 uses the canonical preset')
    parser.add_argument('--output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')


def _configure_oracle_rolling_review(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--log-path', default='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl', help='Append-only JSONL oracle event log path')
    parser.add_argument('--horizon', default='weekly', help='Named horizon preset for the rolling review')
    parser.add_argument('--window-size', type=int, default=0, help='Override the default window size for the selected horizon; 0 uses the canonical preset')
    parser.add_argument('--output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')


def _configure_oracle_rolling_review_checkpoint(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--log-path', default='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl', help='Append-only JSONL oracle event log path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--horizon', default='weekly', help='Named horizon preset for the rolling review')
    parser.add_argument('--window-size', type=int, default=0, help='Override the default window size for the selected horizon; 0 uses the canonical preset')
    parser.add_argument('--signing-private-key', default='', help='Optional Ed25519 private key PEM for DSSE signing')
    parser.add_argument('--report-output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')
    parser.add_argument('--checkpoint-markdown-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.md path')
    parser.add_argument('--output', default='', help='Write ORACLE_EVENT_CHECKPOINT.json path')
    parser.add_argument('--dsse-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.dsse.json path')
    parser.add_argument('--verification-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.verification.json path')


def _configure_oracle_event_checkpoint(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--lane-path', required=True, help='Append-only JSONL oracle event log path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--view-label', default='rolling', help='Label for the derived view window')
    parser.add_argument('--window-size', type=int, default=7, help='Rolling window size in event-log entries')
    parser.add_argument('--signing-private-key', default='', help='Optional Ed25519 private key PEM for DSSE signing')
    parser.add_argument('--report-output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')
    parser.add_argument('--checkpoint-markdown-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.md path')
    parser.add_argument('--output', default='', help='Write ORACLE_EVENT_CHECKPOINT.json path')
    parser.add_argument('--dsse-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.dsse.json path')
    parser.add_argument('--verification-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.verification.json path')


def _configure_oracle_horizon_checkpoint(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--log-path', default='docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl', help='Append-only JSONL oracle event log path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--horizon', default='weekly', help='Named horizon preset for the checkpoint')
    parser.add_argument('--window-size', type=int, default=0, help='Override the default window size for the selected horizon; 0 uses the canonical preset')
    parser.add_argument('--signing-private-key', default='', help='Optional Ed25519 private key PEM for DSSE signing')
    parser.add_argument('--report-output', default='', help='Write ORACLE_DERIVED_VIEW.json path')
    parser.add_argument('--markdown-output', default='', help='Write ORACLE_DERIVED_VIEW.md path')
    parser.add_argument('--checkpoint-metadata-output', default='', help='Write incremental ORACLE_DERIVED_VIEW checkpoint metadata JSON path')
    parser.add_argument('--checkpoint-markdown-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.md path')
    parser.add_argument('--output', default='', help='Write ORACLE_EVENT_CHECKPOINT.json path')
    parser.add_argument('--dsse-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.dsse.json path')
    parser.add_argument('--verification-output', default='', help='Write ORACLE_EVENT_CHECKPOINT.verification.json path')


def _configure_verify_oracle_event_checkpoint(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('manifest', help='ORACLE_EVENT_CHECKPOINT.json path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--dsse', default='', help='Optional DSSE envelope path')
    parser.add_argument('--public-key', default='', help='Optional Ed25519 public key PEM')
    parser.add_argument('--output', default='', help='Write ORACLE_EVENT_CHECKPOINT.verification.json path')
