"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidenceChain, type UiEvidenceChainQuery } from "@/hooks/useUiEvidenceChain";
import type { UiEvidenceChainEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type StreamMode = "all" | "decision_ledger" | "operator_action_journal";
type ChainedMode = "all" | "chained" | "unchained";
type ChainRow = UiEvidenceChainEntry & { __id: string };

const STREAMS: StreamMode[] = ["all", "decision_ledger", "operator_action_journal"];
const CHAINED: ChainedMode[] = ["all", "chained", "unchained"];

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  return Object.entries(counts ?? {})
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([k, v]) => ({ k, v: String(v) }));
}

function chainedParam(mode: ChainedMode): boolean | null {
  if (mode === "chained") return true;
  if (mode === "unchained") return false;
  return null;
}

export default function EvidenceChainIntegrityPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [streamMode, setStreamMode] = useState<StreamMode>("all");
  const [chainedMode, setChainedMode] = useState<ChainedMode>("all");
  const [statusNeedle, setStatusNeedle] = useState("");
  const [issueCode, setIssueCode] = useState("");
  const [actorNeedle, setActorNeedle] = useState("");
  const [aggregateNeedle, setAggregateNeedle] = useState("");
  const [eventTypeNeedle, setEventTypeNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiEvidenceChainQuery = useMemo(
    () => ({
      streamFamily: streamMode === "all" ? null : streamMode,
      chained: chainedParam(chainedMode),
      status: statusNeedle.trim() || null,
      issueCode: issueCode.trim() || null,
      actorContains: actorNeedle.trim() || null,
      aggregateContains: aggregateNeedle.trim() || null,
      eventTypeContains: eventTypeNeedle.trim() || null,
      limit: 300,
    }),
    [actorNeedle, aggregateNeedle, chainedMode, eventTypeNeedle, issueCode, statusNeedle, streamMode],
  );

  const chain = useUiEvidenceChain(query);
  const summary = chain.data?.summary;
  const rows = useMemo<ChainRow[]>(
    () =>
      [...(chain.data?.timeline?.entries ?? [])]
        .reverse()
        .map((entry, i) => ({ ...entry, __id: `${entry.stream_family}:${entry.record_id || entry.event_hash || i}:${i}` })),
    [chain.data?.timeline?.entries],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(chain.data?.degraded);
  const guardrails = asStringArray(chain.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "evidence-chain-posture",
        severity: chain.data?.ok ? "ok" : "warn",
        text: `evidence_chain ok=${String(chain.data?.ok ?? false)} returned=${summary?.returned_event_count ?? chain.data?.timeline?.returned_count ?? 0}/${summary?.event_count_total ?? 0} issues=${summary?.chain_issue_count_total ?? 0}`,
      },
      {
        id: "evidence-chain-guardrail",
        severity: "info",
        text: "read-plane only · observes append-only decision/operator chains; no repair or promotion authority",
      },
    ],
    [chain.data, summary],
  );
  const ticker = useMemo(
    () => [
      { severity: chain.data?.ok ? ("ok" as const) : ("warn" as const), text: `EC ${summary?.returned_event_count ?? rows.length}` },
      { severity: (summary?.unchained_filtered_event_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `UNCH ${summary?.unchained_filtered_event_count ?? 0}` },
    ],
    [chain.data?.ok, rows.length, summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ChainRow>[] = useMemo(
    () => [
      { key: "time", header: "created", width: "18%", cell: (row) => <code>{text(row.created_at_utc)}</code> },
      { key: "stream", header: "stream", width: "15%", cell: (row) => <StatusBadge raw={row.stream_family} /> },
      { key: "seq", header: "seq", width: "6%", cell: (row) => <code>{text(row.sequence_number)}</code> },
      { key: "type", header: "event", width: "16%", cell: (row) => <code>{text(row.event_type ?? row.action)}</code> },
      { key: "status", header: "status", width: "11%", cell: (row) => <StatusBadge raw={row.status ?? row.promotion_state} /> },
      { key: "actor", header: "actor", width: "11%", cell: (row) => <code>{text(row.actor_id ?? row.operator_id ?? row.writer_identity)}</code> },
      { key: "aggregate", header: "aggregate", width: "12%", cell: (row) => <code>{text(row.aggregate_id ?? row.experiment_id ?? row.action_event_id)}</code> },
      { key: "issues", header: "issues", cell: (row) => (row.issue_codes?.length ? row.issue_codes.join(", ") : row.chained ? "chained" : "unchained") },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">EVIDENCE · CHAIN INTEGRITY</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">EVIDENCE · CHAIN INTEGRITY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/evidence-chain · append-only decision ledger + operator-action journal integrity timeline
      </p>

      {chain.isLoading && <p className="muted">Loading…</p>}
      {chain.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {chain.error instanceof Error ? chain.error.message : String(chain.error)}
        </p>
      )}

      {chain.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Chain posture" badge={<StatusBadge raw={chain.data.ok ? "OK" : "DEGRADED"} />} onInspect={() => openInspector({ title: "/ui/evidence-chain", rawJson: chain.data })}>
              <TermKV rows={[{ k: "schema", v: chain.data.schema_version }, { k: "ok", v: String(chain.data.ok) }, { k: "readonly", v: String(chain.data.readonly) }, { k: "issues", v: String(summary.chain_issue_count_total) }, { k: "database", v: text(chain.data.database_path) }]} />
            </Pane>
            <Pane title="Stream inventory">
              <TermKV rows={[{ k: "total", v: String(summary.event_count_total) }, { k: "filtered", v: String(summary.filtered_event_count ?? chain.data.timeline.filtered_count ?? chain.data.timeline.entry_count) }, { k: "returned", v: String(summary.returned_event_count ?? chain.data.timeline.returned_count) }, { k: "decision_events", v: String(summary.decision_ledger_event_count) }, { k: "operator_events", v: String(summary.operator_action_event_count) }, { k: "unchained", v: String(summary.unchained_filtered_event_count ?? 0) }]} />
            </Pane>
            <Pane title="Selected record" onInspect={selectedRow ? () => openInspector({ title: "Evidence chain record", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "record", v: selectedRow?.record_id ?? "—" }, { k: "summary", v: selectedRow?.summary_line ?? "—" }, { k: "hash", v: shortDigest(selectedRow?.event_hash) }, { k: "prev", v: shortDigest(selectedRow?.previous_event_hash ?? null) }, { k: "payload", v: shortDigest(selectedRow?.payload_digest_sha256 ?? selectedRow?.target_payload_digest) }]} />
              {(selectedRow?.event_hash || selectedRow?.payload_digest_sha256 || selectedRow?.target_payload_digest) && (
                <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.event_hash ?? selectedRow.payload_digest_sha256 ?? selectedRow.target_payload_digest ?? null)}>
                  Copy digest target
                </button>
              )}
            </Pane>
          </PaneGrid>

          <PaneGrid cols={3}>
            <Pane title="Stream counts"><TermKV rows={countRows(summary.stream_family_counts)} /></Pane>
            <Pane title="Status counts"><TermKV rows={countRows(summary.status_counts)} /></Pane>
            <Pane title="Issue counts"><TermKV rows={countRows(summary.issue_code_counts)} /></Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {STREAMS.map((mode) => (
                <button key={mode} type="button" className={streamMode === mode ? "term-chip active" : "term-chip"} onClick={() => setStreamMode(mode)}>
                  {mode}
                </button>
              ))}
              {CHAINED.map((mode) => (
                <button key={mode} type="button" className={chainedMode === mode ? "term-chip active" : "term-chip"} onClick={() => setChainedMode(mode)}>
                  {mode}
                </button>
              ))}
              <label className="term-field"><span>status</span><input className="term-input" value={statusNeedle} onChange={(e) => setStatusNeedle(e.target.value)} placeholder="APPROVED / rejected" style={{ width: "150px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueCode} onChange={(e) => setIssueCode(e.target.value)} placeholder="issue code" style={{ width: "170px" }} /></label>
              <label className="term-field"><span>actor</span><input className="term-input" value={actorNeedle} onChange={(e) => setActorNeedle(e.target.value)} placeholder="operator / writer" style={{ width: "150px" }} /></label>
              <label className="term-field"><span>aggregate</span><input className="term-input" value={aggregateNeedle} onChange={(e) => setAggregateNeedle(e.target.value)} placeholder="experiment / work item" style={{ width: "180px" }} /></label>
              <label className="term-field"><span>event</span><input className="term-input" value={eventTypeNeedle} onChange={(e) => setEventTypeNeedle(e.target.value)} placeholder="claim / adjudication" style={{ width: "170px" }} /></label>
            </div>
          </Pane>

          <Pane title="Integrity timeline">
            <DenseTable<ChainRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No evidence chain records matched the current filters." />
          </Pane>

          {degraded.length > 0 && (
            <Pane title="Degraded reads" badge={<StatusBadge raw="DEGRADED" />}>
              <ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          )}
          <Pane title="Guardrails">
            <ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul>
          </Pane>
          <JsonDetails summary="Drilldown: /ui/evidence-chain JSON" data={chain.data} />
        </>
      )}
    </div>
  );
}
