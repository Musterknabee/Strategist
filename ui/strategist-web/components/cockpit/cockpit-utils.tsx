import type { ReactNode } from "react";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { DenseColumn } from "@/components/terminal/DenseTable";
import { TermKV } from "@/components/terminal/TermKV";
import { asRecord, asString, classifyOperationalStatus } from "@/lib/operator/payload-utils";
import type {
  ActionRow,
  EvidenceRow,
  MatrixRow,
  ProviderRow,
  StatusTone,
  StrategyRow,
  WorkRow,
} from "./cockpit-types";

export const UNKNOWN = "UNKNOWN";

export function value(v: unknown, fallback = UNKNOWN): string {
  if (typeof v === "string" && v.trim()) return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  return fallback;
}

export function boolStatus(v: boolean | null | undefined, ok = "OK", bad = "DEGRADED"): string {
  if (v === true) return ok;
  if (v === false) return bad;
  return UNKNOWN;
}

export function digest(v: unknown): string {
  const s = asString(v);
  return s ? s.slice(0, 18) : "PENDING";
}

export function entryTime(e: Record<string, unknown>): string {
  return (
    asString(e.accepted_at_utc) ??
    asString(e.event_time_utc) ??
    asString(e.occurred_at_utc) ??
    asString(e.timestamp_utc) ??
    asString(e.updated_at_utc) ??
    "PENDING"
  );
}

export function inspectBody({
  status,
  summary,
  warnings = [],
  details = [],
}: {
  status: string;
  summary: string;
  warnings?: string[];
  details?: { k: string; v: ReactNode }[];
}) {
  return (
    <div className="inspector-stack">
      <TermKV rows={[{ k: "status", v: <StatusBadge raw={status} /> }, ...details]} />
      <div className="inspector-section">
        <span className="inspector-label">SUMMARY</span>
        <p>{summary}</p>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">WARNINGS</span>
        {warnings.length ? (
          warnings.map((w) => <p key={w}>{w}</p>)
        ) : (
          <p>NONE_REPORTED</p>
        )}
      </div>
    </div>
  );
}

export function metricTone(status: string): StatusTone {
  return classifyOperationalStatus(status);
}

export function buildReadinessColumns(): DenseColumn<MatrixRow>[] {
  return [
    { key: "id", header: "Check ID", cell: (r) => <code>{r.checkId}</code> },
    { key: "st", header: "Status", width: "76px", cell: (r) => <StatusBadge raw={r.status} /> },
    { key: "sev", header: "Severity", width: "64px", cell: (r) => r.severity },
    { key: "code", header: "Blocker Code", cell: (r) => r.blockerCode },
    { key: "rem", header: "Remediation", cell: (r) => r.remediation },
  ];
}

export function buildEvidenceColumns(): DenseColumn<EvidenceRow>[] {
  return [
    { key: "step", header: "Step", cell: (r) => r.step },
    { key: "status", header: "Status", width: "92px", cell: (r) => <StatusBadge raw={r.status} /> },
    { key: "digest", header: "Digest", cell: (r) => <code>{r.digest}</code> },
    { key: "time", header: "Time UTC", cell: (r) => r.time },
  ];
}

export function buildProviderColumns(): DenseColumn<ProviderRow>[] {
  return [
    {
      key: "p",
      header: "Provider",
      cell: (r) => <span className={r.__id === "alpaca" ? "term-row-emph" : ""}>{asString(r.display_name) ?? r.__id}</span>,
    },
    { key: "a", header: "Access", cell: (r) => value(r.access_type) },
    { key: "s", header: "Status", width: "96px", cell: (r) => <StatusBadge raw={asString(r.classified_status)} /> },
    { key: "pit", header: "PIT", cell: (r) => value(r.pit_suitability) },
    { key: "t", header: "Trust", cell: (r) => value(r.trust_level) },
    { key: "h", header: "HTTP", width: "54px", cell: (r) => value(r.http_status, "PENDING") },
  ];
}

export function buildActionColumns(): DenseColumn<ActionRow>[] {
  return [
    { key: "t", header: "Time UTC", cell: (r) => entryTime(r) },
    { key: "actor", header: "Actor", cell: (r) => asString(r.operator_id) ?? asString(r.actor) ?? UNKNOWN },
    { key: "act", header: "Action", cell: (r) => asString(r.action) ?? UNKNOWN },
    { key: "target", header: "Target", cell: (r) => asString(r.target) ?? asString(r.target_id) ?? "PENDING" },
    { key: "dig", header: "Digest", cell: (r) => <code>{digest(r.event_hash)}</code> },
  ];
}

export function buildWorkColumns(): DenseColumn<WorkRow>[] {
  return [
    { key: "id", header: "ID", cell: (r) => asString(r.work_item_key) ?? r.__id },
    { key: "s", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status)} /> },
    { key: "type", header: "Type", cell: (r) => asString(r.source_kind) ?? asString(r.item_type) ?? UNKNOWN },
    { key: "age", header: "Age", cell: (r) => asString(r.age) ?? asString(r.age_label) ?? "PENDING" },
    { key: "owner", header: "Owner", cell: (r) => asString(r.owner) ?? asString(r.claimed_by) ?? "PENDING" },
    { key: "upd", header: "Updated UTC", cell: (r) => asString(r.updated_at_utc) ?? entryTime(r) },
  ];
}

export function buildStrategyColumns(): DenseColumn<StrategyRow>[] {
  return [
    { key: "id", header: "Strategy / Work Item", cell: (r) => <code>{digest(r.work_item_key)}</code> },
    { key: "target", header: "Target", cell: (r) => asString(r.review_target) ?? UNKNOWN },
    { key: "state", header: "State", cell: (r) => <StatusBadge raw={asString(r.attention_state) ?? asString(r.urgency)} /> },
    { key: "score", header: "Score", width: "54px", cell: (r) => value(r.priority_score ?? r.score, "0") },
    {
      key: "action",
      header: "Test / Next",
      cell: (r) => asString(asRecord(r.command_readiness)?.top_action) ?? asString(r.recommended_action) ?? "PENDING",
    },
  ];
}
