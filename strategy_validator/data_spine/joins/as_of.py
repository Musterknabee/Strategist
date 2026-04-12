"""Point-in-time as-of joins with explicit revision policy and UTC semantics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Tuple, List

import pandas as pd
from strategy_validator.contracts.data_spine import PITJoinProvenance, RevisionLineageProvenance

FeatureKind = Literal["standard", "macro"]
RevisionSelection = Literal["latest_revision", "earliest_revision"]


def _require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"{label}: missing required columns: {missing}")


def _assert_series_utc_datetime(s: pd.Series, name: str) -> pd.Series:
    if not pd.api.types.is_datetime64_any_dtype(s):
        raise TypeError(f"{name}: expected datetime64 dtype, got {s.dtype}")
    tz = getattr(s.dtype, "tz", None)
    if tz is None:
        raise ValueError(f"{name}: naive datetimes are rejected; use tz-aware UTC")
    if str(tz) != "UTC":
        raise ValueError(f"{name}: only UTC storage is allowed; got tz={tz!r}")
    return s


@dataclass(frozen=True)
class AsOfJoinEngine:
    decision_time_col: str
    available_at_col: str
    group_keys: list[str]
    latency_buffer_ms: int = 0
    macro_embargo_ms: int = 0
    feature_kind: FeatureKind = "standard"
    revision_col: str | None = None
    revision_selection: RevisionSelection = "latest_revision"

    def __post_init__(self):
        if self.latency_buffer_ms < 0:
            raise ValueError("latency_buffer_ms must be non-negative")
        if self.macro_embargo_ms < 0:
            raise ValueError("macro_embargo_ms must be non-negative")
        if not self.group_keys:
            raise ValueError("group_keys must not be empty")
        if len(set(self.group_keys)) != len(self.group_keys):
            raise ValueError("duplicates detected in group_keys")

    def execute(self, target_df: pd.DataFrame, feature_df: pd.DataFrame, dataset_id: str = "unknown") -> Tuple[pd.DataFrame, PITJoinProvenance]:
        if self.feature_kind not in ("standard", "macro"):
            raise ValueError(f"feature_kind must be 'standard' or 'macro', got {self.feature_kind!r}")
        
        _require_columns(target_df, list(self.group_keys) + [self.decision_time_col], "target_df")
        required_feature = list(self.group_keys) + [self.available_at_col]
        if self.revision_col is not None:
            required_feature.append(self.revision_col)
        _require_columns(feature_df, required_feature, "feature_df")

        left = target_df.copy()
        right = feature_df.copy()
        left[self.decision_time_col] = _assert_series_utc_datetime(left[self.decision_time_col], self.decision_time_col)
        right[self.available_at_col] = _assert_series_utc_datetime(right[self.available_at_col], self.available_at_col)

        row_count_before = len(right)
        
        # Revision Lineage Selection
        right, lineage = self._apply_revision_policy_with_lineage(right, dataset_id)
        
        total_ms = self.latency_buffer_ms + (self.macro_embargo_ms if self.feature_kind == "macro" else 0)
        total_lag = pd.to_timedelta(total_ms, unit="ms")

        # Lawful Cutoff enforcement
        left["_pit_join_cutoff"] = left[self.decision_time_col] - total_lag
        
        left = left.sort_values(list(self.group_keys) + ["_pit_join_cutoff"], kind="mergesort").reset_index(drop=True)
        right = right.sort_values(list(self.group_keys) + [self.available_at_col], kind="mergesort").reset_index(drop=True)

        merged = pd.merge_asof(
            left,
            right,
            left_on="_pit_join_cutoff",
            right_on=self.available_at_col,
            by=self.group_keys,
            direction="backward",
            suffixes=("", "_pit_feature"),
        )
        
        out = merged.loc[merged[self.available_at_col].notna()].copy()
        
        provenance = PITJoinProvenance(
            dataset_id=dataset_id,
            decision_time_utc=left[self.decision_time_col].max().to_pydatetime(),
            available_at_cutoff_utc=(left[self.decision_time_col].max() - total_lag).to_pydatetime(),
            revision_policy=f"{self.revision_col or 'none'}:{self.revision_selection}",
            latency_buffer_ms=self.latency_buffer_ms,
            macro_embargo_ms=self.macro_embargo_ms if self.feature_kind == "macro" else 0,
            row_count_before=row_count_before,
            row_count_after=len(out),
            lineage=lineage
        )
        
        return out.reset_index(drop=True), provenance

    def _apply_revision_policy_with_lineage(
        self, 
        right: pd.DataFrame, 
        dataset_id: str
    ) -> Tuple[pd.DataFrame, RevisionLineageProvenance | None]:
        tie_keys = list(self.group_keys) + [self.available_at_col]
        
        # Optimization: skip lineage if no ties possible
        if not right.duplicated(subset=tie_keys, keep=False).any():
            return right, None
            
        if self.revision_col is None:
            raise ValueError(
                "Revision ties detected on feature availability; set revision_col and revision_selection explicitly."
            )

        ascending = self.revision_selection == "earliest_revision"
        sorted_right = right.sort_values(
            tie_keys + [self.revision_col],
            ascending=[True] * len(tie_keys) + [ascending],
        )
        
        # Capture winning vs discarded
        # Note: In a real production spine, we'd record the full set of discarded IDs.
        # Here we extract them from the sorted/dropped dataframe.
        keepers = sorted_right.drop_duplicates(subset=tie_keys, keep="first")
        discarded_mask = ~sorted_right.index.isin(keepers.index)
        discarded_ids = sorted_right.loc[discarded_mask, self.revision_col].astype(str).tolist()
        
        # Winning identification (taking example from first row for provenance simplicity)
        win_row = keepers.iloc[0]
        lineage = RevisionLineageProvenance(
            dataset_id=dataset_id,
            selected_revision_id=str(win_row[self.revision_col]),
            selected_available_at_utc=win_row[self.available_at_col].to_pydatetime(),
            discarded_revision_ids=discarded_ids[:50], # Sample for provenance
            revision_policy=self.revision_selection,
            selection_reason=f"Tie-break via {self.revision_selection} on {self.revision_col}"
        )
        
        return keepers, lineage
