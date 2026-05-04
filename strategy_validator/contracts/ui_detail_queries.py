from __future__ import annotations

from pydantic import BaseModel


class UiEvidenceQuery(BaseModel):
    repo_root: str | None = None
    search_root: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            'repo_root': self.repo_root,
            'search_root': self.search_root,
        }


class UiPackDetailQuery(BaseModel):
    search_root: str | None = None
    board_label: str = 'operator'
    pack_kind: str | None = None
    manifest_path: str | None = None

    def to_payload(self) -> dict[str, object]:
        return {
            'search_root': self.search_root,
            'board_label': self.board_label,
            'pack_kind': self.pack_kind,
            'manifest_path': self.manifest_path,
        }


__all__ = ['UiEvidenceQuery', 'UiPackDetailQuery']
