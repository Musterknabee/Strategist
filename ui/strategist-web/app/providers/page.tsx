"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiProviderHealth } from "@/hooks/useUiProviderHealth";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import {
  classifyProviderClassifiedStatus,
  asNumber,
  asRecord,
  asString,
  asStringArray,
} from "@/lib/operator/payload-utils";
import type { InspectorPayload } from "@/lib/terminal/cockpit-context";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type Pf = "all" | "public" | "keyed" | "missing" | "warn" | "bad";

type ERow = Record<string, unknown> & { __id: string };

function unknownUnless(v: string | undefined, fallback = "UNKNOWN"): string {
  if (v === undefined || v === null || v === "") return fallback;
  return v;
}

function AlpacaExecutionCard({
  alpaca,
  openInspector,
}: {
  alpaca: ERow;
  openInspector: (p: InspectorPayload) => void;
}) {
  const posture = alpaca.execution_posture != null ? asRecord(alpaca.execution_posture) : null;
  const tradingMode = posture ? asString(posture.trading_mode) : undefined;
  const liveApprovedRaw = posture?.personal_live_approved;
  const liveApproved =
    typeof liveApprovedRaw === "boolean" ? (liveApprovedRaw ? "true" : "false") : undefined;
  const authority = posture ? asString(posture.execution_authority) : undefined;
  const paperWarns = posture ? asStringArray(posture.paper_live_warnings) : [];
  const policyBlk = posture ? asStringArray(posture.execution_policy_blockers) : [];
  const entryBlk = Array.isArray(alpaca.blockers) ? (alpaca.blockers as string[]) : [];
  const policyLine =
    [...new Set([...policyBlk, ...entryBlk])].filter(Boolean).join("; ") || "—";

  return (
    <Pane
      title="Alpaca · execution posture (read-plane · no orders)"
      dense
      onInspect={() => openInspector({ title: "Alpaca execution posture", rawJson: alpaca })}
    >
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 6px" }}>
        Env-derived hints from API process. Missing fields = UNKNOWN. Not a trading terminal.
      </p>
      <TermKV
        rows={[
          { k: "configured", v: alpaca.configured ? "yes" : "no" },
          { k: "trading_mode", v: unknownUnless(tradingMode) },
          { k: "personal_live_approved", v: unknownUnless(liveApproved) },
          {
            k: "execution_authority",
            v: unknownUnless(authority, "UNKNOWN"),
          },
          { k: "policy / entry blockers", v: policyLine },
          {
            k: "paper_live_warnings",
            v: paperWarns.length ? paperWarns.join("; ") : "—",
          },
          {
            k: "provider_status",
            v: <StatusBadge raw={asString(alpaca.classified_status)} />,
          },
        ]}
      />
    </Pane>
  );
}

export default function ProvidersPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const health = useUiProviderHealth();
  const [pf, setPf] = useState<Pf>("all");
  const [sel, setSel] = useState<string | null>(null);

  const root = health.data != null ? asRecord(health.data) : null;
  const summary = root?.summary != null ? asRecord(root.summary) : null;
  const entriesRaw = root?.entries;
  const entries = useMemo(() => {
    const raw = Array.isArray(entriesRaw)
      ? entriesRaw.map((x) => asRecord(x)).filter((x): x is Record<string, unknown> => x != null)
      : [];
    return raw.map((e, i) => ({ ...e, __id: asString(e.provider_id) ?? `p${i}` })) as ERow[];
  }, [entriesRaw]);

  const execBlockers = Array.isArray(root?.execution_workflow_blockers)
    ? root.execution_workflow_blockers.filter((x): x is string => typeof x === "string")
    : [];

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      const pub = asString(e.access_type) === "PUBLIC_NO_SIGNUP";
      const miss = !pub && e.configured !== true;
      const st = classifyProviderClassifiedStatus(asString(e.classified_status));
      const wrn = (Array.isArray(e.warnings) && e.warnings.length > 0) || st === "warn";
      const bad = st === "bad";
      if (pf === "public") return pub;
      if (pf === "keyed") return !pub;
      if (pf === "missing") return miss;
      if (pf === "warn") return wrn;
      if (pf === "bad") return bad;
      return true;
    });
  }, [entries, pf]);

  const alpaca = entries.find((e) => asString(e.provider_id) === "alpaca");

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "p",
        severity: "info",
        text: `providers ok=${String(summary?.classified_ok_count ?? "?")} exec_blk=${execBlockers.length}`,
      },
    ],
    [summary, execBlockers.length],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `PR ${String(summary?.classified_ok_count ?? "?")}/${String(entries.length)}` },
    ],
    [summary, entries.length],
  );

  useTerminalPageBind(tape, ticker);

  const cols: DenseColumn<ERow>[] = useMemo(
    () => [
      { key: "id", header: "id", width: "14%", cell: (r) => <code>{asString(r.provider_id)}</code> },
      {
        key: "st",
        header: "status",
        width: "14%",
        cell: (r) => {
          const c = classifyProviderClassifiedStatus(asString(r.classified_status));
          return <span className={`sev sev--${c === "ok" ? "ok" : c === "bad" ? "bad" : "warn"}`}>{asString(r.classified_status)}</span>;
        },
      },
      { key: "cfg", header: "cfg", width: "8%", cell: (r) => (r.configured ? "Y" : "N") },
      { key: "http", header: "http", width: "8%", cell: (r) => String(asNumber(r.http_status) ?? "—") },
      { key: "trust", header: "trust", width: "14%", cell: (r) => asString(r.trust_level)?.slice(0, 12) ?? "—" },
      { key: "pit", header: "pit", width: "14%", cell: (r) => asString(r.pit_suitability)?.slice(0, 14) ?? "—" },
      { key: "gate", header: "gate", width: "8%", cell: (r) => (r.may_gate_live_promotion ? "Y" : "N") },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">PROVIDERS</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">PROVIDERS · MATRIX</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/provider-health · no secrets
      </p>
      {health.isLoading && <p className="muted">Loading…</p>}
      {health.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {health.error instanceof Error ? health.error.message : String(health.error)}
        </p>
      )}

      {root && (
        <>
          {alpaca && <AlpacaExecutionCard alpaca={alpaca} openInspector={openInspector} />}
          {!alpaca && execBlockers.length > 0 && (
            <Pane title="Execution policy blockers (no alpaca row)" dense>
              <TermKV
                rows={execBlockers.map((b, i) => ({
                  k: `blk${i}`,
                  v: b,
                }))}
              />
            </Pane>
          )}

          <div className="term-filter-row">
            {(
              [
                ["all", "all"],
                ["public", "pub"],
                ["keyed", "keyed"],
                ["missing", "miss"],
                ["warn", "wrn"],
                ["bad", "bad"],
              ] as const
            ).map(([k, lab]) => (
              <button key={k} type="button" className={pf === k ? "is-on" : ""} onClick={() => setPf(k)}>
                {lab}
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
              openInspector({
                title: asString(r.display_name) || asString(r.provider_id) || "Provider",
                body: (
                  <TermKV
                    rows={[
                      { k: "access", v: asString(r.access_type) ?? "—" },
                      { k: "http", v: String(asNumber(r.http_status) ?? "—") },
                      {
                        k: "blk",
                        v: Array.isArray(r.blockers) ? (r.blockers as string[]).join("; ") : "—",
                      },
                    ]}
                  />
                ),
                rawJson: r,
                digestToCopy: asString(r.sample_digest_prefix) ?? undefined,
              });
            }}
          />
        </>
      )}

      {health.data && <JsonDetails summary="Drilldown: provider-health JSON" data={health.data} />}
    </div>
  );
}
