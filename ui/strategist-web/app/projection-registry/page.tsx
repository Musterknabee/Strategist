"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiProjectionRegistry, type UiProjectionRegistryQuery } from "@/hooks/useUiProjectionRegistry";
import type { UiProjectionRegistryEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type CheckpointMode = "all" | "checkpoint" | "noncheckpoint";
type RegistryRow = UiProjectionRegistryEntry & { __id: string };

const CHECKPOINT_MODES: CheckpointMode[] = ["all", "checkpoint", "noncheckpoint"];

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  return Object.entries(counts ?? {})
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 10)
    .map(([k, v]) => ({ k, v: String(v) }));
}

function checkpointParam(mode: CheckpointMode): boolean | null {
  if (mode === "checkpoint") return true;
  if (mode === "noncheckpoint") return false;
  return null;
}

export default function ProjectionRegistryPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [checkpointMode, setCheckpointMode] = useState<CheckpointMode>("all");
  const [familyNeedle, setFamilyNeedle] = useState("");
  const [labelNeedle, setLabelNeedle] = useState("");
  const [outputNeedle, setOutputNeedle] = useState("");
  const [handlerNeedle, setHandlerNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiProjectionRegistryQuery = useMemo(
    () => ({
      projectionFamily: familyNeedle.trim() || null,
      projectionLabel: labelNeedle.trim() || null,
      supportsCheckpoints: checkpointParam(checkpointMode),
      outputLabelContains: outputNeedle.trim() || null,
      handlerContains: handlerNeedle.trim() || null,
      limit: 300,
    }),
    [checkpointMode, familyNeedle, handlerNeedle, labelNeedle, outputNeedle],
  );

  const registry = useUiProjectionRegistry(query);
  const summary = registry.data?.summary;
  const rows = useMemo<RegistryRow[]>(
    () => (registry.data?.entries ?? []).map((entry, i) => ({ ...entry, __id: `${entry.projection_family}:${entry.projection_label}:${i}` })),
    [registry.data?.entries],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(registry.data?.degraded);
  const guardrails = asStringArray(registry.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "projection-registry-counts",
        severity: (summary?.invalid_index_artifact_count ?? 0) > 0 || (summary?.orphan_artifact_entry_count ?? 0) > 0 ? "warn" : "ok",
        text: `projection_registry registered=${summary?.registered_projection_count ?? 0} observed=${summary?.observed_artifact_entry_count ?? 0} invalid=${summary?.invalid_index_artifact_count ?? 0} orphan=${summary?.orphan_artifact_entry_count ?? 0}`,
      },
      {
        id: "projection-registry-boundary",
        severity: "info",
        text: "read-plane only · inventories projection contracts/artifacts; no rebuild, checkpoint, or ledger write authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.registered_without_observed_artifacts_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `PRJ ${summary?.returned_projection_count ?? 0}` },
      { severity: (summary?.checkpoint_capable_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `CHK ${summary?.checkpoint_capable_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<RegistryRow>[] = useMemo(
    () => [
      { key: "family", header: "family", width: "22%", cell: (row) => <code>{row.projection_family}</code> },
      { key: "label", header: "label", width: "20%", cell: (row) => <code>{row.projection_label}</code> },
      { key: "checkpoint", header: "checkpoint", width: "10%", cell: (row) => <StatusBadge raw={row.supports_checkpoints ? "YES" : "NO"} /> },
      { key: "observed", header: "observed", width: "9%", cell: (row) => String(row.observed_artifact_count) },
      { key: "latest", header: "latest", width: "18%", cell: (row) => <code>{text(row.latest_generated_at_utc)}</code> },
      { key: "outputs", header: "outputs", cell: (row) => row.output_artifact_labels.slice(0, 3).join(", ") || "—" },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">PROJECTION · REGISTRY</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">PROJECTION · REGISTRY</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/projection-registry · registered projection families, artifact indexes, and rebuild boundary evidence</p>
      {registry.isLoading && <p className="muted">Loading…</p>}
      {registry.isError && <p className="term-error">{registry.error.message}</p>}

      {registry.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Registry inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/projection-registry", rawJson: registry.data })}>
              <TermKV rows={[{ k: "schema", v: registry.data.schema_version }, { k: "registered", v: String(summary.registered_projection_count) }, { k: "filtered", v: String(summary.filtered_projection_count) }, { k: "returned", v: String(summary.returned_projection_count) }, { k: "search_root", v: registry.data.search_root }]} />
            </Pane>
            <Pane title="Artifact index posture">
              <TermKV rows={[{ k: "observed_entries", v: String(summary.observed_artifact_entry_count) }, { k: "orphan_entries", v: String(summary.orphan_artifact_entry_count) }, { k: "invalid_indexes", v: String(summary.invalid_index_artifact_count) }, { k: "no_artifacts", v: String(summary.registered_without_observed_artifacts_count) }, { k: "checkpoint_capable", v: String(summary.checkpoint_capable_count) }]} />
            </Pane>
            <Pane title="Selected projection" onInspect={selectedRow ? () => openInspector({ title: "Projection registry entry", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "family", v: selectedRow?.projection_family ?? "—" }, { k: "label", v: selectedRow?.projection_label ?? "—" }, { k: "handler", v: selectedRow?.rebuild_handler ?? "—" }, { k: "digest", v: shortDigest(selectedRow?.latest_projection_digest_sha256) }, { k: "registries", v: String(selectedRow?.registry_paths.length ?? 0) }]} />
              {selectedRow?.latest_projection_digest_sha256 && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.latest_projection_digest_sha256 ?? null)}>Copy digest target</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {CHECKPOINT_MODES.map((mode) => <button key={mode} type="button" className={checkpointMode === mode ? "term-chip active" : "term-chip"} onClick={() => setCheckpointMode(mode)}>{mode}</button>)}
              <label className="term-field"><span>family</span><input className="term-input" value={familyNeedle} onChange={(e) => setFamilyNeedle(e.target.value)} placeholder="exact family" style={{ width: "210px" }} /></label>
              <label className="term-field"><span>label</span><input className="term-input" value={labelNeedle} onChange={(e) => setLabelNeedle(e.target.value)} placeholder="exact label" style={{ width: "190px" }} /></label>
              <label className="term-field"><span>output</span><input className="term-input" value={outputNeedle} onChange={(e) => setOutputNeedle(e.target.value)} placeholder="contains" style={{ width: "160px" }} /></label>
              <label className="term-field"><span>handler</span><input className="term-input" value={handlerNeedle} onChange={(e) => setHandlerNeedle(e.target.value)} placeholder="contains" style={{ width: "190px" }} /></label>
            </div>
          </Pane>

          <Pane title="Registered projection families">
            <DenseTable<RegistryRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No projection registry entries matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Family counts"><TermKV rows={countRows(registry.data.family_counts)} /></Pane>
            <Pane title="Label counts"><TermKV rows={countRows(registry.data.label_counts)} /></Pane>
            <Pane title="Selected outputs" onInspect={selectedRow ? () => openInspector({ title: "Projection outputs", rawJson: { output_artifact_labels: selectedRow.output_artifact_labels, output_artifact_paths: selectedRow.output_artifact_paths, registry_paths: selectedRow.registry_paths } }) : undefined}>
              <ul className="term-list">{(selectedRow?.output_artifact_paths.length ? selectedRow.output_artifact_paths : selectedRow?.output_artifact_labels ?? []).slice(0, 8).map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          </PaneGrid>

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Projection registry degradation", rawJson: { degraded, orphan_artifact_entries: registry.data?.orphan_artifact_entries, invalid_index_artifacts: registry.data?.invalid_index_artifacts } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/projection-registry JSON" data={registry.data} />
        </>
      )}
    </div>
  );
}
