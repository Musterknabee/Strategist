"use client";

import type { ReactNode } from "react";
import { Fragment, useMemo, useState } from "react";
import { useProbeApiRoot } from "@/hooks/useProbeApiRoot";
import { useProbeHealthz } from "@/hooks/useProbeHealthz";
import { useProbeLivez } from "@/hooks/useProbeLivez";
import { useProbeReadyz } from "@/hooks/useProbeReadyz";
import { useReadinessDeployment } from "@/hooks/useReadinessDeployment";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiEvidence } from "@/hooks/useUiEvidence";
import { useUiEvidenceChain } from "@/hooks/useUiEvidenceChain";
import { useUiFacade } from "@/hooks/useUiFacade";
import { useUiOperatorActions } from "@/hooks/useUiOperatorActions";
import { useUiProviderHealth } from "@/hooks/useUiProviderHealth";
import { useUiProviderSetup } from "@/hooks/useUiProviderSetup";
import { useUiPaperExecutionCockpit } from "@/hooks/useUiPaperExecution";
import { useUiPaperBrokerStatus } from "@/hooks/useUiPaperBroker";
import { useUiResearchCompute } from "@/hooks/useUiResearchCompute";
import { useUiResearchOsHandoffLatest } from "@/hooks/useUiResearchOsHandoff";
import { useUiResearchOsHandoffSignoffLatest } from "@/hooks/useUiResearchOsHandoffSignoff";
import { useUiResearchOsReleaseReadinessLatest } from "@/hooks/useUiResearchOsReleaseReadiness";
import { useUiResearchOsReviewJournalLatest } from "@/hooks/useUiResearchOsReviewJournal";
import { useUiResearchOsExportLatest } from "@/hooks/useUiResearchOsExport";
import { useUiResearchOsDriftLatest } from "@/hooks/useUiResearchOsDrift";
import { useUiResearchOsExceptionLatest } from "@/hooks/useUiResearchOsException";
import { useUiResearchOsPolicyGateLatest } from "@/hooks/useUiResearchOsPolicyGate";
import { useUiResearchOsRemediationLatest } from "@/hooks/useUiResearchOsRemediation";
import { useUiResearchOsStatus } from "@/hooks/useUiResearchOsStatus";
import { useUiRuntime } from "@/hooks/useUiRuntime";
import { useUiShadowBookLatest } from "@/hooks/useUiShadowBook";
import { useUiStrategyBatches, useUiStrategyBatchesLatest } from "@/hooks/useUiStrategyBatches";
import { useUiStrategyGraveyardLatest } from "@/hooks/useUiStrategyGraveyard";
import { useUiStrategyMemoryLatest } from "@/hooks/useUiStrategyMemory";
import { useUiStrategyIntakeLatest } from "@/hooks/useUiStrategyIntake";
import { useUiStrategyThesisGenerationLatest, useUiStrategyThesisLatest } from "@/hooks/useUiStrategyThesis";
import { useUiSurfaceHealth } from "@/hooks/useUiSurfaceHealth";
import { useUiWorkboard } from "@/hooks/useUiWorkboard";
import { useUiBacktestForensicsLatest } from "@/hooks/useUiBacktestForensics";
import { useUiPaperTrackingLatest } from "@/hooks/useUiPaperTracking";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { chainIntegrityLabel } from "@/lib/operator/evidence-provenance-map";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  asStringArray,
  classifyProviderClassifiedStatus,
  readinessBlockerRows,
  readinessCheckRows,
  workboardQueueItemCount,
} from "@/lib/operator/payload-utils";
import {
  buildPaperExecutionEvidenceRows,
  buildResearchOsEvidenceRows,
  researchOsAggregateDigest,
} from "@/lib/operator/cockpit-evidence-drilldown-rows";
import { parseMutationSafety } from "@/lib/operator/operator-mutation-guard";
import { readUiEvidenceCockpit } from "@/lib/operator/ui-evidence-cockpit";
import uiFacadeRoutesContract from "@/lib/contracts/ui-facade-routes.json";
import { buildSystemTopology, type FacadeRoutesContract } from "@/lib/operator/system-topology-model";
import {
  deriveOperatorModeNextFocusLines,
  getOperatorModeDefinition,
  getPostGridSectionOrder,
  modeShowsOperatorCommandPane,
  type CockpitPostGridSectionKey,
  type OperatorModeFocusContext,
  type OperatorModeId,
} from "@/lib/operator/operator-modes";
import type { OperatorHealthAlertsInput } from "@/lib/operator/operator-health-alerts-model";
import type { RemediationGovernanceInput } from "@/lib/operator/remediation-governance-model";
import type { UiWorkboardQueueEntry } from "@/lib/api/types";
import { useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import type { InspectorPayload, TapeLine } from "@/lib/terminal/cockpit-context";
import {
  FirstRunDeploymentCockpitPane,
  deploymentCodesFromPayload,
} from "./FirstRunDeploymentCockpitPane";
import { ProviderSetupReadinessPane } from "./ProviderSetupReadinessPane";
import { ResearchBatchForensicsPane } from "./ResearchBatchForensicsPane";
import { ReleaseControlPane } from "./ReleaseControlPane";
import { EvidenceRunbookPane } from "./EvidenceRunbookPane";
import { AuditForensicPane } from "./AuditForensicPane";
import { PolicyRiskGatesPane } from "./PolicyRiskGatesPane";
import { PromotionEvidenceDossierPane } from "./PromotionEvidenceDossierPane";
import { StrategyLifecyclePane } from "./StrategyLifecyclePane";
import { EvidenceChainPane } from "./EvidenceChainPane";
import { OperatorActionsPane } from "./OperatorActionsPane";
import { OperatorCommandCockpitPane } from "./OperatorCommandCockpitPane";
import { PaperExecutionEvidenceDrilldownPane } from "./PaperExecutionEvidenceDrilldownPane";
import { CapitalExecutionFirewallPane } from "./CapitalExecutionFirewallPane";
import { OperatorHealthAlertsPane } from "./OperatorHealthAlertsPane";
import { RemediationGovernancePane } from "./RemediationGovernancePane";
import { OverviewPane } from "./OverviewPane";
import { ProviderMatrixPane } from "./ProviderMatrixPane";
import { ReadinessMatrixPane } from "./ReadinessMatrixPane";
import { ResearchOsEvidenceDrilldownPane } from "./ResearchOsEvidenceDrilldownPane";
import { RuntimePane } from "./RuntimePane";
import type { FirstRunChecklistInput } from "@/lib/operator/first-run-deployment-checklist";
import type { PaneEvidenceProvenance } from "./cockpit-provenance-types";
import type {
  ActionRow,
  EvidenceRow,
  MatrixRow,
  OverviewTile,
  ProviderRow,
  StrategyRow,
  WorkRow,
} from "./cockpit-types";
import { UNKNOWN, boolStatus, digest, entryTime, inspectBody, value } from "./cockpit-utils";
import { WorkboardPane } from "./WorkboardPane";
import { SystemTopologyPane } from "./SystemTopologyPane";
import { OperatorModeSwitchboard } from "./OperatorModeSwitchboard";

export function CockpitPageShell() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const apiBaseDisplay = config.ok ? config.baseUrl : UNKNOWN;
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const facade = useUiFacade();
  const apiRoot = useProbeApiRoot();
  const healthz = useProbeHealthz();
  const livez = useProbeLivez();
  const readyz = useProbeReadyz();
  const deploymentReadiness = useReadinessDeployment();
  const providerSetup = useUiProviderSetup();
  const uiHealth = useUiSurfaceHealth();
  const workboard = useUiWorkboard("operator");
  const providers = useUiProviderHealth();
  const evidence = useUiEvidence(undefined);
  const evidenceChain = useUiEvidenceChain();
  const operatorIdx = useUiOperatorActions();
  const runtime = useUiRuntime("operator");
  const researchCompute = useUiResearchCompute();
  const researchOsStatus = useUiResearchOsStatus();
  const paperExecution = useUiPaperExecutionCockpit();
  const paperBroker = useUiPaperBrokerStatus();
  const strategyBatchLatest = useUiStrategyBatchesLatest();
  const strategyBatches = useUiStrategyBatches();
  const backtestForensicsLatest = useUiBacktestForensicsLatest();
  const paperTrackingLatest = useUiPaperTrackingLatest();
  const strategyGraveyardLatest = useUiStrategyGraveyardLatest();
  const strategyMemoryLatest = useUiStrategyMemoryLatest();
  const strategyThesisLatest = useUiStrategyThesisLatest();
  const strategyThesisGenerationLatest = useUiStrategyThesisGenerationLatest();
  const strategyIntakeLatest = useUiStrategyIntakeLatest();
  const shadowBookLatest = useUiShadowBookLatest();
  const releaseReadinessLatest = useUiResearchOsReleaseReadinessLatest();
  const researchOsHandoffLatest = useUiResearchOsHandoffLatest();
  const researchOsHandoffSignoffLatest = useUiResearchOsHandoffSignoffLatest();
  const researchOsReviewJournalLatest = useUiResearchOsReviewJournalLatest();
  const researchOsExportLatest = useUiResearchOsExportLatest();
  const researchOsDriftLatest = useUiResearchOsDriftLatest();
  const researchOsExceptionLatest = useUiResearchOsExceptionLatest();
  const researchOsRemediationLatest = useUiResearchOsRemediationLatest();
  const researchOsPolicyGateLatest = useUiResearchOsPolicyGateLatest();
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [operatorMode, setOperatorMode] = useState<OperatorModeId>("DAILY_OPS");

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

  const providerWarnings = useMemo(
    () => providerRows.filter((r) => classifyProviderClassifiedStatus(asString(r.classified_status)) !== "ok").length,
    [providerRows],
  );

  const frontendClaimed = facade.data?.frontend_readiness_claimed === true;

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
    researchCompute.isError ||
    researchOsStatus.isError ||
    paperExecution.isError ||
    paperBroker.isError ||
    strategyBatchLatest.isError ||
    strategyBatches.isError ||
    backtestForensicsLatest.isError ||
    paperTrackingLatest.isError ||
    strategyGraveyardLatest.isError ||
    strategyMemoryLatest.isError ||
    strategyThesisLatest.isError ||
    strategyThesisGenerationLatest.isError ||
    strategyIntakeLatest.isError ||
    shadowBookLatest.isError ||
    deploymentReadiness.isError ||
    providerSetup.isError ||
    evidenceChain.isError ||
    releaseReadinessLatest.isError ||
    researchOsHandoffLatest.isError ||
    researchOsHandoffSignoffLatest.isError ||
    researchOsReviewJournalLatest.isError ||
    researchOsExportLatest.isError ||
    researchOsDriftLatest.isError ||
    researchOsExceptionLatest.isError ||
    researchOsRemediationLatest.isError ||
    researchOsPolicyGateLatest.isError;

  const rosStatusRec = researchOsStatus.data != null ? asRecord(researchOsStatus.data) : null;
  const paperExecRec = paperExecution.data != null ? asRecord(paperExecution.data) : null;
  const paperBrokerRec = paperBroker.data != null ? asRecord(paperBroker.data) : null;

  const researchOsRows = useMemo(() => buildResearchOsEvidenceRows(rosStatusRec), [rosStatusRec]);
  const paperExecutionRows = useMemo(() => buildPaperExecutionEvidenceRows(paperExecRec), [paperExecRec]);

  const researchOsProvenance = useMemo((): PaneEvidenceProvenance => {
    const dig = researchOsAggregateDigest(rosStatusRec);
    const topBlk = Array.isArray(rosStatusRec?.degraded) ? rosStatusRec.degraded.length : 0;
    const topWrn = Array.isArray(rosStatusRec?.warnings) ? rosStatusRec.warnings.length : 0;
    const closure = asRecord(rosStatusRec?.research_os_closure_latest);
    const latest = closure != null ? asRecord(closure.latest) : null;
    return {
      sourceLabel: "READ · /ui/research-os/status (nested latest payloads)",
      schemaVersion: asString(rosStatusRec?.schema_version),
      generatedAtUtc: asString(rosStatusRec?.generated_at_utc),
      digestPreview: digest(dig),
      digestFull: dig,
      trustStatus: asString(latest?.trust_banner),
      projectionSnapshotVerified: asBool(rosStatusRec?.read_plane_only) ?? null,
      freshnessStatus: topBlk > 0 ? "DEGRADED" : "CURRENT",
      blockerCount: topBlk,
      warningCount: topWrn,
      supplementalLine: asString(asRecord(rosStatusRec?.artifact_root_summary)?.artifact_root)?.slice(0, 120),
    };
  }, [rosStatusRec]);

  const paperExecutionProvenance = useMemo((): PaneEvidenceProvenance => {
    const summary = paperExecRec ? asRecord(paperExecRec.summary) : null;
    const dig =
      asString(summary?.latest_evidence_bundle_sha256) ??
      asString(asRecord(paperExecRec?.latest_evidence_bundle)?.artifact_sha256);
    const blk =
      (typeof summary?.submission_guard_blocker_count === "number" ? summary.submission_guard_blocker_count : 0) +
      (typeof summary?.evidence_bundle_blocker_count === "number" ? summary.evidence_bundle_blocker_count : 0) +
      (typeof summary?.timeline_blocker_count === "number" ? summary.timeline_blocker_count : 0) +
      (typeof summary?.evidence_freshness_blocker_count === "number" ? summary.evidence_freshness_blocker_count : 0);
    const wrn =
      (typeof summary?.timeline_warning_count === "number" ? summary.timeline_warning_count : 0) +
      (typeof summary?.position_reconciliation_warning_count === "number" ? summary.position_reconciliation_warning_count : 0);
    return {
      sourceLabel: "READ · /ui/paper-execution/latest",
      schemaVersion: asString(paperExecRec?.schema_version),
      generatedAtUtc: asString(paperExecRec?.generated_at_utc),
      digestPreview: digest(dig),
      digestFull: dig,
      trustStatus: asString(summary?.latest_evidence_bundle_trust_banner),
      projectionSnapshotVerified: asBool(paperExecRec?.read_plane_only) ?? null,
      freshnessStatus: asString(summary?.evidence_freshness_status) ?? UNKNOWN,
      blockerCount: blk,
      warningCount: wrn,
      supplementalLine: (() => {
        const cap = asString(summary?.paper_submission_capability);
        if (!cap) return paperExecRec?.no_live_trading === true ? "PAPER_ONLY" : undefined;
        return paperExecRec?.no_live_trading === true ? `${cap} · PAPER_ONLY` : cap;
      })(),
    };
  }, [paperExecRec]);

  const researchOsInspectorPayload = useMemo((): InspectorPayload => {
    return {
      title: "Research OS status",
      subtitle: "Aggregated read-plane status",
      body: inspectBody({
        status: rosStatusRec && Array.isArray(rosStatusRec.degraded) && rosStatusRec.degraded.length ? "DEGRADED" : "OK",
        summary:
          "Single GET /ui/research-os/status embeds closure, attestation, drift, policy gate, release readiness, exceptions, and remediation latest payloads.",
        warnings: Array.isArray(rosStatusRec?.degraded) ? (rosStatusRec.degraded as string[]).slice(0, 12) : [],
        details: [{ k: "read_plane_only", v: String(rosStatusRec?.read_plane_only ?? UNKNOWN) }],
      }),
      rawJson: rosStatusRec ?? {},
      digestToCopy: researchOsAggregateDigest(rosStatusRec),
    };
  }, [rosStatusRec]);

  const paperExecutionInspectorPayload = useMemo((): InspectorPayload => {
    const summary = paperExecRec ? asRecord(paperExecRec.summary) : null;
    return {
      title: "Paper execution cockpit",
      subtitle: "Read-plane evidence (no browser orders)",
      body: inspectBody({
        status: asString(summary?.broker_policy_status) ?? UNKNOWN,
        summary: "Dry-run, submission receipts, evidence bundles, verification, drift, attestation, closure, and retention views.",
        details: [
          { k: "no_live_trading", v: String(paperExecRec?.no_live_trading ?? UNKNOWN) },
          { k: "no_browser_orders", v: String(paperExecRec?.no_browser_orders ?? UNKNOWN) },
        ],
      }),
      rawJson: paperExecRec ?? {},
      digestToCopy: asString(summary?.latest_evidence_bundle_sha256),
    };
  }, [paperExecRec]);

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

  const selectedWorkCommandTarget = useMemo((): UiWorkboardQueueEntry | null => {
    const row = workRows.find((w) => w.__id === selectedKey);
    return row ?? null;
  }, [workRows, selectedKey]);

  const cockpitMutationSafety = useMemo(() => parseMutationSafety(runtimeBody?.mutation_safety), [runtimeBody]);

  const operatorHealthInput = useMemo((): OperatorHealthAlertsInput => {
    return {
      healthz: { data: healthz.data ?? null, isError: healthz.isError, isLoading: healthz.isLoading },
      livez: { httpStatus: livez.data?.httpStatus, isError: livez.isError, isLoading: livez.isLoading },
      readyz: {
        httpStatus: readyz.data?.httpStatus,
        body: readyBody,
        isError: readyz.isError,
        isLoading: readyz.isLoading,
      },
      runtimeBody,
      runtimeError: runtime.isError,
      runtimeLoading: runtime.isLoading,
      mutationSafety: cockpitMutationSafety,
      evidencePayload: ev,
      evidenceError: evidence.isError,
      evidenceLoading: evidence.isLoading,
      cockpit: readUiEvidenceCockpit(ev),
      evidenceChain: {
        data: evidenceChain.data ?? null,
        isError: evidenceChain.isError,
        isLoading: evidenceChain.isLoading,
      },
      providerSetup: {
        data: providerSetup.data ?? null,
        isError: providerSetup.isError,
        isLoading: providerSetup.isLoading,
      },
      providerHealth: providers.data != null ? asRecord(providers.data) : null,
      providerHealthError: providers.isError,
      deploymentReadiness: deploymentReadiness.data != null ? asRecord(deploymentReadiness.data) : null,
      deploymentReadinessError: deploymentReadiness.isError,
      deploymentReadinessLoading: deploymentReadiness.isLoading,
      facade: facade.data != null ? asRecord(facade.data as unknown) : null,
      facadeError: facade.isError,
      facadeLoading: facade.isLoading,
      releaseReadiness: releaseReadinessLatest.data != null ? asRecord(releaseReadinessLatest.data) : null,
      releaseReadinessError: releaseReadinessLatest.isError,
      releaseReadinessLoading: releaseReadinessLatest.isLoading,
      researchOsDrift: researchOsDriftLatest.data != null ? asRecord(researchOsDriftLatest.data) : null,
      researchOsDriftError: researchOsDriftLatest.isError,
      researchOsDriftLoading: researchOsDriftLatest.isLoading,
      paperExecution: paperExecRec,
      paperExecutionError: paperExecution.isError,
      paperBroker: paperBrokerRec,
      paperBrokerError: paperBroker.isError,
    };
  }, [
    healthz.data,
    healthz.isError,
    healthz.isLoading,
    livez.data?.httpStatus,
    livez.isError,
    livez.isLoading,
    readyz.data?.httpStatus,
    readyBody,
    readyz.isError,
    readyz.isLoading,
    runtimeBody,
    runtime.isError,
    runtime.isLoading,
    cockpitMutationSafety,
    ev,
    evidence.isError,
    evidence.isLoading,
    evidenceChain.data,
    evidenceChain.isError,
    evidenceChain.isLoading,
    providerSetup.data,
    providerSetup.isError,
    providerSetup.isLoading,
    providers.data,
    providers.isError,
    deploymentReadiness.data,
    deploymentReadiness.isError,
    deploymentReadiness.isLoading,
    facade.data,
    facade.isError,
    facade.isLoading,
    releaseReadinessLatest.data,
    releaseReadinessLatest.isError,
    releaseReadinessLatest.isLoading,
    researchOsDriftLatest.data,
    researchOsDriftLatest.isError,
    researchOsDriftLatest.isLoading,
    paperExecRec,
    paperExecution.isError,
    paperBrokerRec,
    paperBroker.isError,
  ]);

  const remediationGovernanceInput = useMemo((): RemediationGovernanceInput => {
    const ps = providerSetup.data;
    const sm = ps?.summary;
    const havePs = !providerSetup.isLoading && !providerSetup.isError && sm != null;
    return {
      readyzBody: readyBody,
      readyzLoading: readyz.isLoading,
      readyzError: readyz.isError,
      deployment: deploymentReadiness.data != null ? asRecord(deploymentReadiness.data) : null,
      deploymentLoading: deploymentReadiness.isLoading,
      deploymentError: deploymentReadiness.isError,
      policyGatePayload: researchOsPolicyGateLatest.data ?? null,
      policyGateLoading: researchOsPolicyGateLatest.isLoading,
      policyGateError: researchOsPolicyGateLatest.isError,
      exceptionPayload: researchOsExceptionLatest.data ?? null,
      exceptionLoading: researchOsExceptionLatest.isLoading,
      exceptionError: researchOsExceptionLatest.isError,
      remediationPayload: researchOsRemediationLatest.data ?? null,
      remediationLoading: researchOsRemediationLatest.isLoading,
      remediationError: researchOsRemediationLatest.isError,
      drift: researchOsDriftLatest.data != null ? asRecord(researchOsDriftLatest.data) : null,
      driftLoading: researchOsDriftLatest.isLoading,
      driftError: researchOsDriftLatest.isError,
      releaseReadiness: releaseReadinessLatest.data != null ? asRecord(releaseReadinessLatest.data) : null,
      releaseLoading: releaseReadinessLatest.isLoading,
      releaseError: releaseReadinessLatest.isError,
      reviewJournal: researchOsReviewJournalLatest.data != null ? asRecord(researchOsReviewJournalLatest.data) : null,
      reviewJournalLoading: researchOsReviewJournalLatest.isLoading,
      reviewJournalError: researchOsReviewJournalLatest.isError,
      providerStaleCount: havePs ? asNumber(sm.stale_count) ?? 0 : null,
      providerBlockedCount: havePs ? asNumber(sm.blocked_count) ?? 0 : null,
    };
  }, [
    readyBody,
    readyz.isLoading,
    readyz.isError,
    deploymentReadiness.data,
    deploymentReadiness.isLoading,
    deploymentReadiness.isError,
    researchOsPolicyGateLatest.data,
    researchOsPolicyGateLatest.isLoading,
    researchOsPolicyGateLatest.isError,
    researchOsExceptionLatest.data,
    researchOsExceptionLatest.isLoading,
    researchOsExceptionLatest.isError,
    researchOsRemediationLatest.data,
    researchOsRemediationLatest.isLoading,
    researchOsRemediationLatest.isError,
    researchOsDriftLatest.data,
    researchOsDriftLatest.isLoading,
    researchOsDriftLatest.isError,
    releaseReadinessLatest.data,
    releaseReadinessLatest.isLoading,
    releaseReadinessLatest.isError,
    researchOsReviewJournalLatest.data,
    researchOsReviewJournalLatest.isLoading,
    researchOsReviewJournalLatest.isError,
    providerSetup.data,
    providerSetup.isLoading,
    providerSetup.isError,
  ]);

  const firstRunInput: FirstRunChecklistInput = useMemo(() => {
    const cockpitFields = readUiEvidenceCockpit(ev);
    return {
      deployment: {
        data: deploymentReadiness.data ?? undefined,
        isLoading: deploymentReadiness.isLoading,
        isError: deploymentReadiness.isError,
      },
      readyz: {
        httpStatus: readyz.data?.httpStatus,
        body: readyBody,
        isError: readyz.isError,
        isLoading: readyz.isLoading,
      },
      healthz: {
        isError: healthz.isError,
        isLoading: healthz.isLoading,
        data: healthz.data ?? null,
      },
      livez: {
        httpStatus: livez.data?.httpStatus,
        isError: livez.isError,
        isLoading: livez.isLoading,
      },
      facade: {
        data: facade.data ?? null,
        isError: facade.isError,
      },
      mutationSafety: cockpitMutationSafety,
      cockpit: cockpitFields,
      evidencePayload: ev,
      providerSetup: {
        data: providerSetup.data ?? null,
        isError: providerSetup.isError,
        isLoading: providerSetup.isLoading,
      },
      evidenceChain: {
        data: evidenceChain.data ?? null,
        isError: evidenceChain.isError,
        isLoading: evidenceChain.isLoading,
      },
    };
  }, [
    deploymentReadiness.data,
    deploymentReadiness.isLoading,
    deploymentReadiness.isError,
    readyz.data?.httpStatus,
    readyz.isError,
    readyz.isLoading,
    readyBody,
    healthz.isError,
    healthz.isLoading,
    healthz.data,
    livez.data?.httpStatus,
    livez.isError,
    livez.isLoading,
    facade.data,
    facade.isError,
    cockpitMutationSafety,
    ev,
    providerSetup.data,
    providerSetup.isError,
    providerSetup.isLoading,
    evidenceChain.data,
    evidenceChain.isError,
    evidenceChain.isLoading,
  ]);

  const deploymentTierCodes = useMemo(
    () => deploymentCodesFromPayload(deploymentReadiness.data),
    [deploymentReadiness.data],
  );

  const paneTopologyDegraded = useMemo(
    () => ({
      overview:
        facade.isError ||
        healthz.isError ||
        readyz.isError ||
        evidence.isError ||
        operatorIdx.isError ||
        workboard.isError,
      "readiness-matrix": readyz.isError || deploymentReadiness.isError,
      "evidence-chain": evidenceChain.isError,
      "operator-health-alerts":
        healthz.isError ||
        livez.isError ||
        readyz.isError ||
        runtime.isError ||
        evidence.isError ||
        evidenceChain.isError ||
        facade.isError ||
        deploymentReadiness.isError ||
        providerSetup.isError ||
        providers.isError ||
        releaseReadinessLatest.isError ||
        researchOsDriftLatest.isError ||
        paperExecution.isError ||
        paperBroker.isError,
      "capital-firewall":
        paperExecution.isError ||
        paperBroker.isError ||
        paperTrackingLatest.isError ||
        providerSetup.isError ||
        providers.isError,
      "remediation-governance":
        readyz.isError ||
        deploymentReadiness.isError ||
        researchOsPolicyGateLatest.isError ||
        researchOsExceptionLatest.isError ||
        researchOsRemediationLatest.isError ||
        researchOsDriftLatest.isError ||
        releaseReadinessLatest.isError ||
        researchOsReviewJournalLatest.isError ||
        providerSetup.isError,
      "first-run":
        deploymentReadiness.isError ||
        readyz.isError ||
        healthz.isError ||
        facade.isError ||
        providerSetup.isError ||
        evidenceChain.isError,
      "release-control":
        facade.isError ||
        evidence.isError ||
        evidenceChain.isError ||
        releaseReadinessLatest.isError ||
        researchOsHandoffLatest.isError ||
        researchOsHandoffSignoffLatest.isError ||
        researchOsReviewJournalLatest.isError,
      "provider-setup-readiness": providerSetup.isError || providers.isError,
    }),
    [
      facade.isError,
      healthz.isError,
      readyz.isError,
      evidence.isError,
      operatorIdx.isError,
      workboard.isError,
      deploymentReadiness.isError,
      evidenceChain.isError,
      livez.isError,
      runtime.isError,
      providerSetup.isError,
      providers.isError,
      releaseReadinessLatest.isError,
      researchOsDriftLatest.isError,
      paperExecution.isError,
      paperBroker.isError,
      paperTrackingLatest.isError,
      researchOsPolicyGateLatest.isError,
      researchOsExceptionLatest.isError,
      researchOsRemediationLatest.isError,
      researchOsHandoffLatest.isError,
      researchOsHandoffSignoffLatest.isError,
      researchOsReviewJournalLatest.isError,
    ],
  );

  const systemTopology = useMemo(
    () =>
      buildSystemTopology({
        contract: uiFacadeRoutesContract as FacadeRoutesContract,
        facadePayload: facade.data != null ? (facade.data as unknown as Record<string, unknown>) : null,
        paneDegraded: paneTopologyDegraded,
      }),
    [facade.data, paneTopologyDegraded],
  );

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
      {
        step: "Env Check",
        status: readyStatus,
        digest: digest(asString(readyBody?.config_fingerprint)),
        time: asString(readyBody?.checked_at_utc) ?? generated,
        raw: readyBody,
      },
      {
        step: "Preflight",
        status: boolStatus(cockpit?.deployment_evidence_ok, "OK", "DEGRADED"),
        digest: digest(registry?.projection_digest_sha256),
        time: generated,
        raw: verification,
      },
      {
        step: "Backup / Restore",
        status: boolStatus(cockpit?.backup_restore_ok, "OK", "PENDING"),
        digest: digest(registry?.projection_digest_sha256),
        time: generated,
        raw: cockpit,
      },
      {
        step: "API Smoke",
        status: boolStatus(cockpit?.api_smoke_ok, "OK", "DEGRADED"),
        digest: digest(registry?.projection_digest_sha256),
        time: generated,
        raw: cockpit,
      },
      {
        step: "Provider Evidence",
        status: providerRows.length ? "AVAILABLE" : UNKNOWN,
        digest: digest(asRecord(providers.data)?.samples_manifest_digest_prefix),
        time: asString(asRecord(providers.data)?.generated_at_utc) ?? generated,
        raw: providers.data,
      },
      {
        step: "Operator Sign-off",
        status: boolStatus(cockpit?.manual_operator_signoff_present, "SIGNED", "PENDING"),
        digest: digest(registry?.projection_digest_sha256),
        time: generated,
        raw: cockpit,
      },
    ];
  }, [cockpit, ev, providerRows.length, providers.data, readyBody, readyStatus, registry, verification]);

  const overviewProvenance = useMemo((): PaneEvidenceProvenance => {
    const facadeRec = asRecord(facade.data);
    const lineageRec = asRecord(ev?.lineage);
    const lineageWarn = asStringArray(lineageRec?.warnings).length;
    const integWarn = asStringArray(asRecord(verification)?.integrity_warnings).length;
    return {
      sourceLabel: "AGGREGATE · /ui/facade + /ui/evidence + /readyz",
      schemaVersion: asString(facadeRec?.schema_version) ?? asString(ev?.schema_version),
      generatedAtUtc: asString(ev?.generated_at_utc) ?? asString(readyBody?.checked_at_utc),
      digestPreview: digest(registry?.projection_digest_sha256),
      digestFull: asString(registry?.projection_digest_sha256),
      trustStatus: asString(verification?.trust_status),
      projectionSnapshotVerified: asBool(asRecord(verification)?.projection_snapshot_verified) ?? null,
      freshnessStatus: cockpit?.deployment_status ?? readyStatus,
      blockerCount: blockers.length,
      warningCount: warnings.length + lineageWarn + integWarn,
      supplementalLine: asString(verification?.lineage_reason)?.slice(0, 140) || undefined,
    };
  }, [facade.data, ev, readyBody, registry, verification, cockpit, readyStatus, blockers.length, warnings.length]);

  const evidenceChainProvenance = useMemo((): PaneEvidenceProvenance => {
    const lineageRec = asRecord(ev?.lineage);
    const lineageWarn = asStringArray(lineageRec?.warnings).length;
    const integWarn = asStringArray(asRecord(verification)?.integrity_warnings).length;
    const verified = asBool(asRecord(verification)?.projection_snapshot_verified);
    return {
      sourceLabel: "READ · /ui/evidence",
      schemaVersion: asString(ev?.schema_version),
      generatedAtUtc: asString(ev?.generated_at_utc),
      digestPreview: digest(registry?.projection_digest_sha256),
      digestFull: asString(registry?.projection_digest_sha256),
      trustStatus: asString(verification?.trust_status),
      projectionSnapshotVerified: verified ?? null,
      freshnessStatus: cockpit?.deployment_status ?? UNKNOWN,
      blockerCount: verified === false ? 1 : 0,
      warningCount: lineageWarn + integWarn,
      supplementalLine: asString(ev?.search_root) ?? undefined,
    };
  }, [ev, registry, verification, cockpit]);

  const providerProvenance = useMemo((): PaneEvidenceProvenance => {
    const p = asRecord(providers.data);
    const entries = p?.entries;
    const first = Array.isArray(entries) && entries.length > 0 ? asRecord(entries[0]) : null;
    const execBlockers = Array.isArray(p?.execution_workflow_blockers) ? p.execution_workflow_blockers.length : 0;
    const rowWarnAgg = providerRows.reduce((n, r) => n + (Array.isArray(r.warnings) ? r.warnings.length : 0), 0);
    return {
      sourceLabel: "READ · /ui/provider-health",
      schemaVersion: asString(p?.schema_version),
      generatedAtUtc: asString(p?.generated_at_utc),
      digestPreview: digest(p?.samples_manifest_digest_prefix),
      digestFull: asString(p?.samples_manifest_digest_prefix) ?? undefined,
      trustStatus: asString(first?.trust_level) ?? UNKNOWN,
      projectionSnapshotVerified: null,
      freshnessStatus: asString(first?.classified_status) ?? UNKNOWN,
      blockerCount: execBlockers,
      warningCount: providerWarnings + rowWarnAgg,
      supplementalLine: asString(p?.samples_manifest_path) ?? undefined,
    };
  }, [providers.data, providerRows, providerWarnings]);

  const operatorProvenance = useMemo((): PaneEvidenceProvenance => {
    const idx = asRecord(operatorIdx.data);
    const last = actionRows.length ? actionRows[actionRows.length - 1] : null;
    const h = last ? asString(last.event_hash) : undefined;
    const chainOk = asBool(idx?.chain_ok);
    const issueCount = asNumber(idx?.chain_issue_count);
    return {
      sourceLabel: "READ · /ui/operator-actions",
      schemaVersion: asString(idx?.schema_version),
      generatedAtUtc: last ? entryTime(last) : undefined,
      digestPreview: h ? digest(h) : undefined,
      digestFull: h,
      trustStatus: chainIntegrityLabel(chainOk, issueCount ?? 0),
      projectionSnapshotVerified: null,
      freshnessStatus: boolStatus(chainOk, "LIVE", "STALE"),
      blockerCount: issueCount ?? 0,
      warningCount: asNumber(idx?.rejected_event_count) ?? 0,
      supplementalLine: asString(idx?.read_model) ?? undefined,
    };
  }, [operatorIdx.data, actionRows]);

  const operatorHealthQueryFailed =
    healthz.isError ||
    livez.isError ||
    readyz.isError ||
    runtime.isError ||
    evidence.isError ||
    evidenceChain.isError ||
    facade.isError ||
    deploymentReadiness.isError ||
    providerSetup.isError ||
    providers.isError ||
    releaseReadinessLatest.isError ||
    researchOsDriftLatest.isError ||
    paperExecution.isError ||
    paperBroker.isError;

  const researchLifecycleQueryFailed =
    strategyIntakeLatest.isError ||
    strategyThesisLatest.isError ||
    strategyThesisGenerationLatest.isError ||
    strategyMemoryLatest.isError ||
    strategyGraveyardLatest.isError ||
    paperTrackingLatest.isError ||
    backtestForensicsLatest.isError ||
    strategyBatchLatest.isError ||
    workboard.isError ||
    evidenceChain.isError;

  const releaseControlQueryFailed =
    facade.isError ||
    evidence.isError ||
    evidenceChain.isError ||
    releaseReadinessLatest.isError ||
    researchOsHandoffLatest.isError ||
    researchOsHandoffSignoffLatest.isError ||
    researchOsReviewJournalLatest.isError;

  const remediationQueryFailed =
    readyz.isError ||
    deploymentReadiness.isError ||
    researchOsPolicyGateLatest.isError ||
    researchOsExceptionLatest.isError ||
    researchOsRemediationLatest.isError ||
    researchOsDriftLatest.isError ||
    releaseReadinessLatest.isError ||
    researchOsReviewJournalLatest.isError ||
    providerSetup.isError;

  const paperCapitalQueryFailed =
    paperExecution.isError ||
    paperBroker.isError ||
    paperTrackingLatest.isError ||
    providerSetup.isError ||
    providers.isError;

  const auditForensicQueryFailed =
    evidenceChain.isError ||
    operatorIdx.isError ||
    evidence.isError ||
    releaseReadinessLatest.isError ||
    researchOsHandoffLatest.isError ||
    researchOsHandoffSignoffLatest.isError ||
    researchOsReviewJournalLatest.isError ||
    researchOsExportLatest.isError ||
    researchOsDriftLatest.isError ||
    paperExecution.isError;

  const topologyContractUnknown =
    systemTopology.nodes.find((n) => n.node_id === "snapshot:facade-contract")?.status === "UNKNOWN";

  const modeFocusContext = useMemo((): OperatorModeFocusContext => {
    return {
      readyStatus,
      anyHookError: anyError,
      deploymentReadinessFailed: deploymentReadiness.isError,
      deploymentBlockerCodes: deploymentTierCodes.blockers,
      deploymentWarningCodes: deploymentTierCodes.warnings,
      cockpitDeploymentStatus: cockpit?.deployment_status,
      operatorHealthFailed: operatorHealthQueryFailed,
      researchLifecycleFailed: researchLifecycleQueryFailed,
      releaseControlFailed: releaseControlQueryFailed,
      remediationFailed: remediationQueryFailed,
      paperCapitalFailed: paperCapitalQueryFailed,
      auditForensicFailed: auditForensicQueryFailed,
      topologyContractUnknown,
      chainIntegrityLabel: operatorProvenance.trustStatus,
    };
  }, [
    readyStatus,
    anyError,
    deploymentReadiness.isError,
    deploymentTierCodes.blockers,
    deploymentTierCodes.warnings,
    cockpit?.deployment_status,
    operatorHealthQueryFailed,
    researchLifecycleQueryFailed,
    releaseControlQueryFailed,
    remediationQueryFailed,
    paperCapitalQueryFailed,
    auditForensicQueryFailed,
    topologyContractUnknown,
    operatorProvenance.trustStatus,
  ]);

  const modeNextFocusLines = useMemo(
    () => deriveOperatorModeNextFocusLines(operatorMode, modeFocusContext),
    [operatorMode, modeFocusContext],
  );

  const postGridSectionOrder = useMemo(() => {
    const o = getPostGridSectionOrder(operatorMode);
    if (modeShowsOperatorCommandPane(operatorMode)) return o;
    return o.filter((k) => k !== "operator_command");
  }, [operatorMode]);

  const workboardProvenance = useMemo((): PaneEvidenceProvenance => {
    const d = workboard.data;
    const mat = d ? asRecord(d.materialization) : null;
    const blocked = d?.stats.blocked_count ?? 0;
    const stale = d?.stats.stale_link_count ?? 0;
    const downstreamBlocked = asNumber(mat?.journal_downstream_closure_blocked_count) ?? 0;
    const postMergeStale = asNumber(mat?.journal_post_merge_stale_count) ?? 0;
    return {
      sourceLabel: "READ · /ui/workboard",
      schemaVersion: d?.schema_version,
      generatedAtUtc: d?.generated_at_utc,
      digestPreview: digest(mat?.latest_projection_generated_at_utc),
      digestFull: asString(mat?.latest_projection_generated_at_utc) || undefined,
      trustStatus: asString(mat?.projection_trust_status),
      projectionSnapshotVerified: null,
      freshnessStatus: d?.stats.freshness_state ?? UNKNOWN,
      blockerCount: blocked + downstreamBlocked,
      warningCount: stale + postMergeStale,
      supplementalLine: asString(mat?.materialization_state) ?? undefined,
    };
  }, [workboard.data]);

  const overviewInspectorPayload = useMemo((): InspectorPayload => {
    return {
      title: "System Summary",
      subtitle: "Read-plane aggregate",
      body: inspectBody({
        status: readyStatus,
        summary:
          "Overview tiles are derived from /healthz, /readyz, /ui/evidence, /ui/facade, /ui/operator-actions, and /ui/workboard.",
        warnings: anyError ? ["READ_PLANE_QUERY_DEGRADED"] : [],
        details: [
          { k: "api", v: apiBaseDisplay },
          { k: "frontend", v: frontendClaimed ? "CLAIMED" : "NOT_CLAIMED" },
        ],
      }),
      rawJson: { readyBody, cockpit, facade: facade.data },
      digestToCopy: asString(registry?.projection_digest_sha256),
    };
  }, [readyStatus, anyError, apiBaseDisplay, frontendClaimed, readyBody, cockpit, facade.data, registry]);

  const evidenceChainInspectorPayload = useMemo((): InspectorPayload => {
    return {
      title: "Evidence Chain",
      body: inspectBody({
        status: cockpit?.deployment_status ?? UNKNOWN,
        summary: `Chain Status: ${cockpit?.deployment_status ?? UNKNOWN}; Length: ${evidenceRows.length}`,
        details: [{ k: "digest", v: digest(registry?.projection_digest_sha256) }],
      }),
      rawJson: evidence.data,
      digestToCopy: asString(registry?.projection_digest_sha256),
    };
  }, [cockpit?.deployment_status, evidenceRows.length, registry, evidence.data]);

  const providerInspectorPayload = useMemo((): InspectorPayload => {
    return {
      title: "Provider Matrix",
      body: inspectBody({
        status: providerWarnings ? "DEGRADED" : "OK",
        summary: `${providerRows.length} provider rows; Alpaca execution constraints highlighted when present.`,
        warnings: providerWarnings ? [`PROVIDER_WARNINGS=${providerWarnings}`] : [],
      }),
      rawJson: providers.data,
    };
  }, [providerWarnings, providerRows.length, providers.data]);

  const operatorInspectorPayload = useMemo((): InspectorPayload => {
    const idx = asRecord(operatorIdx.data);
    return {
      title: "Ledger / Operator Actions",
      body: inspectBody({
        status: boolStatus(asBool(idx?.chain_ok), "LEDGER_OK", "DEGRADED"),
        summary: `Events=${value(idx?.event_count, "0")} latest=${
          actionRows.length ? digest(actionRows[actionRows.length - 1].event_hash) : "PENDING"
        }`,
        details: [{ k: "immutable", v: asBool(idx?.chain_ok) !== false ? "YES" : "NO" }],
      }),
      rawJson: operatorIdx.data,
    };
  }, [operatorIdx.data, actionRows]);

  const workboardInspectorPayload = useMemo((): InspectorPayload => {
    const d = workboard.data;
    const qc = d ? workboardQueueItemCount(d) : null;
    return {
      title: "Workboard",
      body: inspectBody({
        status: d?.stats.freshness_state ?? UNKNOWN,
        summary: `Active=${d?.stats.active_count ?? "UNKNOWN"} Governed=${d?.stats.governed_count ?? "UNKNOWN"} Journaled=${
          d?.stats.journaled_count ?? "UNKNOWN"
        }`,
        details: [{ k: "items", v: String(qc ?? "UNKNOWN") }],
      }),
      rawJson: d,
    };
  }, [workboard.data]);

  const overviewTiles: OverviewTile[] = [
    {
      label: "Health",
      status: healthz.data ? boolStatus(asBool(healthz.data.ok), "HEALTHY", "DEGRADED") : UNKNOWN,
      hint: `/healthz ${healthz.data ? "200" : "PENDING"}`,
      raw: healthz.data,
    },
    {
      label: "Readiness",
      status: readyStatus,
      hint: `${blockers.length} blockers / ${warnings.length} warnings`,
      raw: readyBody,
    },
    {
      label: "API Smoke",
      status: boolStatus(cockpit?.api_smoke_ok),
      hint: cockpit?.api_smoke_status ?? "evidence-derived",
      raw: cockpit,
    },
    {
      label: "Backup / Restore",
      status: boolStatus(cockpit?.backup_restore_ok),
      hint: "artifact evidence",
      raw: cockpit,
    },
    {
      label: "Ledger Integrity",
      status: boolStatus(cockpit?.ledger_integrity_ok, "VERIFIED", "DEGRADED"),
      hint: `events ${value(asRecord(operatorIdx.data)?.event_count, "0")}`,
      raw: operatorIdx.data,
    },
    {
      label: "Operator Sign-off",
      status: boolStatus(cockpit?.manual_operator_signoff_present, "SIGNED", "PENDING"),
      hint: cockpit?.operator_decision ?? "PENDING",
      raw: cockpit,
    },
    {
      label: "Frontend Status",
      status: facade.data?.frontend_readiness_claimed ? "CLAIMED" : "NOT_CLAIMED",
      hint: facade.data?.frontend_readiness_claimed
        ? "single-tenant evidence gate passed"
        : "formal evidence gate absent",
      raw: facade.data,
    },
    {
      label: "System Posture",
      status:
        readyStatus === "READY" && cockpit?.deployment_status === "PASS" ? "GREEN" : "DEGRADED",
      hint: `read_plane=${String(facade.data?.read_plane_only ?? "UNKNOWN")}`,
      raw: { readyBody, cockpit, facade: facade.data },
    },
  ];

  const pass = readinessRows.filter((r) => r.status === "PASS").length;
  const warn = readinessRows.filter((r) => r.status === "WARN" || r.status === UNKNOWN).length;
  const fail = readinessRows.filter((r) => r.status === "FAIL").length;
  const crit = readinessRows.filter((r) => r.severity === "CRIT").length;
  const readinessPct = readinessRows.length ? Math.round((pass / readinessRows.length) * 100) : 0;
  const wbCount = workboard.data ? workboardQueueItemCount(workboard.data) : null;

  const tape: TapeLine[] = useMemo(() => {
    const ts = cockpit?.evidence_generated_at_utc ?? asString(ev?.generated_at_utc) ?? undefined;
    return [
      { id: "ready", ts, severity: readyStatus === "READY" ? "ok" : "warn", text: `READY=${readyStatus}` },
      {
        id: "api-smoke",
        ts,
        severity: cockpit?.api_smoke_ok === true ? "ok" : "warn",
        text: `API_SMOKE_${cockpit?.api_smoke_ok === true ? "OK" : "PENDING"}`,
      },
      {
        id: "backup",
        ts,
        severity: cockpit?.backup_restore_ok === true ? "ok" : "warn",
        text: `BACKUP_${cockpit?.backup_restore_ok === true ? "OK" : "PENDING"}`,
      },
      {
        id: "restore",
        ts,
        severity: cockpit?.backup_restore_ok === true ? "ok" : "warn",
        text: `RESTORE_${cockpit?.backup_restore_ok === true ? "OK" : "PENDING"}`,
      },
      {
        id: "preflight",
        ts,
        severity: cockpit?.deployment_evidence_ok === true ? "ok" : "warn",
        text: `PREFLIGHT_${cockpit?.deployment_evidence_ok === true ? "OK" : "PENDING"}`,
      },
      {
        id: "providers",
        ts: asString(asRecord(providers.data)?.generated_at_utc),
        severity: providerWarnings ? "warn" : "ok",
        text: `PROVIDER_WARNINGS=${providerWarnings}`,
      },
      {
        id: "ledger",
        ts,
        severity: asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "ok" : "bad",
        text: `LEDGER_${asBool(asRecord(operatorIdx.data)?.chain_ok) !== false ? "OK" : "DEGRADED"}`,
      },
      {
        id: "workboard",
        ts: workboard.data?.generated_at_utc,
        severity: (wbCount ?? 0) > 0 ? "info" : "neutral",
        text: `WORKBOARD_ACTIVE=${wbCount ?? 0}`,
      },
      {
        id: "frontend",
        ts,
        severity: frontendClaimed ? "ok" : "warn",
        text: frontendClaimed ? "FRONTEND_CLAIMED" : "FRONTEND_NOT_CLAIMED",
      },
    ];
  }, [cockpit, ev, frontendClaimed, operatorIdx.data, providerWarnings, providers.data, readyStatus, wbCount, workboard.data?.generated_at_utc]);

  const ticker = useMemo(
    () => [
      { severity: readyStatus === "READY" ? ("ok" as const) : ("warn" as const), text: `READY ${readyStatus}` },
      {
        severity: cockpit?.deployment_status === "PASS" ? ("ok" as const) : ("warn" as const),
        text: `DEP ${cockpit?.deployment_status ?? UNKNOWN}`,
      },
      {
        severity: facade.data?.read_plane_only ? ("ok" as const) : ("bad" as const),
        text: `READ_PLANE ${String(facade.data?.read_plane_only ?? UNKNOWN)}`,
      },
      {
        severity: frontendClaimed ? ("ok" as const) : ("warn" as const),
        text: `FRONTEND ${frontendClaimed ? "CLAIMED" : "NOT_CLAIMED"}`,
      },
    ],
    [cockpit?.deployment_status, facade.data?.read_plane_only, frontendClaimed, readyStatus],
  );

  useTerminalPageBind(tape, ticker);

  if (!config.ok) {
    return (
      <div className="term-page cockpit-page">
        <div className="term-page__banner">{config.error.message}</div>
      </div>
    );
  }

  const renderPostGridSection = (key: CockpitPostGridSectionKey): ReactNode => {
    switch (key) {
      case "topology":
        return (
          <div className="cockpit-topology-row" data-operator-section="topology">
            <SystemTopologyPane
              topologyNodes={systemTopology.nodes}
              facadeReadPlaneOnly={facade.data?.read_plane_only ?? null}
              mutationRouteLabel={facade.data?.mutation_route ?? null}
              openInspector={openInspector}
            />
          </div>
        );
      case "research_paper_drilldown":
        return (
          <div className="cockpit-drilldown-row" data-operator-section="research_paper_drilldown">
            <ResearchOsEvidenceDrilldownPane
              rows={researchOsRows}
              queryFailed={researchOsStatus.isError}
              selectedKey={selectedKey}
              setSelectedKey={setSelectedKey}
              openInspector={openInspector}
              setLastDigest={setLastDigest}
              provenance={researchOsProvenance}
              inspectorPayload={researchOsInspectorPayload}
            />
            <PaperExecutionEvidenceDrilldownPane
              rows={paperExecutionRows}
              queryFailed={paperExecution.isError}
              selectedKey={selectedKey}
              setSelectedKey={setSelectedKey}
              openInspector={openInspector}
              setLastDigest={setLastDigest}
              provenance={paperExecutionProvenance}
              inspectorPayload={paperExecutionInspectorPayload}
            />
          </div>
        );
      case "capital_firewall":
        return (
          <div className="cockpit-drilldown-row" data-operator-section="capital_firewall">
            <CapitalExecutionFirewallPane
              paperExecution={paperExecRec}
              paperBroker={paperBrokerRec}
              paperTracking={paperTrackingLatest.data != null ? asRecord(paperTrackingLatest.data) : null}
              providerSetup={providerSetup.data != null ? asRecord(providerSetup.data) : null}
              providerHealth={providers.data != null ? asRecord(providers.data) : null}
              runtimeMutationSafety={cockpitMutationSafety}
              executionAuthorityHint={asString(runtimeBody?.execution_authority) ?? null}
              queryFailed={
                paperExecution.isError ||
                paperBroker.isError ||
                paperTrackingLatest.isError ||
                providerSetup.isError ||
                providers.isError
              }
              openInspector={openInspector}
            />
          </div>
        );
      case "operator_health":
        return (
          <div data-operator-section="operator_health">
            <OperatorHealthAlertsPane
              healthInput={operatorHealthInput}
              queryFailed={operatorHealthQueryFailed}
              openInspector={openInspector}
            />
          </div>
        );
      case "remediation":
        return (
          <div data-operator-section="remediation">
            <RemediationGovernancePane
              governanceInput={remediationGovernanceInput}
              queryFailed={remediationQueryFailed}
              openInspector={openInspector}
            />
          </div>
        );
      case "first_run":
        return (
          <div data-operator-section="first_run">
            <FirstRunDeploymentCockpitPane
              checklistInput={firstRunInput}
              deploymentBlockerCodes={deploymentTierCodes.blockers}
              deploymentWarningCodes={deploymentTierCodes.warnings}
              facadeOperatorHint={facade.data?.frontend_operator_console_hint}
              openInspector={openInspector}
            />
          </div>
        );
      case "provider_setup":
        return (
          <div data-operator-section="provider_setup">
            <ProviderSetupReadinessPane
              providerSetupData={providerSetup.data ?? null}
              providerHealthData={providers.data}
              openInspector={openInspector}
            />
          </div>
        );
      case "strategy_lifecycle":
        return (
          <div data-operator-section="strategy_lifecycle">
            <StrategyLifecyclePane
              strategyIntakeLatest={strategyIntakeLatest.data ?? null}
              strategyThesisLatest={strategyThesisLatest.data ?? null}
              strategyThesisGenerationLatest={strategyThesisGenerationLatest.data ?? null}
              strategyMemoryLatest={strategyMemoryLatest.data ?? null}
              strategyGraveyardLatest={strategyGraveyardLatest.data ?? null}
              paperTrackingLatest={paperTrackingLatest.data ?? null}
              backtestForensicsLatest={backtestForensicsLatest.data ?? null}
              strategyBatchLatest={strategyBatchLatest.data ?? null}
              workboard={workboard.data ?? null}
              evidenceChain={evidenceChain.data ?? null}
              mutationSafety={cockpitMutationSafety}
              queryFailed={researchLifecycleQueryFailed}
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "release_control":
        return (
          <div data-operator-section="release_control">
            <ReleaseControlPane
              facade={facade.data ?? null}
              evidence={evidence.data ?? null}
              evidenceChain={evidenceChain.data ?? null}
              releaseReadiness={releaseReadinessLatest.data ?? null}
              handoff={researchOsHandoffLatest.data ?? null}
              handoffSignoff={researchOsHandoffSignoffLatest.data ?? null}
              reviewJournal={researchOsReviewJournalLatest.data ?? null}
              queryFailed={releaseControlQueryFailed}
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "evidence_runbook":
        return (
          <div data-operator-section="evidence_runbook">
            <EvidenceRunbookPane
              facade={facade.data ?? null}
              evidence={evidence.data ?? null}
              evidenceChain={evidenceChain.data ?? null}
              operatorActions={operatorIdx.data ?? null}
              releaseReadiness={releaseReadinessLatest.data ?? null}
              handoff={researchOsHandoffLatest.data ?? null}
              handoffSignoff={researchOsHandoffSignoffLatest.data ?? null}
              reviewJournal={researchOsReviewJournalLatest.data ?? null}
              exportLatest={researchOsExportLatest.data ?? null}
              queryFailed={
                evidence.isError ||
                evidenceChain.isError ||
                operatorIdx.isError ||
                releaseReadinessLatest.isError ||
                researchOsHandoffLatest.isError ||
                researchOsHandoffSignoffLatest.isError ||
                researchOsReviewJournalLatest.isError ||
                researchOsExportLatest.isError
              }
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "audit_forensic":
        return (
          <div data-operator-section="audit_forensic">
            <AuditForensicPane
              evidenceChain={evidenceChain.data ?? null}
              operatorActions={operatorIdx.data ?? null}
              evidence={evidence.data ?? null}
              releaseReadiness={releaseReadinessLatest.data ?? null}
              handoff={researchOsHandoffLatest.data ?? null}
              handoffSignoff={researchOsHandoffSignoffLatest.data ?? null}
              reviewJournal={researchOsReviewJournalLatest.data ?? null}
              exportLatest={researchOsExportLatest.data ?? null}
              driftLatest={researchOsDriftLatest.data ?? null}
              paperExecution={paperExecution.data ?? null}
              queryFailed={auditForensicQueryFailed}
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "policy_risk":
        return (
          <div data-operator-section="policy_risk">
            <PolicyRiskGatesPane
              readyzBody={readyBody}
              readyzError={readyz.isError}
              runtimeBody={runtimeBody}
              mutationSafety={cockpitMutationSafety}
              facade={asRecord(facade.data)}
              evidence={ev}
              operatorActions={asRecord(operatorIdx.data)}
              providerHealth={asRecord(providers.data)}
              backtestForensics={asRecord(backtestForensicsLatest.data)}
              paperExecution={paperExecRec}
              paperTracking={asRecord(paperTrackingLatest.data)}
              queryFailed={
                facade.isError ||
                readyz.isError ||
                runtime.isError ||
                evidence.isError ||
                providers.isError ||
                backtestForensicsLatest.isError ||
                paperExecution.isError ||
                paperTrackingLatest.isError ||
                operatorIdx.isError
              }
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "promotion_dossier":
        return (
          <div data-operator-section="promotion_dossier">
            <PromotionEvidenceDossierPane
              readyzBody={readyBody}
              strategyIntakeLatest={strategyIntakeLatest.data ?? null}
              strategyThesisLatest={strategyThesisLatest.data ?? null}
              strategyThesisGenerationLatest={strategyThesisGenerationLatest.data ?? null}
              paperTrackingLatest={paperTrackingLatest.data ?? null}
              strategyBatchLatest={strategyBatchLatest.data ?? null}
              backtestForensicsLatest={backtestForensicsLatest.data ?? null}
              evidenceChain={evidenceChain.data ?? null}
              operatorActions={operatorIdx.data ?? null}
              workboard={workboard.data ?? null}
              evidence={evidence.data ?? null}
              paperExecution={paperExecution.data ?? null}
              queryFailed={
                evidenceChain.isError ||
                operatorIdx.isError ||
                workboard.isError ||
                strategyIntakeLatest.isError ||
                strategyThesisLatest.isError ||
                strategyThesisGenerationLatest.isError ||
                paperTrackingLatest.isError ||
                strategyBatchLatest.isError ||
                backtestForensicsLatest.isError ||
                evidence.isError ||
                paperExecution.isError ||
                readyz.isError
              }
              openInspector={openInspector}
              setLastDigest={setLastDigest}
            />
          </div>
        );
      case "research_batch":
        return (
          <div data-operator-section="research_batch">
            <ResearchBatchForensicsPane
              strategyBatchLatest={strategyBatchLatest.data ?? null}
              strategyBatchesList={strategyBatches.data ?? null}
              backtestForensicsLatest={backtestForensicsLatest.data ?? null}
              paperTrackingLatest={paperTrackingLatest.data ?? null}
              strategyGraveyardLatest={strategyGraveyardLatest.data ?? null}
              strategyMemoryLatest={strategyMemoryLatest.data ?? null}
              strategyThesisLatest={strategyThesisLatest.data ?? null}
              shadowBookLatest={shadowBookLatest.data ?? null}
              openInspector={openInspector}
            />
          </div>
        );
      case "operator_command":
        return (
          <div className="cockpit-command-row" data-operator-section="operator_command">
            <OperatorCommandCockpitPane
              selectedWorkTarget={selectedWorkCommandTarget}
              mutationSafety={cockpitMutationSafety}
              mutationRoute={facade.data?.mutation_route ?? null}
              readPlaneOnly={facade.data?.read_plane_only ?? null}
              runtimeEnvironment={asString(runtimeBody?.environment) ?? null}
              openInspector={openInspector}
            />
          </div>
        );
      default: {
        const _exhaustive: never = key;
        return _exhaustive;
      }
    }
  };

  return (
    <div className="term-page cockpit-page">
      {anyError && (
        <div className="term-page__banner cockpit-alert">
          DEGRADED · one or more read-plane queries failed; missing data remains UNKNOWN.
        </div>
      )}
      <OperatorModeSwitchboard
        mode={operatorMode}
        onChange={setOperatorMode}
        definition={getOperatorModeDefinition(operatorMode)}
        nextFocusLines={modeNextFocusLines}
        postGridOrderPreview={postGridSectionOrder}
      />
      <div className="cockpit-grid" data-testid="cockpit-seven-pane-grid">
        <OverviewPane
          overviewTiles={overviewTiles}
          provenance={overviewProvenance}
          inspectorPayload={overviewInspectorPayload}
          openInspector={openInspector}
          setLastDigest={setLastDigest}
        />
        <ReadinessMatrixPane
          readyStatus={readyStatus}
          pass={pass}
          warn={warn}
          fail={fail}
          crit={crit}
          readinessPct={readinessPct}
          readinessRows={readinessRows}
          warnings={warnings}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          readyBody={readyBody}
          openInspector={openInspector}
        />
        <EvidenceChainPane
          deploymentStatus={cockpit?.deployment_status}
          evidenceRows={evidenceRows}
          registryProjectionDigest={registry?.projection_digest_sha256}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          openInspector={openInspector}
          setLastDigest={setLastDigest}
          provenance={evidenceChainProvenance}
          inspectorPayload={evidenceChainInspectorPayload}
        />
        <ProviderMatrixPane
          providerRows={providerRows}
          providerWarnings={providerWarnings}
          providersData={providers.data}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          openInspector={openInspector}
          provenance={providerProvenance}
          inspectorPayload={providerInspectorPayload}
          setLastDigest={setLastDigest}
        />
        <OperatorActionsPane
          operatorIdxData={operatorIdx.data}
          actionRows={actionRows}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          openInspector={openInspector}
          setLastDigest={setLastDigest}
          provenance={operatorProvenance}
          inspectorPayload={operatorInspectorPayload}
        />
        <WorkboardPane
          workboardData={workboard.data}
          wbCount={wbCount}
          strategyRows={strategyRows}
          workRows={workRows}
          selectedKey={selectedKey}
          setSelectedKey={setSelectedKey}
          openInspector={openInspector}
          provenance={workboardProvenance}
          inspectorPayload={workboardInspectorPayload}
          setLastDigest={setLastDigest}
        />
        <RuntimePane
          facadeData={facade.data}
          runtimeBody={runtimeBody}
          readPlane={readPlane}
          backend={backend}
          gpuProbe={gpuProbe}
          gpuHardware={gpuHardware}
          researchBody={researchBody}
          apiRootData={apiRoot.data}
          runtimeData={runtime.data}
          researchComputeData={researchCompute.data}
          openInspector={openInspector}
        />
      </div>
      {postGridSectionOrder.map((k) => (
        <Fragment key={k}>{renderPostGridSection(k)}</Fragment>
      ))}
    </div>
  );
}
