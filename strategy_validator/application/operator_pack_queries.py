from __future__ import annotations

from pathlib import Path

from strategy_validator.application.projection_queries import (
    build_operator_pack_query_request,
    query_operator_packs,
)
from strategy_validator.control_plane.operator_pack_navigation import (
    build_operator_pack_navigation_request,
    materialize_operator_pack_navigation,
)
from strategy_validator.control_plane.operator_pack_timeline import (
    build_operator_pack_timeline_request,
    materialize_operator_pack_timeline,
)
from strategy_validator.control_plane.operator_pack_workbench import (
    build_operator_pack_workbench_request,
    materialize_operator_pack_workbench,
)
from strategy_validator.projections.operator_terminal_record_service import (
    materialize_operator_terminal_record_publication,
)


def build_operator_pack_query_payload(**kwargs) -> dict:
    return query_operator_packs(build_operator_pack_query_request(**kwargs)).to_payload()



def build_operator_pack_workbench_payload(**kwargs) -> dict:
    return materialize_operator_pack_workbench(
        build_operator_pack_workbench_request(**kwargs)
    ).to_payload()



def build_operator_pack_navigation_payload(**kwargs) -> dict:
    return materialize_operator_pack_navigation(
        build_operator_pack_navigation_request(**kwargs)
    ).to_payload()



def build_operator_pack_timeline_payload(**kwargs) -> dict:
    return materialize_operator_pack_timeline(
        build_operator_pack_timeline_request(**kwargs)
    ).to_payload()



def publish_operator_terminal_record_payload(
    *,
    publication_root: Path,
    record,
    repo_root: Path | None = None,
    index_path: Path | None = None,
) -> dict:
    publication = materialize_operator_terminal_record_publication(
        publication_root,
        record,
        repo_root=repo_root,
        index_path=index_path,
    )
    return {
        'schema_version': 'oracle_operator_terminal_record_publication/v1',
        'record': record.to_payload(),
        'manifest': publication.manifest,
        'index': publication.index,
        'publication_root': str(publication.result.publication_root),
        'json_path': str(publication.result.json_path),
        'markdown_path': str(publication.result.markdown_path),
        'manifest_path': str(publication.result.manifest_path),
        'index_path': str(publication.result.index_path),
    }


__all__ = [
    'build_operator_pack_query_payload',
    'build_operator_pack_workbench_payload',
    'build_operator_pack_navigation_payload',
    'build_operator_pack_timeline_payload',
    'publish_operator_terminal_record_payload',
]
