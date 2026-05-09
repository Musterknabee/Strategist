"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiResearchCompute, type UiResearchComputeQuery } from "@/hooks/useUiResearchCompute";
import type { UiResearchComputeResultEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type BackendMode = "all" | "cpu" | "cuda";
type FallbackMode = "all" | "NONE" | "TORCH_NOT_INSTALLED" | "CUDA_UNAVAILABLE" | "CUDA_BACKEND_ERROR" | "REQUESTED_CPU" | "GPU_UNAVAILABLE_CPU_FALLBACK";
type ResultRow = UiResearchComputeResultEntry & { __id: string };
const BACKENDS: BackendMode[] = ["all", "cpu", "cuda"];
const FALLBACKS: FallbackMode[] = ["all", "NONE", "TORCH_NOT_INSTALLED", "CUDA_UNAVAILABLE", "CUDA_BACKEND_ERROR", "REQUESTED_CPU", "GPU_UNAVAILABLE_CPU_FALLBACK"];
function text(v: unknown, f = "—") { if (v === null || v === undefined || v === "") return f; return String(v); }
function fixed(v: unknown) { return typeof v === "number" && !Number.isNaN(v) ? v.toFixed(4) : "—"; }
function shortDigest(v: string | null | undefined) { return v ? (v.length > 18 ? `${v.slice(0, 10)}…${v.slice(-6)}` : v) : "—"; }
function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] { return Object.entries(counts ?? {}).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).map(([k,v])=>({k,v:String(v)})); }

