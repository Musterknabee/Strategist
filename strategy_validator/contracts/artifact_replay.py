"""Canonical replay-manifest contracts for paper research artifact integrity."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReplayArtifactEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str
    path: str
    sha256: str

    @field_validator("kind", "path")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("artifact fields must be non-empty")
        return text

    @field_validator("sha256")
    @classmethod
    def _sha256_hex(cls, value: str) -> str:
        text = value.strip()
        if len(text) != 64 or any(ch not in "0123456789abcdefABCDEF" for ch in text):
            raise ValueError("sha256 must be a 64-character hex digest")
        return text.lower()


class PaperResearchReplayManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["paper_research_replay_manifest/v1"] = "paper_research_replay_manifest/v1"
    artifact_id: str
    artifact_kind: str = "provider_paper_loop"
    generated_at_utc: datetime
    command: str
    command_args_redacted: tuple[str, ...] = ()
    git_commit: str = "UNKNOWN"
    code_fingerprint: str = "UNKNOWN"
    config_fingerprint: str = "UNKNOWN"
    provider_id: str = "UNKNOWN"
    provider_name: str = "UNKNOWN"
    provider_mode: str = "OFFLINE_REPLAY"
    provider_key_required: bool = False
    provider_key_present: bool = False
    trust_banner: str = "UNKNOWN"
    license_usage_caveat: str = "UNKNOWN"
    source_label: str = "UNKNOWN"
    replayable_offline: bool = True
    paper_only: bool = True
    live_trading_blocked: bool = True
    input_artifacts: tuple[ReplayArtifactEntry, ...] = ()
    output_artifacts: tuple[ReplayArtifactEntry, ...] = ()
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return value

    @field_validator("replayable_offline")
    @classmethod
    def _replayable_offline_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("replayable_offline must be true")
        return value

    @field_validator("paper_only")
    @classmethod
    def _paper_only_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("paper_only must be true")
        return value

    @field_validator("live_trading_blocked")
    @classmethod
    def _live_trading_blocked_true(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("live_trading_blocked must be true")
        return value


class PaperResearchReplayVerificationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["paper_research_replay_verify/v1"] = "paper_research_replay_verify/v1"
    ok: bool
    replay_manifest_path: str
    generated_at_utc: datetime
    input_artifact_count: int = Field(ge=0)
    output_artifact_count: int = Field(ge=0)
    missing_artifact_count: int = Field(ge=0)
    digest_mismatch_count: int = Field(ge=0)
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return value


__all__ = [
    "PaperResearchReplayManifest",
    "PaperResearchReplayVerificationSummary",
    "ReplayArtifactEntry",
]
