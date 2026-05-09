"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiOperatorPackWorkbench, useUiPackDetail } from "@/hooks/useUiOperatorPacks";
import type { UiOperatorPackWorkbenchItem } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type PackRow = UiOperatorPackWorkbenchItem & { __id: string; __column: string };
type Filter = "all" | "trusted" | "restricted" | "untrusted" | "missing-output";

function shortPath(value: string | null | undefined): string {
  if (!value) return "—";
  const parts = value.split(/[\\/]/).filter(Boolean);
  return parts.slice(-3).join("/") || value;
}

function trustFilter(row: PackRow, filter: Filter): boolean {
  const status = String(row.trust_status ?? "").toUpperCase();
  if (filter === "trusted") return status === "TRUSTED";
  if (filter === "restricted") return status === "TRUST_RESTRICTED";
  if (filter === "untrusted") return status === "UNTRUSTED" || status === "TRUST_UNAVAILABLE" || status === "UNKNOWN" || !status;
  if (filter === "missing-output") return !row.primary_output_artifact_path;
  return true;
}

export default function OperatorPacksPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const workbench = useUiOperatorPackWorkbench();
  const { openInspector } = useTerminalCockpit();
  const [filter, setFilter] = useState<Filter>("all");
  const [selected, setSelected] = useState<string | null>(null);

  const rows = useMemo<PackRow[]>(() => {
    const columns = Array.isArray(workbench.data?.columns) ? workbench.data.columns : [];
    return columns.flatMap((column) =>
      (Array.isArray(column.items) ? column.items : []).map((item, i) => ({
        ...item,
        __column: column.pack_kind,
        __id: `${item.pack_kind}:${item.manifest_path || i}`,
      })),
    );
  }, [workbench.data]);

  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const detail = useUiPackDetail({ manifestPath: selectedRow?.manifest_path ?? null, packKind: selectedRow?.pack_kind ?? null });

  const filteredRows = useMemo(() => rows.filter((row) => trustFilter(row, filter)), [filter, rows]);
  const trustedCount = rows.filter((row) => String(row.trust_status ?? "").toUpperCase() === "TRUSTED").length;
  const restrictedCount = rows.filter((row) => String(row.trust_status ?? "").toUpperCase() === "TRUST_RESTRICTED").length;
  const missingOutputCount = rows.filter((row) => !row.primary_output_artifact_path).length;
  const packKinds = new Set(rows.map((row) => row.pack_kind)).size;

  const commandHints = asStringArray(detail.data?.command_hints);
  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "operator-packs-workbench",
        severity: rows.length > 0 ? "ok" : "warn",
        text: `operator_packs items=${rows.length} kinds=${packKinds} trusted=${trustedCount} restricted=${restrictedCount}`,
      },
      {
        id: "operator-packs-guardrail",
        severity: "info",
        text: "read-plane only · command hints are advisory · mutations stay behind governed command route",
      },
    ],
    [packKinds, restrictedCount, rows.length, trustedCount],
  );
  const ticker = useMemo(
    () => [
      { severity: rows.length > 0 ? ("ok" as const) : ("warn" as const), text: `PACK ${rows.length}` },
      { severity: missingOutputCount > 0 ? ("warn" as const) : ("neutral" as const), text: `NO_OUT ${missingOutputCount}` },
    ],
    [missingOutputCount, rows.length],
  );
  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<PackRow>[] = useMemo(
    () => [
      { key: "kind", header: "kind", width: "15%", cell: (row) => <code>{row.pack_kind}</code> },
      { key: "trust", header: "trust", width: "14%", cell: (row) => <StatusBadge raw={row.trust_status ?? "UNKNOWN"} /> },
      { key: "generated", header: "generated", width: "18%", cell: (row) => <code>{row.generated_at_utc ?? "—"}</code> },
      { key: "summary", header: "summary", cell: (row) => row.summary_line ?? "—" },
      { key: "output", header: "primary output", width: "20%", cell: (row) => <code>{shortPath(row.primary_output_artifact_path)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">OPERATOR · PACKS</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">OPERATOR · PACK WORKBENCH</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/packs/workbench · GET /ui/packs/detail · read-only discovery, navigation, lifecycle hints, and escalation context
      </p>

      {workbench.isLoading && <p className="muted">Loading…</p>}
      {workbench.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {workbench.error instanceof Error ? workbench.error.message : String(workbench.error)}
        </p>
      )}

      {workbench.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Workbench" onInspect={() => openInspector({ title: "Operator pack workbench", rawJson: workbench.data })}>
              <TermKV
                rows={[
                  { k: "schema", v: workbench.data.schema_version },
                  { k: "search_root", v: workbench.data.search_root },
                  { k: "columns", v: String(workbench.data.column_count) },
                  { k: "items", v: String(workbench.data.total_item_count) },
                ]}
              />
            </Pane>
            <Pane title="Trust posture">
              <TermKV
                rows={[
                  { k: "trusted", v: String(trustedCount) },
                  { k: "restricted", v: String(restrictedCount) },
                  { k: "unknown/untrusted", v: String(rows.length - trustedCount - restrictedCount) },
                  { k: "missing_output", v: String(missingOutputCount) },
                ]}
              />
            </Pane>
            <Pane title="Selected detail" onInspect={detail.data ? () => openInspector({ title: "Pack detail", rawJson: detail.data }) : undefined}>
              <TermKV
                rows={[
                  { k: "pack", v: selectedRow?.pack_kind ?? "—" },
                  { k: "navigation", v: String(detail.data?.navigation?.item_count ?? 0) },
                  { k: "timeline", v: String(detail.data?.timeline?.item_count ?? 0) },
                  { k: "hints", v: String(commandHints.length) },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Indexed packs" dense onInspect={() => openInspector({ title: "Filtered operator packs", rawJson: filteredRows })}>
            <div style={{ display: "flex", gap: "6px", flexWrap: "wrap", marginBottom: "8px" }}>
              {(["all", "trusted", "restricted", "untrusted", "missing-output"] as Filter[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  className={`term-btn term-btn--sm${filter === f ? " is-active" : ""}`}
                  onClick={() => setFilter(f)}
                >
                  {f.toUpperCase()}
                </button>
              ))}
            </div>
            <DenseTable
              columns={cols}
              rows={filteredRows}
              rowKey={(row) => row.__id}
              selectedKey={selectedRow?.__id ?? null}
              onRowClick={(row) => {
                setSelected(row.__id);
                openInspector({ title: `Operator pack · ${row.pack_kind}`, rawJson: row });
              }}
              empty="No operator packs matched the current filter."
            />
          </Pane>

          {(commandHints.length > 0 || detail.data?.timeline?.items?.length) && (
            <PaneGrid cols={2}>
              <Pane title="Command hints">
                {commandHints.length > 0 ? (
                  <div className="term-tape" style={{ maxHeight: "140px" }}>
                    {commandHints.map((hint) => (
                      <div key={hint} className="term-tape__line">
                        <span className="sev sev--info">HINT</span>
                        <span className="term-tape__text">{hint}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="muted">No governed command hints for the selected pack.</p>
                )}
              </Pane>
              <Pane title="Timeline">
                <div className="term-tape" style={{ maxHeight: "140px" }}>
                  {(detail.data?.timeline?.items ?? []).slice(0, 8).map((item, i) => (
                    <div key={`${String(item.manifest_path ?? i)}:${i}`} className="term-tape__line">
                      <span className="sev sev--neutral">{String(item.pack_kind ?? "PACK")}</span>
                      <span className="term-tape__text">{String(item.generated_at_utc ?? "unknown")} · {String(item.summary_line ?? "No summary recorded")}</span>
                    </div>
                  ))}
                </div>
              </Pane>
            </PaneGrid>
          )}
        </>
      )}

      {workbench.data && <JsonDetails summary="Drilldown: full /ui/packs/workbench JSON" data={workbench.data} />}
      {detail.data && <JsonDetails summary="Drilldown: selected /ui/packs/detail JSON" data={detail.data} />}
    </div>
  );
}
