from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.projections.service import build_projection_artifact_query, run_projection_artifact_operator_query


def register_oracle_projection_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec(
                'oracle-projection-artifact-query',
                'Query the shared projection artifact index for discoverable oracle projection outputs',
                _configure_oracle_projection_artifact_query,
                runners['oracle-projection-artifact-query'],
            )
        ],
    )


def _configure_oracle_projection_artifact_query(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--search-root', required=True, help='Artifact search root containing ORACLE_PROJECTION_ARTIFACT_INDEX.json files')
    parser.add_argument('--repo-root', default='', help='Optional repository root used for artifact path resolution')
    parser.add_argument('--projection-label', action='append', default=[], help='Optional projection label filter; may be passed multiple times')
    parser.add_argument('--projection-family', default='', help='Optional projection family filter')
    parser.add_argument('--output-artifact-label-contains', default='', help='Optional substring filter over indexed output artifact labels')
    parser.add_argument('--output', default='', help='Write ORACLE_PROJECTION_ARTIFACT_QUERY_REPORT.json path')


def cmd_oracle_projection_artifact_query(ns: argparse.Namespace) -> int:
    query = build_projection_artifact_query(
        search_root=Path(ns.search_root).resolve(),
        repo_root=Path(ns.repo_root).resolve() if getattr(ns, 'repo_root', '') else None,
        projection_labels=tuple(label.strip() for label in getattr(ns, 'projection_label', []) if label.strip()),
        projection_family=(ns.projection_family or None),
        output_artifact_label_contains=(ns.output_artifact_label_contains or None),
    )
    payload = run_projection_artifact_operator_query(query).to_payload()
    if ns.output:
        output_path = Path(ns.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    else:
        print(json.dumps(payload, indent=2))
    return 0
