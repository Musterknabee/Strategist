from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
@dataclass(frozen=True)
class OracleTrustBanner:
    trust_status: str = "TRUST_RESTRICTED"
    lineage_reason: str = "Lineage could not be fully verified from supplied artifact context."
    remediation: str|None = None
    evidence: tuple[str,...] = field(default_factory=tuple)
    def model_dump(self, mode: str="json")->dict[str,Any]:
        return {"trust_status":self.trust_status,"lineage_reason":self.lineage_reason,"remediation":self.remediation,"evidence":list(self.evidence)}
def infer_repo_root_from_artifact_path(path: str|Path)->Path:
    cur=Path(path).resolve()
    if cur.is_file(): cur=cur.parent
    for c in (cur,*cur.parents):
        if (c/"pyproject.toml").exists() or (c/"strategy_validator").exists(): return c
    return cur
def maybe_verify_oracle_lineage(*args: Any, **kwargs: Any)->OracleTrustBanner: return OracleTrustBanner()
def trust_banner_for_lineage_verification(verification: Any)->OracleTrustBanner:
    seal=getattr(verification,"seal_status",None); comp=getattr(verification,"completeness_percent",None)
    ok=seal in {"SEALED","VERIFIED"} and (comp is None or float(comp)>=100.0)
    return OracleTrustBanner(trust_status="TRUSTED" if ok else "TRUST_RESTRICTED", lineage_reason=f"lineage seal_status={seal or 'UNKNOWN'} completeness={comp if comp is not None else 'UNKNOWN'}")
def trust_banner_for_constitutional_gate(*args: Any, **kwargs: Any)->OracleTrustBanner: return OracleTrustBanner(lineage_reason="Constitutional gate trust requires current machine evidence.")
def trust_banner_for_derived_view(*args: Any, **kwargs: Any)->OracleTrustBanner: return OracleTrustBanner(lineage_reason="Derived view trust is restricted unless checkpoint-backed.")
def trust_banner_for_event_checkpoint(*args: Any, **kwargs: Any)->OracleTrustBanner: return OracleTrustBanner(lineage_reason="Event checkpoint trust requires signed checkpoint verification.")
def trust_banner_for_legacy_surface(*args: Any, **kwargs: Any)->OracleTrustBanner: return OracleTrustBanner(lineage_reason="Legacy surface is advisory and trust-restricted by default.")
def render_oracle_trust_banner(banner: OracleTrustBanner)->str: return f"[{banner.trust_status}] {banner.lineage_reason}"
