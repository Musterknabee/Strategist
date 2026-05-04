from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands


def register_oracle_temporal_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec(
                'extract-temporal-semantic-batch',
                'Extract provisional day-isolated temporal semantics through the configured semantic provider',
                _configure_extract_temporal_semantic_batch,
                runners['extract-temporal-semantic-batch'],
            ),
            CommandSpec(
                'verify-temporal-semantic-batch',
                'Verify a temporal semantic batch manifest for PIT, ordering, and citation-lawfulness',
                _configure_verify_temporal_semantic_batch,
                runners['verify-temporal-semantic-batch'],
            ),
            CommandSpec(
                'canonicalize-temporal-semantic-batch',
                'Materialize a verified temporal semantic batch into daily oracle evidence artifacts',
                _configure_canonicalize_temporal_semantic_batch,
                runners['canonicalize-temporal-semantic-batch'],
            ),
            CommandSpec(
                'append-temporal-canonicalization-event-log',
                'Append canonicalized daily oracle evidence artifacts into the Oracle Event Log',
                _configure_append_temporal_canonicalization_event_log,
                runners['append-temporal-canonicalization-event-log'],
            ),
            CommandSpec(
                'summarize-temporal-lane',
                'Summarize temporal extraction, verification, canonicalization, and append coverage for operators',
                _configure_summarize_temporal_lane,
                runners['summarize-temporal-lane'],
            ),
            CommandSpec(
                'fetch-openbb-temporal-sensor-inputs',
                'Fetch OpenBB-backed macro and microstructure daily sensor ingress payloads',
                _configure_fetch_openbb_temporal_sensor_inputs,
                runners['fetch-openbb-temporal-sensor-inputs'],
            ),
            CommandSpec(
                'canonicalize-temporal-semantic-batch-openbb',
                'Fetch OpenBB-backed daily sensor ingress payloads and canonicalize a temporal semantic batch',
                _configure_canonicalize_temporal_semantic_batch_openbb,
                runners['canonicalize-temporal-semantic-batch-openbb'],
            ),
        ],
    )


def _configure_extract_temporal_semantic_batch(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--input', required=True, help='Temporal semantic extraction batch request JSON path')
    parser.add_argument('--config', default='', help='Optional config path for provider enablement/settings')
    parser.add_argument('--artifact-root', default='', help='Optional artifact directory for raw request/response capture')
    parser.add_argument('--temperature', type=float, default=0.0, help='Semantic extraction temperature')
    parser.add_argument('--output', default='', help='Write extraction payload JSON path')


def _configure_verify_temporal_semantic_batch(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--input', required=True, help='Temporal semantic batch manifest JSON path')
    parser.add_argument('--output', default='', help='Write verification payload JSON path')


def _configure_canonicalize_temporal_semantic_batch(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--input', required=True, help='Temporal semantic batch manifest JSON path')
    parser.add_argument('--universe-label', required=True, help='Universe label for resulting daily sensor payloads')
    parser.add_argument('--output-root', required=True, help='Artifact root for canonical daily oracle outputs')
    parser.add_argument('--macro-by-date', required=True, help='JSON mapping YYYY-MM-DD -> OracleSensorRawMacroInput')
    parser.add_argument('--microstructure-by-date', required=True, help='JSON mapping YYYY-MM-DD -> OracleSensorRawMicrostructureInput')
    parser.add_argument('--generated-for-by-date', default='', help='Optional JSON mapping YYYY-MM-DD -> ISO timestamp')
    parser.add_argument('--strategies-by-date', default='', help='Optional JSON mapping YYYY-MM-DD -> list[StrategyHealthSnapshot]')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for relative path resolution')
    parser.add_argument('--output', default='', help='Write canonicalization payload JSON path')


def _configure_append_temporal_canonicalization_event_log(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--input', required=True, help='Temporal canonicalization batch result JSON path')
    parser.add_argument('--log-path', required=True, help='Oracle Event Log JSONL path')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for relative path resolution')
    parser.add_argument('--require-complete-success', action='store_true', help='Fail closed when any day was skipped during canonicalization')
    parser.add_argument('--output', default='', help='Write event-log append payload JSON path')


def _configure_summarize_temporal_lane(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--manifest', required=True, help='Temporal semantic batch manifest JSON path')
    parser.add_argument('--universe-label', required=True, help='Universe label for operator summary context')
    parser.add_argument('--verification', default='', help='Optional temporal verification JSON path')
    parser.add_argument('--canonicalization', default='', help='Optional canonicalization JSON path')
    parser.add_argument('--append-report', default='', help='Optional temporal event-log append JSON path')
    parser.add_argument('--output', default='', help='Write temporal status payload JSON path')
    parser.add_argument('--artifact-root', default='', help='Optional artifact directory for ORACLE_TEMPORAL_LANE_STATUS.json')


def _configure_fetch_openbb_temporal_sensor_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--dates', required=True, help='JSON array of YYYY-MM-DD dates')
    parser.add_argument('--universe-label', required=True, help='Universe label for OpenBB sensor ingress')
    parser.add_argument('--config', default='', help='Optional config path for OpenBB provider enablement/settings')
    parser.add_argument('--output', default='', help='Write ingress payload JSON path')


def _configure_canonicalize_temporal_semantic_batch_openbb(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--input', required=True, help='Temporal semantic batch manifest JSON path')
    parser.add_argument('--universe-label', required=True, help='Universe label for resulting daily sensor payloads')
    parser.add_argument('--output-root', required=True, help='Artifact root for canonical daily oracle outputs')
    parser.add_argument('--config', default='', help='Optional config path for OpenBB provider enablement/settings')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for relative path resolution')
    parser.add_argument('--generated-for-by-date', default='', help='Optional JSON mapping YYYY-MM-DD -> ISO timestamp')
    parser.add_argument('--strategies-by-date', default='', help='Optional JSON mapping YYYY-MM-DD -> list[StrategyHealthSnapshot]')
    parser.add_argument('--output', default='', help='Write canonicalization payload JSON path')
