"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiBacktestForensicsLatest, type UiBacktestForensicsQuery } from "@/hooks/useUiBacktestForensics";
import type { UiBacktestForensicsStrategy } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type StrategyRow = UiBacktestForensicsStrategy & { __id: string };
type PostureMode = "all" | "REVIEW_READY" | "NEEDS_EVIDENCE" | "PAPER_ONLY" | "BLOCKED" | "OBSERVE";
type StatusMode = "all" | "PASSED" | "PAPER_ONLY" | "BLOCKED" | "FAILED" | "PENDING";
type DataPlaneMode = "all" | "SYNTHETIC" | "PROVIDER_SNAPSHOT" | "REAL_LOCAL" | "UNKNOWN";
type PromotionMode = "all" | "eligible" | "blocked";

const POSTURES: PostureMode[] = ["all", "REVIEW_READY", "NEEDS_EVIDENCE", "PAPER_ONLY", "BLOCKED", "OBSERVE"];
const STATUSES: StatusMode[] = ["all", "PASSED", "PAPER_ONLY", "BLOCKED", "FAILED", "PENDING"];
const DATA_PLANES: DataPlaneMode[] = ["all", "SYNTHETIC", "PROVIDER_SNAPSHOT", "REAL_LOCAL", "UNKNOWN"];

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : fallback;
  if (typeof value === "boolean") return String(value);
  return String(value);
}

function fixed(value: unknown, digits = 3): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

function countRows(counts: unknown): { k: string; v: string }[] {
  if (!counts || typeof counts !== "object" || Array.isArray(counts)) return [];
  return Object.entries(counts as Record<string, unknown>)
    .sort((a, b) => Number(b[1] ?? 0) - Number(a[1] ?? 0) || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([k, v]) => ({ k, v: text(v, "0") }));
}

function digestFrom(row: StrategyRow | null): string | null {
  const artifacts = row?.artifacts;
  const observed = artifacts && typeof artifacts === "object" && !Array.isArray(artifacts) ? (artifacts as { observed_sha256?: Record<string, unknown> }).observed_sha256 : null;
  if (!observed || typeof observed !== "object") return null;
  for (const value of Object.values(observed)) {
    if (typeof value === "string" && value) return value;
  }
  return null;
}

function promotionFilter(mode: PromotionMode): boolean | null {
  if (mode === "eligible") return true;
  if (mode === "blocked") return false;
  return null;
}