export default function ResearchComputePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [backendMode, setBackendMode] = useState<BackendMode>("all");
  const [fallbackMode, setFallbackMode] = useState<FallbackMode>("all");
  const [strategyNeedle, setStrategyNeedle] = useState("");
  const [taskNeedle, setTaskNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const query: UiResearchComputeQuery = useMemo(() => ({ backendUsed: backendMode === "all" ? null : backendMode, fallbackReason: fallbackMode === "all" ? null : fallbackMode, strategyIdContains: strategyNeedle.trim() || null, taskContains: taskNeedle.trim() || null, warningContains: issueNeedle.trim() || null, blockerContains: issueNeedle.trim() || null, limit: 300 }), [backendMode, fallbackMode, issueNeedle, strategyNeedle, taskNeedle]);
  const compute = useUiResearchCompute(query);
  const rows = useMemo<ResultRow[]>(() => (compute.data?.results ?? []).map((r, i) => ({ ...r, __id: `${r.run_id}:${r.backend_used}:${i}` })), [compute.data?.results]);
  const selectedRow = useMemo(() => rows.find((r) => r.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const summary = compute.data?.summary;
  const probe = compute.data?.gpu_probe;
  const benchmark = compute.data?.last_benchmark;
  const guardrails = asStringArray(compute.data?.guardrails);
  const invalid = Array.isArray(compute.data?.invalid_artifacts) ? compute.data.invalid_artifacts : [];
  const tape: TapeLine[] = useMemo(() => [{ id: "research-compute-readiness", severity: compute.data?.research_compute_readiness === "RESEARCH_COMPUTE_ARTIFACTS_DEGRADED" ? "warn" : compute.data?.gpu_available ? "ok" : "info", text: `research_compute ${compute.data?.research_compute_readiness ?? "UNKNOWN"} results=${summary?.result_count_returned ?? 0}/${summary?.result_count_total ?? 0} invalid=${summary?.invalid_artifact_count ?? 0}` }, { id: "research-compute-guardrail", severity: "info", text: "read-plane only · optional CPU/CUDA acceleration evidence · no compute execution from UI" }], [compute.data, summary]);
  const ticker = useMemo(() => [{ severity: compute.data?.gpu_available ? ("ok" as const) : ("neutral" as const), text: `GPU ${String(compute.data?.gpu_available ?? false)}` }, { severity: (summary?.invalid_artifact_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `RC ${summary?.result_count_returned ?? 0}` }], [compute.data?.gpu_available, summary]);
  useTerminalPageBind(tape, ticker);
  const columns: DenseColumn<ResultRow>[] = useMemo(() => [
    { key: "run", header: "run", width: "16%", cell: (r) => <code>{r.run_id}</code> },
    { key: "strategy", header: "strategy", width: "12%", cell: (r) => <code>{r.strategy_id ?? "—"}</code> },
    { key: "backend", header: "backend", width: "9%", cell: (r) => <StatusBadge raw={r.backend_used} /> },
    { key: "fallback", header: "fallback", width: "16%", cell: (r) => <code>{r.fallback_reason}</code> },
    { key: "duration", header: "ms", width: "7%", cell: (r) => text(r.duration_ms) },
    { key: "risk", header: "mean / cvar / dd", width: "18%", cell: (r) => `${fixed(r.mean_return)}/${fixed(r.cvar_95)}/${fixed(r.max_drawdown_like)}` },
    { key: "issues", header: "warn/block", width: "9%", cell: (r) => `${r.warning_count}/${r.blocker_count}` },
    { key: "digest", header: "digest", cell: (r) => <code>{shortDigest(r.result_digest ?? r.artifact_sha256)}</code> },
  ], []);
  if (!config.ok) return <div className="term-page"><h1 className="term-page__title">RESEARCH · COMPUTE</h1><p className="muted">{config.error.message}</p></div>;
  return <div className="term-page"><h1 className="term-page__title">RESEARCH · COMPUTE</h1><p className="muted" style={{ fontSize: "10px" }}>GET /ui/research-compute · optional CPU/CUDA acceleration evidence, benchmark posture, and result artifact inventory</p>{compute.isLoading && <p className="muted">Loading…</p>}{compute.isError && <p className="term-page__banner" style={{ color: "#f85149" }}>{compute.error instanceof Error ? compute.error.message : String(compute.error)}</p>}{compute.data && summary && <><PaneGrid cols={3}><Pane title="Compute readiness" badge={<StatusBadge raw={compute.data.research_compute_readiness} />} onInspect={() => openInspector({ title: "/ui/research-compute", rawJson: compute.data })}><TermKV rows={[{ k: "schema", v: compute.data.schema_version }, { k: "gpu_available", v: String(compute.data.gpu_available) }, { k: "cpu_fallback", v: compute.data.cpu_fallback_status }, { k: "fallback", v: text(compute.data.fallback_reason) }, { k: "artifact_root", v: summary.artifact_root }]} /></Pane><Pane title="Probe / benchmark" onInspect={() => openInspector({ title: "Research compute probe", rawJson: { probe, benchmark } })}><TermKV rows={[{ k: "probe_backend", v: text(probe?.backend) }, { k: "torch", v: String(probe?.torch_available ?? "UNKNOWN") }, { k: "cuda", v: String(probe?.cuda_available ?? "UNKNOWN") }, { k: "device_count", v: text(probe?.device_count) }, { k: "benchmark_cpu_ms", v: text(benchmark?.cpu_duration_ms) }, { k: "benchmark_pool_ms", v: text(benchmark?.process_pool_duration_ms) }]} /></Pane><Pane title="Result inventory"><TermKV rows={[{ k: "total", v: String(summary.result_count_total) }, { k: "filtered", v: String(summary.result_count_filtered) }, { k: "returned", v: String(summary.result_count_returned) }, { k: "invalid", v: String(summary.invalid_artifact_count) }, { k: "warnings", v: String(summary.warning_count) }, { k: "blockers", v: String(summary.blocker_count) }, { k: "latest", v: text(summary.latest_completed_at_utc) }]} /></Pane></PaneGrid><PaneGrid cols={3}><Pane title="Backend counts"><TermKV rows={countRows(summary.backend_used_counts)} /></Pane><Pane title="Fallback counts"><TermKV rows={countRows(summary.fallback_reason_counts)} /></Pane><Pane title="Selected result" onInspect={selectedRow ? () => openInspector({ title: "Research compute result", rawJson: selectedRow }) : undefined}><TermKV rows={[{ k: "run", v: selectedRow?.run_id ?? "—" }, { k: "task", v: selectedRow?.research_task_id ?? "—" }, { k: "pit", v: selectedRow?.pit_as_of_utc ?? "—" }, { k: "seed", v: text(selectedRow?.deterministic_seed) }, { k: "artifact", v: selectedRow?.artifact_path ?? "—" }, { k: "sha256", v: shortDigest(selectedRow?.artifact_sha256) }]} />{selectedRow?.result_digest && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.result_digest ?? null)}>Copy digest target</button>}</Pane></PaneGrid><Pane title="Filters"><div className="term-toolbar">{BACKENDS.map((m)=><button key={m} type="button" className={backendMode === m ? "term-chip active" : "term-chip"} onClick={() => setBackendMode(m)}>{m}</button>)}<select className="term-input" value={fallbackMode} onChange={(e)=>setFallbackMode(e.target.value as FallbackMode)} aria-label="fallback filter" style={{ width: "230px" }}>{FALLBACKS.map((m)=><option key={m} value={m}>{m}</option>)}</select><label className="term-field"><span>strategy</span><input className="term-input" value={strategyNeedle} onChange={(e)=>setStrategyNeedle(e.target.value)} placeholder="contains" style={{ width: "160px" }} /></label><label className="term-field"><span>task</span><input className="term-input" value={taskNeedle} onChange={(e)=>setTaskNeedle(e.target.value)} placeholder="task/run" style={{ width: "160px" }} /></label><label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e)=>setIssueNeedle(e.target.value)} placeholder="warning/blocker" style={{ width: "190px" }} /></label></div></Pane><Pane title="Compute result artifacts"><DenseTable<ResultRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No research compute result artifacts matched the current filters." /></Pane>{invalid.length > 0 && <Pane title="Invalid artifacts" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Invalid research compute artifacts", rawJson: invalid })}><ul className="term-list">{invalid.slice(0, 8).map((item, i) => <li key={`${item.path ?? i}:${item.reason ?? "invalid"}`}><code>{text(item.reason)}</code> · {text(item.path)}</li>)}</ul></Pane>}<Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane><JsonDetails summary="Drilldown: /ui/research-compute JSON" data={compute.data} /></>}</div>;
}
