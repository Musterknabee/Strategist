"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiOperatorActions } from "@/hooks/useUiOperatorActions";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asBool, asNumber, asRecord, asString } from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

function entryTime(e: Record<string, unknown>): string | undefined {
  return (
    asString(e.accepted_at_utc) ??
    asString(e.event_time_utc) ??
    asString(e.occurred_at_utc) ??
    asString(e.timestamp_utc)
  );
}

type Row = Record<string, unknown> & { __id: string };

export default function LedgerPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const index = useUiOperatorActions();
  const [sel, setSel] = useState<string | null>(null);

  const data = index.data != null ? asRecord(index.data) : null;
  const entriesRaw = data?.entries;
  const entries = useMemo(() => {
    const raw = Array.isArray(entriesRaw)
      ? entriesRaw.map((x) => asRecord(x)).filter((x): x is Record<string, unknown> => x != null)
      : [];
    return raw.map((e, i) => ({
      ...e,
      __id: asString(e.action_event_id) ?? asString(e.event_hash) ?? `r${i}`,
    })) as Row[];
  }, [entriesRaw]);

  let latestIso: string | undefined;
  for (const e of entries) {
    const t = entryTime(e);
    if (t && (!latestIso || t > latestIso)) latestIso = t;
  }

  const last = entries.length ? entries[entries.length - 1] : null;
  const lastHash = last ? asString(last.event_hash) : null;

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "lc",
        severity: asBool(data?.chain_ok) ? "ok" : "warn",
        text: `ledger chain_ok=${String(data?.chain_ok)} events=${String(data?.event_count ?? "—")}`,
      },
      {
        id: "la",
        severity: "info",
        text: last ? `last ${asString(last.action) ?? "—"} ${asString(last.status) ?? ""}` : "no actions",
      },
    ],
    [data, last],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `LG ${String(data?.event_count ?? "?")}` },
      {
        severity: asBool(data?.chain_ok) ? ("ok" as const) : ("warn" as const),
        text: `CHAIN ${String(data?.chain_ok)}`,
      },
    ],
    [data],
  );

  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<Row>[] = useMemo(
    () => [
      { key: "a", header: "action", width: "28%", cell: (r) => <code>{asString(r.action) ?? "—"}</code> },
      { key: "s", header: "st", width: "10%", cell: (r) => asString(r.status) ?? "—" },
      { key: "o", header: "op", width: "14%", cell: (r) => asString(r.operator_id) ?? "—" },
      {
        key: "h",
        header: "hash",
        cell: (r) => (
          <span className="mono-value">{asString(r.event_hash)?.slice(0, 14) ?? "—"}</span>
        ),
      },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">LEDGER</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">LEDGER · OPERATOR TAPE</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/operator-actions?readonly=true · CLI owns forensic depth
      </p>
      {index.isLoading && <p className="muted">Loading…</p>}
      {index.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {index.error instanceof Error ? index.error.message : String(index.error)}
        </p>
      )}

      {data && (
        <>
          <Pane
            title="Chain summary"
            onInspect={() => openInspector({ title: "Operator index", rawJson: data })}
          >
            <TermKV
              rows={[
                { k: "events", v: String(asNumber(data.event_count) ?? "—") },
                { k: "chain_ok", v: String(asBool(data.chain_ok) ?? "—") },
                { k: "issues", v: String(asNumber(data.chain_issue_count) ?? "—") },
                { k: "ok_agg", v: String(asBool(data.ok) ?? "—") },
                { k: "latest_ts", v: latestIso ?? "—" },
                { k: "db", v: asString(data.database_path)?.slice(-48) ?? "—" },
              ]}
            />
          </Pane>

          {entries.length === 0 ? (
            <p className="muted">No events · cold journal or empty projection.</p>
          ) : (
            <DenseTable
              columns={cols}
              rows={entries.slice(-80)}
              rowKey={(r) => r.__id}
              selectedKey={sel}
              onRowClick={(r) => {
                setSel(r.__id);
                const h = asString(r.event_hash);
                if (h) setLastDigest(h);
                openInspector({
                  title: `Action · ${asString(r.action) ?? "—"}`,
                  body: (
                    <TermKV
                      rows={[
                        { k: "status", v: asString(r.status) ?? "—" },
                        { k: "operator", v: asString(r.operator_id) ?? "—" },
                        { k: "chained", v: String(r.chained ?? "—") },
                      ]}
                    />
                  ),
                  rawJson: r,
                  digestToCopy: h ?? undefined,
                });
              }}
            />
          )}
          {entries.length > 80 && (
            <p className="muted" style={{ fontSize: "10px" }}>
              Showing last 80 of {entries.length} · full JSON in drilldown
            </p>
          )}
        </>
      )}

      {index.data && <JsonDetails summary="Drilldown: full operator-actions JSON" data={index.data} />}
    </div>
  );
}
