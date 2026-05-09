"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiTribunal } from "@/hooks/useUiTribunal";
import type { UiTribunalEvaluation, UiTribunalGraphEdge, UiTribunalHistoryEntry, UiTribunalWorkflow } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type WorkflowRow = UiTribunalWorkflow & { id: string };
type EvalRow = UiTribunalEvaluation & { id: string; family: string };
type HistoryRow = UiTribunalHistoryEntry & { id: string; family: string };

type StageFilter = "all" | "GENERATOR" | "SKEPTIC" | "JUDGE";

const STAGES: StageFilter[] = ["all", "GENERATOR", "SKEPTIC", "JUDGE"];

function summarizeText(value: string | undefined, max = 96): string {
  if (!value) return "—";
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}

function graphEdgeLabel(edge: UiTribunalGraphEdge): string {
  const source = edge.source ?? "?";
  const relation = edge.relation ?? "relates";
  const target = edge.target ?? "?";
  return `${source} ─${relation}→ ${target}`;
}

function workflowRows(payload: Record<string, unknown> | null, stageFilter: StageFilter): WorkflowRow[] {
  const workflows = asRecord(payload?.agent_workflows);
  if (!workflows) return [];
  return Object.entries(workflows)
    .map(([id, value]) => ({ id, ...(asRecord(value) ?? {}) }) as WorkflowRow)
    .filter((row) => stageFilter === "all" || row.stage === stageFilter);
}

function evaluationRows(payload: Record<string, unknown> | null, stageFilter: StageFilter): EvalRow[] {
  const promptEvaluations = Array.isArray(payload?.prompt_evaluations) ? payload?.prompt_evaluations : [];
  const falsificationChecks = Array.isArray(payload?.falsification_checks) ? payload?.falsification_checks : [];
  const rows = [
    ...promptEvaluations.map((item, i) => ({ id: asString(asRecord(item)?.evaluation_id) ?? `prompt-${i}`, family: "prompt", ...(asRecord(item) ?? {}) }) as EvalRow),
    ...falsificationChecks.map((item, i) => ({ id: asString(asRecord(item)?.check_id) ?? `check-${i}`, family: "falsification", ...(asRecord(item) ?? {}) }) as EvalRow),
  ];
  return rows.filter((row) => stageFilter === "all" || row.stage === stageFilter || !row.stage);
}

function historyRows(payload: Record<string, unknown> | null): HistoryRow[] {
  const sealed = Array.isArray(payload?.sealed_history) ? payload?.sealed_history : [];
  const doctrine = Array.isArray(payload?.doctrine_memory) ? payload?.doctrine_memory : [];
  return [
    ...sealed.map((item, i) => ({ id: asString(asRecord(item)?.event_id) ?? `sealed-${i}`, family: "history", ...(asRecord(item) ?? {}) }) as HistoryRow),
    ...doctrine.map((item, i) => ({ id: asString(asRecord(item)?.doctrine_key) ?? `doctrine-${i}`, family: "doctrine", ...(asRecord(item) ?? {}) }) as HistoryRow),
  ];
}

