"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiStrategyMemoryLatest } from "@/hooks/useUiStrategyMemory";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

type Row = Record<string, unknown> & { __id: string };

export default function StrategyMemoryPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const q = useUiStrategyMemoryLatest();

  const root = q.data ? asRecord(q.data) : null;
  const latest = root?.latest ? asRecord(root.latest) : null;
  const degraded = useMemo(() => (root ? asStringArray(root.degraded) : []), [root]);
  const records = useMemo(() => {
    const raw = Array.isArray(latest?.memory_records) ? latest?.memory_records : [];
    return raw
      .map((x, i) => {
        const r = asRecord(x);
        if (!r) return null;
        return { ...r, __id: asString(r.strategy_id) ?? `strategy-${i}` };
      })
      .filter((x): x is Row => x !== null);
  }, [latest]);
  const graveyard = Array.isArray(latest?.recent_graveyard_entries) ? latest?.recent_graveyard_entries : [];
  const dupes = Array.isArray(latest?.duplicate_variant_warnings) ? latest?.duplicate_variant_warnings : [];
  const failures = latest?.top_failure_reasons && typeof latest.top_failure_reasons === "object" ? (latest.top_failure_reasons as Record<string, unknown>) : {};

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "memory",
        ts: asString(root?.generated_at_utc),
        severity: degraded.length ? "warn" : "ok",
        text: degraded.length ? degraded.join(",") : `STRATEGY_MEMORY records=${records.length}`,
      },
    ],
    [degraded, records.length, root],
  );
  useTerminalPageBind(tape, []);

  const cols: DenseColumn<Row>[] = [
    { key: "id", header: "Strategy", cell: (r) => <code>{asString(r.strategy_id) ?? "—"}</code> },
    { key: "family", header: "Family", cell: (r) => <code>{asString(r.family_id) ?? "—"}</code> },
    { key: "status", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status) ?? "—"} /> },
    { key: "type", header: "Type", cell: (r) => asString(r.strategy_type) ?? "—" },
    { key: "universe", header: "Universe", cell: (r) => asString(r.universe) ?? "—" },
    { key: "plane", header: "Data", cell: (r) => asString(r.data_plane) ?? "—" },
    {
      key: "reasons",
      header: "Failure reasons",
      cell: (r) => (Array.isArray(r.failure_reasons) ? r.failure_reasons.join(", ") : "—"),
    },
    { key: "digest", header: "Digest", cell: (r) => <code>{(asString(r.record_sha256) ?? "—").slice(0, 12)}</code> },
  ];

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  return (
    <main className="console">
      <div className="console-header">
        <div>
          <h1>Strategy Memory</h1>
          <p className="muted">Candidate graveyard · lineage memory · duplicate warning surface · research only</p>
        </div>
      </div>

      <div className="readiness" role="status">
        <strong>No live trading</strong>
        <p className="muted" style={{ margin: "0.35rem 0 0" }}>
          Strategy Memory records why candidates were rejected or killed so the operator does not rediscover the same bad ideas. It is not a profitability claim and exposes no broker/order controls.
        </p>
      </div>

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane title="Memory index" dense onInspect={() => openInspector({ title: "Strategy Memory latest", rawJson: q.data ?? {} })}>
          {q.isError && <p className="muted">DEGRADED · could not load /ui/strategy-memory/latest</p>}
          {degraded.length > 0 && <p className="muted">{degraded.join(", ")}</p>}
          <TermKV
            rows={[
              { k: "active", v: String(asNumber(latest?.active_count) ?? 0) },
              { k: "killed", v: String(asNumber(latest?.killed_count) ?? 0) },
              { k: "rejected", v: String(asNumber(latest?.rejected_count) ?? 0) },
              { k: "duplicate_variant", v: String(asNumber(latest?.duplicate_variant_count) ?? 0) },
              { k: "families", v: String(asNumber(latest?.family_count) ?? 0) },
              { k: "index_sha256", v: (asString(latest?.index_sha256) ?? "—").slice(0, 16) },
              { k: "scan_root", v: asString(root?.scan_root) ?? "—" },
            ]}
          />
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-strategy-memory ingest-batch --batch-run artifacts/strategy_runs/&lt;run-id&gt; --json
          </pre>
        </Pane>

        <Pane title="Failure reason histogram" dense onInspect={() => openInspector({ title: "Failure reasons", rawJson: failures })}>
          {Object.keys(failures).length ? (
            <ul style={{ margin: 0, paddingLeft: "1.1rem", fontSize: "11px" }}>
              {Object.entries(failures).map(([k, v]) => (
                <li key={k}>
                  <code>{k}</code> · {String(v)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No failures indexed yet.</p>
          )}
        </Pane>

        <Pane title="Duplicate warnings" dense onInspect={() => openInspector({ title: "Duplicate warnings", rawJson: dupes })}>
          {dupes.length ? <JsonDetails summary="duplicate warnings" data={dupes} /> : <p className="muted">No duplicate variants flagged.</p>}
        </Pane>

        <Pane title="Graveyard" dense onInspect={() => openInspector({ title: "Candidate graveyard", rawJson: graveyard })}>
          {graveyard.length ? <JsonDetails summary="recent graveyard entries" data={graveyard} /> : <p className="muted">No killed/rejected candidates indexed yet.</p>}
        </Pane>

        <Pane title="Strategy records" dense>
          <DenseTable
            columns={cols}
            rows={records}
            rowKey={(r) => r.__id}
            onRowClick={(r) => openInspector({ title: `Strategy Memory · ${asString(r.strategy_id)}`, rawJson: r })}
          />
        </Pane>
      </div>
    </main>
  );
}
