"use client";

import { useMemo, useState } from "react";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { StatusBadge } from "@/components/operator/StatusBadge";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import {
  buildEvidencePacketModel,
  buildEvidenceRunbookMarkdown,
  type EvidenceArtifactRow,
} from "@/lib/operator/evidence-packet-model";
import { localOpsCommandById } from "@/lib/operator/local-ops-command-hints";
import { readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { asRecord } from "@/lib/operator/payload-utils";

export type EvidenceRunbookPaneProps = {
  facade: unknown;
  evidence: unknown;
  evidenceChain: unknown;
  operatorActions: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  exportLatest: unknown;
  queryFailed: boolean;
  openInspector: (payload: InspectorPayload) => void;
  setLastDigest?: (digest: string) => void;
};

const columns: DenseColumn<EvidenceArtifactRow>[] = [
  { key: "label", header: "Artifact", width: "200px", cell: (row) => row.label },
  {
    key: "presence",
    header: "Presence",
    width: "100px",
    cell: (row) => <StatusBadge raw={row.presence} />,
  },
  { key: "digest", header: "Digest", width: "100px", cell: (row) => row.digest_prefix },
  { key: "cockpit", header: "Cockpit", width: "160px", cell: (row) => row.cockpit_pane },
  {
    key: "review",
    header: "Op review",
    width: "72px",
    cell: (row) => (row.operator_review_only ? "yes" : "—"),
  },
];

function paneBadge(model: ReturnType<typeof buildEvidencePacketModel>, queryFailed: boolean): string {
  if (queryFailed) return "DEGRADED";
  if (model.packet_status === "NOT_APPROVED") return "NOT_APPROVED";
  if (model.packet_status === "REVIEW_REQUIRED") return "REVIEW";
  return "UNKNOWN";
}

export function EvidenceRunbookPane({
  facade: _facade,
  evidence,
  evidenceChain,
  operatorActions,
  releaseReadiness,
  handoff,
  handoffSignoff,
  reviewJournal,
  exportLatest,
  queryFailed,
  openInspector,
  setLastDigest,
}: EvidenceRunbookPaneProps) {
  const ev = asRecord(evidence);
  const cockpit = useMemo(() => readUiEvidenceCockpit(ev), [ev]);
  const model = useMemo(
    () =>
      buildEvidencePacketModel({
        evidence,
        evidenceChain,
        operatorActions,
        releaseReadiness,
        handoff,
        handoffSignoff,
        reviewJournal,
        exportLatest,
        cockpit,
      }),
    [cockpit, evidence, evidenceChain, exportLatest, handoff, handoffSignoff, operatorActions, releaseReadiness, reviewJournal],
  );
  const md = useMemo(() => buildEvidenceRunbookMarkdown(model), [model]);
  const [copied, setCopied] = useState<"md" | null>(null);

  return (
    <div className="cockpit-release-control-row" data-testid="cockpit-evidence-runbook">
      <Pane
        title="Evidence packet & runbook checklist"
        dense
        badge={<StatusBadge raw={paneBadge(model, queryFailed)} />}
        onInspect={() =>
          openInspector({
            title: "Evidence packet · read-plane bundle",
            subtitle: model.recommended_next_review_action,
            rawJson: {
              normalized: model,
              evidence: evidence ?? {},
              evidence_chain: evidenceChain ?? {},
              operator_actions: operatorActions ?? {},
              release_readiness: releaseReadiness ?? {},
              handoff,
              handoff_signoff: handoffSignoff,
              review_journal: reviewJournal,
              export_latest: exportLatest ?? {},
            },
          })
        }
      >
        <div className="term-page__banner" style={{ fontSize: "10px", marginBottom: "8px" }} data-testid="cockpit-evidence-runbook-disclaimer">
          <strong>Frontend checklist is not deployment approval.</strong> Operator signoff requires backend evidence (manifests,
          ledger projections, Research OS artifacts). Missing or stale rows block confidence — UNKNOWN means the API returned no
          payload or an incomplete projection.
        </div>
        <TermKV
          rows={[
            { k: "packet_id", v: model.packet_id },
            { k: "packet_status", v: <StatusBadge raw={model.packet_status} /> },
            { k: "trust_status", v: <StatusBadge raw={model.trust_status} /> },
            { k: "search_root", v: model.search_root },
            { k: "generated_at_utc", v: model.generated_at_utc },
            {
              k: "artifact_counts",
              v: `${model.present_count} present · ${model.missing_count} missing · ${model.stale_count} stale · ${model.warn_count} warn`,
            },
            { k: "blocker_signals", v: String(model.blocker_count) },
            {
              k: "recommended_next_review_action",
              v: <StatusBadge raw={model.recommended_next_review_action} />,
            },
          ]}
        />
        <DenseTable
          columns={columns}
          rows={model.rows}
          rowKey={(row) => row.__id}
          onRowClick={(row) => {
            if (row.digest_full) setLastDigest?.(row.digest_full);
            openInspector({
              title: row.label,
              subtitle: row.expected_evidence,
              rawJson: row.raw,
            });
          }}
          empty="UNKNOWN · no read-plane evidence payloads"
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginTop: "10px", alignItems: "center" }}>
          <button
            type="button"
            className="linkish"
            data-testid="cockpit-evidence-runbook-copy-markdown"
            onClick={() => {
              void navigator.clipboard.writeText(md).then(() => {
                setCopied("md");
                window.setTimeout(() => setCopied(null), 2000);
              });
            }}
          >
            {copied === "md" ? "Copied checklist" : "Copy markdown checklist"}
          </button>
          <span className="muted" style={{ fontSize: "9px" }}>
            Clipboard only — no file write, no shell execution.
          </span>
        </div>
        <section aria-label="Command provenance" style={{ marginTop: "10px" }}>
          <h3 className="muted" style={{ fontSize: "11px", margin: "0 0 4px", fontWeight: 600 }}>
            Command provenance (registry)
          </h3>
          <ul style={{ margin: 0, paddingLeft: "16px", fontSize: "9px" }} className="muted">
            {model.rows
              .filter((r) => r.command_hint_id)
              .map((r) => {
                const cmd = r.command_hint_id ? localOpsCommandById(r.command_hint_id) : undefined;
                return (
                  <li key={r.__id} style={{ marginBottom: "4px" }}>
                    <strong>{r.label}</strong> → {cmd?.label ?? r.command_hint_id}
                    {cmd ? (
                      <button
                        type="button"
                        className="linkish"
                        style={{ marginLeft: "6px", fontSize: "9px" }}
                        data-testid={`cockpit-evidence-runbook-copy-cmd-${r.command_hint_id}`}
                        onClick={() => void navigator.clipboard.writeText(cmd.commandText)}
                      >
                        Copy CLI
                      </button>
                    ) : null}
                  </li>
                );
              })}
          </ul>
        </section>
      </Pane>
    </div>
  );
}
