"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiDailyOperatorRunLatest } from "@/hooks/useUiDailyOperatorRun";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import type { UiDailyOperatorRunComponent } from "@/lib/api/types";
import { useMemo } from "react";

type Row = UiDailyOperatorRunComponent & { __id: string };

export default function DailyOperatorRunPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiDailyOperatorRunLatest();
  const root = q.data ? asRecord(q.data) : null;
  const summary = root?.summary ? asRecord(root.summary) : null;
  const warnings = root ? asStringArray(root.warnings) : [];
  const blockers = root ? asStringArray(root.blockers) : [];
  const actions = root ? asStringArray(root.recommended_actions) : [];
  const components = useMemo<Row[]>(() => {
    const raw = Array.isArray(root?.components) ? root.components : [];
    return raw.map((x, i) => ({ ...((asRecord(x) ?? {}) as UiDailyOperatorRunComponent), __id: asString(asRecord(x)?.component_id) ?? `component-${i}` }));
  }, [root]);
  const tape: TapeLine[] = useMemo(() => [{ id: "daily-run", ts: asString(root?.generated_at_utc), severity: blockers.length ? "bad" : warnings.length || q.isError ? "warn" : "ok", text: root ? `DAILY_RUN ${asString(root.status) ?? "UNKNOWN"} · components=${components.length}` : "NO_DAILY_OPERATOR_RUN" }], [blockers.length, components.length, q.isError, root, warnings.length]);
  useTerminalPageBind(tape, []);
  const cols: DenseColumn<Row>[] = [
    { key: "component", header: "Component", cell: (r) => <code>{r.component_id}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={r.status} /> },
    { key: "posture", header: "Posture", cell: (r) => <StatusBadge raw={r.posture} /> },
    { key: "route", header: "Source", cell: (r) => <code>{r.source_route}</code> },
    { key: "warn", header: "Warn", cell: (r) => String((r.warnings ?? []).length) },
    { key: "block", header: "Block", cell: (r) => String((r.blockers ?? []).length) },
    { key: "action", header: "First action", cell: (r) => (r.recommended_actions ?? []).slice(0, 1).join("; ") || "—" },
  ];
  if (!config.ok) return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  return <main className="console">
    <div className="console-header"><div><h1>Daily Operator Run</h1><p className="muted">Composite briefing · provider setup → intake → forensics → graveyard → evidence chain → Research OS run</p></div></div>
    <div className="readiness" role="status"><strong>Read-plane briefing only</strong><p className="muted" style={{ margin: "0.35rem 0 0" }}>This page merges evidence surfaces into a daily checklist. It does not authorize promotion, broker orders, live trading, or ledger mutation.</p></div>
    <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
      <Pane title="Daily status" dense onInspect={() => openInspector({ title: "Daily operator run", rawJson: q.data ?? {} })}>
        {q.isError && <p className="term-page__banner">Could not load /ui/daily-operator-run/latest</p>}
        <TermKV rows={[{ k: "status", v: <StatusBadge raw={asString(root?.status) ?? "UNKNOWN"} /> }, { k: "trust_banner", v: <StatusBadge raw={asString(root?.trust_banner) ?? "UNKNOWN"} /> }, { k: "components", v: String(asNumber(summary?.component_count) ?? components.length) }, { k: "ok", v: String(asNumber(summary?.ok_count) ?? 0) }, { k: "warnings", v: String(asNumber(summary?.warning_count) ?? warnings.length) }, { k: "blocked", v: String(asNumber(summary?.blocked_count) ?? blockers.length) }, { k: "strategy_intakes", v: String(asNumber(summary?.strategy_intake_count) ?? 0) }, { k: "backtest_strategies", v: String(asNumber(summary?.backtest_strategy_count) ?? 0) }, { k: "graveyard_entries", v: String(asNumber(summary?.graveyard_entry_count) ?? 0) }, { k: "evidence_chain_issues", v: String(asNumber(summary?.evidence_chain_issue_count) ?? 0) }]} />
      </Pane>
      <Pane title="Recommended next actions" dense onInspect={() => openInspector({ title: "Daily recommended actions", rawJson: actions })}>{actions.length ? <ol style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "11px" }}>{actions.slice(0, 10).map((a, i) => <li key={`${a}-${i}`}>{a}</li>)}</ol> : <p className="muted">No daily actions returned.</p>}</Pane>
      <Pane title="Component checklist" dense><DenseTable columns={cols} rows={components} rowKey={(r) => r.__id} onRowClick={(r) => openInspector({ title: `Daily component · ${r.component_id}`, rawJson: r })} /></Pane>
      <Pane title="Warnings / blockers" dense>{warnings.length ? <JsonDetails summary="warnings" data={warnings} /> : <p className="muted">No daily warnings indexed.</p>}{blockers.length ? <JsonDetails summary="blockers" data={blockers} /> : <p className="muted">No daily blockers indexed.</p>}</Pane>
    </div>
  </main>;
}
