"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidenceChain } from "@/hooks/useUiEvidenceChain";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import type { UiEvidenceChainEntry } from "@/lib/api/types";
import { useMemo, useState } from "react";

type Row = UiEvidenceChainEntry & { __id: string };

function entryKind(row: Record<string, unknown>): string {
  return asString(row.action) ?? asString(row.event_type) ?? "—";
}

function entryActor(row: Record<string, unknown>): string {
  return asString(row.operator_id) ?? asString(row.writer_identity) ?? asString(row.actor_id) ?? "—";
}

function issueList(row: Record<string, unknown>): string[] {
  return asStringArray(row.issue_codes);
}

export default function LedgerPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const evidenceChain = useUiEvidenceChain();
  const [sel, setSel] = useState<string | null>(null);

  const data = evidenceChain.data != null ? asRecord(evidenceChain.data) : null;
  const summary = data ? asRecord(data.summary) : null;
  const streams = data ? asRecord(data.streams) : null;
  const timeline = data ? asRecord(data.timeline) : null;

  const entriesRaw = timeline?.entries;
  const entries = useMemo(() => {
    const raw = Array.isArray(entriesRaw)
      ? entriesRaw.map((x) => asRecord(x)).filter((x): x is Record<string, unknown> => x != null)
      : [];
    return raw.map((e, i) => ({
      ...e,
      __id: `${asString(e.stream_family) ?? "stream"}:${asString(e.record_id) ?? asString(e.event_hash) ?? `r${i}`}`,
    })) as Row[];
  }, [entriesRaw]);

  const last = entries.length ? entries[entries.length - 1] : null;
  const lastHash = last ? asString(last.event_hash) : null;

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "ec",
        severity: asBool(data?.ok) ? "ok" : "warn",
        text: `evidence_chain ok=${String(data?.ok)} events=${String(summary?.event_count_total ?? "—")}`,
      },
      {
        id: "es",
        severity: "info",
        text: last ? `last ${asString(last.stream_family) ?? "—"} ${entryKind(last)}` : "no evidence events",
      },
    ],
    [data, summary, last],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `EVCH ${String(summary?.event_count_total ?? "?")}` },
      {
        severity: asBool(data?.ok) ? ("ok" as const) : ("warn" as const),
        text: `CHAIN ${String(data?.ok)}`,
      },
    ],
    [data, summary],
  );

  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<Row>[] = useMemo(
    () => [
      {
        key: "stream",
        header: "stream",
        width: "19%",
        cell: (r) => <code>{asString(r.stream_family)?.replace("_", "·") ?? "—"}</code>,
      },
      { key: "seq", header: "seq", width: "64px", cell: (r) => String(r.sequence_number ?? "—") },
      { key: "kind", header: "event/action", width: "24%", cell: (r) => <code>{entryKind(r)}</code> },
      { key: "status", header: "status", width: "13%", cell: (r) => asString(r.status) ?? "—" },
      { key: "actor", header: "actor", width: "15%", cell: (r) => entryActor(r) },
      {
        key: "hash",
        header: "hash",
        cell: (r) => <span className="mono-value">{asString(r.event_hash)?.slice(0, 14) ?? "—"}</span>,
      },
      {
        key: "issues",
        header: "issues",
        width: "72px",
        cell: (r) => String(issueList(r).length),
      },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">LEDGER</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">LEDGER · EVIDENCE CHAIN</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/evidence-chain?readonly=true · decision ledger + operator-action journal · read-plane only
      </p>
      {evidenceChain.isLoading && <p className="muted">Loading…</p>}
      {evidenceChain.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {evidenceChain.error instanceof Error ? evidenceChain.error.message : String(evidenceChain.error)}
        </p>
      )}

      {data && (
        <>
          <PaneGrid>
            <Pane title="Forensic chain summary" onInspect={() => openInspector({ title: "Evidence chain", rawJson: data })}>
              <TermKV
                rows={[
                  { k: "ok", v: String(asBool(data.ok) ?? "—") },
                  { k: "events_total", v: String(asNumber(summary?.event_count_total) ?? "—") },
                  { k: "issues_total", v: String(asNumber(summary?.chain_issue_count_total) ?? "—") },
                  { k: "decision_events", v: String(asNumber(summary?.decision_ledger_event_count) ?? "—") },
                  { k: "operator_events", v: String(asNumber(summary?.operator_action_event_count) ?? "—") },
                  { k: "readonly", v: String(asBool(data.readonly) ?? "—") },
                  { k: "db", v: asString(data.database_path)?.slice(-48) ?? "—" },
                ]}
              />
            </Pane>
            <Pane title="Authority boundary">
              <TermKV
                rows={[
                  { k: "mutation", v: asString(data.mutation_authority) ?? "—" },
                  { k: "promotion", v: asString(data.promotion_authority) ?? "—" },
                  { k: "execution", v: asString(data.execution_authority) ?? "—" },
                  { k: "degraded", v: String(asStringArray(data.degraded).length) },
                  { k: "last_hash", v: lastHash?.slice(0, 24) ?? "—" },
                ]}
              />
            </Pane>
            <Pane title="Stream health" onInspect={() => openInspector({ title: "Evidence streams", rawJson: streams ?? {} })}>
              <div className="stack-sm">
                <StatusBadge label="decision ledger" raw={asBool(summary?.decision_ledger_chain_ok) ? "OK" : "WARN"} />
                <StatusBadge label="operator journal" raw={asBool(summary?.operator_action_chain_ok) ? "OK" : "WARN"} />
              </div>
            </Pane>
          </PaneGrid>

          {entries.length === 0 ? (
            <p className="muted">No events · cold ledger/journal or readonly storage unavailable.</p>
          ) : (
            <DenseTable
              columns={cols}
              rows={entries.slice(-120)}
              rowKey={(r) => r.__id}
              selectedKey={sel}
              onRowClick={(r) => {
                setSel(r.__id);
                const h = asString(r.event_hash);
                if (h) setLastDigest(h);
                openInspector({
                  title: `${asString(r.stream_family) ?? "stream"} · ${entryKind(r)}`,
                  body: (
                    <TermKV
                      rows={[
                        { k: "status", v: asString(r.status) ?? "—" },
                        { k: "actor", v: entryActor(r) },
                        { k: "sequence", v: String(r.sequence_number ?? "—") },
                        { k: "chained", v: String(r.chained ?? "—") },
                        { k: "issues", v: issueList(r).join(", ") || "—" },
                      ]}
                    />
                  ),
                  rawJson: r,
                  digestToCopy: h ?? undefined,
                });
              }}
            />
          )}
          {entries.length > 120 && (
            <p className="muted" style={{ fontSize: "10px" }}>
              Showing last 120 of {entries.length} · full JSON in drilldown
            </p>
          )}
        </>
      )}

      {evidenceChain.data && <JsonDetails summary="Drilldown: full evidence-chain JSON" data={evidenceChain.data} />}
    </div>
  );
}
