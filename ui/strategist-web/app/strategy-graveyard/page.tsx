"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiStrategyGraveyardLatest } from "@/hooks/useUiStrategyGraveyard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type Row = Record<string, unknown> & { __id: string };

export default function StrategyGraveyardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiStrategyGraveyardLatest();
  const root = q.data ? asRecord(q.data) : null;
  const summary = root?.summary ? asRecord(root.summary) : null;
  const degraded = root ? asStringArray(root.degraded) : [];
  const entries = useMemo<Row[]>(() => {
    const raw = Array.isArray(root?.entries) ? root.entries : [];
    return raw.map((x, i) => ({ ...(asRecord(x) ?? {}), __id: asString(asRecord(x)?.strategy_id) ?? `graveyard-${i}` }));
  }, [root]);
  const tape: TapeLine[] = useMemo(() => [{ id: "graveyard", ts: asString(root?.generated_at_utc), severity: degraded.length || q.isError ? "warn" : "ok", text: `STRATEGY_GRAVEYARD entries=${entries.length}` }], [degraded.length, entries.length, q.isError, root]);
  useTerminalPageBind(tape, []);
  const cols: DenseColumn<Row>[] = [
    { key: "strategy", header: "Strategy", cell: (r) => <code>{asString(r.strategy_id) ?? "—"}</code> },
    { key: "family", header: "Family", cell: (r) => <code>{asString(r.family_id) ?? "—"}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status) ?? "—"} /> },
    { key: "res", header: "Resurrection", cell: (r) => <StatusBadge raw={asString(r.resurrectability) ?? "—"} /> },
    { key: "blockers", header: "Hard blockers", cell: (r) => asStringArray(r.hard_blockers).slice(0, 2).join(", ") || "—" },
  ];
  if (!config.ok) return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  return <main className="console">
    <div className="console-header"><div><h1>Strategy Graveyard</h1><p className="muted">Killed/rejected candidates · resurrection rules · research memory only</p></div></div>
    <div className="readiness" role="status"><strong>No promotion authority</strong><p className="muted" style={{ margin: "0.35rem 0 0" }}>This page explains what evidence is required to reopen a dead strategy. It does not approve promotion or execution.</p></div>
    <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
      <Pane title="Graveyard summary" dense onInspect={() => openInspector({ title: "Strategy Graveyard latest", rawJson: q.data ?? {} })}>
        {q.isError && <p className="muted">DEGRADED · could not load /ui/strategy-graveyard/latest</p>}
        {degraded.length > 0 && <p className="muted">{degraded.join(", ")}</p>}
        <TermKV rows={[{ k: "entries", v: String(asNumber(summary?.entry_count) ?? 0) }, { k: "hard_blocked", v: String(asNumber(summary?.hard_blocked_count) ?? 0) }, { k: "conditional_retry", v: String(asNumber(summary?.conditional_retry_count) ?? 0) }, { k: "duplicate_superseded", v: String(asNumber(summary?.duplicate_superseded_count) ?? 0) }, { k: "operator_review", v: String(asNumber(summary?.operator_review_count) ?? 0) }, { k: "scan_root", v: asString(root?.scan_root) ?? "—" }]} />
      </Pane>
      <Pane title="Graveyard rows" dense><DenseTable columns={cols} rows={entries} rowKey={(r) => r.__id} onRowClick={(r) => openInspector({ title: `Strategy Graveyard · ${asString(r.strategy_id) ?? "strategy"}`, rawJson: r })} /></Pane>
      <Pane title="Resurrection rules" dense><JsonDetails summary="rules" data={entries.map((e) => ({ strategy_id: e.strategy_id, rules: e.resurrection_rules }))} /></Pane>
    </div>
  </main>;
}
