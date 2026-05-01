"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { TermKV } from "@/components/terminal/TermKV";
import { useProbeApiRoot } from "@/hooks/useProbeApiRoot";
import { useProbeHealthz } from "@/hooks/useProbeHealthz";
import { useProbeReadyz } from "@/hooks/useProbeReadyz";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidence } from "@/hooks/useUiEvidence";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiOperatorActions } from "@/hooks/useUiOperatorActions";
import { useUiProviderHealth } from "@/hooks/useUiProviderHealth";
import { useUiSurfaceHealth } from "@/hooks/useUiSurfaceHealth";
import { useUiWorkboard } from "@/hooks/useUiWorkboard";
import { UI_FACADE_PATH } from "@/lib/contracts/paths";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  workboardQueueItemCount,
} from "@/lib/operator/payload-utils";
import { formatCockpitOk, readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";

export default function HomePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector } = useTerminalCockpit();
  const facade = useUiFacade();
  const apiRoot = useProbeApiRoot();
  const healthz = useProbeHealthz();
  const readyz = useProbeReadyz();
  const uiHealth = useUiSurfaceHealth();
  const workboard = useUiWorkboard("operator");
  const providers = useUiProviderHealth();
  const evidence = useUiEvidence(undefined);
  const operatorIdx = useUiOperatorActions();

  const readyBody = readyz.data?.data != null ? asRecord(readyz.data.data) : null;
  const readyStatus = readyBody ? asString(readyBody.status) : undefined;
  const blockers = readyBody?.blockers;
  const warnings = readyBody?.warnings;
  const blockerN = Array.isArray(blockers) ? blockers.length : null;
  const warningN = Array.isArray(warnings) ? warnings.length : null;
  const topBlockers = Array.isArray(blockers)
    ? blockers
        .slice(0, 3)
        .map((b) => asRecord(b))
        .filter(Boolean)
        .map((b) => asString(b?.code) ?? "—")
    : [];

  const healthOk = healthz.data != null ? asBool(healthz.data.ok) : null;
  const uiHealthOk = uiHealth.data != null ? asBool(uiHealth.data.ok) : null;
  const wbCount = workboard.data ? workboardQueueItemCount(workboard.data) : null;
  const provSummary = providers.data != null ? asRecord(providers.data.summary) : null;
  const classifiedOk = provSummary ? asNumber(provSummary.classified_ok_count) : undefined;
  const pendingStub = provSummary ? asNumber(provSummary.pending_or_stub_count) : undefined;
  const execBlockers = Array.isArray((providers.data as Record<string, unknown> | undefined)?.execution_workflow_blockers)
    ? (providers.data as { execution_workflow_blockers: string[] }).execution_workflow_blockers
    : [];

  const ev = evidence.data != null ? asRecord(evidence.data) : null;
  const cockpit = readUiEvidenceCockpit(ev);
  const registry = ev ? asRecord(ev.registry) : null;

  const opEntries = operatorIdx.data != null ? (operatorIdx.data as { entries?: unknown[] }).entries : undefined;
  const lastOp = Array.isArray(opEntries) && opEntries.length > 0 ? asRecord(opEntries[opEntries.length - 1]) : null;

  const loading =
    facade.isLoading ||
    healthz.isLoading ||
    readyz.isLoading ||
    uiHealth.isLoading ||
    workboard.isLoading ||
    providers.isLoading ||
    evidence.isLoading;

  const anyErr =
    facade.isError ||
    healthz.isError ||
    readyz.isError ||
    uiHealth.isError ||
    workboard.isError ||
    providers.isError ||
    evidence.isError;

  const tape: TapeLine[] = useMemo(() => {
    const lines: TapeLine[] = [
      {
        id: "t-ready",
        severity: readyStatus === "READY" ? "ok" : readyStatus ? "bad" : "neutral",
        text: `readyz ${readyStatus ?? "UNKNOWN"} HTTP ${readyz.data?.httpStatus ?? "—"}`,
      },
      {
        id: "t-dep",
        severity:
          cockpit?.deployment_status === "PASS"
            ? "ok"
            : cockpit?.deployment_status === "FAIL"
              ? "bad"
              : "warn",
        text: `deploy ${cockpit?.deployment_status ?? "UNKNOWN"} smoke_ok=${formatCockpitOk(cockpit?.api_smoke_ok)}`,
      },
      {
        id: "t-pr",
        severity: "info",
        text: `providers OK=${classifiedOk ?? "—"} pending=${pendingStub ?? "—"}`,
      },
    ];
    if (lastOp) {
      lines.push({
        id: "t-op",
        severity: "info",
        text: `last_action ${asString(lastOp.action) ?? "—"} ${asString(lastOp.status) ?? ""}`,
      });
    }
    return lines;
  }, [
    readyStatus,
    readyz.data?.httpStatus,
    cockpit?.deployment_status,
    cockpit?.api_smoke_ok,
    classifiedOk,
    pendingStub,
    lastOp,
  ]);

  const ticker = useMemo(
    () => [
      { severity: "neutral" as const, text: `API ${config.ok ? config.baseUrl : "—"}` },
      {
        severity: readyStatus === "READY" ? ("ok" as const) : ("warn" as const),
        text: `RDY ${readyStatus ?? "?"}`,
      },
      {
        severity: cockpit?.deployment_status === "PASS" ? ("ok" as const) : ("neutral" as const),
        text: `DEP ${cockpit?.deployment_status ?? "?"}`,
      },
      { severity: "info" as const, text: `PR ${classifiedOk ?? "?"}/${pendingStub ?? "?"}` },
    ],
    [config, readyStatus, cockpit?.deployment_status, classifiedOk, pendingStub],
  );

  useTerminalPageBind(tape, ticker);

  if (!config.ok) {
    return (
      <div className="term-page">
        <h1 className="term-page__title">OVERVIEW</h1>
        <p className="term-page__banner muted">{config.error.message}</p>
      </div>
    );
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">OVERVIEW · TERMINAL GRID</h1>
      <p className="term-page__banner muted">
        NOT_CLAIMED · read-plane · <code>{UI_FACADE_PATH}</code> ·{" "}
        <button
          type="button"
          className="term-btn term-btn--sm"
          disabled={loading}
          onClick={() => {
            void facade.refetch();
            void apiRoot.refetch();
            void healthz.refetch();
            void readyz.refetch();
            void uiHealth.refetch();
            void workboard.refetch();
            void providers.refetch();
            void evidence.refetch();
            void operatorIdx.refetch();
          }}
        >
          Refresh page
        </button>
      </p>
      {loading && <p className="muted">Loading…</p>}
      {anyErr && (
        <p className="term-page__banner" style={{ borderColor: "#da3633", color: "#f85149" }}>
          DEGRADED · one or more read-plane queries failed — drill routes for detail.
        </p>
      )}

      <PaneGrid cols={3}>
        <Pane
          title="System"
          onInspect={() =>
            openInspector({
              title: "System / probes",
              body: <TermKV rows={[{ k: "facade", v: facade.data?.schema_version ?? "—" }]} />,
              rawJson: {
                healthz: healthz.data,
                readyz: { http: readyz.data?.httpStatus, body: readyz.data?.data },
                ui_health: uiHealth.data,
                api_root: apiRoot.data,
              },
            })
          }
        >
          <TermKV
            rows={[
              { k: "API", v: config.baseUrl },
              { k: "healthz", v: healthz.isError ? "ERR" : healthOk === true ? "OK" : healthOk === false ? "NO" : "—" },
              {
                k: "readyz",
                v: `${readyz.data?.httpStatus ?? "—"} ${readyStatus ?? "—"}`,
              },
              { k: "ui/health", v: uiHealth.isError ? "ERR" : uiHealthOk ? "OK" : "—" },
              { k: "facade", v: facade.data?.schema_version ?? "—" },
              {
                k: "read_plane",
                v: facade.data ? String(facade.data.read_plane_only) : "—",
              },
              {
                k: "GET /",
                v: apiRoot.isError ? "ERR" : asString(apiRoot.data?.schema_version) ?? "—",
              },
            ]}
          />
        </Pane>

        <Pane
          title="Deployment"
          onInspect={() =>
            openInspector({
              title: "Deployment cockpit",
              subtitle: "Artifact-backed fields only",
              body: (
                <TermKV
                  rows={[
                    { k: "deploy_st", v: cockpit?.deployment_status ?? "—" },
                    { k: "evidence_ok", v: formatCockpitOk(cockpit?.deployment_evidence_ok) },
                    { k: "smoke", v: formatCockpitOk(cockpit?.api_smoke_ok) },
                    { k: "backup", v: formatCockpitOk(cockpit?.backup_restore_ok) },
                    { k: "ledger", v: formatCockpitOk(cockpit?.ledger_integrity_ok) },
                    { k: "signoff", v: formatCockpitOk(cockpit?.manual_operator_signoff_present) },
                  ]}
                />
              ),
              rawJson: cockpit,
            })
          }
        >
          <TermKV
            rows={[
              { k: "status", v: <StatusBadge raw={cockpit?.deployment_status} /> },
              { k: "evidence_ok", v: formatCockpitOk(cockpit?.deployment_evidence_ok) },
              { k: "operator", v: cockpit?.operator_decision ?? "—" },
              { k: "signoff", v: formatCockpitOk(cockpit?.manual_operator_signoff_present) },
              { k: "smoke_ok", v: formatCockpitOk(cockpit?.api_smoke_ok) },
              { k: "bkup_ok", v: formatCockpitOk(cockpit?.backup_restore_ok) },
              { k: "ledger_ok", v: formatCockpitOk(cockpit?.ledger_integrity_ok) },
              {
                k: "fe_ready",
                v: <StatusBadge raw={cockpit?.frontend_readiness_status} />,
              },
            ]}
          />
        </Pane>

        <Pane
          title="Readiness"
          onInspect={() =>
            openInspector({
              title: "Readiness matrix",
              body: (
                <TermKV
                  rows={[
                    { k: "blockers", v: String(blockerN ?? "—") },
                    { k: "warnings", v: String(warningN ?? "—") },
                    { k: "sample", v: topBlockers.join(", ") || "—" },
                  ]}
                />
              ),
              rawJson: readyBody,
            })
          }
        >
          <TermKV
            rows={[
              { k: "status", v: <StatusBadge raw={readyStatus} /> },
              { k: "blk", v: String(blockerN ?? "—") },
              { k: "warn", v: String(warningN ?? "—") },
              { k: "top", v: topBlockers.join(" · ") || "—" },
            ]}
          />
          <p className="muted" style={{ margin: "6px 0 0", fontSize: "10px" }}>
            <Link href="/readiness">matrix →</Link>
          </p>
        </Pane>

        <Pane
          title="Providers"
          onInspect={() =>
            openInspector({
              title: "Provider matrix",
              rawJson: providers.data,
            })
          }
        >
          <TermKV
            rows={[
              { k: "ok", v: String(classifiedOk ?? "—") },
              { k: "pend", v: String(pendingStub ?? "—") },
              { k: "alpaca_guard", v: execBlockers.length ? execBlockers.join(", ") : "—" },
            ]}
          />
          <p className="muted" style={{ margin: "6px 0 0", fontSize: "10px" }}>
            <Link href="/providers">matrix →</Link>
          </p>
        </Pane>

        <Pane
          title="Workboard"
          onInspect={() =>
            openInspector({
              title: "Workboard",
              rawJson: workboard.data,
            })
          }
        >
          <TermKV
            rows={[
              { k: "q_items", v: String(wbCount ?? "—") },
              {
                k: "fresh",
                v: workboard.data?.stats.freshness_state ?? "—",
              },
              {
                k: "act/gov/jour",
                v: workboard.data
                  ? `${workboard.data.stats.active_count}/${workboard.data.stats.governed_count}/${workboard.data.stats.journaled_count}`
                  : "—",
              },
            ]}
          />
          <p className="muted" style={{ margin: "6px 0 0", fontSize: "10px" }}>
            <Link href="/workboard">queue →</Link>
          </p>
        </Pane>

        <Pane
          title="Lineage"
          dense
          onInspect={() =>
            openInspector({
              title: "Evidence projection",
              rawJson: ev,
            })
          }
        >
          <TermKV
            rows={[
              {
                k: "reg_ct",
                v: registry?.source_artifact_count != null ? String(registry.source_artifact_count) : "—",
              },
              {
                k: "trust",
                v: ev ? asString(asRecord(ev.verification)?.trust_status) ?? "—" : "—",
              },
            ]}
          />
          <p className="muted" style={{ margin: "6px 0 0", fontSize: "10px" }}>
            <Link href="/evidence">chain →</Link>
          </p>
        </Pane>
      </PaneGrid>

      <p className="muted" style={{ marginTop: "8px", fontSize: "10px" }}>
        Routes: <Link href="/ledger">ledger</Link> · <Link href="/runtime">runtime</Link> · NEXT_PUBLIC_STRATEGIST_API_BASE_URL
        required for prod browser builds.
      </p>
    </div>
  );
}
