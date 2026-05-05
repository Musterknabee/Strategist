"use client";

import { useMemo, useState } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildAuditTimelineModel,
  filterAuditTimeline,
  type AuditTimelineEntry,
  type AuditTimelineFilter,
} from "@/lib/operator/audit-timeline-model";

export type AuditForensicPaneProps = {
  evidenceChain: unknown;
  operatorActions: unknown;
  evidence: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  exportLatest: unknown;
  driftLatest: unknown;
  paperExecution: unknown;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

const FILTERS: { id: AuditTimelineFilter; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "PROMOTION_LEDGER", label: "Promotion ledger" },
  { id: "OPERATOR_ACTIONS", label: "Operator actions" },
  { id: "RESEARCH_OS", label: "Research OS" },
  { id: "RELEASE_DEPLOYMENT", label: "Release / deploy" },
  { id: "PAPER_EXECUTION", label: "Paper execution" },
  { id: "BROKEN_LINEAGE", label: "Broken / unchained" },
  { id: "ISSUES", label: "Issues" },
];

const columns: DenseColumn<AuditTimelineEntry>[] = [
  { key: "ts", header: "Time (UTC)", width: "150px", cell: (row) => row.timestamp.slice(0, 19) },
  { key: "fam", header: "Family", width: "120px", cell: (row) => row.source_family },
  { key: "act", header: "Action / type", width: "160px", cell: (row) => `${row.action} · ${row.event_type}` },
  {
    key: "chain",
    header: "Chain",
    width: "100px",
    cell: (row) => <StatusBadge raw={row.chain_semantic} />,
  },
  {
    key: "trust",
    header: "Trust",
    width: "100px",
    cell: (row) => <StatusBadge raw={row.trust_semantic} />,
  },
  {
    key: "pf",
    header: "Status",
    width: "88px",
    cell: (row) => <StatusBadge raw={row.pass_fail} />,
  },
  { key: "dig", header: "Digest", width: "100px", cell: (row) => row.digest_prefix },
  { key: "iss", header: "Iss", width: "40px", cell: (row) => String(row.issue_count) },
];

function paneBadge(queryFailed: boolean, chainOk: boolean | null): string {
  if (queryFailed) return "DEGRADED";
  if (chainOk === false) return "FAIL";
  if (chainOk === true) return "PASS";
  return "UNKNOWN";
}

export function AuditForensicPane({
  evidenceChain,
  operatorActions,
  evidence,
  releaseReadiness,
  handoff,
  handoffSignoff,
  reviewJournal,
  exportLatest,
  driftLatest,
  paperExecution,
  queryFailed,
  openInspector,
  setLastDigest,
}: AuditForensicPaneProps) {
  const [filter, setFilter] = useState<AuditTimelineFilter>("ALL");
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const model = useMemo(
    () =>
      buildAuditTimelineModel({
        evidenceChain,
        operatorActions,
        evidence,
        releaseReadiness,
        handoff,
        handoffSignoff,
        reviewJournal,
        exportLatest,
        driftLatest,
        paperExecution,
      }),
    [
      driftLatest,
      evidence,
      evidenceChain,
      exportLatest,
      handoff,
      handoffSignoff,
      operatorActions,
      paperExecution,
      releaseReadiness,
      reviewJournal,
    ],
  );

  const visible = useMemo(() => filterAuditTimeline(model.entries, filter), [filter, model.entries]);

  return (
    <div className="cockpit-release-control-row" data-testid="cockpit-audit-forensic">
      <Pane
        title="Audit trail & forensic diff"
        dense
        badge={<StatusBadge raw={paneBadge(queryFailed, model.chain_summary_ok)} />}
        onInspect={() =>
          openInspector({
            title: "Audit timeline · read-plane bundle",
            subtitle: model.timeline_id,
            rawJson: {
              normalized_summary: {
                timeline_id: model.timeline_id,
                entry_count: model.entry_count,
                degraded: model.degraded,
                chain_summary_ok: model.chain_summary_ok,
              },
              evidence_chain: evidenceChain ?? {},
              forensic_diffs: model.forensic_diffs,
            },
          })
        }
      >
        <p className="muted" style={{ fontSize: "10px", margin: "0 0 8px" }} data-testid="cockpit-audit-forensic-note">
          Chronological merge of <code>/ui/evidence-chain</code> timeline (decision ledger + operator journal), supplemented by
          latest artifact timestamps from read-plane surfaces. Chain semantics follow backend <code>chained</code> and{" "}
          <code>issue_codes</code> only — not re-verified in the browser.
        </p>
        <TermKV
          rows={[
            { k: "timeline_id", v: model.timeline_id },
            { k: "entries", v: String(model.entry_count) },
            { k: "degraded_flags", v: String(model.degraded.length) },
            { k: "evidence_chain_ok", v: String(model.chain_summary_ok ?? "UNKNOWN") },
          ]}
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", margin: "10px 0" }} data-testid="cockpit-audit-forensic-filters">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              className="linkish"
              style={{ fontSize: "10px", fontWeight: filter === f.id ? 700 : 400 }}
              data-testid={`cockpit-audit-filter-${f.id}`}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <section aria-label="Forensic diff summaries" style={{ marginBottom: "10px" }}>
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 4px", fontWeight: 600 }}>
            Forensic diff summaries
          </h3>
          {model.forensic_diffs.map((b) => (
            <div key={b.id} style={{ marginBottom: "8px", fontSize: "10px" }} data-testid={`cockpit-audit-forensic-diff-${b.id}`}>
              <strong>{b.title}</strong> · <StatusBadge raw={b.baseline} />
              <ul style={{ margin: "4px 0 0", paddingLeft: "16px" }} className="muted">
                {b.lines.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </div>
          ))}
        </section>
        <DenseTable
          columns={columns}
          rows={visible}
          rowKey={(row) => row.timeline_id}
          selectedKey={selectedKey}
          onRowClick={(row) => {
            setSelectedKey(row.timeline_id);
            if (row.digest_full) setLastDigest?.(row.digest_full);
            openInspector({
              title: row.related_artifact || row.event_type,
              subtitle: `${row.source_family} · ${row.timestamp}`,
              rawJson: {
                ...row.raw,
                _audit: {
                  timeline_id: row.timeline_id,
                  chain_semantic: row.chain_semantic,
                  trust_semantic: row.trust_semantic,
                  issue_codes: row.issue_codes,
                },
              },
            });
          }}
          empty="UNKNOWN · no timeline entries for this filter"
        />
      </Pane>
    </div>
  );
}
