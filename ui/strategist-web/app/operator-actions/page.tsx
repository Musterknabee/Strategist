"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiOperatorActions, type UiOperatorActionsQuery } from "@/hooks/useUiOperatorActions";
import type { UiOperatorActionJournalEntry } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type AcceptedMode = "all" | "accepted" | "rejected";
type ActionMode = "all" | "claim-item" | "renew-lease" | "acknowledge-reentry" | "control-plane-event";
type StatusMode = "all" | "accepted" | "recorded" | "rejected";

type JournalRow = UiOperatorActionJournalEntry & { __id: string };

const ACTIONS: ActionMode[] = ["all", "claim-item", "renew-lease", "acknowledge-reentry", "control-plane-event"];
const STATUSES: StatusMode[] = ["all", "accepted", "recorded", "rejected"];

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function countMapRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  if (!counts) return [];
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 6)
    .map(([k, v]) => ({ k, v: String(v) }));
}

function acceptedParam(mode: AcceptedMode): boolean | null {
  if (mode === "accepted") return true;
  if (mode === "rejected") return false;
  return null;
}

export default function OperatorActionsJournalPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const [acceptedMode, setAcceptedMode] = useState<AcceptedMode>("all");
  const [actionMode, setActionMode] = useState<ActionMode>("all");
  const [statusMode, setStatusMode] = useState<StatusMode>("all");
  const [operatorId, setOperatorId] = useState("");
  const [workItemKey, setWorkItemKey] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiOperatorActionsQuery = useMemo(
    () => ({
      operatorId: operatorId.trim() || null,
      workItemKey: workItemKey.trim() || null,
      action: actionMode === "all" ? null : actionMode,
      status: statusMode === "all" ? null : statusMode,
      accepted: acceptedParam(acceptedMode),
      controlPlaneOnly: actionMode === "control-plane-event",
      limit: 200,
    }),
    [acceptedMode, actionMode, operatorId, statusMode, workItemKey],
  );

  const journal = useUiOperatorActions(query);
  const rows = useMemo<JournalRow[]>(() => {
    const entries = Array.isArray(journal.data?.entries) ? journal.data.entries : [];
    return [...entries]
      .reverse()
      .map((entry, i) => ({ ...entry, __id: entry.action_event_id || `${entry.sequence_number ?? i}:${i}` }));
  }, [journal.data]);
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const chainIssues = asStringArray(journal.data?.chain_issues);

  const actionRows = useMemo(() => countMapRows(journal.data?.action_counts), [journal.data?.action_counts]);
  const operatorRows = useMemo(() => countMapRows(journal.data?.operator_counts), [journal.data?.operator_counts]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "operator-actions-chain",
        severity: journal.data?.ok ? "ok" : "warn",
        text: `operator_action_journal events=${journal.data?.event_count ?? 0}/${journal.data?.unfiltered_event_count ?? 0} chain_ok=${String(journal.data?.chain_ok ?? false)} issues=${journal.data?.chain_issue_count ?? 0}`,
      },
      {
        id: "operator-actions-guardrail",
        severity: "info",
        text: "read-plane only · this page observes journaled commands; mutations remain behind /ui/commands/{action}",
      },
    ],
    [journal.data],
  );
  const ticker = useMemo(
    () => [
      { severity: journal.data?.chain_ok ? ("ok" as const) : ("warn" as const), text: `OA ${journal.data?.event_count ?? 0}` },
      { severity: (journal.data?.rejected_event_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `REJ ${journal.data?.rejected_event_count ?? 0}` },
    ],
    [journal.data],
  );
  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<JournalRow>[] = useMemo(
    () => [
      { key: "seq", header: "seq", width: "7%", cell: (row) => <code>{row.sequence_number ?? "—"}</code> },
      { key: "time", header: "created", width: "18%", cell: (row) => <code>{row.created_at_utc ?? "—"}</code> },
      { key: "action", header: "action", width: "16%", cell: (row) => <code>{row.action}</code> },
      { key: "status", header: "status", width: "12%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "operator", header: "operator", width: "12%", cell: (row) => <code>{row.operator_id}</code> },
      { key: "summary", header: "summary", cell: (row) => row.summary_line || "—" },
      { key: "hash", header: "hash", width: "14%", cell: (row) => <code>{shortDigest(row.event_hash)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">OPERATOR · ACTION JOURNAL</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">OPERATOR · ACTION JOURNAL</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/operator-actions · append-only event projection · read-only chain integrity, command history, and control-plane provenance
      </p>

      {journal.isLoading && <p className="muted">Loading…</p>}
      {journal.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {journal.error instanceof Error ? journal.error.message : String(journal.error)}
        </p>
      )}

      {journal.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Journal projection" onInspect={() => openInspector({ title: "Operator action journal", rawJson: journal.data })}>
              <TermKV
                rows={[
                  { k: "schema", v: journal.data.schema_version },
                  { k: "read_model", v: String(journal.data.read_model ?? "operator_action_event_projection_index") },
                  { k: "events", v: `${journal.data.event_count}/${journal.data.unfiltered_event_count}` },
                  { k: "latest_seq", v: String(journal.data.latest_sequence_number ?? "—") },
                  { k: "returned", v: String(journal.data.returned_event_count ?? rows.length) },
                ]}
              />
            </Pane>
            <Pane title="Chain posture">
              <TermKV
                rows={[
                  { k: "ok", v: String(journal.data.ok) },
                  { k: "chain_ok", v: String(journal.data.chain_ok) },
                  { k: "chained", v: String(journal.data.chained_event_count) },
                  { k: "legacy", v: String(journal.data.legacy_event_count) },
                  { k: "issues", v: String(journal.data.chain_issue_count) },
                ]}
              />
            </Pane>
            <Pane title="Selected event" onInspect={selectedRow ? () => openInspector({ title: "Operator action event", rawJson: selectedRow }) : undefined}>
              <TermKV
                rows={[
                  { k: "id", v: selectedRow?.action_event_id ?? "—" },
                  { k: "work_item", v: selectedRow?.work_item_key ?? "—" },
                  { k: "review_target", v: selectedRow?.review_target ?? "—" },
                  { k: "idempotency", v: selectedRow?.idempotency_key ?? "—" },
                  { k: "payload_digest", v: shortDigest(selectedRow?.target_payload_digest) },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Filters" dense>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
              <label className="muted" style={{ fontSize: "10px" }}>
                operator&nbsp;
                <input
                  className="term-input"
                  value={operatorId}
                  onChange={(event) => setOperatorId(event.target.value)}
                  placeholder="operator_id"
                  style={{ width: "150px" }}
                />
              </label>
              <label className="muted" style={{ fontSize: "10px" }}>
                work item&nbsp;
                <input
                  className="term-input"
                  value={workItemKey}
                  onChange={(event) => setWorkItemKey(event.target.value)}
                  placeholder="work_item_key"
                  style={{ width: "170px" }}
                />
              </label>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {ACTIONS.map((action) => (
                  <button
                    key={action}
                    type="button"
                    className={`term-btn term-btn--sm${actionMode === action ? " is-active" : ""}`}
                    onClick={() => setActionMode(action)}
                  >
                    {action.toUpperCase()}
                  </button>
                ))}
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {STATUSES.map((status) => (
                  <button
                    key={status}
                    type="button"
                    className={`term-btn term-btn--sm${statusMode === status ? " is-active" : ""}`}
                    onClick={() => setStatusMode(status)}
                  >
                    {status.toUpperCase()}
                  </button>
                ))}
              </div>
              <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {(["all", "accepted", "rejected"] as AcceptedMode[]).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    className={`term-btn term-btn--sm${acceptedMode === mode ? " is-active" : ""}`}
                    onClick={() => setAcceptedMode(mode)}
                  >
                    {mode.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
          </Pane>

          <Pane title="Journal tail" dense onInspect={() => openInspector({ title: "Operator action rows", rawJson: rows })}>
            <DenseTable
              columns={cols}
              rows={rows}
              rowKey={(row) => row.__id}
              selectedKey={selectedRow?.__id ?? null}
              onRowClick={(row) => {
                setSelected(row.__id);
                openInspector({ title: `Operator action · ${row.action}`, rawJson: row });
              }}
              empty="No operator action events matched the current filters."
            />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Action counts">
              <TermKV rows={actionRows.length > 0 ? actionRows : [{ k: "none", v: "0" }]} />
            </Pane>
            <Pane title="Operator counts">
              <TermKV rows={operatorRows.length > 0 ? operatorRows : [{ k: "none", v: "0" }]} />
            </Pane>
            <Pane title="Chain issues">
              {chainIssues.length > 0 ? (
                <div className="term-tape" style={{ maxHeight: "140px" }}>
                  {chainIssues.slice(0, 6).map((issue) => (
                    <div key={issue} className="term-tape__line">
                      <span className="sev sev--warn">ISSUE</span>
                      <span className="term-tape__text">{issue}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No chain issues reported by the read-only verifier.</p>
              )}
            </Pane>
          </PaneGrid>
        </>
      )}

      {journal.data && <JsonDetails summary="Drilldown: full /ui/operator-actions JSON" data={journal.data} />}
    </div>
  );
}
