"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiShadowBookLatest } from "@/hooks/useUiShadowBook";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type Row = Record<string, unknown> & { __id: string };

export default function ShadowBookPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiShadowBookLatest();
  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const snapshot = root?.latest_snapshot ? asRecord(root.latest_snapshot) : null;
  const risk = root?.latest_risk_summary ? asRecord(root.latest_risk_summary) : null;
  const degraded = root ? asStringArray(root.degraded) : [];

  const positions = useMemo(() => {
    const raw = Array.isArray(snapshot?.positions) ? snapshot.positions : [];
    return raw
      .map((x, i) => {
        const r = asRecord(x);
        if (!r) return null;
        return { ...r, __id: `${asString(r.strategy_id) ?? "strategy"}-${asString(r.symbol) ?? i}` };
      })
      .filter((x): x is Row => x !== null);
  }, [snapshot]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "shadow-book",
        ts: asString(root?.generated_at_utc),
        severity: degraded.length ? "warn" : "ok",
        text: degraded.length ? degraded.join(",") : `SHADOW_BOOK positions=${positions.length}`,
      },
    ],
    [degraded, positions.length, root],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<Row>[] = [
    { key: "strategy", header: "Strategy", cell: (r) => <code>{asString(r.strategy_id) ?? "—"}</code> },
    { key: "symbol", header: "Symbol", cell: (r) => asString(r.symbol) ?? "—" },
    { key: "qty", header: "Qty", cell: (r) => String(asNumber(r.quantity) ?? 0) },
    { key: "last", header: "Last", cell: (r) => String(asNumber(r.last_price) ?? 0) },
    { key: "mv", header: "Market value", cell: (r) => String(asNumber(r.market_value) ?? 0) },
    { key: "pnl", header: "Unrealized P&L", cell: (r) => String(asNumber(r.unrealized_pnl) ?? 0) },
    { key: "weight", header: "Weight", cell: (r) => String(asNumber(r.weight) ?? 0) },
  ];

  if (!config.ok) {
    return <div className="term-page cockpit-page"><div className="term-page__banner">{config.error.message}</div></div>;
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Shadow Book</h1>
          <p className="muted">Paper-only portfolio simulator · simulated fills · risk flags · no broker orders</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>No live trading · no order controls</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          Shadow Book is an evidence surface for hypothetical allocations and paper P&amp;L. It never submits broker orders and does not certify profitability.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Book manifest" dense onInspect={() => openInspector({ title: "Shadow Book latest", rawJson: q.data ?? {} })}>
          {q.isError && <p className="muted">DEGRADED · could not load /ui/shadow-book/latest</p>}
          {degraded.length > 0 && <p className="muted">{degraded.join(", ")}</p>}
          <TermKV
            rows={[
              { k: "book_id", v: asString(latest?.book_id) ?? "—" },
              { k: "status", v: <StatusBadge raw={asString(latest?.status) ?? "—"} /> },
              { k: "starting_capital", v: String(asNumber(latest?.starting_capital) ?? 0) },
              { k: "cash", v: String(asNumber(latest?.cash) ?? 0) },
              { k: "manifest_sha256", v: (asString(latest?.manifest_sha256) ?? "—").slice(0, 16) },
              { k: "scan_root", v: asString(root?.scan_root) ?? "—" },
            ]}
          />
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-shadow-book create --book-id demo --strategy-id momentum-SPY --weight 0.25 --json
          </pre>
        </Pane>

        <Pane title="Risk" dense onInspect={() => openInspector({ title: "Shadow Book risk", rawJson: risk ?? {} })}>
          <TermKV
            rows={[
              { k: "risk_status", v: <StatusBadge raw={asString(risk?.status) ?? "—"} /> },
              { k: "gross_exposure", v: String(asNumber(risk?.gross_exposure) ?? 0) },
              { k: "net_liquidation_value", v: String(asNumber(risk?.net_liquidation_value) ?? 0) },
              { k: "max_drawdown", v: String(asNumber(risk?.max_drawdown) ?? 0) },
              { k: "risk_sha256", v: (asString(risk?.risk_sha256) ?? "—").slice(0, 16) },
            ]}
          />
          {Array.isArray(risk?.risk_flags) && risk.risk_flags.length > 0 ? <JsonDetails summary="risk flags" data={risk.risk_flags} /> : <p className="muted">No risk flags indexed.</p>}
        </Pane>

        <Pane title="Positions" dense>
          <DenseTable columns={cols} rows={positions} rowKey={(r) => r.__id} onRowClick={(r) => openInspector({ title: `Shadow position · ${asString(r.strategy_id)}`, rawJson: r })} />
        </Pane>
      </div>
    </main>
  );
}
