/**
 * Top-level GET /ui/evidence cockpit fields (backend ui_evidence_cockpit_summary).
 */
import { asString } from "@/lib/operator/payload-utils";

export type UiEvidenceCockpitFields = {
  deployment_status: string | undefined;
  deployment_evidence_ok: boolean | null | undefined;
  operator_decision: string | undefined;
  manual_operator_signoff_present: boolean | null | undefined;
  api_smoke_status: string | undefined;
  api_smoke_ok: boolean | null | undefined;
  backup_restore_ok: boolean | null | undefined;
  ledger_integrity_ok: boolean | null | undefined;
  ci_local_verify_ok: boolean | null | undefined;
  frontend_readiness_status: string | undefined;
  evidence_generated_at_utc: string | undefined;
};

function triBool(v: unknown): boolean | null | undefined {
  if (v === null) return null;
  if (typeof v === "boolean") return v;
  return undefined;
}

/** Extract stable cockpit keys from an evidence payload record. */
export function readUiEvidenceCockpit(ev: Record<string, unknown> | null | undefined): UiEvidenceCockpitFields | null {
  if (!ev) return null;
  return {
    deployment_status: asString(ev.deployment_status),
    deployment_evidence_ok: triBool(ev.deployment_evidence_ok),
    operator_decision: asString(ev.operator_decision),
    manual_operator_signoff_present: triBool(ev.manual_operator_signoff_present),
    api_smoke_status: asString(ev.api_smoke_status),
    api_smoke_ok: triBool(ev.api_smoke_ok),
    backup_restore_ok: triBool(ev.backup_restore_ok),
    ledger_integrity_ok: triBool(ev.ledger_integrity_ok),
    ci_local_verify_ok: triBool(ev.ci_local_verify_ok),
    frontend_readiness_status: asString(ev.frontend_readiness_status),
    evidence_generated_at_utc: asString(ev.evidence_generated_at_utc),
  };
}

export function formatCockpitOk(v: boolean | null | undefined): string {
  if (v === true) return "yes";
  if (v === false) return "no";
  return "—";
}