export default function BacktestForensicsPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [postureMode, setPostureMode] = useState<PostureMode>("all");
  const [statusMode, setStatusMode] = useState<StatusMode>("all");
  const [dataPlaneMode, setDataPlaneMode] = useState<DataPlaneMode>("all");
  const [promotionMode, setPromotionMode] = useState<PromotionMode>("all");
  const [strategyNeedle, setStrategyNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [riskFlagNeedle, setRiskFlagNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiBacktestForensicsQuery = useMemo(
    () => ({
      reviewPosture: postureMode === "all" ? null : postureMode,
      status: statusMode === "all" ? null : statusMode,
      dataPlane: dataPlaneMode === "all" ? null : dataPlaneMode,
      promotionEligible: promotionFilter(promotionMode),
      strategyIdContains: strategyNeedle.trim() || null,
      blockerContains: issueNeedle.trim() || null,
      warningContains: issueNeedle.trim() || null,
      riskFlag: riskFlagNeedle.trim().toUpperCase() || null,
      limit: 200,
    }),
    [dataPlaneMode, issueNeedle, postureMode, promotionMode, riskFlagNeedle, statusMode, strategyNeedle],
  );

  const forensics = useUiBacktestForensicsLatest(query);
  const rows = useMemo<StrategyRow[]>(() => {
    const strategies = Array.isArray(forensics.data?.strategies) ? forensics.data.strategies : [];
    return strategies.map((row, index) => ({ ...row, __id: `${row.strategy_id}:${row.status}:${index}` }));
  }, [forensics.data?.strategies]);
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const summary = forensics.data?.filtered_summary ?? forensics.data?.summary ?? {};
  const degraded = asStringArray(forensics.data?.degraded);
  const guardrails = asStringArray(forensics.data?.guardrails);
  const selectedDigest = digestFrom(selectedRow);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "backtest-forensics-posture",
        severity: (Number(summary.blocked_count ?? 0) > 0 || degraded.length > 0) ? "warn" : "ok",
        text: `backtest_forensics strategies=${forensics.data?.returned_strategy_count ?? rows.length}/${forensics.data?.total_strategy_count ?? 0} review_ready=${text(summary.review_ready_count, "0")} blocked=${text(summary.blocked_count, "0")}`,
      },
      {
        id: "backtest-forensics-guardrail",
        severity: "info",
        text: "read-plane only · evidence review surface · promotion still requires governed validator/orchestrator path",
      },
    ],
    [degraded.length, forensics.data?.returned_strategy_count, forensics.data?.total_strategy_count, rows.length, summary],
  );
  const ticker = useMemo(
    () => [
      { severity: Number(summary.review_ready_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `READY ${text(summary.review_ready_count, "0")}` },
      { severity: Number(summary.blocker_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BLK ${text(summary.blocker_count, "0")}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<StrategyRow>[] = useMemo(
    () => [
      { key: "posture", header: "posture", width: "13%", cell: (row) => <StatusBadge raw={row.review_posture} /> },
      { key: "strategy", header: "strategy", width: "16%", cell: (row) => <code>{row.strategy_id}</code> },
      { key: "status", header: "status", width: "10%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "data", header: "data", width: "12%", cell: (row) => <code>{row.data_plane}</code> },
      { key: "eligible", header: "eligible", width: "8%", cell: (row) => String(row.promotion_eligible) },
      { key: "return", header: "return/dd", width: "12%", cell: (row) => `${fixed(row.metrics?.total_return)}/${fixed(row.metrics?.max_drawdown)}` },
      { key: "flags", header: "risk flags", cell: (row) => row.risk_flags.slice(0, 3).join(" · ") || "—" },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">BACKTEST · FORENSICS</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">BACKTEST · FORENSICS</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/backtest-forensics/latest · strategy-batch forensic read model · evidence posture, promotion blockers, and risk flag review
      </p>

      {forensics.isLoading && <p className="muted">Loading…</p>}
      {forensics.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {forensics.error instanceof Error ? forensics.error.message : String(forensics.error)}
        </p>
      )}

      {forensics.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Forensic batch" onInspect={() => openInspector({ title: "Backtest forensics payload", rawJson: forensics.data })}>
              <TermKV
                rows={[
                  { k: "schema", v: forensics.data.schema_version },
                  { k: "summary_path", v: forensics.data.summary_path ?? "—" },
                  { k: "route", v: forensics.data.raw_strategy_batch_route ?? "—" },
                  { k: "strategies", v: `${forensics.data.returned_strategy_count ?? rows.length}/${forensics.data.filtered_strategy_count ?? rows.length}/${forensics.data.total_strategy_count ?? rows.length}` },
                  { k: "degraded", v: degraded.join(" · ") || "—" },
                ]}
              />
            </Pane>
            <Pane title="Filtered posture">
              <TermKV
                rows={[
                  { k: "review_ready", v: text(summary.review_ready_count, "0") },
                  { k: "needs_evidence", v: text(summary.needs_evidence_count, "0") },
                  { k: "paper_only", v: text(summary.paper_only_count, "0") },
                  { k: "blocked", v: text(summary.blocked_count, "0") },
                  { k: "promotion_eligible", v: text(summary.promotion_eligible_count, "0") },
                ]}
              />
            </Pane>
            <Pane title="Selected strategy" onInspect={selectedRow ? () => openInspector({ title: "Backtest forensic strategy", rawJson: selectedRow }) : undefined}>
              <TermKV
                rows={[
                  { k: "strategy", v: selectedRow?.strategy_id ?? "—" },
                  { k: "recommendation", v: selectedRow?.review_recommendation ?? "—" },
                  { k: "pit", v: selectedRow?.pit_status ?? "—" },
                  { k: "bars", v: text(selectedRow?.bars_row_count) },
                  { k: "digest", v: selectedDigest ? `${selectedDigest.slice(0, 18)}…` : "—" },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Filters" dense>
            <div className="term-toolbar">
              <label className="term-field">
                <span>strategy</span>
                <input className="term-input" value={strategyNeedle} onChange={(event) => setStrategyNeedle(event.target.value)} placeholder="strategy id contains" style={{ width: "180px" }} />
              </label>
              <label className="term-field">
                <span>issue</span>
                <input className="term-input" value={issueNeedle} onChange={(event) => setIssueNeedle(event.target.value)} placeholder="warning/blocker contains" style={{ width: "190px" }} />
              </label>
              <label className="term-field">
                <span>risk</span>
                <input className="term-input" value={riskFlagNeedle} onChange={(event) => setRiskFlagNeedle(event.target.value)} placeholder="risk flag exact" style={{ width: "170px" }} />
              </label>
              <select className="term-input" value={promotionMode} onChange={(event) => setPromotionMode(event.target.value as PromotionMode)} aria-label="promotion filter" style={{ width: "120px" }}>
                <option value="all">all promo</option>
                <option value="eligible">eligible</option>
                <option value="blocked">blocked</option>
              </select>
            </div>
            <div className="term-toolbar" style={{ marginTop: "6px" }}>
              {POSTURES.map((mode) => (
                <button key={mode} type="button" className={`term-btn term-btn--sm${postureMode === mode ? " is-active" : ""}`} onClick={() => setPostureMode(mode)}>
                  {mode}
                </button>
              ))}
            </div>
            <div className="term-toolbar" style={{ marginTop: "6px" }}>
              {STATUSES.map((mode) => (
                <button key={mode} type="button" className={`term-btn term-btn--sm${statusMode === mode ? " is-active" : ""}`} onClick={() => setStatusMode(mode)}>
                  {mode}
                </button>
              ))}
            </div>
            <div className="term-toolbar" style={{ marginTop: "6px" }}>
              {DATA_PLANES.map((mode) => (
                <button key={mode} type="button" className={`term-btn term-btn--sm${dataPlaneMode === mode ? " is-active" : ""}`} onClick={() => setDataPlaneMode(mode)}>
                  {mode}
                </button>
              ))}
            </div>
          </Pane>

          <Pane title="Strategy forensics" dense onInspect={() => openInspector({ title: "Backtest forensic rows", rawJson: rows })}>
            <DenseTable
              columns={columns}
              rows={rows}
              rowKey={(row) => row.__id}
              selectedKey={selectedRow?.__id ?? null}
              onRowClick={(row) => {
                setSelected(row.__id);
                const digest = digestFrom(row);
                if (digest) setLastDigest(digest);
                openInspector({ title: `Backtest forensic · ${row.strategy_id}`, rawJson: row });
              }}
              empty="No strategy rows matched the selected forensic filters."
            />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Review posture counts" dense>
              <DenseTable columns={[{ key: "k", header: "posture", cell: (row: { k: string; v: string }) => row.k }, { key: "v", header: "count", cell: (row: { k: string; v: string }) => row.v }]} rows={countRows(summary.review_posture_counts)} rowKey={(row) => row.k} />
            </Pane>
            <Pane title="Risk flag pressure" dense>
              <DenseTable columns={[{ key: "k", header: "flag", cell: (row: { k: string; v: string }) => row.k }, { key: "v", header: "count", cell: (row: { k: string; v: string }) => row.v }]} rows={countRows(summary.risk_flag_counts)} rowKey={(row) => row.k} />
            </Pane>
            <Pane title="Guardrails" dense>
              <ul className="term-list">
                {guardrails.map((line) => <li key={line}>{line}</li>)}
                {!guardrails.length && <li>Read-plane only · no live execution authority.</li>}
              </ul>
            </Pane>
          </PaneGrid>

          <PaneGrid cols={2}>
            <Pane title="Gate matrix" dense onInspect={selectedRow ? () => openInspector({ title: "Selected gate matrix", rawJson: selectedRow.gate_matrix }) : undefined}>
              <pre className="json-preview">{JSON.stringify(selectedRow?.gate_matrix ?? {}, null, 2)}</pre>
            </Pane>
            <Pane title="Artifacts" dense onInspect={selectedRow ? () => openInspector({ title: "Selected forensic artifacts", rawJson: selectedRow.artifacts }) : undefined}>
              <pre className="json-preview">{JSON.stringify(selectedRow?.artifacts ?? {}, null, 2)}</pre>
            </Pane>
          </PaneGrid>

          <JsonDetails summary="Drilldown: full /ui/backtest-forensics/latest JSON" data={forensics.data} />
        </>
      )}
    </div>
  );
}
