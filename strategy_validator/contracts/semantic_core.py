from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

# Strict types with non-empty constraints
NonEmptyString = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


class SemanticBaseModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
