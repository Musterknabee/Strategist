"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffAuditPacket, type UiSemanticValidatorHandoffAuditPacketQuery } from "@/hooks/useUiSemanticValidatorHandoffAuditPacket";
import type { UiSemanticValidatorHandoffAuditPacketAction, UiSemanticValidatorHandoffAuditPacketRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type PacketStatusMode = "all" | "CLOSED_AUDIT_READY" | "AWAITING_EXTERNAL_ARTIFACT" | "BLOCKED_EVIDENCE_GAPS" | "OPEN_EXCEPTIONS_BLOCKING" | "OPEN_CHAIN_ACTION_REQUIRED" | "AUDIT_PACKET_REVIEW_REQUIRED";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type PacketRow = UiSemanticValidatorHandoffAuditPacketRecord & { __id: string };

const PACKET_STATUS_MODES: PacketStatusMode[] = ["all", "CLOSED_AUDIT_READY", "AWAITING_EXTERNAL_ARTIFACT", "BLOCKED_EVIDENCE_GAPS", "OPEN_EXCEPTIONS_BLOCKING", "OPEN_CHAIN_ACTION_REQUIRED", "AUDIT_PACKET_REVIEW_REQUIRED"];
const TRUST_MODES: TrustMode[] = ["all", "TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"];
const BOOL_MODES: BoolMode[] = ["all", "yes", "no"];

function boolParam(mode: BoolMode): boolean | null {
  if (mode === "yes") return true;
  if (mode === "no") return false;
  return null;
}

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function shortDigest(value: unknown): string {
  const s = typeof value === "string" ? value : "";
  if (!s) return "—";
  return s.length > 18 ? `${s.slice(0, 12)}…${s.slice(-6)}` : s;
}

function countRows(counts?: Record<string, number>) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

function selectedActions(row: PacketRow | null): UiSemanticValidatorHandoffAuditPacketAction[] {
  return row?.required_actions ?? [];
}

export default function SemanticValidatorHandoffAuditPacketPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [packetStatusMode, setPacketStatusMode] = useState<PacketStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [attentionMode, setAttentionMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffAuditPacketQuery = useMemo(
    () => ({
      packetStatus: packetStatusMode === "all" ? null : packetStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      operatorAttentionRequired: boolParam(attentionMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [attentionMode, experimentNeedle, issueNeedle, packetStatusMode, trustMode],
  );

  const packets = useUiSemanticValidatorHandoffAuditPacket(query);
  const summary = packets.data?.summary ?? {};
  const rows = useMemo<PacketRow[]>(
    () => (packets.data?.audit_packets ?? []).map((row, i) => ({ ...row, __id: `${row.audit_packet_id}:${i}` })),
    [packets.data?.audit_packets],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(packets.data?.degraded);
  const guardrails = asStringArray(packets.data?.guardrails);
  const selectedIssues = asStringArray(selectedRow?.issue_codes);
  const actions = selectedActions(selectedRow);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-audit-packet-status",
        severity: Number(summary.blocked_packet_count ?? 0) > 0 || Number(summary.untrusted_count ?? 0) > 0 ? "bad" : Number(summary.operator_attention_required_count ?? 0) > 0 || degraded.length ? "warn" : "ok",
        text: `handoff audit packets=${summary.audit_packet_count_returned ?? 0}/${summary.audit_packet_count_total ?? 0} ready=${summary.audit_ready_count ?? 0} attention=${summary.operator_attention_required_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-audit-packet-boundary",
        severity: "info",
        text: "audit packet cockpit read-plane only · no packet file materialization, artifact mutation, validator submission, promotion, or execution authority",
      },
    ],
    [degraded.length, summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.audit_ready_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `READY ${summary.audit_ready_count ?? 0}` },
      { severity: Number(summary.operator_attention_required_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `ATTN ${summary.operator_attention_required_count ?? 0}` },
      { severity: Number(summary.execution_allowed_count ?? 0) > 0 ? ("bad" as const) : ("ok" as const), text: `EXEC ${summary.execution_allowed_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<PacketRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "10%", cell: (row) => <StatusBadge raw={row.trust_banner} /> },
      { key: "status", header: "packet", width: "20%", cell: (row) => <StatusBadge raw={row.packet_status} /> },
      { key: "experiment", header: "experiment", width: "16%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "stage", header: "stage", width: "8%", cell: (row) => <code>{text(row.current_stage)}</code> },
      { key: "ready", header: "audit_ready", width: "10%", cell: (row) => <StatusBadge raw={row.audit_ready ? "YES" : "NO"} /> },
      { key: "gaps", header: "gaps", width: "7%", cell: (row) => <code>{row.gap_count}</code> },
      { key: "exceptions", header: "exceptions", width: "9%", cell: (row) => <code>{row.exception_count}</code> },
      { key: "actions", header: "actions", width: "8%", cell: (row) => <code>{row.required_action_count}</code> },
      { key: "digest", header: "digest", cell: (row) => <code>{shortDigest(row.audit_packet_digest)}</code> },
    ],
    [],
  );

  const actionColumns: DenseColumn<UiSemanticValidatorHandoffAuditPacketAction>[] = useMemo(
    () => [
      { key: "priority", header: "priority", width: "9%", cell: (row) => <StatusBadge raw={row.priority ?? "P2"} /> },
      { key: "severity", header: "severity", width: "10%", cell: (row) => <StatusBadge raw={row.severity ?? "WARN"} /> },
      { key: "source", header: "source", width: "12%", cell: (row) => <code>{row.source}</code> },
      { key: "action", header: "operator action", width: "34%", cell: (row) => <code>{text(row.operator_action)}</code> },
      { key: "route", header: "route", cell: (row) => <code>{text(row.route)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF AUDIT PACKET</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR HANDOFF AUDIT PACKET</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/audit-packet · consolidated read-only packet over continuity, timeline, exceptions, and evidence gaps</p>
      {packets.isLoading && <p className="muted">Loading…</p>}
      {packets.isError && <p className="term-error">{packets.error.message}</p>}

      {packets.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Audit packet inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/audit-packet", rawJson: packets.data })}>
              <TermKV rows={[{ k: "schema", v: packets.data.schema_version }, { k: "total", v: String(summary.audit_packet_count_total ?? 0) }, { k: "returned", v: String(summary.audit_packet_count_returned ?? 0) }, { k: "ready", v: String(summary.audit_ready_count ?? 0) }, { k: "attention", v: String(summary.operator_attention_required_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected packet" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff audit packet", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "packet", v: text(selectedRow?.audit_packet_id) }, { k: "status", v: text(selectedRow?.packet_status) }, { k: "chain", v: text(selectedRow?.chain_id) }, { k: "digest", v: shortDigest(selectedRow?.audit_packet_digest) }, { k: "actions", v: String(selectedRow?.required_action_count ?? 0) }]} />
              {selectedRow?.audit_packet_digest && <button className="term-button" onClick={() => setLastDigest(selectedRow.audit_packet_digest)}>pin digest</button>}
            </Pane>
            <Pane title="Authority boundary">
              <TermKV rows={[{ k: "read_plane", v: String(packets.data.read_plane_only) }, { k: "packet_materialize", v: packets.data.packet_materialization_authority }, { k: "artifact_write", v: packets.data.external_artifact_write_authority }, { k: "submit", v: packets.data.validator_submission_authority }, { k: "execute", v: packets.data.execution_authority }]} />
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-filter-row">
              <label>Status <select value={packetStatusMode} onChange={(e) => setPacketStatusMode(e.target.value as PacketStatusMode)}>{PACKET_STATUS_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Trust <select value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)}>{TRUST_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Attention <select value={attentionMode} onChange={(e) => setAttentionMode(e.target.value as BoolMode)}>{BOOL_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select></label>
              <label>Experiment <input value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="EXP-…" /></label>
              <label>Issue <input value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="closure, gap, digest…" /></label>
            </div>
          </Pane>

          <Pane title="Audit packets" badge={<StatusBadge raw={`${rows.length} rows`} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic-validator handoff audit packets matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Packet statuses"><TermKV rows={countRows(packets.data.packet_status_counts)} /></Pane>
            <Pane title="Trust banners"><TermKV rows={countRows(packets.data.trust_banner_counts)} /></Pane>
            <Pane title="Selected issues"><ul className="term-list">{selectedIssues.length ? selectedIssues.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
          </PaneGrid>

          <Pane title="Required actions" badge={<StatusBadge raw={`${actions.length} actions`} />}>
            <DenseTable columns={actionColumns} rows={actions} rowKey={(row, i) => `${row.source}:${row.source_id ?? i}`} empty="No required actions for the selected packet." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Lanes"><TermKV rows={countRows(packets.data.packet_lane_counts)} /></Pane>
            <Pane title="Degraded"><ul className="term-list">{degraded.length ? degraded.map((item) => <li key={item}><code>{item}</code></li>) : <li>—</li>}</ul></Pane>
            <Pane title="Guardrails"><ul className="term-list">{guardrails.map((item) => <li key={item}><code>{item}</code></li>)}</ul></Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/audit-packet JSON" data={packets.data} />
        </>
      )}
    </div>
  );
}
