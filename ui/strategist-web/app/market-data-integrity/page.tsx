"use client";

import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiMarketDataIntegrity, type UiMarketDataIntegrityQuery } from "@/hooks/useUiMarketDataIntegrity";
import type { UiMarketDataIntegrityEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type IntegrityRow = UiMarketDataIntegrityEntry & { __id: string };
type GateMode = "all" | "PROVEN" | "WARNING" | "BLOCKED" | "NOT_APPLICABLE";
type AdjustedMode = "all" | "ADJUSTED" | "UNADJUSTED" | "UNKNOWN";

const GATES: GateMode[] = ["all", "PROVEN", "WARNING", "BLOCKED", "NOT_APPLICABLE"];
const ADJUSTED: AdjustedMode[] = ["all", "ADJUSTED", "UNADJUSTED", "UNKNOWN"];

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 18)}…` : value;
}

function numberText(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  if (!counts) return [];
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .map(([k, v]) => ({ k, v: String(v) }));
}

export default function MarketDataIntegrityPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [gateMode, setGateMode] = useState<GateMode>("all");
  const [adjustedMode, setAdjustedMode] = useState<AdjustedMode>("all");
  const [providerId, setProviderId] = useState("");
  const [strategyNeedle, setStrategyNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiMarketDataIntegrityQuery = useMemo(
    () => ({
      gateStatus: gateMode === "all" ? null : gateMode,
      adjustedStatus: adjustedMode === "all" ? null : adjustedMode,
      providerId: providerId.trim() || null,
      strategyIdContains: strategyNeedle.trim() || null,
      blockerContains: issueNeedle.trim() || null,
      warningContains: issueNeedle.trim() || null,
      limit: 200,
    }),
    [adjustedMode, gateMode, issueNeedle, providerId, strategyNeedle],
  );

  const integrity = useUiMarketDataIntegrity(query);
  const rows = useMemo<IntegrityRow[]>(() => {
    const entries = Array.isArray(integrity.data?.entries) ? integrity.data.entries : [];
    return entries.map((entry, i) => ({
      ...entry,
      __id: `${entry.artifact_path || entry.strategy_id || "mdi"}:${entry.evidence_sha256 || i}`,
    }));
  }, [integrity.data]);
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(integrity.data?.degraded);
  const guardrails = asStringArray(integrity.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "mdi-posture",
        severity:
          (integrity.data?.summary?.blocked_count ?? 0) > 0 || degraded.length > 0
            ? "bad"
            : (integrity.data?.summary?.warning_gate_count ?? 0) > 0
              ? "warn"
              : "ok",
        text: `market_data_integrity artifacts=${integrity.data?.filtered_artifact_count ?? 0}/${integrity.data?.artifact_count ?? 0} worst=${integrity.data?.summary?.worst_gate_status ?? "UNKNOWN"}`,
      },
      {
        id: "mdi-guardrail",
        severity: "info",
        text: "read-plane only · no provider calls · no promotion or live execution authority",
      },
    ],
    [degraded.length, integrity.data],
  );
  const ticker = useMemo(
    () => [
      { severity: (integrity.data?.summary?.blocked_count ?? 0) > 0 ? ("bad" as const) : ("neutral" as const), text: `MDI ${integrity.data?.filtered_artifact_count ?? 0}` },
      { severity: (integrity.data?.summary?.total_warning_count ?? 0) > 0 ? ("warn" as const) : ("ok" as const), text: `WARN ${integrity.data?.summary?.total_warning_count ?? 0}` },
    ],
    [integrity.data],
  );
  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<IntegrityRow>[] = useMemo(
    () => [
      { key: "gate", header: "gate", width: "11%", cell: (row) => <StatusBadge raw={row.gate_status} /> },
      { key: "strategy", header: "strategy", width: "16%", cell: (row) => <code>{row.strategy_id}</code> },
      { key: "provider", header: "provider", width: "13%", cell: (row) => <code>{row.provider_id}</code> },
      { key: "adjusted", header: "adjusted", width: "11%", cell: (row) => <StatusBadge raw={row.adjusted_status} /> },
      { key: "rows", header: "rows/symbols", width: "10%", cell: (row) => `${row.row_count}/${row.symbol_count}` },
      { key: "stale", header: "stale h", width: "8%", cell: (row) => <code>{numberText(row.stale_last_bar_hours)}</code> },
      { key: "issues", header: "warn/block", width: "9%", cell: (row) => `${row.warning_count}/${row.blocker_count}` },
      { key: "digest", header: "sha256", width: "13%", cell: (row) => <code>{shortDigest(row.evidence_sha256)}</code> },
      { key: "summary", header: "summary", cell: (row) => row.summary_line },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">MARKET DATA · INTEGRITY</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">MARKET DATA · INTEGRITY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/market-data-integrity · PIT artifact scanner · stale bars, adjustedness, survivorship, calendar, and corporate-action warnings
      </p>

      {integrity.isLoading && <p className="muted">Loading…</p>}
      {integrity.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {integrity.error instanceof Error ? integrity.error.message : String(integrity.error)}
        </p>
      )}

      {integrity.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Projection" onInspect={() => openInspector({ title: "Market-data integrity projection", rawJson: integrity.data })}>
              <TermKV
                rows={[
                  { k: "schema", v: integrity.data.schema_version },
                  { k: "scan_root", v: integrity.data.scan_root },
                  { k: "artifacts", v: `${integrity.data.filtered_artifact_count}/${integrity.data.artifact_count}` },
                  { k: "returned", v: String(integrity.data.returned_artifact_count) },
                  { k: "invalid", v: String(integrity.data.invalid_artifact_count) },
                ]}
              />
            </Pane>
            <Pane title="Gate posture">
              <TermKV
                rows={[
                  { k: "worst", v: <StatusBadge raw={integrity.data.summary.worst_gate_status} /> },
                  { k: "blocked", v: String(integrity.data.summary.blocked_count) },
                  { k: "warning", v: String(integrity.data.summary.warning_gate_count) },
                  { k: "proven", v: String(integrity.data.summary.proven_count) },
                  { k: "degraded", v: degraded.length ? degraded.join(", ") : "none" },
                ]}
              />
            </Pane>
            <Pane title="Issue pressure">
              <TermKV
                rows={[
                  { k: "warnings", v: String(integrity.data.summary.total_warning_count) },
                  { k: "blockers", v: String(integrity.data.summary.total_blocker_count) },
                  { k: "stale_blocked", v: String(integrity.data.summary.stale_blocked_count) },
                  { k: "corp_action", v: String(integrity.data.summary.corporate_action_warning_count) },
                  { k: "survivorship", v: String(integrity.data.summary.survivorship_warning_count) },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Filters" dense>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <label className="muted" style={{ fontSize: "10px" }}>
                provider&nbsp;
                <input className="term-input" value={providerId} onChange={(event) => setProviderId(event.target.value)} placeholder="provider_id" style={{ width: "145px" }} />
              </label>
              <label className="muted" style={{ fontSize: "10px" }}>
                strategy&nbsp;
                <input className="term-input" value={strategyNeedle} onChange={(event) => setStrategyNeedle(event.target.value)} placeholder="strategy contains" style={{ width: "165px" }} />
              </label>
              <label className="muted" style={{ fontSize: "10px" }}>
                issue&nbsp;
                <input className="term-input" value={issueNeedle} onChange={(event) => setIssueNeedle(event.target.value)} placeholder="warning/blocker contains" style={{ width: "190px" }} />
              </label>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {GATES.map((gate) => (
                  <button key={gate} type="button" className={`term-btn term-btn--sm${gateMode === gate ? " is-active" : ""}`} onClick={() => setGateMode(gate)}>
                    {gate}
                  </button>
                ))}
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {ADJUSTED.map((mode) => (
                  <button key={mode} type="button" className={`term-btn term-btn--sm${adjustedMode === mode ? " is-active" : ""}`} onClick={() => setAdjustedMode(mode)}>
                    {mode}
                  </button>
                ))}
              </div>
            </div>
          </Pane>

          <Pane title="Integrity artifacts" dense onInspect={() => openInspector({ title: "Market-data integrity rows", rawJson: rows })}>
            <DenseTable
              columns={cols}
              rows={rows}
              rowKey={(row) => row.__id}
              selectedKey={selectedRow?.__id ?? null}
              onRowClick={(row) => {
                setSelected(row.__id);
                if (row.evidence_sha256) setLastDigest(row.evidence_sha256);
                openInspector({
                  title: `Market-data integrity · ${row.strategy_id}`,
                  subtitle: row.summary_line,
                  rawJson: row,
                  digestToCopy: row.evidence_sha256 ?? undefined,
                });
              }}
              empty="No market-data integrity artifacts matched the current filters."
            />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Gate counts"><TermKV rows={countRows(integrity.data.gate_counts)} /></Pane>
            <Pane title="Provider counts"><TermKV rows={countRows(integrity.data.provider_counts)} /></Pane>
            <Pane title="Adjustedness counts"><TermKV rows={countRows(integrity.data.adjusted_status_counts)} /></Pane>
          </PaneGrid>

          <PaneGrid cols={2}>
            <Pane title="Selected artifact" onInspect={selectedRow ? () => openInspector({ title: "Selected market-data integrity artifact", rawJson: selectedRow }) : undefined}>
              <TermKV
                rows={[
                  { k: "strategy", v: selectedRow?.strategy_id ?? "—" },
                  { k: "run", v: selectedRow?.run_id ?? "—" },
                  { k: "calendar", v: selectedRow?.calendar_status ?? "—" },
                  { k: "missing_days", v: String(selectedRow?.missing_trading_days ?? "—") },
                  { k: "missing_ratio", v: numberText(selectedRow?.missing_date_ratio, 3) },
                  { k: "artifact", v: selectedRow?.artifact_path ?? "—" },
                ]}
              />
            </Pane>
            <Pane title="Guardrails">
              <ul className="term-list">
                {guardrails.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </Pane>
          </PaneGrid>
        </>
      )}
    </div>
  );
}
