from __future__ import annotations

from pydantic import BaseModel, Field


class UiWorkboardQuery(BaseModel):
    board_label: str = 'operator'
    search_root: str | None = None
    pack_kinds: list[str] = Field(default_factory=list)
    trust_statuses: list[str] = Field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return {
            'board_label': self.board_label,
            'search_root': self.search_root,
            'pack_kinds': list(self.pack_kinds),
            'trust_statuses': list(self.trust_statuses),
        }


__all__ = ['UiWorkboardQuery']
