from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import List, Tuple, Set

import pandas as pd
from strategy_validator.contracts.data_spine import UniverseProvenance, AssetMembership


def _to_utc_timestamp(value: datetime) -> pd.Timestamp:
    """Convert decision timestamps to UTC without reinterpreting aware offsets."""
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")

class PITUniverseGovernor:
    """
    Enforces lawful Point-In-Time universe membership.
    Protects against survivorship bias by strictly filtering assets based on 
    their validity windows at the decision timestamp.
    """
    
    def __init__(self, universe_id: str, snapshot_hash: str):
        self.universe_id = universe_id
        self.snapshot_hash = snapshot_hash

    def get_lawful_membership(
        self, 
        membership_df: pd.DataFrame, 
        decision_time: datetime,
        asset_ids: List[str] | None = None
    ) -> UniverseProvenance:
        """
        Calculates the lawful membership for a given decision time.
        membership_df must have: [asset_id, valid_from, valid_to]
        """
        # 1. Filter by Decision Time
        df = membership_df.copy()
        df["valid_from"] = pd.to_datetime(df["valid_from"], utc=True)
        df["valid_to"] = pd.to_datetime(df["valid_to"], utc=True)
        
        utc_dt = _to_utc_timestamp(decision_time)
        
        is_member = (df["valid_from"] <= utc_dt) & (df["valid_to"] >= utc_dt)
        members = df[is_member].copy()
        
        if asset_ids:
            # If specific assets were requested, report on their status
            requested_df = pd.DataFrame({"asset_id": asset_ids})
            results = pd.merge(requested_df, df, on="asset_id", how="left")
            results["is_member"] = (results["valid_from"] <= utc_dt) & (results["valid_to"] >= utc_dt)
            results["is_member"] = results["is_member"].fillna(False)
        else:
            results = members
            results["is_member"] = True

        memberships = [
            AssetMembership(
                asset_id=row["asset_id"],
                is_member=bool(row["is_member"]),
                valid_from_utc=row["valid_from"].to_pydatetime() if pd.notna(row["valid_from"]) else None,
                valid_to_utc=row["valid_to"].to_pydatetime() if pd.notna(row["valid_to"]) else None,
                inclusion_reason=row.get("inclusion_reason")
            )
            for _, row in results.iterrows()
        ]

        return UniverseProvenance(
            universe_id=self.universe_id,
            universe_snapshot_hash=self.snapshot_hash,
            decision_time_utc=utc_dt.to_pydatetime(),
            member_count=len(members),
            memberships=memberships
        )

    def filter_df_to_universe(
        self, 
        df: pd.DataFrame, 
        membership_df: pd.DataFrame, 
        decision_time: datetime,
        asset_col: str = "asset_id"
    ) -> Tuple[pd.DataFrame, UniverseProvenance]:
        """
        Drops all observations for assets that are not lawfully in universe 
        at the decision time.
        """
        prov = self.get_lawful_membership(membership_df, decision_time, asset_ids=list(df[asset_col].unique()))
        lawful_assets = {m.asset_id for m in prov.memberships if m.is_member}
        
        out = df[df[asset_col].isin(lawful_assets)].copy()
        return out.reset_index(drop=True), prov
