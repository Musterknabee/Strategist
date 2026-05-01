"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useProbeHealthz } from "@/hooks/useProbeHealthz";
import { useProbeLivez } from "@/hooks/useProbeLivez";
import { useProbeReadyz } from "@/hooks/useProbeReadyz";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSurfaceHealth } from "@/hooks/useUiSurfaceHealth";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  readinessBlockerRows,
  readinessCheckRows,
} from "@/lib/operator/payload-utils";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo, useState } from "react";

type CheckRow = { key: string; ok: boolean | null; detail: string };
type Filter = "all" | "failed" | "passed" | "unknown";

export default function ReadinessPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const healthz = useProbeHealthz();
  const livez = useProbeLivez();
  const readyz = useProbeReadyz();
  const uiHealth = useUiSurfaceHealth();
  const [filter, setFilter] = useState<Filter>("all");
  const [selCheck, setSelCheck] = useState<string | null>(null);

  const readyPayload = readyz.data?.data != null ? asRecord(readyz.data.data) : null;
  const status = readyPayload ? asString(readyPayload.status) : undefined;
  const schemaVersion = readyPayload ? asNumber(readyPayload.schema_version) : undefined;
  const expectedSchema = readyPayload ? asNumber(readyPayload.expected_schema_version) : undefined;
  const checks = readinessCheckRows(readyPayload?.checks);
  const blockerRows = readinessBlockerRows(readyPayload?.blockers);
  const warningRows = readinessBlockerRows(readyPayload?.warnings);
  const remediationLines = [
    ...new Set(
      [...blockerRows, ...warningRows].map((r) => r.remediation).filter((x): x is string => Boolean(x)),
    ),
  ];

  const filteredChecks = useMemo(() => {
    if (filter === "all") return checks;
    if (filter === "failed") return checks.filter((c) => c.ok === false);
    if (filter === "passed") return checks.filter((c) => c.ok === true);
    return checks.filter((c) => c.ok === null);
  }, [checks, filter]);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "rdy",
        severity: status === "READY" ? "ok" : status ? "bad" : "neutral",
        text: `readyz ${status ?? "UNKNOWN"} HTTP ${readyz.data?.httpStatus ?? "—"}`,
      },
      {
        id: "blk",
        severity: blockerRows.length ? "bad" : "ok",
        text: `blockers ${blockerRows.length} warnings ${warningRows.length}`,
      },
    ],
    [status, readyz.data?.httpStatus, blockerRows.length, warningRows.length],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `RDY ${status ?? "?"}` },
      {
        severity: blockerRows.length ? ("bad" as const) : ("ok" as const),
        text: `BLK ${blockerRows.length}`,
      },
    ],
    [status, blockerRows.length],
  );

  useTerminalPageBind(tape, ticker);

  const checkColumns: DenseColumn<CheckRow>[] = useMemo(
    () => [
      { key: "id", header: "check", width: "38%", cell: (r) => <code>{r.key}</code> },
      {
        key: "ok",
        header: "ok",
        width: "12%",
        cell: (r) => (r.ok === null ? "?" : r.ok ? "Y" : "N"),
      },
      { key: "detail", header: "detail", cell: (r) => r.detail || "—" },
    ],
    [],
  );

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">READINESS</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  const loading = healthz.isLoading || livez.isLoading || readyz.isLoading || uiHealth.isLoading;
  const err =
    healthz.isError || livez.isError || readyz.isError || uiHealth.isError
      ? [healthz.error, livez.error, readyz.error, uiHealth.error].find(Boolean)
      : null;

  return (
    <div className="term-page">
      <h1 className="term-page__title">READINESS · MATRIX</h1>
      <p className="muted" style={{ fontSize: "10px", margin: "0 0 6px" }}>
        /healthz /livez /readyz (503+JSON normal when blocked) /ui/health · <code>{config.baseUrl}</code>
      </p>
      {loading && <p className="muted">Loading…</p>}
      {err && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {String(err instanceof Error ? err.message : err)}
        </p>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) minmax(0,1.2fr)", gap: "6px" }}>
        <Pane
          title="Probes"
          onInspect={() =>
            openInspector({
              title: "Probe summary",
              rawJson: {
                healthz: healthz.data,
                livez: { http: livez.data?.httpStatus, body: livez.data?.data },
                readyz: { http: readyz.data?.httpStatus, body: readyz.data?.data },
                ui_health: uiHealth.data,
              },
            })
          }
        >
          <TermKV
            rows={[
              { k: "healthz", v: healthz.data ? (asBool(healthz.data.ok) ? "OK" : "NO") : "—" },
              {
                k: "livez",
                v: livez.isError
                  ? "ERR"
                  : livez.data
                    ? `${livez.data.httpStatus} ${asString(livez.data.data?.status) ?? ""}`
                    : "—",
              },
              {
                k: "readyz",
                v: `${readyz.data?.httpStatus ?? "—"} ${status ?? ""}`,
              },
              { k: "ui/hlth", v: uiHealth.data ? (asBool(uiHealth.data.ok) ? "OK" : "NO") : "—" },
              { k: "runtime", v: <StatusBadge raw={status} /> },
            ]}
          />
        </Pane>
        <Pane
          title="Gate"
          onInspect={() => openInspector({ title: "Readyz payload", rawJson: readyPayload })}
        >
          <TermKV
            rows={[
              { k: "schema", v: String(schemaVersion ?? "—") },
              { k: "expect", v: String(expectedSchema ?? "—") },
              { k: "adj", v: String(readyPayload?.adjudication_allowed ?? "—") },
              { k: "blk#", v: String(blockerRows.length) },
              { k: "wrn#", v: String(warningRows.length) },
            ]}
          />
        </Pane>
      </div>

      {(blockerRows.length > 0 || warningRows.length > 0) && (
        <Pane title="Blocker / warning tape" dense>
          <div className="term-tape term-tape--empty" style={{ maxHeight: "100px" }}>
            {blockerRows.map((b) => (
              <div key={b.code} className="term-tape__line">
                <span className="sev sev--bad">BLK</span>
                <span className="term-tape__text">
                  {b.code} {b.message}
                </span>
              </div>
            ))}
            {warningRows.map((b) => (
              <div key={`w-${b.code}`} className="term-tape__line">
                <span className="sev sev--warn">WRN</span>
                <span className="term-tape__text">
                  {b.code} {b.message}
                </span>
              </div>
            ))}
          </div>
          {remediationLines.length > 0 && (
            <ul className="compact-list muted" style={{ fontSize: "10px", margin: "4px 0 0" }}>
              {remediationLines.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          )}
        </Pane>
      )}

      {checks.length > 0 && (
        <>
          <div className="term-filter-row">
            {(
              [
                ["all", "all"],
                ["failed", "failed"],
                ["passed", "passed"],
                ["unknown", "unknown"],
              ] as const
            ).map(([k, lab]) => (
              <button
                key={k}
                type="button"
                className={filter === k ? "is-on" : ""}
                onClick={() => setFilter(k)}
              >
                {lab}
              </button>
            ))}
          </div>
          <DenseTable
            columns={checkColumns}
            rows={filteredChecks}
            rowKey={(r) => r.key}
            selectedKey={selCheck}
            onRowClick={(r) => {
              setSelCheck(r.key);
              openInspector({
                title: `Check · ${r.key}`,
                body: (
                  <TermKV
                    rows={[
                      { k: "ok", v: r.ok === null ? "UNKNOWN" : r.ok ? "Y" : "N" },
                      { k: "detail", v: r.detail || "—" },
                    ]}
                  />
                ),
                rawJson: r,
              });
            }}
          />
        </>
      )}

      <JsonDetails
        summary="Collapsed: full probe JSON blobs"
        data={{
          healthz: healthz.data,
          livez: livez.isError ? { error: String(livez.error) } : livez.data,
          readyz: readyz.data,
          ui_health: uiHealth.data,
        }}
      />
    </div>
  );
}
