"""Compatibility facade for Research OS handoff verification and reviewer signoff operations."""
from __future__ import annotations

from strategy_validator.application.research_os_handoff_signoff_common import (
    _SCHEMA,
    _artifact_root,
    _canonical_sha256,
    _contains_secret_marker,
    _list,
    _observed_handoff_spine,
    _observed_manifest_sha,
    _read_json,
    _sha256_file,
    _write_json,
    research_os_handoff_reviewer_signoff_latest_path,
    research_os_handoff_signoff_root,
    research_os_handoff_verification_latest_path,
)
from strategy_validator.application.research_os_handoff_signoff_reviewer import (
    _with_signoff_digest,
    build_and_write_research_os_handoff_reviewer_signoff,
    build_research_os_handoff_reviewer_signoff,
    load_latest_research_os_handoff_reviewer_signoff,
    write_research_os_handoff_reviewer_signoff,
)
from strategy_validator.application.research_os_handoff_signoff_ui import build_ui_research_os_handoff_signoff_latest_payload
from strategy_validator.application.research_os_handoff_signoff_verification import (
    _source_check,
    _with_verification_digest,
    build_and_write_research_os_handoff_verification_result,
    build_research_os_handoff_verification_result,
    load_latest_research_os_handoff_verification_result,
    write_research_os_handoff_verification_result,
)

__all__ = [
    "_SCHEMA",
    "_artifact_root",
    "_canonical_sha256",
    "_contains_secret_marker",
    "_list",
    "_observed_handoff_spine",
    "_observed_manifest_sha",
    "_read_json",
    "_sha256_file",
    "_source_check",
    "_with_signoff_digest",
    "_with_verification_digest",
    "_write_json",
    "build_and_write_research_os_handoff_reviewer_signoff",
    "build_and_write_research_os_handoff_verification_result",
    "build_research_os_handoff_reviewer_signoff",
    "build_research_os_handoff_verification_result",
    "build_ui_research_os_handoff_signoff_latest_payload",
    "load_latest_research_os_handoff_reviewer_signoff",
    "load_latest_research_os_handoff_verification_result",
    "research_os_handoff_reviewer_signoff_latest_path",
    "research_os_handoff_signoff_root",
    "research_os_handoff_verification_latest_path",
    "write_research_os_handoff_reviewer_signoff",
    "write_research_os_handoff_verification_result",
]
