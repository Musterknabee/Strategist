"use client";

import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
} from "recharts";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { MetricProvenanceCard } from "@/features/shared/components/metric-provenance-card";
import { MetricEvidenceHint } from "@/features/shared/components/metric-evidence-hint";
import type { UiBurnInDashboard } from "@/lib/contracts/ui";

function MetricCard({ title, value, description }: { title: string; value: string; description: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-zinc-300">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold text-zinc-50">{value}</div>
        <CardDescription className="mt-1">{description}</CardDescription>
      </CardContent>
    </Card>
  );
}

function SectionHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
      <div>
        <div className="text-base font-semibold text-zinc-100">{title}</div>
        <div className="mt-1 text-sm text-zinc-400">{description}</div>
      </div>
      {action}
    </div>
  );
}

export function BurnInMetrics({
  data,
  initialExecutiveMode = true,
}: {
  data: UiBurnInDashboard;
  initialExecutiveMode?: boolean;
}) {
  const [mode, setMode] = useState<"executive" | "forensic">(
    initialExecutiveMode ? "executive" : "forensic"
  );

  const realismRadar = useMemo(
    () => [
      { metric: "Market Hours", value: data.metrics.realism.marketHoursCompliance },
      { metric: "Capacity", value: data.metrics.realism.capacityStress },
      { metric: "Liquidity", value: data.metrics.realism.liquidityIntegrity },
      { metric: "Borrow", value: Math.max(0, 100 - data.metrics.realism.borrowCostBps / 10) },
      { metric: "Slippage", value: Math.max(0, 100 - data.metrics.realism.slippageBps * 2) },
    ],
    [data.metrics.realism]
  );

  const executiveMode = mode === "executive";

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Validator Burn-in Diagnostics</CardTitle>
            <CardDescription>
              Promotion posture, robustness, and realism diagnostics rendered from the projection-backed validator surface.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button variant={executiveMode ? "default" : "outline"} onClick={() => setMode("executive")}>Executive</Button>
            <Button variant={!executiveMode ? "default" : "outline"} onClick={() => setMode("forensic")}>Forensic</Button>
            <ExportSnapshotActions payload={data} fileStem={`validator-burnin-${mode}`} />
          </div>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-2 pt-0">
          <Badge>{data.metrics.dsrPbo.promotionPosture}</Badge>
          <Badge>{data.metrics.dsrPbo.overfitRisk}</Badge>
          <Badge>{data.artifact_summary.artifact_count} artifacts</Badge>
          <Badge>{data.artifact_summary.total_round_count} rounds</Badge>
          {data.artifact_summary.total_fallback_count > 0 ? <Badge>{data.artifact_summary.total_fallback_count} fallbacks</Badge> : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-4">
        <MetricCard title="Incrementality p-value" value={data.metrics.incrementality.pValue.toFixed(4)} description="Orthogonal incrementality significance" />
        <MetricCard title="Coefficient" value={data.metrics.incrementality.coefficient.toFixed(4)} description="Post-cost benchmark delta proxy" />
        <MetricCard title="Deflated Sharpe" value={data.metrics.dsrPbo.deflatedSharpeRatio.toFixed(2)} description="Deflated Sharpe ratio diagnostic" />
        <MetricCard title="PBO" value={`${(data.metrics.dsrPbo.probabilityOfBacktestOverfitting * 100).toFixed(1)}%`} description="Probability of backtest overfitting" />
      </div>

      <MetricProvenanceCard title="Promotion diagnostics" provenance={data.metrics.metricProvenance.dsrPbo} />

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1.3fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3"><CardTitle>Promotion Posture</CardTitle><MetricEvidenceHint label="Evidence" provenance={data.metrics.metricProvenance.dsrPbo} /></div>
            <CardDescription>{data.metrics.forensicSummary.primary_warning}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Posture</div>
                <div className="mt-2 text-xl font-semibold text-zinc-100">{data.metrics.forensicSummary.promotion_posture}</div>
                <div className="mt-2 text-sm text-zinc-400">Current release orientation based on incrementality, CPCV, and realism surfaces.</div>
              </div>
              <div className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Overfit risk</div>
                <div className="mt-2 text-xl font-semibold text-zinc-100">{data.metrics.forensicSummary.overfit_risk}</div>
                <div className="mt-2 text-sm text-zinc-400">Treat elevated PBO as a governance brake even when other indicators remain strong.</div>
              </div>
            </div>
            <div className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/60 p-4">
              <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Forensic notes</div>
              <ul className="mt-3 space-y-2 text-sm text-zinc-300">
                {data.metrics.forensicSummary.forensic_notes.map((note) => (
                  <li key={note}>• {note}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3"><CardTitle>{executiveMode ? "CPCV Coverage" : "Path Stability vs Dispersion"}</CardTitle><MetricEvidenceHint label="Evidence" provenance={executiveMode ? data.metrics.metricProvenance.cpcvCoverage : data.metrics.metricProvenance.pathStability} /></div>
            <CardDescription>
              {executiveMode
                ? "Path coverage across replay folds and burn-in windows."
                : "Forensic view surfaces both stability and dispersion across the same replay windows."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <MetricProvenanceCard
              title={executiveMode ? "CPCV coverage" : "Path stability"}
              provenance={
                executiveMode
                  ? data.metrics.metricProvenance.cpcvCoverage
                  : data.metrics.metricProvenance.pathStability
              }
            />
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                {executiveMode ? (
                  <BarChart data={data.metrics.cpcvCoverage}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="fold" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" domain={[0, 1]} />
                    <Tooltip />
                    <Bar dataKey="coverage" radius={[8, 8, 0, 0]} fill="#22c55e" />
                  </BarChart>
                ) : (
                  <LineChart data={data.metrics.pathStability}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="window" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" domain={[0, 1]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="stability" stroke="#34d399" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="dispersion" stroke="#f59e0b" strokeWidth={2} dot={false} />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3"><CardTitle>Calibration Curve</CardTitle><MetricEvidenceHint label="Evidence" provenance={data.metrics.metricProvenance.calibrationCurve} /></div>
            <CardDescription>Predicted vs realized outcome buckets.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <MetricProvenanceCard title="Calibration curve" provenance={data.metrics.metricProvenance.calibrationCurve} />
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.metrics.calibrationCurve}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                  <XAxis dataKey="bucket" stroke="#a1a1aa" />
                  <YAxis stroke="#a1a1aa" domain={[0, 1]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="predicted" stroke="#34d399" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="realized" stroke="#60a5fa" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3"><CardTitle>Cost & Realism Surface</CardTitle><MetricEvidenceHint label="Evidence" provenance={data.metrics.metricProvenance.realismConstraints} /></div>
            <CardDescription>Slippage, borrow, liquidity, and session realism.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <MetricProvenanceCard title="Realism constraints" provenance={data.metrics.metricProvenance.realismConstraints} />
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={realismRadar}>
                  <PolarGrid stroke="#3f3f46" />
                  <PolarAngleAxis dataKey="metric" stroke="#a1a1aa" />
                  <PolarRadiusAxis stroke="#71717a" />
                  <Radar dataKey="value" stroke="#34d399" fill="#34d399" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <SectionHeader
                title="Realism constraints"
                description="Promotion-facing realism checks rendered as governance constraints rather than raw market microstructure numbers."
              />
              <MetricEvidenceHint label="Evidence" provenance={data.metrics.metricProvenance.realismConstraints} />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.metrics.realismConstraints.map((constraint) => (
              <div key={constraint.name} className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-zinc-100">{constraint.name}</div>
                    <div className="mt-1 text-sm text-zinc-400">{constraint.summary_line}</div>
                  </div>
                  <Badge>{constraint.status}</Badge>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  <div className="rounded-xl border border-zinc-800 p-3">
                    <div className="text-xs uppercase tracking-wide text-zinc-500">Observed</div>
                    <div className="mt-1 text-sm text-zinc-100">{constraint.value.toFixed(1)} {constraint.unit}</div>
                  </div>
                  <div className="rounded-xl border border-zinc-800 p-3">
                    <div className="text-xs uppercase tracking-wide text-zinc-500">Target</div>
                    <div className="mt-1 text-sm text-zinc-100">{constraint.target.toFixed(1)} {constraint.unit}</div>
                  </div>
                  <div className="rounded-xl border border-zinc-800 p-3">
                    <div className="text-xs uppercase tracking-wide text-zinc-500">Mode</div>
                    <div className="mt-1 text-sm text-zinc-100">{executiveMode ? "Executive" : "Forensic"}</div>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <SectionHeader
                title="Provider paths"
                description="Connector posture across Alpaca, OpenBB, HTTP JSON, and NIM. Treat as provenance and liveness, not execution authority."
              />
              <MetricEvidenceHint label="Evidence" provenance={data.metrics.metricProvenance.providerPaths} />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <MetricProvenanceCard title="Provider paths" provenance={data.metrics.metricProvenance.providerPaths} />
            <div className="space-y-3">
              {data.metrics.providerPaths.map((provider) => (
                <div key={`${provider.provider}-${provider.path}`} className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/70 p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-zinc-100">{provider.provider}</div>
                    <Badge>{provider.status}</Badge>
                  </div>
                  <div className="mt-2 text-xs text-zinc-500">{provider.path}</div>
                  <div className="mt-3 text-xs text-zinc-400">
                    {provider.status === "ENABLED"
                      ? "Provider is configured for validator ingress and can be cross-checked in forensic review."
                      : "Provider is not active in this environment and should not be assumed in promotion decisions."}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
