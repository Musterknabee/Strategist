"use client";

import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidence } from "@/hooks/useUiEvidence";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  asStringArray,
} from "@/lib/operator/payload-utils";
import { formatCockpitOk, readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";
import { useMemo } from "react";

export default function EvidencePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const evidence = useUiEvidence(undefined);

  const root = evidence.data;
  const ev = root != null ? asRecord(root) : null;
  const verification = ev ? asRecord(ev.verification) : null;
  const host = ev ? asRecord(ev.host_fingerprint) : null;
  const checklist = ev ? asRecord(ev.daily_checklist) : null;
  const runtimeReview = ev ? asRecord(ev.runtime_review) : null;
  const lineage = ev ? asRecord(ev.lineage) : null;
  const registry = ev ? asRecord(ev.registry) : null;
  const operatorLines = ev ? asStringArray(ev.operator_lines) : [];
  const cockpit = readUiEvidenceCockpit(ev);

  const digestPrefix = asString(registry?.projection_digest_sha256)?.slice(0, 24);

  const layerRows = useMemo(() => {
    if (!lineage || !Array.isArray(lineage.layers)) return [];
    return lineage.layers.map((layer: unknown, i: number) => {
      const L = asRecord(layer);
      return { id: String(i), layer: L ? asString(L.layer) ?? "—" : "—", count: L ? asNumber(L.count) ?? "—" : "—" };
    });
  }, [lineage]);

  const layerCols: DenseColumn<(typeof layerRows)[0]>[] = useMemo(
    () => [
      { key: "layer", header: "layer", cell: (r) => r.layer },
      { key: "ct", header: "n", width: "64px", cell: (r) => String(r.count) },
    ],
    [],
  );

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "cockpit",
        severity: cockpit?.deployment_status === "PASS" ? "ok" : "warn",
        text: `evidence_chain deploy=${cockpit?.deployment_status ?? "?"} smoke=${formatCockpitOk(cockpit?.api_smoke_ok)}`,
      },
      {
        id: "trust",
        severity: "info",
        text: `trust ${asString(verification?.trust_status) ?? "—"} seal ${asString(verification?.seal_status) ?? "—"}`,
      },
    ],
    [cockpit, verification],
  );

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `EV ${asString(ev?.schema_version) ?? "?"}` },
      { severity: "info" as const, text: `DEP ${cockpit?.deployment_status ?? "?"}` },
    ],
    [ev, cockpit?.deployment_status],
  );

  useTerminalPageBind(tape, ticker);

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">EVIDENCE</h1>
        <p className="muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">EVIDENCE · CHAIN</h1>
      <p className="muted" style={{ fontSize: "10px" }}>
        GET /ui/evidence · not on-disk bundle · NOT_CLAIMED SPA
      </p>
      {evidence.isLoading && <p className="muted">Loading…</p>}
      {evidence.isError && (
        <p className="term-page__banner" style={{ color: "#f85149" }}>
          {evidence.error instanceof Error ? evidence.error.message : String(evidence.error)}
        </p>
      )}

      {ev && (
        <>
          <PaneGrid cols={3}>
            <Pane
              title="Snapshot"
              onInspect={() => openInspector({ title: "Snapshot", rawJson: { schema: ev.schema_version, search_root: ev.search_root } })}
            >
              <TermKV
                rows={[
                  { k: "schema", v: asString(ev.schema_version) ?? "—" },
                  { k: "root", v: asString(ev.search_root) ?? "—" },
                  { k: "gen_utc", v: asString(ev.generated_at_utc) ?? "—" },
                ]}
              />
            </Pane>
            <Pane
              title="Cockpit"
              onInspect={() => openInspector({ title: "Cockpit fields", rawJson: cockpit, digestToCopy: digestPrefix })}
            >
              <TermKV
                rows={[
                  { k: "deploy", v: <StatusBadge raw={cockpit?.deployment_status} /> },
                  { k: "ok", v: formatCockpitOk(cockpit?.deployment_evidence_ok) },
                  { k: "smoke", v: formatCockpitOk(cockpit?.api_smoke_ok) },
                  { k: "signoff", v: formatCockpitOk(cockpit?.manual_operator_signoff_present) },
                ]}
              />
              {digestPrefix && (
                <button
                  type="button"
                  className="term-btn term-btn--sm"
                  style={{ marginTop: "6px" }}
                  onClick={() => {
                    setLastDigest(digestPrefix);
                    void navigator.clipboard.writeText(digestPrefix);
                  }}
                >
                  Copy digest prefix
                </button>
              )}
            </Pane>
            <Pane
              title="Verify"
              onInspect={() => openInspector({ title: "Verification", rawJson: verification })}
            >
              <TermKV
                rows={[
                  { k: "proj_ok", v: String(asBool(verification?.projection_snapshot_verified) ?? "—") },
                  { k: "trust", v: <StatusBadge raw={asString(verification?.trust_status)} /> },
                  { k: "seal", v: asString(verification?.seal_status) ?? "—" },
                  { k: "pct", v: String(asNumber(verification?.completeness_percent) ?? "—") },
                ]}
              />
            </Pane>
          </PaneGrid>

          <PaneGrid cols={2}>
            <Pane title="Host" dense onInspect={() => openInspector({ title: "Host", rawJson: host })}>
              <TermKV
                rows={[
                  { k: "kind", v: asString(host?.host_kind) ?? "—" },
                  { k: "label", v: asString(host?.host_label) ?? "—" },
                  { k: "mode", v: asString(host?.runtime_mode) ?? "—" },
                  { k: "git", v: asString(host?.git_commit)?.slice(0, 12) ?? "—" },
                ]}
              />
            </Pane>
            <Pane title="Checklist" dense onInspect={() => openInspector({ title: "Daily checklist", rawJson: checklist })}>
              <TermKV
                rows={[
                  { k: "rdy", v: <StatusBadge raw={asString(checklist?.readiness_status)} /> },
                  { k: "startup", v: String(asBool(checklist?.startup_check_passed) ?? "—") },
                  { k: "prov", v: String(asBool(checklist?.provider_availability_ok) ?? "—") },
                  { k: "fresh_anom", v: String(asNumber(checklist?.freshness_anomaly_count) ?? "—") },
                ]}
              />
            </Pane>
          </PaneGrid>

          <Pane title="Runtime review" dense onInspect={() => openInspector({ title: "Runtime review", rawJson: runtimeReview })}>
            <TermKV
              rows={[
                { k: "decision", v: asString(runtimeReview?.decision) ?? "—" },
                { k: "signoff", v: asString(runtimeReview?.signoff_status) ?? "—" },
              ]}
            />
          </Pane>

          {layerRows.length > 0 && (
            <Pane title="Lineage layers" dense>
              <DenseTable
                columns={layerCols}
                rows={layerRows}
                rowKey={(r) => r.id}
                onRowClick={(r) =>
                  openInspector({ title: `Layer ${r.layer}`, body: <TermKV rows={[{ k: "count", v: String(r.count) }]} /> })
                }
              />
            </Pane>
          )}

          {operatorLines.length > 0 && (
            <div className="term-tape" style={{ maxHeight: "72px", marginTop: "6px" }}>
              {operatorLines.map((line) => (
                <div key={line.slice(0, 80)} className="term-tape__line">
                  <span className="sev sev--info">LINE</span>
                  <span className="term-tape__text">{line}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {evidence.data && <JsonDetails summary="Drilldown: full /ui/evidence JSON" data={evidence.data} />}
    </div>
  );
}
