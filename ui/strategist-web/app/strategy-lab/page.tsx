"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { StrategyLabCharts } from "@/components/strategy-lab/StrategyLabCharts";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiStrategyBatchLatest, useUiStrategyBatchList } from "@/hooks/useUiStrategyBatches";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type StatusFilter = "ALL" | "PASSED" | "FAILED" | "BLOCKED" | "PAPER_ONLY";

type SRow = Record<string, unknown> & { __id: string };

export default function StrategyLabPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const latest = useUiStrategyBatchLatest();
  const list = useUiStrategyBatchList();
  const [filter, setFilter] = useState<StatusFilter>("ALL");
  const [sel, setSel] = useState<string | null>(null);

  const latestRoot = latest.data != null ? asRecord(latest.data) : null;
  const batch = latestRoot?.latest != null ? asRecord(latestRoot.latest as object) : null;
  const degraded = latestRoot ? asStringArray(latestRoot.degraded) : [];
  const strategiesRaw = batch?.strategies;
  const rows: SRow[] = useMemo(() => {
    const raw = Array.isArray(strategiesRaw) ? strategiesRaw : [];
    return raw
      .map((x, i) => {
        const r = asRecord(x);
        if (!r) return null;
        return { ...r, __id: asString(r.strategy_id) ?? `s-${i}` };
      })
      .filter((x): x is SRow => x != null);
  }, [strategiesRaw]);

  const filtered = useMemo(() => {
    if (filter === "ALL") return rows;
    return rows.filter((r) => asString(r.status)?.toUpperCase() === filter);
  }, [rows, filter]);

  const selectedRow = useMemo(() => {
    if (!sel) return null;
    return rows.find((r) => r.__id === sel) ?? null;
  }, [rows, sel]);

  const batchRanking = batch?.batch_ranking;
  const chartRows = useMemo(() => rows.map((r) => ({ ...r } as Record<string, unknown>)), [rows]);

  const syntheticWarn = useMemo(
    () =>
      rows.some((r) => {
        const plane = asString(r.data_plane);
        if (plane === "SYNTHETIC") return true;
        const w = r.warnings;
        if (!Array.isArray(w)) return false;
        return w.some((x) => String(x).includes("SYNTHETIC"));
      }),
    [rows],
  );

  const hasRealLocal = useMemo(() => rows.some((r) => asString(r.data_plane) === "REAL_LOCAL"), [rows]);

  const tape: TapeLine[] = useMemo(() => {
    const ts = asString(latestRoot?.generated_at_utc);
    return [
      {
        id: "batch",
        ts,
        severity: batch ? "ok" : "warn",
        text: batch ? `BATCH ${asString(batch.batch_id)}` : "NO_BATCH_ARTIFACTS",
      },
      {
        id: "rows",
        ts,
        severity: rows.length ? "ok" : "neutral",
        text: `STRATEGIES ${rows.length}`,
      },
    ];
  }, [batch, latestRoot, rows.length]);

  useTerminalPageBind(tape, []);

  const dataBadge = (r: SRow) => {
    const plane = asString(r.data_plane);
    if (plane === "REAL_LOCAL") return <span className="cockpit-nav-link active">REAL</span>;
    if (plane === "SYNTHETIC") return <span className="muted">PAPER_ONLY</span>;
    return <span className="muted">—</span>;
  };

  const portfolio = batch?.portfolio_correlation_summary;
  const portfolioRec = portfolio != null && typeof portfolio === "object" ? (portfolio as Record<string, unknown>) : null;
  const allocRaw = latestRoot?.portfolio_allocation;
  const allocRec = allocRaw != null && typeof allocRaw === "object" ? (allocRaw as Record<string, unknown>) : null;
  const topCand = batch?.top_candidate;
  const promoCounts = batch?.promotion_blocked_counts;

  const cols: DenseColumn<SRow>[] = [
    {
      key: "rk",
      header: "Rank",
      width: "48px",
      cell: (r) => (r.analytics_rank != null ? String(r.analytics_rank) : "—"),
    },
    { key: "id", header: "Strategy", cell: (r) => <code>{asString(r.strategy_id)}</code> },
    {
      key: "sc",
      header: "Score",
      width: "64px",
      cell: (r) => (typeof r.analytics_score === "number" ? r.analytics_score.toFixed(2) : "—"),
    },
    {
      key: "tr",
      header: "Tot ret",
      width: "72px",
      cell: (r) => {
        const x = r.total_return ?? (r.metrics as { total_return?: number } | undefined)?.total_return;
        return typeof x === "number" ? x.toFixed(3) : "—";
      },
    },
    {
      key: "mdd",
      header: "Max DD",
      width: "64px",
      cell: (r) => {
        const x = r.max_drawdown ?? (r.metrics as { max_drawdown?: number } | undefined)?.max_drawdown;
        return typeof x === "number" ? x.toFixed(3) : "—";
      },
    },
    {
      key: "sh",
      header: "Sharpe~",
      width: "64px",
      cell: (r) => {
        const x = r.sharpe_like ?? (r.metrics as { sharpe_like?: number } | undefined)?.sharpe_like;
        return typeof x === "number" ? x.toFixed(2) : "—";
      },
    },
    { key: "st", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status)} /> },
    { key: "db", header: "Data plane", width: "88px", cell: dataBadge },
    {
      key: "dq",
      header: "DQ",
      width: "72px",
      cell: (r) => {
        const g = r.gate_summary;
        const fromGate =
          g && typeof g === "object" && "data_quality_gate" in g
            ? asString((g as { data_quality_gate?: string }).data_quality_gate)
            : null;
        return <StatusBadge raw={fromGate ?? asString(r.data_quality_gate_status) ?? "—"} />;
      },
    },
    { key: "pit", header: "PIT", width: "72px", cell: (r) => asString(r.pit_status) ?? "—" },
    {
      key: "pitsnap",
      header: "PIT snap",
      width: "96px",
      cell: (r) => asString(r.pit_snapshot_status) ?? "—",
    },
    { key: "data", header: "Data", width: "88px", cell: (r) => asString(r.data_status) ?? "—" },
    {
      key: "rows",
      header: "Bars",
      width: "52px",
      cell: (r) => (r.bars_row_count != null ? String(r.bars_row_count) : "—"),
    },
    {
      key: "dig",
      header: "Bars digest",
      cell: (r) => {
        const d = asString(r.data_snapshot_digest);
        return <code>{d ? d.slice(0, 12) : "—"}</code>;
      },
    },
    {
      key: "promo",
      header: "Promo",
      width: "64px",
      cell: (r) => {
        const g = r.gate_summary;
        const eligible = g && typeof g === "object" && "promotion_eligible" in g ? Boolean((g as { promotion_eligible?: boolean }).promotion_eligible) : false;
        return eligible ? "true" : "false";
      },
    },
    {
      key: "xreal",
      header: "Exec real",
      width: "88px",
      cell: (r) => {
        const g = r.gate_summary;
        const fromRow = asString(r.execution_realism_gate);
        const fromGate =
          g && typeof g === "object" && "execution_realism_gate" in g
            ? asString((g as { execution_realism_gate?: string }).execution_realism_gate)
            : null;
        const raw = fromRow ?? fromGate ?? "—";
        return <StatusBadge raw={raw} />;
      },
    },
    {
      key: "rob",
      header: "Robustness",
      width: "96px",
      cell: (r) => {
        const fromRow = asString(r.robustness_gate_status);
        const g = r.gate_summary;
        const fromGate =
          g && typeof g === "object" && "robustness_gate" in g
            ? asString((g as { robustness_gate?: string }).robustness_gate)
            : null;
        const raw = fromRow ?? fromGate ?? "—";
        return <StatusBadge raw={raw} />;
      },
    },
    {
      key: "cpcv",
      header: "CPCV",
      width: "72px",
      cell: (r) => <StatusBadge raw={asString(r.cpcv_robustness_gate_status) ?? "—"} />,
    },
    {
      key: "ps",
      header: "Param",
      width: "72px",
      cell: (r) => {
        const g = r.gate_summary;
        const fromGate =
          g && typeof g === "object" && "parameter_sensitivity_gate" in g
            ? asString((g as { parameter_sensitivity_gate?: string }).parameter_sensitivity_gate)
            : null;
        return <StatusBadge raw={fromGate ?? asString(r.parameter_sensitivity_gate_status) ?? "—"} />;
      },
    },
    {
      key: "reg",
      header: "Regime",
      width: "72px",
      cell: (r) => {
        const g = r.gate_summary;
        const fromGate =
          g && typeof g === "object" && "regime_analysis_gate" in g
            ? asString((g as { regime_analysis_gate?: string }).regime_analysis_gate)
            : null;
        return <StatusBadge raw={fromGate ?? asString(r.regime_analysis_gate_status) ?? "—"} />;
      },
    },
    {
      key: "folds",
      header: "Folds",
      width: "52px",
      cell: (r) => (r.robustness_fold_count != null ? String(r.robustness_fold_count) : "—"),
    },
    {
      key: "pfr",
      header: "Pos fold %",
      width: "72px",
      cell: (r) => {
        const x = r.positive_fold_ratio;
        return typeof x === "number" ? `${(x * 100).toFixed(0)}%` : "—";
      },
    },
    {
      key: "wfr",
      header: "Worst fold",
      width: "80px",
      cell: (r) => {
        const x = r.worst_fold_return;
        return typeof x === "number" ? x.toFixed(3) : "—";
      },
    },
    {
      key: "pbo",
      header: "PBO-like",
      width: "72px",
      cell: (r) => {
        const x = r.pbo_like_score;
        return typeof x === "number" ? x.toFixed(2) : "—";
      },
    },
    {
      key: "dsr",
      header: "DSR-like",
      width: "72px",
      cell: (r) => {
        const x = r.dsr_like_score;
        return typeof x === "number" ? x.toFixed(2) : "—";
      },
    },
    { key: "adj", header: "Adj", width: "72px", cell: (r) => asString(r.adjudication_status) ?? "—" },
    {
      key: "ev",
      header: "Evidence",
      cell: (r) => <code>{(asString(r.evidence_manifest_sha256) ?? "—").slice(0, 10)}</code>,
    },
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
          <h1>Strategy Lab</h1>
          <p className="muted">Read-plane batch results · research/paper only · no live trading</p>
        </div>
      </div>

      {syntheticWarn && (
        <div className="readiness" role="status">
          <strong>Synthetic demo data</strong>
          <p className="muted" style={{ margin: "0.35rem 0 0" }}>
            Synthetic paths stay PAPER_ONLY; robustness is NOT_APPLICABLE on demo data; promotion stays false until
            walk-forward robustness and execution realism are PROVEN on governed local bars.
          </p>
        </div>
      )}

      {hasRealLocal && (
        <div className="readiness" role="status">
          <strong>Real local bars</strong>
          <p className="muted" style={{ margin: "0.35rem 0 0" }}>
            Rows marked REAL use repo-local CSV/JSON snapshots. Open a strategy row to inspect gate_summary and
            data_snapshot_digest; read data_snapshot_manifest.json under the strategy artifact directory.
          </p>
        </div>
      )}

      <div className="cockpit-grid" style={{ gridTemplateColumns: "1fr" }}>
        <Pane
          title="Latest batch"
          dense
          onInspect={() =>
            openInspector({
              title: "Strategy batch · latest",
              rawJson: latest.data ?? {},
            })
          }
        >
          {latest.isError && <p className="muted">DEGRADED · could not load /ui/strategy-batches/latest</p>}
          {degraded.length > 0 && (
            <p className="muted" style={{ fontSize: "11px" }}>
              {degraded.join(", ")}
            </p>
          )}
          {batch ? (
            <TermKV
              rows={[
                { k: "batch_id", v: asString(batch.batch_id) ?? "—" },
                { k: "run_id", v: asString(batch.run_id) ?? "—" },
                { k: "generated_at_utc", v: asString(batch.generated_at_utc) ?? "—" },
                { k: "strategies", v: String(batch.strategy_count ?? "0") },
                { k: "ok", v: String(batch.ok) },
                { k: "passed", v: String(batch.passed_count ?? "0") },
                { k: "paper_only", v: String(batch.paper_only_count ?? "0") },
                { k: "failed", v: String(batch.failed_count ?? "0") },
                { k: "blocked", v: String(batch.blocked_count ?? "0") },
                {
                  k: "top_candidate",
                  v: topCand && typeof topCand === "object" ? JSON.stringify(topCand) : "—",
                },
                {
                  k: "portfolio_gate",
                  v: asString(portfolioRec?.portfolio_gate_status) ?? "—",
                },
                {
                  k: "diversification_score",
                  v:
                    typeof portfolioRec?.diversification_score === "number"
                      ? String(portfolioRec.diversification_score)
                      : "—",
                },
                {
                  k: "promo_block_counts",
                  v: promoCounts && typeof promoCounts === "object" ? JSON.stringify(promoCounts) : "—",
                },
                {
                  k: "summary_path",
                  v: asString(latestRoot?.summary_path) ?? "—",
                },
              ]}
            />
          ) : (
            <p className="muted">No batch artifacts under scan root. Run the CLI to generate evidence.</p>
          )}
          <pre className="json-preview" style={{ marginTop: "0.75rem", fontSize: "10px" }}>
            strategy-validator-strategy-batch-run --batch configs/strategy_batches/example_batch.json --output-root
            artifacts/strategy_runs --max-workers 4 --mode paper --run-id my-run --overwrite --json
          </pre>
        </Pane>

        <Pane
          title="Portfolio correlation (batch)"
          dense
          onInspect={() =>
            openInspector({
              title: "Portfolio correlation summary",
              rawJson: portfolioRec ?? {},
            })
          }
        >
          {!portfolioRec ? (
            <p className="muted">No portfolio summary on this batch (single strategy or synthetic-only).</p>
          ) : (
            <div style={{ fontSize: "11px" }}>
              <p style={{ margin: "0 0 0.5rem" }}>
                <strong>{asString(portfolioRec.portfolio_gate_status as string) ?? "—"}</strong>
                <span className="muted"> · avg corr </span>
                {typeof portfolioRec.average_correlation === "number"
                  ? (portfolioRec.average_correlation as number).toFixed(3)
                  : "—"}
              </p>
              {Array.isArray(portfolioRec.high_correlation_pairs) &&
              (portfolioRec.high_correlation_pairs as unknown[]).length > 0 ? (
                <ul style={{ margin: 0, paddingLeft: "1.1rem" }}>
                  {(portfolioRec.high_correlation_pairs as { a?: string; b?: string; correlation?: number }[]).map(
                    (p, i) => (
                      <li key={i}>
                        <code>{p.a}</code> ↔ <code>{p.b}</code>{" "}
                        {typeof p.correlation === "number" ? p.correlation.toFixed(3) : ""}
                      </li>
                    ),
                  )}
                </ul>
              ) : (
                <p className="muted" style={{ margin: 0 }}>
                  No high-correlation pairs flagged (&gt;0.90).
                </p>
              )}
            </div>
          )}
        </Pane>

        <Pane
          title="Portfolio allocation (simulated)"
          dense
          onInspect={() => openInspector({ title: "Portfolio allocation result", rawJson: allocRec ?? {} })}
        >
          {!allocRec ? (
            <p className="muted">
              No <code>portfolio_allocation_result.json</code> beside this batch. Run{" "}
              <code>strategy-validator-portfolio-sim --batch-run &lt;run-dir&gt; --json</code>.
            </p>
          ) : (
            <div style={{ fontSize: "11px" }}>
              <p style={{ margin: "0 0 0.5rem" }}>
                <strong>{asString(allocRec.allocation_gate_status as string) ?? "—"}</strong>
                <span className="muted"> · digest </span>
                <code>{(asString(allocRec.evidence_digest as string) ?? "—").slice(0, 12)}</code>
              </p>
              <p className="muted" style={{ margin: 0 }}>
                Research/paper simulation only — not orders, not optimal allocation, no profitability claim.
              </p>
            </div>
          )}
        </Pane>

        <Pane
          title="Recent batches"
          dense
          onInspect={() => openInspector({ title: "Strategy batches · list", rawJson: list.data ?? {} })}
        >
          {list.data && <JsonDetails summary="batch index" data={list.data} />}
        </Pane>

        <Pane title="Strategies" dense>
          <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap", marginBottom: "0.5rem" }}>
            {(["ALL", "PASSED", "FAILED", "BLOCKED", "PAPER_ONLY"] as const).map((f) => (
              <button
                key={f}
                type="button"
                className={filter === f ? "cockpit-nav-link active" : "cockpit-nav-link"}
                style={{ border: "none", cursor: "pointer", background: "transparent" }}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
          <DenseTable
            columns={cols}
            rows={filtered}
            rowKey={(r) => r.__id}
            selectedKey={sel}
            onRowClick={(r) => {
              setSel(r.__id);
              const gs = r.gate_summary;
              openInspector({
                title: `Strategy · ${asString(r.strategy_id)}`,
                subtitle: asString(r.decision) ?? undefined,
                rawJson: {
                  ...r,
                  gate_matrix: gs,
                  promotion_blocked_reasons:
                    gs && typeof gs === "object" && "promotion_blocked_reasons" in gs
                      ? (gs as { promotion_blocked_reasons?: string[] }).promotion_blocked_reasons
                      : [],
                  data_snapshot_inspector: {
                    digest: r.data_snapshot_digest ?? null,
                    manifest_path: r.data_snapshot_manifest_path ?? null,
                    manifest_sha256: r.data_snapshot_manifest_sha256 ?? null,
                    bars_row_count: r.bars_row_count ?? null,
                    pit_snapshot_status: r.pit_snapshot_status ?? null,
                  },
                  execution_realism_inspector: {
                    model_label: asString(r.execution_realism_model_label),
                    gate_status: asString(r.execution_realism_gate),
                    estimated_slippage_bps: r.execution_realism_est_slippage_bps ?? null,
                    estimated_fee_bps: r.execution_realism_est_fee_bps ?? null,
                    capacity_notional: r.execution_realism_capacity_notional ?? null,
                    estimated_participation: r.execution_realism_est_participation ?? null,
                    evidence_digest: r.execution_realism_digest ?? null,
                    artifact_note: "See execution_realism_result.json next to evidence_manifest.json",
                  },
                  robustness_inspector: {
                    model_label: asString(r.robustness_model_label),
                    gate_status: asString(r.robustness_gate_status),
                    fold_count: r.robustness_fold_count ?? null,
                    positive_fold_ratio: r.positive_fold_ratio ?? null,
                    worst_fold_return: r.worst_fold_return ?? null,
                    pbo_like_score: r.pbo_like_score ?? null,
                    dsr_like_score: r.dsr_like_score ?? null,
                    evidence_digest: r.robustness_evidence_sha256 ?? null,
                    artifact_path: r.robustness_artifact_path ?? null,
                    cpcv_gate: asString(r.cpcv_robustness_gate_status),
                    cpcv_artifact_path: asString(r.cpcv_artifact_path),
                    cpcv_evidence_digest: asString(r.cpcv_evidence_sha256),
                    explanation:
                      "Walk-forward is a heuristic baseline; CPCV path (cpcv_result.json) adds a stronger combinatorial layer when sample permits. Neither proves profitability.",
                  },
                  gauntlet_inspector: {
                    data_quality_path: r.data_quality_artifact_path ?? null,
                    data_quality_gate: asString(r.data_quality_gate_status),
                    parameter_sensitivity_path: r.parameter_sensitivity_artifact_path ?? null,
                    parameter_sensitivity_gate: asString(r.parameter_sensitivity_gate_status),
                    regime_analysis_path: r.regime_analysis_artifact_path ?? null,
                    regime_analysis_gate: asString(r.regime_analysis_gate_status),
                    trade_markers_path: r.trade_markers_path ?? null,
                  },
                  chart_inspector: {
                    equity_curve_path: r.equity_curve_path ?? null,
                    drawdown_curve_path: r.drawdown_curve_path ?? null,
                    rolling_metrics_path: r.rolling_metrics_path ?? null,
                    fold_performance_path: r.fold_performance_path ?? null,
                    strategy_scorecard_path: r.strategy_scorecard_path ?? null,
                    digests: asRecord(r.charts_compact)?.digests ?? null,
                    analytics_score: r.analytics_score ?? null,
                    analytics_rank: r.analytics_rank ?? null,
                    rank_explanation: r.analytics_rank_explanation ?? null,
                  },
                },
              });
            }}
            empty="No strategies for this filter · run a batch or widen filter"
          />
        </Pane>

        <Pane
          title={selectedRow ? `Analytics · ${asString(selectedRow.strategy_id) ?? ""}` : "Analytics · select a strategy"}
          dense
          onInspect={() =>
            openInspector({
              title: "Strategy Lab · chart metadata",
              rawJson: {
                batch_ranking: batchRanking ?? [],
                selected_strategy_id: selectedRow ? asString(selectedRow.strategy_id) : null,
                chart_artifact_paths: selectedRow
                  ? {
                      equity_curve: selectedRow.equity_curve_path ?? null,
                      drawdown_curve: selectedRow.drawdown_curve_path ?? null,
                      rolling_metrics: selectedRow.rolling_metrics_path ?? null,
                      fold_performance: selectedRow.fold_performance_path ?? null,
                      strategy_scorecard: selectedRow.strategy_scorecard_path ?? null,
                    }
                  : null,
                charts_compact_schema: selectedRow
                  ? asString(asRecord(selectedRow.charts_compact)?.schema_version)
                  : null,
                score_explanation: selectedRow ? (selectedRow.analytics_rank_explanation as string | undefined) : null,
                analytics_score: selectedRow ? selectedRow.analytics_score : null,
                analytics_rank: selectedRow ? selectedRow.analytics_rank : null,
              },
            })
          }
        >
          {!batch ? (
            <p className="muted">No batch loaded — charts appear after a strategy batch run.</p>
          ) : (
            <StrategyLabCharts
              batchRanking={batchRanking ?? []}
              rows={chartRows}
              selected={selectedRow ? ({ ...selectedRow } as Record<string, unknown>) : null}
            />
          )}
        </Pane>
      </div>
    </main>
  );
}