export default function TribunalPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const tribunal = useUiTribunal();
  const [stageFilter, setStageFilter] = useState<StageFilter>("all");
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null);

  const payload = tribunal.data ? asRecord(tribunal.data) : null;
  const blindness = asRecord(payload?.blindness);
  const summary = asRecord(payload?.summary);
  const guardrails = asRecord(payload?.guardrails);
  const doctrineStats = asRecord(payload?.doctrine_stats);
  const graph = asRecord(payload?.thesis_graph);
  const graphNodes = Array.isArray(graph?.nodes) ? graph.nodes : [];
  const graphEdges = (Array.isArray(graph?.edges) ? graph.edges : [])
    .map((item) => asRecord(item))
    .filter((item): item is UiTribunalGraphEdge => item != null);

  const workflows = useMemo(() => workflowRows(payload, stageFilter), [payload, stageFilter]);
  const evaluations = useMemo(() => evaluationRows(payload, stageFilter), [payload, stageFilter]);
  const history = useMemo(() => historyRows(payload), [payload]);
  const selectedEvaluation = evaluations.find((row) => row.id === selectedEvalId) ?? evaluations[0] ?? null;
  const forbidden = asStringArray(blindness?.forbidden_metric_families);
  const operatorLines = asStringArray(payload?.operator_lines);

  const blindnessOk = asString(blindness?.mode) === "ENFORCED" && asBool(blindness?.quantitative_payloads_present) === false;
  const readOnly = asBool(guardrails?.read_plane_only) ?? asBool(summary?.read_plane_only) ?? false;

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "tribunal-blindness",
        severity: blindnessOk ? "ok" : "warn",
        text: `tribunal blindness=${asString(blindness?.mode) ?? "UNKNOWN"} quantitative_payloads=${String(asBool(blindness?.quantitative_payloads_present) ?? "?")}`,
      },
      {
        id: "tribunal-guardrail",
        severity: readOnly ? "info" : "warn",
        text: "qualitative-only read-plane · validator metrics and mutation authority remain excluded",
      },
    ],
    [blindness, blindnessOk, readOnly],
  );
  const ticker = useMemo(
    () => [
      { severity: blindnessOk ? ("ok" as const) : ("warn" as const), text: `TRIB ${asString(blindness?.mode) ?? "?"}` },
      { severity: "neutral" as const, text: `WF ${asNumber(summary?.workflow_count) ?? workflows.length}` },
      { severity: "neutral" as const, text: `DOC ${asNumber(summary?.active_doctrine_count) ?? asNumber(doctrineStats?.active_doctrine_count) ?? 0}` },
    ],
    [blindness, blindnessOk, doctrineStats, summary, workflows.length],
  );
  useTerminalPageBind(tape, ticker);

  const workflowCols: DenseColumn<WorkflowRow>[] = useMemo(
    () => [
      { key: "stage", header: "stage", width: "14%", cell: (row) => <code>{row.stage ?? row.id}</code> },
      { key: "status", header: "status", width: "12%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "summary", header: "summary", cell: (row) => summarizeText(row.summary_line) },
      { key: "law", header: "prompt law", cell: (row) => summarizeText(row.prompt_law, 120) },
    ],
    [],
  );
  const evalCols: DenseColumn<EvalRow>[] = useMemo(
    () => [
      { key: "family", header: "family", width: "13%", cell: (row) => <code>{row.family}</code> },
      { key: "stage", header: "stage", width: "13%", cell: (row) => <code>{row.stage ?? "ALL"}</code> },
      { key: "status", header: "status", width: "12%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "constraint", header: "constraint", width: "24%", cell: (row) => <code>{row.constraint ?? row.check_id ?? "—"}</code> },
      { key: "summary", header: "summary", cell: (row) => summarizeText(row.summary_line) },
    ],
    [],
  );
  const historyCols: DenseColumn<HistoryRow>[] = useMemo(
    () => [
      { key: "family", header: "family", width: "12%", cell: (row) => <code>{row.family}</code> },
      { key: "id", header: "id", width: "24%", cell: (row) => <code>{row.event_id ?? row.doctrine_key ?? row.id}</code> },
      { key: "status", header: "status", width: "16%", cell: (row) => <StatusBadge raw={row.forensic_status ?? row.adaptation_status} /> },
      { key: "summary", header: "summary", cell: (row) => summarizeText(row.summary_line) },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">TRIBUNAL</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">TRIBUNAL · QUALITATIVE WORKSPACE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/tribunal · blindness-safe qualitative review plane · no validator metrics, mutations, promotion, or execution authority
      </p>

      {tribunal.isLoading && <p className="muted">Loading…</p>}
      {tribunal.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {tribunal.error instanceof Error ? tribunal.error.message : String(tribunal.error)}
        </p>
      )}

      {payload && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Blindness boundary" onInspect={() => openInspector({ title: "Tribunal blindness", rawJson: blindness ?? {} })}>
              <TermKV
                rows={[
                  { k: "mode", v: <StatusBadge raw={asString(blindness?.mode) ?? "UNKNOWN"} /> },
                  { k: "quant_payloads", v: String(asBool(blindness?.quantitative_payloads_present) ?? "—") },
                  { k: "forbidden_metric_families", v: String(forbidden.length) },
                  { k: "message", v: summarizeText(asString(blindness?.operator_message), 84) },
                ]}
              />
            </Pane>
            <Pane title="Authority guardrails" onInspect={() => openInspector({ title: "Tribunal guardrails", rawJson: guardrails ?? {} })}>
              <TermKV
                rows={[
                  { k: "read_plane", v: String(readOnly) },
                  { k: "mutation", v: asString(guardrails?.mutation_authority) ?? "NONE" },
                  { k: "promotion", v: asString(guardrails?.promotion_authority) ?? "NONE" },
                  { k: "execution", v: asString(guardrails?.execution_authority) ?? "NONE" },
                  { k: "blindness_enforced", v: String(asBool(guardrails?.blindness_enforced) ?? blindnessOk) },
                ]}
              />
            </Pane>
            <Pane title="Qualitative counts" onInspect={() => openInspector({ title: "Tribunal summary", rawJson: summary ?? doctrineStats ?? {} })}>
              <TermKV
                rows={[
                  { k: "workflows", v: String(asNumber(summary?.workflow_count) ?? workflows.length) },
                  { k: "prompt_evals", v: String(asNumber(summary?.prompt_evaluation_count) ?? 0) },
                  { k: "falsification", v: String(asNumber(summary?.falsification_check_count) ?? 0) },
                  { k: "history", v: String(asNumber(summary?.sealed_history_count) ?? asNumber(doctrineStats?.sealed_history_count) ?? 0) },
                  { k: "doctrine", v: String(asNumber(summary?.active_doctrine_count) ?? asNumber(doctrineStats?.active_doctrine_count) ?? 0) },
                  { k: "graph", v: `${graphNodes.length} nodes / ${graphEdges.length} edges` },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Stage filter">
            <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
              {STAGES.map((stage) => (
                <button
                  key={stage}
                  type="button"
                  className={`term-btn term-btn--sm${stageFilter === stage ? " is-active" : ""}`}
                  onClick={() => setStageFilter(stage)}
                >
                  {stage}
                </button>
              ))}
            </div>
          </Pane>

          <Pane title="Agent workflow stack" onInspect={() => openInspector({ title: "Tribunal workflows", rawJson: payload.agent_workflows ?? {} })}>
            <DenseTable columns={workflowCols} rows={workflows} rowKey={(row) => row.id} empty="No workflow stages in tribunal payload." />
          </Pane>

          <PaneGrid>
            <Pane title="Prompt + falsification gates" onInspect={() => openInspector({ title: "Tribunal evaluations", rawJson: evaluations })}>
              <DenseTable
                columns={evalCols}
                rows={evaluations}
                rowKey={(row) => row.id}
                selectedKey={selectedEvalId}
                onRowClick={(row) => {
                  setSelectedEvalId(row.id);
                  openInspector({ title: `Tribunal ${row.family} · ${row.id}`, rawJson: row });
                }}
                empty="No prompt/falsification checks."
              />
            </Pane>
            <Pane title="Selected check">
              <TermKV
                rows={[
                  { k: "id", v: selectedEvaluation?.id ?? "—" },
                  { k: "family", v: selectedEvaluation?.family ?? "—" },
                  { k: "stage", v: selectedEvaluation?.stage ?? "ALL" },
                  { k: "status", v: selectedEvaluation?.status ?? "—" },
                  { k: "constraint", v: selectedEvaluation?.constraint ?? selectedEvaluation?.check_id ?? "—" },
                  { k: "summary", v: summarizeText(selectedEvaluation?.summary_line, 160) },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Sealed history + doctrine memory" onInspect={() => openInspector({ title: "Tribunal history + doctrine", rawJson: history })}>
            <DenseTable columns={historyCols} rows={history} rowKey={(row) => row.id} empty="No sealed history or doctrine memory." />
          </Pane>

          <PaneGrid>
            <Pane title="Thesis graph">
              <TermKV
                rows={[
                  { k: "nodes", v: String(graphNodes.length) },
                  { k: "edges", v: String(graphEdges.length) },
                  { k: "density", v: asString(doctrineStats?.graph_density_label) ?? "—" },
                ]}
              />
              <ul className="term-list">
                {graphEdges.slice(0, 8).map((edge, i) => (
                  <li key={`${edge.source ?? "?"}-${edge.target ?? "?"}-${i}`}>
                    <code>{graphEdgeLabel(edge)}</code>
                  </li>
                ))}
              </ul>
            </Pane>
            <Pane title="Operator laws">
              <ul className="term-list">
                {operatorLines.map((line, i) => (
                  <li key={`${line}-${i}`}>{line}</li>
                ))}
                {operatorLines.length === 0 && <li className="muted">No operator lines emitted.</li>}
              </ul>
            </Pane>
          </PaneGrid>

          {forbidden.length > 0 && (
            <Pane title="Redacted quantitative families">
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {forbidden.map((family) => (
                  <span key={family} className="term-chip">
                    {family}
                  </span>
                ))}
              </div>
            </Pane>
          )}
        </>
      )}

      {tribunal.data && <JsonDetails summary="Drilldown: full /ui/tribunal JSON" data={tribunal.data} />}
    </div>
  );
}
