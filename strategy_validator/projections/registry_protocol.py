from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class ProjectionRegistryEntry(BaseModel):
    projection_family: str = Field(min_length=1)
    projection_label: str = Field(min_length=1)
    output_artifact_labels: tuple[str, ...] = ()
    supports_checkpoints: bool = False
    rebuild_handler: str = Field(min_length=1)

    model_config = {'extra': 'forbid'}


def default_projection_registry() -> tuple[ProjectionRegistryEntry, ...]:
    return (
        ProjectionRegistryEntry(
            projection_family='canonical_event_projection',
            projection_label='oracle_derived_view',
            output_artifact_labels=('derived-view',),
            supports_checkpoints=True,
            rebuild_handler='strategy_validator.application.projection_backfill.backfill_projection_family',
        ),
        ProjectionRegistryEntry(
            projection_family='canonical_event_checkpoint_projection',
            projection_label='oracle_event_checkpoint',
            output_artifact_labels=('checkpoint',),
            supports_checkpoints=True,
            rebuild_handler='strategy_validator.application.projection_backfill.backfill_projection_family',
        ),
        ProjectionRegistryEntry(
            projection_family='operator_action_event_projection',
            projection_label='operator_action_event_index',
            output_artifact_labels=('operator-action-event-index',),
            supports_checkpoints=False,
            rebuild_handler='strategy_validator.projections.operator_action_event_index.write_operator_action_event_projection_index',
        ),
    )
