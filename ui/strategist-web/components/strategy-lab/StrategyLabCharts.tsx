"use client";

import { asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import type { ReactNode } from "react";

function normalizeSeries(values: number[]): { min: number; max: number; norm: number[] } {
  if (!values.length) return { min: 0, max: 1, norm: [] };
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return { min, max, norm: values.map((x) => (x - min) / span) };
}

function SvgSparkline({ points, stroke, height = 56 }: { points: number[]; stroke: string; height?: number }) {
  const w = 280;
  const h = height;
  const pad = 4;
  if (!points.length) {
    return (
      <svg width={w} height={h} className="lab-chart-svg" aria-label="empty chart">
        <text x={pad} y={h / 2} fontSize="10" fill="var(--muted-fg, #888)">
          No series
        </text>
      </svg>
    );
  }
  const { norm } = normalizeSeries(points);
  const innerW = w - pad * 2;
  const innerH = h - pad * 2;
  const step = innerW / Math.max(1, norm.length - 1);
  const pts = norm
    .map((y, i) => `${pad + i * step},${pad + innerH - y * innerH}`)
    .join(" ");
  return (
    <svg width={w} height={h} className="lab-chart-svg" aria-hidden>
      <polyline fill="none" stroke={stroke} strokeWidth="1.25" points={pts} />
    </svg>
  );
}

function parseCompactSeries(o: unknown): { t: string; v: number }[] {
  const r = asRecord(o);
  if (!r) return [];
  const ts = asStringArray(r.t);
  const vs = r.v;
  if (!Array.isArray(vs)) return [];
  const out: { t: string; v: number }[] = [];
  for (let i = 0; i < Math.min(ts.length, vs.length); i++) {
    const n = asNumber(vs[i]);
    if (n !== undefined) out.push({ t: ts[i] ?? "", v: n });
  }
  return out;
}

function FoldBars({ folds }: { folds: unknown }) {
  if (!Array.isArray(folds) || !folds.length) {
    return <p className="muted" style={{ fontSize: "11px" }}>No fold performance (robustness not run or insufficient sample).</p>;
  }
  const w = 280;
  const h = 72;
  const pad = 8;
  const vals = folds.map((f) => {
    const r = asRecord(f);
    return asNumber(r?.test_return) ?? 0;
  });
  const { min, max, norm } = normalizeSeries(vals);
  const barW = (w - pad * 2) / Math.max(1, vals.length) - 2;
  return (
    <svg width={w} height={h} aria-label="fold test returns">
      {vals.map((v, i) => {
        const nh = norm[i] ?? 0;
        const bh = Math.max(2, nh * (h - pad * 2));
        const x = pad + i * (barW + 2);
        const y = pad + (h - pad * 2) - bh;
        const neg = v < 0;
        return <rect key={i} x={x} y={y} width={barW} height={bh} fill={neg ? "#b44" : "#4a8"} rx={1} />;
      })}
      <text x={pad} y={h - 1} fontSize="9" fill="var(--muted-fg, #888)">
        folds min {min.toFixed(3)} max {max.toFixed(3)}
      </text>
    </svg>
  );
}

function ScatterRvDd({ rows }: { rows: Array<Record<string, unknown>> }) {
  const pts: { id: string; r: number; d: number }[] = [];
  for (const row of rows) {
    const id = asString(row.strategy_id) ?? "?";
    const cc = asRecord(row.charts_compact);
    const sc = cc ? asRecord(cc.scatter) : null;
    let r = asNumber(sc?.total_return);
    let d = asNumber(sc?.max_drawdown);
    if (r === undefined) r = asNumber(asRecord(row.metrics)?.total_return) ?? 0;
    if (d === undefined) d = asNumber(asRecord(row.metrics)?.max_drawdown) ?? 0;
    pts.push({ id, r, d });
  }
  const w = 280;
  const h = 120;
  const pad = 24;
  if (!pts.length) return null;
  const rs = pts.map((p) => p.r);
  const ds = pts.map((p) => p.d);
  const rMin = Math.min(...rs);
  const rMax = Math.max(...rs);
  const dMin = Math.min(...ds);
  const dMax = Math.max(...ds);
  const rSpan = rMax - rMin || 1e-9;
  const dSpan = dMax - dMin || 1e-9;
  return (
    <svg width={w} height={h} aria-label="return vs drawdown">
      <text x={pad} y={h - 4} fontSize="9" fill="var(--muted-fg, #888)">
        x drawdown · y return
      </text>
      {pts.map((p, i) => {
        const x = pad + ((p.d - dMin) / dSpan) * (w - pad * 2);
        const y = pad + (1 - (p.r - rMin) / rSpan) * (h - pad * 2);
        return <circle key={i} cx={x} cy={y} r={4} fill="#6ae" opacity={0.85} />;
      })}
    </svg>
  );
}

function GateCell({ label }: { label: string }) {
  const u = label.toUpperCase();
  let bg = "rgba(120,120,120,0.25)";
  if (
    u === "PROVEN" ||
    u === "PIT_VERIFIED" ||
    u === "PASS" ||
    u === "LOCAL_HISTORICAL_BARS" ||
    u === "STABLE" ||
    u === "DIVERSIFYING"
  )
    bg = "rgba(40,140,80,0.35)";
  else if (u.includes("BLOCK") || u === "FAILED" || u === "FRAGILE" || u === "DUPLICATIVE") bg = "rgba(180,50,50,0.35)";
  else if (u.includes("WARN") || u === "NOT_APPLICABLE" || u === "SYNTHETIC") bg = "rgba(180,140,40,0.35)";
  return (
    <td style={{ background: bg, fontSize: "10px", padding: "4px", textAlign: "center" }} title={label}>
      {label.length > 14 ? `${label.slice(0, 12)}…` : label}
    </td>
  );
}

export type StrategyLabChartsProps = {
  batchRanking: unknown;
  rows: Array<Record<string, unknown>>;
  selected: Record<string, unknown> | null;
};

export function StrategyLabCharts({ batchRanking, rows, selected }: StrategyLabChartsProps): ReactNode {
  const cc = selected ? asRecord(selected.charts_compact) : null;
  const equityPts = cc ? parseCompactSeries(cc.equity) : [];
  const ddPts = cc ? parseCompactSeries(cc.drawdown) : [];
  const folds = cc?.folds;

  const ranking = Array.isArray(batchRanking) ? batchRanking : [];

  return (
    <div className="lab-charts" data-testid="strategy-lab-charts" style={{ display: "grid", gap: "1rem" }}>
      <p className="muted" style={{ fontSize: "11px", margin: 0 }}>
        Charts are derived from batch evidence (equity_curve.json, etc.). Research only — no profitability guarantee.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
        <div>
          <div className="muted" style={{ fontSize: "11px", marginBottom: "0.25rem" }}>
            Equity (toy evaluator)
          </div>
          <SvgSparkline points={equityPts.map((p) => p.v)} stroke="#7cc" />
        </div>
        <div>
          <div className="muted" style={{ fontSize: "11px", marginBottom: "0.25rem" }}>
            Drawdown
          </div>
          <SvgSparkline points={ddPts.map((p) => p.v)} stroke="#c77" />
        </div>
        <div>
          <div className="muted" style={{ fontSize: "11px", marginBottom: "0.25rem" }}>
            Fold test returns
          </div>
          <FoldBars folds={folds} />
        </div>
        <div>
          <div className="muted" style={{ fontSize: "11px", marginBottom: "0.25rem" }}>
            Return vs drawdown
          </div>
          <ScatterRvDd rows={rows} />
        </div>
      </div>
      <div>
        <div className="muted" style={{ fontSize: "11px", marginBottom: "0.35rem" }}>
          Batch ranking (heuristic score; BLOCKED never listed first)
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="dense-table" style={{ width: "100%", fontSize: "11px", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "4px" }}>Rank</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Strategy</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Score</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Tot ret</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Max DD</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Sharpe~</th>
                <th style={{ textAlign: "left", padding: "4px" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {ranking.length === 0 ? (
                <tr>
                  <td colSpan={7} className="muted">
                    No ranking data
                  </td>
                </tr>
              ) : (
                ranking.map((raw, i) => {
                  const r = asRecord(raw);
                  if (!r) return null;
                  const sid = asString(r.strategy_id);
                  const rowMatch = rows.find((x) => asString(x.strategy_id) === sid);
                  const m = rowMatch ? asRecord(rowMatch.metrics) : null;
                  const tr = asNumber(m?.total_return);
                  const dd = asNumber(m?.max_drawdown);
                  const sh = asNumber(m?.sharpe_like);
                  return (
                    <tr key={sid ?? `rk-${i}`}>
                      <td style={{ padding: "4px" }}>{String(r.rank ?? "")}</td>
                      <td style={{ padding: "4px" }}>
                        <code>{sid}</code>
                      </td>
                      <td style={{ padding: "4px" }}>{r.score != null ? Number(r.score).toFixed(3) : "—"}</td>
                      <td style={{ padding: "4px" }}>{tr !== undefined ? tr.toFixed(3) : "—"}</td>
                      <td style={{ padding: "4px" }}>{dd !== undefined ? dd.toFixed(3) : "—"}</td>
                      <td style={{ padding: "4px" }}>{sh !== undefined ? sh.toFixed(2) : "—"}</td>
                      <td style={{ padding: "4px" }}>{asString(r.status) ?? "—"}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
      <div>
        <div className="muted" style={{ fontSize: "11px", marginBottom: "0.35rem" }}>
          Gate matrix
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ fontSize: "10px", borderCollapse: "collapse", width: "100%" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "4px" }}>Strategy</th>
                <th style={{ padding: "4px" }}>DQ</th>
                <th style={{ padding: "4px" }}>PIT</th>
                <th style={{ padding: "4px" }}>Cov</th>
                <th style={{ padding: "4px" }}>Exec</th>
                <th style={{ padding: "4px" }}>Rob</th>
                <th style={{ padding: "4px" }}>Param</th>
                <th style={{ padding: "4px" }}>Reg</th>
                <th style={{ padding: "4px" }}>Promo</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const gs = asRecord(row.gate_summary);
                const pid = asString(row.strategy_id) ?? `g-${i}`;
                const promo =
                  gs && typeof gs.promotion_eligible === "boolean"
                    ? (gs.promotion_eligible ? "ELIGIBLE" : "BLOCKED")
                    : "—";
                return (
                  <tr key={pid}>
                    <td style={{ padding: "4px" }}>
                      <code>{pid}</code>
                    </td>
                    <GateCell label={asString(gs?.data_quality_gate) ?? asString(row.data_quality_gate_status) ?? "—"} />
                    <GateCell label={asString(gs?.pit_gate) ?? asString(row.pit_status) ?? "—"} />
                    <GateCell label={asString(gs?.data_coverage_gate) ?? "—"} />
                    <GateCell label={asString(gs?.execution_realism_gate) ?? asString(row.execution_realism_gate) ?? "—"} />
                    <GateCell label={asString(gs?.robustness_gate) ?? asString(row.robustness_gate_status) ?? "—"} />
                    <GateCell
                      label={
                        asString(gs?.parameter_sensitivity_gate) ?? asString(row.parameter_sensitivity_gate_status) ?? "—"
                      }
                    />
                    <GateCell label={asString(gs?.regime_analysis_gate) ?? asString(row.regime_analysis_gate_status) ?? "—"} />
                    <GateCell label={promo} />
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
