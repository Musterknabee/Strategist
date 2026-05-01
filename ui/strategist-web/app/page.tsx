"use client";

import { useMemo, useState } from "react";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { TermKV } from "@/components/terminal/TermKV";
import { useProbeApiRoot } from "@/hooks/useProbeApiRoot";
import { useProbeHealthz } from "@/hooks/useProbeHealthz";
import { useProbeReadyz } from "@/hooks/useProbeReadyz";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidence } from "@/hooks/useUiEvidence";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiOperatorActions } from "@/hooks/useUiOperatorActions";
import { useUiProviderHealth } from "@/hooks/useUiProviderHealth";
import { useUiResearchCompute } from "@/hooks/useUiResearchCompute";
import { useUiRuntime } from "@/hooks/useUiRuntime";
import { useUiSurfaceHealth } from "@/hooks/useUiSurfaceHealth";
import { useUiWorkboard } from "@/hooks/useUiWorkboard";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  classifyOperationalStatus,
  classifyProviderClassifiedStatus,
  readinessBlockerRows,
  readinessCheckRows,
  workboardQueueItemCount,
} from "@/lib/operator/payload-utils";
import { formatCockpitOk, readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { TapeLine } from "@/lib/terminal/cockpit-context";

type StatusTone = "ok" | "warn" | "bad" | "neutral";
type ProviderRow = Record<string, unknown> & { __id: string };
type ActionRow = Record<string, unknown> & { __id: string };
type WorkRow = Record<string, unknown> & { __id: string };
type StrategyRow = Record<string, unknown> & { __id: string };
type EvidenceRow = { step: string; status: string; digest: string; time: string; raw: unknown };
type MatrixRow = { checkId: string; status: string; severity: string; blockerCode: string; remediation: string; raw: unknown };

const UNKNOWN = "UNKNOWN";

function value(v: unknown, fallback = UNKNOWN): string {
  if (typeof v === "string" && v.trim()) return v;
  if (typeof v === "number" || typeof v === "boolean") return String(v);
  return fallback;
}

function boolStatus(v: boolean | null | undefined, ok = "OK", bad = "DEGRADED"): string {
  if (v === true) return ok;
  if (v === false) return bad;
  return UNKNOWN;
}

function digest(v: unknown): string {
  const s = asString(v);
  return s ? s.slice(0, 18) : "PENDING";
}

function entryTime(e: Record<string, unknown>): string {
  return (
    asString(e.accepted_at_utc) ??
    asString(e.event_time_utc) ??
    asString(e.occurred_at_utc) ??
    asString(e.timestamp_utc) ??
    asString(e.updated_at_utc) ??
    "PENDING"
  );
}

function inspectBody({
  status,
  summary,
  warnings = [],
  details = [],
}: {
  status: string;
  summary: string;
  warnings?: string[];
  details?: { k: string; v: React.ReactNode }[];
}) {
  return (
    <div className="inspector-stack">
      <TermKV rows={[{ k: "status", v: <StatusBadge raw={status} /> }, ...details]} />
      <div className="inspector-section">
        <span className="inspector-label">SUMMARY</span>
        <p>{summary}</p>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">WARNINGS</span>
        {warnings.length ? (
          warnings.map((w) => <p key={w}>{w}</p>)
        ) : (
          <p>NONE_REPORTED</p>
        )}
      </div>
    </div>
  );
}

function metricTone(status: string): StatusTone {
  return classifyOperationalStatus(status);
}

export default function HomePage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const facade = useUiFacade();
  const apiRoot = useProbeApiRoot();
  const healthz = useProbeHealthz();
  const readyz = useProbeReadyz();
  const uiHealth = useUiSurfaceHealth();
  const workboard = useUiWorkboard("operator");
  const providers = useUiProviderHealth();
  const evidence = useUiEvidence(undefined);
  const operatorIdx = useUiOperatorActions();
  const runtime = useUiRuntime("operator");
  const researchCompute = useUiResearchCompute();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  const readyBody = readyz.data?.data != null ? asRecord(readyz.data.data) : null;
  const readyStatus = readyBody ? asString(readyBody.status) ?? UNKNOWN : UNKNOWN;
  const checks = readinessCheckRows(readyBody?.checks);
  const blockers = readinessBlockerRows(readyBody?.blockers);
  const warnings = readinessBlockerRows(readyBody?.warnings);
  const ev = evidence.data != null ? asRecord(evidence.data) : null;
  const cockpit = readUiEvidenceCockpit(ev);
  const verification = ev ? asRecord(ev.verification) : null;
  const registry = ev ? asRecord(ev.registry) : null;
  const runtimeBody = runtime.data != null ? asRecord(runtime.data) : null;
  const readPlane = runtimeBody ? asRecord(runtimeBody.read_plane) : null;
  const backend = runtimeBody ? asRecord(runtimeBody.backend) : null;
  const researchBody = researchCompute.data != null ? asRecord(researchCompute.data) : null;
  const gpuProbe = researchBody ? asRecord(researchBody.gpu_probe) : null;
  const gpuHardware = Array.isArray(gpuProbe?.nvidia_smi_devices) ? asRecord(gpuProbe.nvidia_smi_devices[0]) : null;

  const providerRows = useMemo<ProviderRow[]>(() => {
    const entries = asRecord(providers.data)?.entries;
    if (!Array.isArray(entries)) return [];
    return entries
      .map((entry, i) => {
        const r = asRecord(entry);
        if (!r) return null;
        return { ...r, __id: asString(r.provider_id) ?? asString(r.display_name) ?? `provider-${i}` };
      })
      .filter((x): x is ProviderRow => x != null);
  }, [providers.data]);

  const actionRows = useMemo<ActionRow[]>(() => {
    const entries = asRecord(operatorIdx.data)?.entries;
    if (!Array.isArray(entries)) return [];
    return entries
      .map((entry, i) => {
        const r = asRecord(entry);
        if (!r) return null;
        return { ...r, __id: asString(r.action_event_id) ?? asString(r.event_hash) ?? `action-${i}` };
      })
      .filter((x): x is ActionRow => x != null)
      .slice(-6);
  }, [operatorIdx.data]);

  const workRows = useMemo<WorkRow[]>(() => {
    const entries = workboard.data?.queue?.entries;
    if (!Array.isArray(entries)) return [];
    return entries
      .map((entry, i) => {
        const r = asRecord(entry);
        if (!r) return null;
        return { ...r, __id: asString(r.work_item_key) ?? asString(r.id) ?? `work-${i}` };
      })
      .filter((x): x is WorkRow => x != null)
      .slice(0, 8);
  }, [workboard.data]);

  const strategyRows = useMemo<StrategyRow[]>(() => {
    const ranked = asRecord(workboard.data?.intelligence)?.ranked_items;
    if (!Array.isArray(ranked)) return [];
    return ranked
      .map((entry, i) => {
        const r = asRecord(entry);
        if (!r) return null;
        return { ...r, __id: asString(r.work_item_key) ?? `strategy-${i}` };
      })
      .filter((x): x is StrategyRow => x != null)
      .slice(0, 5);
  }, [workboard.data]);

  const readinessRows = useMemo<MatrixRow[]>(() => {
    const blockRows = blockers.map((b) => ({
      checkId: b.code,
      status: "FAIL",
      severity: "CRIT",
      blockerCode: b.code,
      remediation: b.remediation ?? "PENDING",
      raw: b,
    }));
    const warningRows = warnings.map((w) => ({
      checkId: w.code,
      status: "WARN",
      severity: "WARN",
      blockerCode: w.code,
      remediation: w.remediation ?? "PENDING",
      raw: w,
    }));
    const checkRows = checks.slice(0, 10).map((c) => ({
      checkId: c.key,
      status: c.ok === true ? "PASS" : c.ok === false ? "FAIL" : UNKNOWN,
      severity: c.ok === false ? "FAIL" : c.ok === null ? "WARN" : "PASS",
      blockerCode: c.ok === false ? c.key : "NONE",
      remediation: c.detail || "NONE",
      raw: c,
    }));
    return [...blockRows, ...warningRows, ...checkRows];
  }, [blockers, warnings, checks]);

  const evidenceRows = useMemo<EvidenceRow[]>(() => {
    const generated = cockpit?.evidence_generated_at_utc ?? asString(ev?.generated_at_utc) ?? "PENDING";
    return [
      { step: "Env Check", status: readyStatus, digest: digest(asString(readyBody?.config_fingerprint)), time: asString(readyBody?.checked_at_utc) ?? generated, raw: readyBody },
      { step: "Preflight", status: boolStatus(cockpit?.deployment_evidence_ok, "OK", "DEGRADED"), digest: digest(registry?.projection_digest_sha256), time: generated, raw: verification },
      { step: "Backup / Restore", status: boolStatus(cockpit?.backup_restore_ok, "OK", "PENDING"), digest: digest(registry?.projection_digest_sha256), time: generated, raw: cockpit },
      { step: "API Smoke", status: boolStatus(cockpit?.api_smoke_ok, "OK", "DEGRADED"), digest: digest(registry?.projection_digest_sha256), time: generated, raw: cockpit },
      { step: "Provider Evidence", status: providerRows.length ? "AVAILABLE" : UNKNOWN, digest: digest(asRecord(providers.data)?.samples_manifest_digest_prefix), time: asString(asRecord(providers.data)?.generated_at_utc) ?? generated, raw: providers.data },
      { step: "Operator Sign-off", status: boolStatus(cockpit?.manual_operator_signoff_present, "SIGNED", "PENDING"), digest: digest(registry?.projection_digest_sha256), time: generated, raw: cockpit },
    ];
  }, [cockpit, ev, providerRows.length, providers.data, readyBody, readyStatus, registry, verification]);

  const overviewTiles = [
    { label: "Health", status: healthz.data ? boolStatus(asBool(healthz.data.ok), "HEALTHY", "DEGRADED") : UNKNOWN, hint: `/healthz ${healthz.data ? "200" : "PENDING"}`, raw: healthz.data },
    { label: "Readiness", status: readyStatus, hint: `${blockers.length} blockers / ${warnings.length} warnings`, raw: readyBody },
    { label: "API Smoke", status: boolStatus(cockpit?.api_smoke_ok), hint: cockpit?.api_smoke_status ?? "evidence-derived", raw: cockpit },
    { label: "Backup / Restore", status: boolStatus(cockpit?.backup_restore_ok), hint: "artifact evidence", raw: cockpit },
    { label: "Ledger Integrity", status: boolStatus(cockpit?.ledger_integrity_ok, "VERIFIED", "DEGRADED"), hint: `events ${value(asRecord(operatorIdx.data)?.event_count, "0")}`, raw: operatorIdx.data },
    { label: "Operator Sign-off", status: boolStatus(cockpit?.manual_operator_signoff_present, "SIGNED", "PENDING"), hint: cockpit?.operator_decision ?? "PENDING", raw: cockpit },
    { label: "Frontend Status", status: facade.data?.frontend_readiness_claimed ? "CLAIMED" : "NOT_CLAIMED", hint: facade.data?.frontend_readiness_claimed ? "single-tenant evidence gate passed" : "formal evidence gate absent", raw: facade.data },
    { label: "System Posture", status: readyStatus === "READY" && cockpit?.deployment_status === "PASS" ? "GREEN" : "DEGRADED", hint: `read_plane=${String(facade.data?.read_plane_only ?? "UNKNOWN")}`, raw: { readyBody, cockpit, facade: facade.data } },
  ];

  const pass = readinessRows.filter((r) => r.status === "PASS").length;
  const warn = readinessRows.filter((r) => r.status === "WARN" || r.status === UNKNOWN).length;
  const fail = readinessRows.filter((r) => r.status === "FAIL").length;
  const crit = readinessRows.filter((r) => r.severity === "CRIT").length;
  const readinessPct = readinessRows.length ? Math.round((pass / readinessRows.length) * 100) : 0;
  const providerWarnings = providerRows.filter((r) => classifyProviderClassifiedStatus(asString(r.classified_status)) !== "ok").length;
  const wbCount = workboard.data ? workboardQueueItemCount(workboard.data) : null;
  const frontendClaimed = facade.data?.frontend_readiness_claimed === true;

  const tape: TapeLine[] = useMemo(() => {
    const ts = cockpit?.evidence_generated_at_utc ?? asString(ev?.generated_at_utc) ?? undefined;
    return [
      { id: "ready", ts, severity: readyStatus === "READY" ? "ok" : "warn", text: `READY=${readyStatus}` },
      { id: "api-smoke", ts, severity: cockpit?.api_smoke_ok === true ? "ok" : "warn", text: `API_SMOKE_${cockpit?.api_smoke_ok === true ? "OK" : "PENDING"}` },
      { id: "backup", ts, severity: cockpit?.backup_restore_ok === true ? "ok" : "warn", text: `BACKUP_${cockpit?.backup_restore_ok === true ? "OK" : "PENDING"}` },
      { id: "restore", ts, severity: cockpit?.backup_restore_ok === true ? "ok" : "warn", text: `RESTORE_${cockpit?.backup_restore_ok === true ? "OK" : "PENDING"}` },
      { id: "preflight", ts, severity: cockpit?.deployment_evidence_ok === true ? "ok" : "warn", text: `PREFLIGHT_${cockpit?.deployment_evidence_ok === true ? "OK" : "PENDING"}` },
      { id: "providers", ts: asString(asRecord(providers.data)?.generated_at_utc), severity: providerWarnings ? "warn" : "ok", text: `PROVIDER_WARNINGS=${providerWarnings}` },
      { id: "ledger", ts, severity: asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "ok" : "bad", text: `LEDGER_${asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "OK" : "DEGRADED"}` },
      { id: "workboard", ts: workboard.data?.generated_at_utc, severity: (wbCount ?? 0) > 0 ? "info" : "neutral", text: `WORKBOARD_ACTIVE=${wbCount ?? 0}` },
      { id: "frontend", ts, severity: frontendClaimed ? "ok" : "warn", text: frontendClaimed ? "FRONTEND_CLAIMED" : "FRONTEND_NOT_CLAIMED" },
    ];
  }, [cockpit, ev, frontendClaimed, operatorIdx.data, providerWarnings, providers.data, readyStatus, wbCount, workboard.data?.generated_at_utc]);

  const ticker = useMemo(
    () => [
      { severity: readyStatus === "READY" ? ("ok" as const) : ("warn" as const), text: `READY ${readyStatus}` },
      { severity: cockpit?.deployment_status === "PASS" ? ("ok" as const) : ("warn" as const), text: `DEP ${cockpit?.deployment_status ?? UNKNOWN}` },
      { severity: facade.data?.read_plane_only ? ("ok" as const) : ("bad" as const), text: `READ_PLANE ${String(facade.data?.read_plane_only ?? UNKNOWN)}` },
      { severity: frontendClaimed ? ("ok" as const) : ("warn" as const), text: `FRONTEND ${frontendClaimed ? "CLAIMED" : "NOT_CLAIMED"}` },
    ],
    [cockpit?.deployment_status, facade.data?.read_plane_only, frontendClaimed, readyStatus],
  );

  useTerminalPageBind(tape, ticker);

  const readinessColumns: DenseColumn<MatrixRow>[] = [
    { key: "id", header: "Check ID", cell: (r) => <code>{r.checkId}</code> },
    { key: "st", header: "Status", width: "76px", cell: (r) => <StatusBadge raw={r.status} /> },
    { key: "sev", header: "Severity", width: "64px", cell: (r) => r.severity },
    { key: "code", header: "Blocker Code", cell: (r) => r.blockerCode },
    { key: "rem", header: "Remediation", cell: (r) => r.remediation },
  ];

  const evidenceColumns: DenseColumn<EvidenceRow>[] = [
    { key: "step", header: "Step", cell: (r) => r.step },
    { key: "status", header: "Status", width: "92px", cell: (r) => <StatusBadge raw={r.status} /> },
    { key: "digest", header: "Digest", cell: (r) => <code>{r.digest}</code> },
    { key: "time", header: "Time UTC", cell: (r) => r.time },
  ];

  const providerColumns: DenseColumn<ProviderRow>[] = [
    { key: "p", header: "Provider", cell: (r) => <span className={r.__id === "alpaca" ? "term-row-emph" : ""}>{asString(r.display_name) ?? r.__id}</span> },
    { key: "a", header: "Access", cell: (r) => value(r.access_type) },
    { key: "s", header: "Status", width: "96px", cell: (r) => <StatusBadge raw={asString(r.classified_status)} /> },
    { key: "pit", header: "PIT", cell: (r) => value(r.pit_suitability) },
    { key: "t", header: "Trust", cell: (r) => value(r.trust_level) },
    { key: "h", header: "HTTP", width: "54px", cell: (r) => value(r.http_status, "PENDING") },
  ];

  const actionColumns: DenseColumn<ActionRow>[] = [
    { key: "t", header: "Time UTC", cell: (r) => entryTime(r) },
    { key: "actor", header: "Actor", cell: (r) => asString(r.operator_id) ?? asString(r.actor) ?? UNKNOWN },
    { key: "act", header: "Action", cell: (r) => asString(r.action) ?? UNKNOWN },
    { key: "target", header: "Target", cell: (r) => asString(r.target) ?? asString(r.target_id) ?? "PENDING" },
    { key: "dig", header: "Digest", cell: (r) => <code>{digest(r.event_hash)}</code> },
  ];

  const workColumns: DenseColumn<WorkRow>[] = [
    { key: "id", header: "ID", cell: (r) => asString(r.work_item_key) ?? r.__id },
    { key: "s", header: "Status", cell: (r) => <StatusBadge raw={asString(r.status)} /> },
    { key: "type", header: "Type", cell: (r) => asString(r.source_kind) ?? asString(r.item_type) ?? UNKNOWN },
    { key: "age", header: "Age", cell: (r) => asString(r.age) ?? asString(r.age_label) ?? "PENDING" },
    { key: "owner", header: "Owner", cell: (r) => asString(r.owner) ?? asString(r.claimed_by) ?? "PENDING" },
    { key: "upd", header: "Updated UTC", cell: (r) => asString(r.updated_at_utc) ?? entryTime(r) },
  ];

  const strategyColumns: DenseColumn<StrategyRow>[] = [
    { key: "id", header: "Strategy / Work Item", cell: (r) => <code>{digest(r.work_item_key)}</code> },
    { key: "target", header: "Target", cell: (r) => asString(r.review_target) ?? UNKNOWN },
    { key: "state", header: "State", cell: (r) => <StatusBadge raw={asString(r.attention_state) ?? asString(r.urgency)} /> },
    { key: "score", header: "Score", width: "54px", cell: (r) => value(r.priority_score ?? r.score, "0") },
    { key: "action", header: "Test / Next", cell: (r) => asString(asRecord(r.command_readiness)?.top_action) ?? asString(r.recommended_action) ?? "PENDING" },
  ];

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  const anyError =
    facade.isError ||
    healthz.isError ||
    readyz.isError ||
    uiHealth.isError ||
    workboard.isError ||
    providers.isError ||
    evidence.isError ||
    operatorIdx.isError ||
    runtime.isError ||
    researchCompute.isError;

  return (
    <div className="term-page cockpit-page">
      {anyError && <div className="term-page__banner cockpit-alert">DEGRADED · one or more read-plane queries failed; missing data remains UNKNOWN.</div>}
      <div className="cockpit-grid" data-testid="cockpit-seven-pane-grid">
        <Pane title="Overview" dense onInspect={() => openInspector({ title: "System Summary", subtitle: "Read-plane aggregate", body: inspectBody({ status: readyStatus, summary: "Overview tiles are derived from /healthz, /readyz, /ui/evidence, /ui/facade, /ui/operator-actions, and /ui/workboard.", warnings: anyError ? ["READ_PLANE_QUERY_DEGRADED"] : [], details: [{ k: "api", v: config.baseUrl }, { k: "frontend", v: frontendClaimed ? "CLAIMED" : "NOT_CLAIMED" }] }), rawJson: { readyBody, cockpit, facade: facade.data } })}>
          <div className="status-tile-grid">
            {overviewTiles.map((tile) => (
              <button
                key={tile.label}
                type="button"
                className={`status-tile status-tile--${metricTone(tile.status)}`}
                onClick={() => openInspector({ title: tile.label, subtitle: "Overview tile", body: inspectBody({ status: tile.status, summary: tile.hint, details: [{ k: "source", v: "read-plane" }] }), rawJson: tile.raw })}
              >
                <span>{tile.label}</span>
                <strong>{tile.status}</strong>
                <em>{tile.hint}</em>
              </button>
            ))}
          </div>
        </Pane>

        <Pane title="Readiness Matrix" dense onInspect={() => openInspector({ title: "Readiness Matrix", body: inspectBody({ status: readyStatus, summary: `${pass} PASS / ${warn} WARN / ${fail} FAIL / ${crit} CRIT`, warnings: warnings.map((w) => w.code), details: [{ k: "readiness_pct", v: `${readinessPct}%` }] }), rawJson: readyBody })}>
          <DenseTable
            columns={readinessColumns}
            rows={readinessRows.slice(0, 8)}
            rowKey={(r) => r.checkId}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.checkId);
              openInspector({ title: `Readiness · ${r.checkId}`, body: inspectBody({ status: r.status, summary: r.remediation, details: [{ k: "severity", v: r.severity }, { k: "blocker", v: r.blockerCode }] }), rawJson: r.raw });
            }}
            empty="UNKNOWN · no readiness checks returned"
          />
          <div className="pane-footer">PASS={pass} WARN={warn} FAIL={fail} CRIT={crit} READINESS={readinessPct}%</div>
        </Pane>

        <Pane title="Evidence Chain" dense onInspect={() => openInspector({ title: "Evidence Chain", body: inspectBody({ status: cockpit?.deployment_status ?? UNKNOWN, summary: `Chain Status: ${cockpit?.deployment_status ?? UNKNOWN}; Length: ${evidenceRows.length}`, details: [{ k: "digest", v: digest(registry?.projection_digest_sha256) }] }), rawJson: evidence.data, digestToCopy: asString(registry?.projection_digest_sha256) })}>
          <DenseTable
            columns={evidenceColumns}
            rows={evidenceRows}
            rowKey={(r) => r.step}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.step);
              if (r.digest !== "PENDING") setLastDigest(r.digest);
              openInspector({ title: `Evidence · ${r.step}`, body: inspectBody({ status: r.status, summary: `Evidence step ${r.step} at ${r.time}`, details: [{ k: "digest", v: r.digest }] }), rawJson: r.raw, digestToCopy: r.digest !== "PENDING" ? r.digest : undefined });
            }}
          />
          <div className="pane-footer">CHAIN_STATUS={cockpit?.deployment_status ?? UNKNOWN} LENGTH={evidenceRows.length}</div>
        </Pane>

        <Pane title="Provider Matrix" dense onInspect={() => openInspector({ title: "Provider Matrix", body: inspectBody({ status: providerWarnings ? "DEGRADED" : "OK", summary: `${providerRows.length} provider rows; Alpaca execution constraints highlighted when present.`, warnings: providerWarnings ? [`PROVIDER_WARNINGS=${providerWarnings}`] : [] }), rawJson: providers.data })}>
          <DenseTable
            columns={providerColumns}
            rows={providerRows.slice(0, 8)}
            rowKey={(r) => r.__id}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.__id);
              const exec = asRecord(r.execution_posture);
              const rowWarnings = [
                ...((Array.isArray(r.warnings) ? r.warnings : []) as string[]),
                ...((Array.isArray(exec?.execution_policy_blockers) ? exec?.execution_policy_blockers : []) as string[]),
              ];
              openInspector({ title: `Provider · ${asString(r.display_name) ?? r.__id}`, subtitle: r.__id === "alpaca" ? "Alpaca execution posture is explicitly surfaced" : undefined, body: inspectBody({ status: asString(r.classified_status) ?? UNKNOWN, summary: `${value(r.access_type)} · ${value(r.trust_level)} · ${value(r.pit_suitability)}`, warnings: rowWarnings, details: [{ k: "http", v: value(r.http_status, "PENDING") }, { k: "configured", v: value(r.configured) }, { k: "reachable", v: value(r.reachable) }] }), rawJson: r, digestToCopy: asString(r.sample_digest_prefix) });
            }}
            empty="UNKNOWN · provider health unavailable"
          />
        </Pane>

        <Pane title="Ledger / Operator Actions" dense onInspect={() => openInspector({ title: "Ledger / Operator Actions", body: inspectBody({ status: boolStatus(asBool(asRecord(operatorIdx.data)?.chain_ok), "LEDGER_OK", "DEGRADED"), summary: `Events=${value(asRecord(operatorIdx.data)?.event_count, "0")} latest=${actionRows.length ? digest(actionRows[actionRows.length - 1].event_hash) : "PENDING"}`, details: [{ k: "immutable", v: asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "YES" : "NO" }] }), rawJson: operatorIdx.data })}>
          <TermKV rows={[{ k: "events", v: value(asRecord(operatorIdx.data)?.event_count, "0") }, { k: "latest_digest", v: actionRows.length ? digest(actionRows[actionRows.length - 1].event_hash) : "PENDING" }, { k: "chain_status", v: boolStatus(asBool(asRecord(operatorIdx.data)?.chain_ok), "OK", "DEGRADED") }, { k: "immutable", v: asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "YES" : "NO" }]} />
          <DenseTable
            columns={actionColumns}
            rows={actionRows}
            rowKey={(r) => r.__id}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.__id);
              const h = asString(r.event_hash);
              if (h) setLastDigest(h);
              openInspector({ title: `Action · ${asString(r.action) ?? UNKNOWN}`, body: inspectBody({ status: asString(r.status) ?? "PENDING", summary: `Actor ${asString(r.operator_id) ?? UNKNOWN} targeted ${asString(r.target) ?? "PENDING"}.`, details: [{ k: "time", v: entryTime(r) }, { k: "digest", v: digest(h) }] }), rawJson: r, digestToCopy: h ?? undefined });
            }}
            empty="PENDING · no operator actions returned"
          />
        </Pane>

        <Pane title="Workboard" dense onInspect={() => openInspector({ title: "Workboard", body: inspectBody({ status: workboard.data?.stats.freshness_state ?? UNKNOWN, summary: `Active=${workboard.data?.stats.active_count ?? "UNKNOWN"} Governed=${workboard.data?.stats.governed_count ?? "UNKNOWN"} Journaled=${workboard.data?.stats.journaled_count ?? "UNKNOWN"}`, details: [{ k: "items", v: String(wbCount ?? "UNKNOWN") }] }), rawJson: workboard.data })}>
          {workboard.data && (
            <TermKV rows={[{ k: "active", v: String(workboard.data.stats.active_count) }, { k: "governed", v: String(workboard.data.stats.governed_count) }, { k: "journaled", v: String(workboard.data.stats.journaled_count) }, { k: "freshness", v: <StatusBadge raw={workboard.data.stats.freshness_state} /> }, { k: "items", v: String(wbCount ?? UNKNOWN) }]} />
          )}
          <div className="pane-subtitle">STRATEGY TESTS</div>
          {(workboard.data?.stats.journaled_count ?? 0) === 0 && strategyRows.length > 0 && (
            <p className="muted" style={{ fontSize: "11px", margin: "0 0 0.5rem", lineHeight: 1.35 }}>
              Ranked list is driven by the operator queue: you always have at least the primary governed item. Extra rows require{" "}
              <code style={{ fontSize: "10px" }}>STRATEGY_VALIDATOR_LEDGER_DB_PATH</code> plus accepted actions in the operator journal (see QUEUE below).
            </p>
          )}
          <DenseTable
            columns={strategyColumns}
            rows={strategyRows}
            rowKey={(r) => r.__id}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.__id);
              const readiness = asRecord(r.command_readiness);
              const brief = asRecord(r.operator_brief);
              openInspector({
                title: `Strategy/Test · ${digest(r.work_item_key)}`,
                subtitle: asString(r.review_target) ?? "workboard ranked item",
                body: inspectBody({
                  status: asString(r.attention_state) ?? UNKNOWN,
                  summary: asString(brief?.summary_line) ?? asString(r.recommended_action) ?? "No strategy/test summary supplied.",
                  warnings: [asString(r.blocking_reason), asString(asRecord(r.policy_recommendation)?.operator_line)].filter((x): x is string => !!x),
                  details: [
                    { k: "priority_score", v: value(r.priority_score ?? r.score, "0") },
                    { k: "top_action", v: asString(readiness?.top_action) ?? "PENDING" },
                    { k: "ready/caution/blocked", v: `${value(readiness?.ready_count, "0")}/${value(readiness?.caution_count, "0")}/${value(readiness?.blocked_count, "0")}` },
                  ],
                }),
                rawJson: r,
              });
            }}
            empty="PENDING · no ranked strategy/test items"
          />
          <div className="pane-subtitle">QUEUE</div>
          <DenseTable
            columns={workColumns}
            rows={workRows}
            rowKey={(r) => r.__id}
            selectedKey={selectedKey}
            onRowClick={(r) => {
              setSelectedKey(r.__id);
              openInspector({ title: `Work item · ${asString(r.work_item_key) ?? r.__id}`, body: inspectBody({ status: asString(r.status) ?? UNKNOWN, summary: asString(r.summary_line) ?? asString(r.title) ?? "No work item summary supplied.", details: [{ k: "owner", v: asString(r.owner) ?? "PENDING" }, { k: "updated", v: asString(r.updated_at_utc) ?? "PENDING" }] }), rawJson: r });
            }}
            empty="PENDING · no queue entries"
          />
        </Pane>

        <Pane title="Runtime" dense onInspect={() => openInspector({ title: "Runtime / Facade", body: inspectBody({ status: asString(readPlane?.status) ?? UNKNOWN, summary: "Backend package detection does not mean browser frontend is absent. Frontend readiness remains not claimed. Read-plane mode remains active. GPU hardware detection is separate from CUDA acceleration readiness.", details: [{ k: "routes", v: String(facade.data?.routes?.length ?? UNKNOWN) }, { k: "frontend_readiness_claimed", v: String(facade.data?.frontend_readiness_claimed ?? false) }, { k: "gpu_hardware_detected", v: String(gpuProbe?.gpu_hardware_detected ?? UNKNOWN) }, { k: "gpu_acceleration_ready", v: String(researchBody?.gpu_available ?? false) }] }), rawJson: { runtime: runtime.data, facade: facade.data, root: apiRoot.data, research_compute: researchCompute.data } })}>
          <TermKV
            rows={[
              { k: "schema_read", v: asString(runtimeBody?.schema_version) ?? UNKNOWN },
              { k: "schema_write", v: "NO_MUTATIONS" },
              { k: "facade_routes", v: String(facade.data?.routes?.length ?? UNKNOWN) },
              { k: "read_plane_only", v: String(facade.data?.read_plane_only ?? UNKNOWN) },
              { k: "frontend_readiness_claimed", v: String(facade.data?.frontend_readiness_claimed ?? false) },
              { k: "frontend_package_detected_by_backend", v: String(facade.data?.frontend_package_detected_by_backend ?? facade.data?.frontend_package_present ?? UNKNOWN) },
              { k: "runtime_mode", v: asString(runtimeBody?.environment) ?? asString(backend?.base_mode) ?? UNKNOWN },
              { k: "gpu_hardware_detected", v: String(gpuProbe?.gpu_hardware_detected ?? UNKNOWN) },
              { k: "gpu_name", v: asString(gpuHardware?.name) ?? "UNKNOWN" },
              { k: "gpu_memory_mib", v: value(gpuHardware?.memory_total_mib, "UNKNOWN") },
              { k: "gpu_acceleration_ready", v: String(researchBody?.gpu_available ?? false) },
              { k: "cuda_available", v: String(gpuProbe?.cuda_available ?? UNKNOWN) },
              { k: "compute_backend", v: asString(gpuProbe?.backend) ?? UNKNOWN },
              { k: "uptime", v: asString(runtimeBody?.uptime) ?? "PENDING" },
            ]}
          />
          <p className="runtime-note">backend package detection does not mean browser frontend is absent; frontend readiness remains not claimed; read-plane mode remains active</p>
        </Pane>
      </div>
    </div>
  );
}
