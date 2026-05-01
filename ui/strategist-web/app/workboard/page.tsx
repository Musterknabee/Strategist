"use client";

import { DegradedBanner } from "@/components/operator/DegradedBanner";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { Timestamp } from "@/components/operator/Timestamp";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiWorkboard } from "@/hooks/useUiWorkboard";
import { StrategistApiError } from "@/lib/api/strategist-errors";
import { deriveWorkboardDegradedReason, type UiWorkboardQueueEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asString } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

function formatError(err: unknown): { title: string; detail: string } {
  if (err instanceof StrategistApiError) {
    if (err.kind === "unauthorized") {
      return { title: "Unauthorized", detail: err.message };
    }
    if (err.kind === "unavailable") {
      return { title: "Backend unavailable", detail: err.message };
    }
    return { title: "API error", detail: err.message };
  }
  if (err instanceof Error) {
    return { title: "Error", detail: err.message };
  }
  return { title: "Error", detail: String(err) };
}

function entryCell(entry: UiWorkboardQueueEntry, key: string): string {
  const v = entry[key];
  if (v === undefined || v === null) return "—";
  if (typeof v === "string" || typeof v === "number" || typeof v === "boolean") {
    return String(v);
  }
  return JSON.stringify(v).slice(0, 80);
}

type WRow = UiWorkboardQueueEntry & { __id: string };

export default function WorkboardPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const facadeQuery = useUiFacade();
  const workboardQuery = useUiWorkboard("operator");
  const [sel, setSel] = useState<string | null>(null);

  const facadeError = facadeQuery.isError ? formatError(facadeQuery.error) : null;
  const workboardError = workboardQuery.isError ? formatError(workboardQuery.error) : null;
  const degraded = workboardQuery.data ? deriveWorkboardDegradedReason(workboardQuery.data) : null;
  const queue = workboardQuery.data?.queue;

  const rows: WRow[] = useMemo(() => {
    const entries = workboardQuery.data?.queue?.entries ?? [];
    return entries.map((e, i) => ({
      ...e,
      __id: `${entryCell(e, "work_item_key")}#${i}`,
    }));
  }, [workboardQuery.data]);

  const entryCount = workboardQuery.data?.queue?.entries?.length ?? 0;

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "wb",
        severity: degraded ? "warn" : "info",
        text: `wb items=${entryCount} fresh=${workboardQuery.data?.stats.freshness_state ?? "?"}`,
      },
    ],
    [degraded, entryCount, workboardQuery.data?.stats.freshness_state],
  );

  const ticker = useMemo(
    () => [
      {
        severity: "neutral" as const,
        text: `ACT ${workboardQuery.data?.stats.active_count ?? "?"} GOV ${workboardQuery.data?.stats.governed_count ?? "?"}`,
      },
    ],
    [workboardQuery.data?.stats.active_count, workboardQuery.data?.stats.governed_count],
  );

  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<WRow>[] = useMemo(
    () => [
      { key: "k", header: "work_item", width: "36%", cell: (r) => <code>{entryCell(r, "work_item_key")}</code> },
      { key: "src", header: "source", width: "22%", cell: (r) => entryCell(r, "source_kind") },
      { key: "st", header: "status", width: "20%", cell: (r) => entryCell(r, "status") },
      { key: "flt", header: "filter", width: "22%", cell: (r) => entryCell(r, "filter_label") },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">WORKBOARD</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  const loading = facadeQuery.isLoading || workboardQuery.isLoading;
  const frontendClaimed = facadeQuery.data?.frontend_readiness_claimed === true;

  return (
    <div className="term-page">
      <h1 className="term-page__title">WORKBOARD · QUEUE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        Read-plane: /ui/facade · /ui/workboard · <code>{config.baseUrl}</code> · read-only
      </p>

      <Pane title="Facade · frontend posture (informational)" dense>
        <p className="muted" style={{ fontSize: "10px", margin: 0 }}>
          Backend <code>frontend_readiness_claimed</code>:{" "}
          <StatusBadge raw={frontendClaimed ? "true" : "false"} /> — single-tenant frontend readiness is{" "}
          <strong>{frontendClaimed ? "CLAIMED" : "NOT_CLAIMED"}</strong>.
        </p>
      </Pane>

      {loading && <p className="muted">Loading…</p>}

      {facadeError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          Facade: {facadeError.title}: {facadeError.detail}
        </p>
      )}

      {workboardError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          Workboard: {workboardError.title}: {workboardError.detail}
        </p>
      )}

      {degraded && !workboardError && <DegradedBanner message={degraded} />}

      {workboardQuery.data && !workboardError && (
        <>
          <PaneGrid cols={2}>
            <Pane
              title="Queue rail"
              dense
              onInspect={() =>
                openInspector({
                  title: "Queue",
                  rawJson: queue ?? {},
                })
              }
            >
              {queue?.queue_summary_line && (
                <p style={{ margin: "0 0 4px", fontSize: "11px" }}>{String(queue.queue_summary_line)}</p>
              )}
              <TermKV
                rows={[
                  { k: "queue_key", v: asString(queue?.queue_key) ?? "—" },
                  { k: "work_items", v: String(queue?.work_item_count ?? entryCount) },
                  {
                    k: "generated",
                    v: <Timestamp iso={workboardQuery.data.generated_at_utc} />,
                  },
                  { k: "board", v: workboardQuery.data.board_label },
                  { k: "schema", v: workboardQuery.data.schema_version },
                ]}
              />
            </Pane>
            <Pane
              title="Stats"
              dense
              onInspect={() =>
                openInspector({
                  title: "Workboard stats",
                  rawJson: workboardQuery.data.stats,
                })
              }
            >
              <TermKV
                rows={[
                  { k: "active", v: String(workboardQuery.data.stats.active_count) },
                  { k: "governed", v: String(workboardQuery.data.stats.governed_count) },
                  { k: "journaled", v: String(workboardQuery.data.stats.journaled_count) },
                  {
                    k: "freshness",
                    v: <StatusBadge raw={workboardQuery.data.stats.freshness_state} />,
                  },
                  { k: "pack_items", v: String(workboardQuery.data.stats.pack_item_count) },
                ]}
              />
            </Pane>
          </PaneGrid>

          {rows.length === 0 ? (
            <p className="muted" style={{ fontSize: "11px" }}>
              No queue entries — empty or cold projection.
            </p>
          ) : (
            <DenseTable
              columns={cols}
              rows={rows}
              rowKey={(r) => r.__id}
              selectedKey={sel}
              onRowClick={(r) => {
                setSel(r.__id);
                openInspector({
                  title: entryCell(r, "work_item_key"),
                  body: (
                    <TermKV
                      rows={[
                        { k: "source", v: entryCell(r, "source_kind") },
                        { k: "status", v: entryCell(r, "status") },
                      ]}
                    />
                  ),
                  rawJson: r,
                });
              }}
            />
          )}
        </>
      )}

      {workboardQuery.data && <JsonDetails summary="Drilldown: /ui/workboard JSON" data={workboardQuery.data} />}
    </div>
  );
}
