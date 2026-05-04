from __future__ import annotations

from pydantic import BaseModel, Field


class UiBurninQuery(BaseModel):
    artifact_paths: list[str] = Field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return {
            "artifact_paths": list(self.artifact_paths),
        }


class UiRuntimeQuery(BaseModel):
    role: str = "operator"

    def to_payload(self) -> dict[str, object]:
        return {
            "role": self.role,
        }


class UiTribunalQuery(BaseModel):
    def to_payload(self) -> dict[str, object]:
        return {}


__all__ = ["UiBurninQuery", "UiRuntimeQuery", "UiTribunalQuery"]
