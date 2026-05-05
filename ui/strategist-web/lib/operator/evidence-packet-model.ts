/**
 * Read-plane-only normalization of deployment + Research OS + ledger evidence surfaces
 * for operator runbook / checklist presentation. Does not infer approval.
 */
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import type { UiEvidenceCockpitFields } from "@/lib/operator/ui-evidence-cockpit";
import { localOpsCommandById } from "@/lib/operator/local-ops-command-hints";

export type EvidenceArtifactPresence = "PRESENT" | "MISSING" | "UNKNOWN" | "STALE" | "WARN";

export type EvidencePacketReviewAction =
  | "UNKNOWN"
  | "REFRESH_DEPLOYMENT_EVIDENCE"
  | "RESOLVE_LEDGER_CHAIN_ISSUES"
  | "COMPLETE_HANDOFF_SIGNOFF_REVIEW"
  | "ADD_MISSING_RESEARCH_OS_ARTIFACTS"
  | "REVIEW_RUNTIME_SIGNOFF_ON_DISK"
  | "HUMAN_REVIEW_ONLY_NO_AUTO_APPROVAL";

export type EvidenceArtifactRow = {
  __id: string;
  label: string;
  source_command_summary: string;
  /** Optional local-ops registry id for copyable CLI provenance */
  command_hint_id: string | null;
  expected_evidence: string;
  presence: EvidenceArtifactPresence;
  digest_prefix: string;
  digest_full: string | null;
  cockpit_pane: string;
  blockers_summary: string;
  operator_review_only: boolean;
  raw: Record<string, unknown>;
};

export type EvidencePacketModel = {
  packet_id: string;
  /** Aggregate posture — never implies deployment approval */
  packet_status: "UNKNOWN" | "NOT_APPROVED" | "REVIEW_REQUIRED";
  generated_at_utc: string;
  trust_status: string;
  search_root: string;
  artifact_count: number;
  present_count: number;
  missing_count: number;
  stale_count: number;
  warn_count: number;
  blocker_count: number;
  warning_count: number;
  recommended_next_review_action: EvidencePacketReviewAction;
  rows: EvidenceArtifactRow[];
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 12 ? `${s.slice(0, 12)}…` : s;
}

function digestFull(v: unknown): string | null {
  const s = asString(v);
  return s && s.length >= 16 ? s : null;
}

function summarizeCommand(id: string | null): string {
  if (!id) return "—";
  const c = localOpsCommandById(id);
  return c ? c.label : id;
}

export function buildEvidencePacketModel(input: {
  evidence: unknown;
  evidenceChain: unknown;
  operatorActions: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  exportLatest: unknown;
  cockpit: UiEvidenceCockpitFields | null;
}): EvidencePacketModel {
  const ev = asRecord(input.evidence);
  const registry = ev ? asRecord(ev.registry) : null;
  const verification = ev ? asRecord(ev.verification) : null;
  const chain = asRecord(input.evidenceChain);
  const op = asRecord(input.operatorActions);
  const rr = asRecord(input.releaseReadiness);
  const rrLatest = rr?.latest ? asRecord(rr.latest) : null;
  const rrDegraded = asStringArray(rr?.degraded);
  const ho = asRecord(input.handoff);
  const hoLatest = ho?.latest ? asRecord(ho.latest) : null;
  const hoDegraded = asStringArray(ho?.degraded);
  const hs = asRecord(input.handoffSignoff);
  const ver = hs?.latest_verification ? asRecord(hs.latest_verification) : null;
  const sig = hs?.latest_signoff ? asRecord(hs.latest_signoff) : null;
  const hsDegraded = asStringArray(hs?.degraded);
  const rj = asRecord(input.reviewJournal);
  const rjLatest = rj?.latest ? asRecord(rj.latest) : null;
  const rjDegraded = asStringArray(rj?.degraded);
  const ex = asRecord(input.exportLatest);
  const exManifest = ex?.latest_export ? asRecord(ex.latest_export) : null;
  const exDeg = asStringArray(ex?.degraded);
  const cockpit = input.cockpit;

  const rows: EvidenceArtifactRow[] = [];
  const genAt = asString(ev?.generated_at_utc) ?? asString(registry?.generated_at_utc) ?? "UNKNOWN";
  const searchRoot = asString(ev?.search_root) ?? "UNKNOWN";
  const trust = asString(verification?.trust_status) ?? "UNKNOWN";

  const chainDegraded = asStringArray(chain?.degraded);
  const chainStale = chainDegraded.length > 0;
  const chainSummary = chain?.summary ? asRecord(chain.summary) : null;
  const chainOk = asBool(chainSummary?.operator_action_chain_ok);

  rows.push({
    __id: "pkt-ui-evidence-dashboard",
    label: "UI evidence dashboard (/ui/evidence)",
    source_command_summary: "GET /ui/evidence · projection registry over search_root",
    command_hint_id: null,
    expected_evidence: "ui_evidence_dashboard/v1 + oracle_projection_artifact_registry/v1",
    presence: ev ? "PRESENT" : "UNKNOWN",
    digest_prefix: digestPrefix(registry?.projection_digest_sha256),
    digest_full: digestFull(registry?.projection_digest_sha256),
    cockpit_pane: "EvidenceRunbookPane, OverviewPane",
    blockers_summary: ev ? (asBool(verification?.projection_snapshot_verified) === false ? "registry snapshot not verified" : "—") : "no payload",
    operator_review_only: false,
    raw: { evidence_fragment: { schema_version: ev?.schema_version, search_root: searchRoot } },
  });

  const manifestPath = cockpit?.deployment_evidence_manifest_path;
  const deployOk = cockpit?.deployment_evidence_ok;
  let deployPresence: EvidenceArtifactPresence = "UNKNOWN";
  if (manifestPath && deployOk === true) deployPresence = "PRESENT";
  else if (manifestPath && deployOk === false) deployPresence = "WARN";
  else if (manifestPath) deployPresence = "WARN";
  else deployPresence = "MISSING";

  rows.push({
    __id: "pkt-deployment-evidence-manifest",
    label: "Single-tenant deployment evidence manifest",
    source_command_summary: summarizeCommand("loc_st_evidence_final"),
    command_hint_id: "loc_st_evidence_final",
    expected_evidence: "single_tenant_deployment_evidence/v1 (deployment-evidence.json)",
    presence: deployPresence,
    digest_prefix: digestPrefix(registry?.projection_digest_sha256),
    digest_full: digestFull(registry?.projection_digest_sha256),
    cockpit_pane: "SingleTenantFirstRunWizard, ReleaseControlPane, ProviderSetupReadinessPane",
    blockers_summary:
      deployOk === false ? "deployment_evidence_ok=false" : !manifestPath ? "manifest path unknown" : "—",
    operator_review_only: true,
    raw: {
      deployment_evidence_manifest_path: manifestPath ?? null,
      deployment_evidence_ok: deployOk ?? null,
      deployment_status: cockpit?.deployment_status ?? null,
    },
  });

  const table = ev?.registry_table;
  if (Array.isArray(table)) {
    const cap = 18;
    for (let i = 0; i < Math.min(table.length, cap); i++) {
      const art = asRecord(table[i]);
      if (!art) continue;
      const exists = asBool(art.exists);
      const presence: EvidenceArtifactPresence =
        exists === true ? "PRESENT" : exists === false ? "MISSING" : "UNKNOWN";
      rows.push({
        __id: `pkt-registry-artifact-${i}`,
        label: `Registry · ${asString(art.artifact_label) ?? "artifact"}`,
        source_command_summary: "Disk artifacts under evidence search_root indexed by API",
        command_hint_id: null,
        expected_evidence: asString(art.path) ?? "path",
        presence,
        digest_prefix: digestPrefix(art.sha256),
        digest_full: digestFull(art.sha256),
        cockpit_pane: "EvidenceChainPane, EvidenceRunbookPane",
        blockers_summary: presence === "MISSING" ? "file missing on disk" : "—",
        operator_review_only: false,
        raw: art,
      });
    }
    if (table.length > cap) {
      rows.push({
        __id: "pkt-registry-artifact-overflow",
        label: `Registry · … +${table.length - cap} more`,
        source_command_summary: "—",
        command_hint_id: null,
        expected_evidence: "additional registry_table rows truncated in cockpit",
        presence: "UNKNOWN",
        digest_prefix: "—",
        digest_full: null,
        cockpit_pane: "EvidenceRunbookPane",
        blockers_summary: "inspect full GET /ui/evidence",
        operator_review_only: false,
        raw: { truncated: true, total: table.length },
      });
    }
  }

  rows.push({
    __id: "pkt-evidence-chain",
    label: "Ledger / operator action evidence chain",
    source_command_summary: "GET /ui/evidence-chain · readonly ledger projection",
    command_hint_id: null,
    expected_evidence: "ui_evidence_chain/v1 timeline + stream summaries",
    presence: chain ? (chainStale ? "STALE" : chainOk === false ? "WARN" : "PRESENT") : "UNKNOWN",
    digest_prefix: digestPrefix(chainSummary?.operator_action_event_count),
    digest_full: null,
    cockpit_pane: "EvidenceChainPane, OperatorActionsPane",
    blockers_summary: chainStale ? chainDegraded.slice(0, 3).join(" · ") : "—",
    operator_review_only: true,
    raw: chain ?? {},
  });

  const opEvents = asNumber(op?.event_count) ?? 0;
  rows.push({
    __id: "pkt-operator-actions-index",
    label: "Operator action journal index",
    source_command_summary: "GET /ui/operator-actions · append-only projection",
    command_hint_id: null,
    expected_evidence: "operator_action_event_projection_index",
    presence: op == null ? "UNKNOWN" : opEvents > 0 ? "PRESENT" : "MISSING",
    digest_prefix: digestPrefix(op?.chain_ok === true ? "chain_ok" : "chain_issue"),
    digest_full: null,
    cockpit_pane: "OperatorActionsPane, OperatorCommandCockpitPane",
    blockers_summary: asBool(op?.chain_ok) === false ? `chain_issue_count=${asNumber(op?.chain_issue_count) ?? "?"}` : "—",
    operator_review_only: true,
    raw: op ?? {},
  });

  const rrPresent = rrLatest != null && !rrDegraded.some((d) => d.includes("NO_RESEARCH_OS_RELEASE_READINESS"));
  rows.push({
    __id: "pkt-research-os-release-readiness",
    label: "Research OS release readiness",
    source_command_summary: summarizeCommand("loc_research_os_release_readiness"),
    command_hint_id: "loc_research_os_release_readiness",
    expected_evidence: "release readiness manifest under artifacts/",
    presence: rrPresent ? "PRESENT" : rrDegraded.length ? "STALE" : "MISSING",
    digest_prefix: digestPrefix(rrLatest?.manifest_sha256),
    digest_full: digestFull(rrLatest?.manifest_sha256),
    cockpit_pane: "ReleaseControlPane, ResearchOsEvidenceDrilldownPane",
    blockers_summary: rrDegraded.length ? rrDegraded.slice(0, 2).join(" · ") : "—",
    operator_review_only: true,
    raw: rr ?? {},
  });

  const hoPresent = hoLatest != null && !hoDegraded.some((d) => d.includes("NO_RESEARCH_OS_HANDOFF"));
  rows.push({
    __id: "pkt-research-os-handoff",
    label: "Research OS handoff pack",
    source_command_summary: summarizeCommand("loc_research_os_handoff_build"),
    command_hint_id: "loc_research_os_handoff_build",
    expected_evidence: "handoff bundle under artifacts/",
    presence: hoPresent ? "PRESENT" : hoDegraded.length ? "STALE" : "MISSING",
    digest_prefix: digestPrefix(hoLatest?.manifest_sha256),
    digest_full: digestFull(hoLatest?.manifest_sha256),
    cockpit_pane: "ReleaseControlPane",
    blockers_summary: hoDegraded.length ? hoDegraded.slice(0, 2).join(" · ") : "—",
    operator_review_only: true,
    raw: ho ?? {},
  });

  const hsPresent = ver != null || sig != null;
  rows.push({
    __id: "pkt-research-os-handoff-signoff",
    label: "Handoff verification + reviewer signoff",
    source_command_summary: summarizeCommand("loc_research_os_handoff_signoff_verify"),
    command_hint_id: "loc_research_os_handoff_signoff_verify",
    expected_evidence: "verification + signoff JSON under artifacts/",
    presence: hsPresent ? "PRESENT" : hsDegraded.length ? "STALE" : "MISSING",
    digest_prefix: digestPrefix(ver?.observed_handoff_manifest_sha256 ?? sig?.signoff_id),
    digest_full: digestFull(ver?.observed_handoff_manifest_sha256),
    cockpit_pane: "ReleaseControlPane",
    blockers_summary: hsDegraded.length ? hsDegraded.slice(0, 2).join(" · ") : "—",
    operator_review_only: true,
    raw: hs ?? {},
  });

  const rjPresent = rjLatest != null && !rjDegraded.some((d) => d.includes("NO_RESEARCH_OS_REVIEW_JOURNAL"));
  rows.push({
    __id: "pkt-research-os-review-journal",
    label: "Research OS review journal",
    source_command_summary: summarizeCommand("loc_research_os_review_journal"),
    command_hint_id: "loc_research_os_review_journal",
    expected_evidence: "review journal artifact",
    presence: rjPresent ? "PRESENT" : rjDegraded.length ? "STALE" : "MISSING",
    digest_prefix: digestPrefix(rjLatest?.manifest_sha256),
    digest_full: digestFull(rjLatest?.manifest_sha256),
    cockpit_pane: "ReleaseControlPane",
    blockers_summary: rjDegraded.length ? rjDegraded.slice(0, 2).join(" · ") : "—",
    operator_review_only: true,
    raw: rj ?? {},
  });

  let exportPresence: EvidenceArtifactPresence = "UNKNOWN";
  if (ex == null) exportPresence = "UNKNOWN";
  else if (exDeg.length === 0 && exManifest) exportPresence = "PRESENT";
  else if (exDeg.some((d) => d.includes("NO_RESEARCH_OS_EXPORT_MANIFEST"))) exportPresence = "MISSING";
  else exportPresence = "WARN";
  rows.push({
    __id: "pkt-research-os-export",
    label: "Research OS export (latest read-plane)",
    source_command_summary: "GET /ui/research-os/export/latest",
    command_hint_id: null,
    expected_evidence: "research_os_export_manifest/v1 under artifacts/research_os_exports/latest/",
    presence: exportPresence,
    digest_prefix: digestPrefix(exManifest?.manifest_sha256 ?? exManifest?.export_spine_sha256),
    digest_full: digestFull(exManifest?.manifest_sha256 ?? exManifest?.export_spine_sha256),
    cockpit_pane: "EvidenceRunbookPane",
    blockers_summary: exDeg.length ? exDeg.slice(0, 2).join(" · ") : "—",
    operator_review_only: false,
    raw: ex ?? {},
  });

  const runtimeReview = ev?.runtime_review ? asRecord(ev.runtime_review) : null;
  const signoff = asString(runtimeReview?.signoff_status)?.toUpperCase() ?? "";
  rows.push({
    __id: "pkt-runtime-review-signoff",
    label: "Runtime review (disk) signoff_status",
    source_command_summary: "Recorded in /ui/evidence runtime_review projection",
    command_hint_id: null,
    expected_evidence: "runtime review JSON referenced by evidence explorer",
    presence: runtimeReview ? (signoff.includes("PENDING") ? "WARN" : "PRESENT") : "UNKNOWN",
    digest_prefix: digestPrefix(runtimeReview?.decision),
    digest_full: null,
    cockpit_pane: "SingleTenantFirstRunWizard, ReleaseControlPane",
    blockers_summary: cockpit?.manual_operator_signoff_present === false ? "manual_operator_signoff_present=false" : "—",
    operator_review_only: true,
    raw: runtimeReview ?? {},
  });

  let present = 0;
  let missing = 0;
  let stale = 0;
  let warn = 0;
  for (const r of rows) {
    if (r.presence === "PRESENT") present += 1;
    if (r.presence === "MISSING") missing += 1;
    if (r.presence === "STALE") stale += 1;
    if (r.presence === "WARN") warn += 1;
  }

  let blocker_count = 0;
  if (deployOk === false) blocker_count += 1;
  if (cockpit?.manual_operator_signoff_present === false) blocker_count += 1;
  if (chainStale || chainOk === false) blocker_count += 1;

  const hasReadPlane = ev != null || chain != null || op != null;

  let next: EvidencePacketReviewAction = "UNKNOWN";
  if (!hasReadPlane) next = "UNKNOWN";
  else if (deployOk === false || deployPresence === "MISSING") next = "REFRESH_DEPLOYMENT_EVIDENCE";
  else if (chainStale || chainOk === false) next = "RESOLVE_LEDGER_CHAIN_ISSUES";
  else if (cockpit?.manual_operator_signoff_present === false) next = "REVIEW_RUNTIME_SIGNOFF_ON_DISK";
  else if (!rrPresent || !hoPresent || !rjPresent) next = "ADD_MISSING_RESEARCH_OS_ARTIFACTS";
  else if (!hsPresent || asString(ver?.status)?.toUpperCase() !== "VERIFIED") next = "COMPLETE_HANDOFF_SIGNOFF_REVIEW";
  else next = "HUMAN_REVIEW_ONLY_NO_AUTO_APPROVAL";
  const notApproved =
    deployOk === false ||
    cockpit?.manual_operator_signoff_present === false ||
    chainStale ||
    chainOk === false;
  let packet_status: EvidencePacketModel["packet_status"] = "UNKNOWN";
  if (!hasReadPlane) packet_status = "UNKNOWN";
  else if (notApproved) packet_status = "NOT_APPROVED";
  else packet_status = "REVIEW_REQUIRED";

  const packet_id = `evidence_packet|${digestPrefix(registry?.projection_digest_sha256)}|${genAt.replace(/:/g, "")}`;

  return {
    packet_id,
    packet_status,
    generated_at_utc: genAt,
    trust_status: trust,
    search_root: searchRoot,
    artifact_count: rows.length,
    present_count: present,
    missing_count: missing,
    stale_count: stale,
    warn_count: warn,
    blocker_count,
    warning_count: warn + stale,
    recommended_next_review_action: next,
    rows,
  };
}

/** Markdown runbook for clipboard — no file writes; strip paths to basenames only. */
export function buildEvidenceRunbookMarkdown(model: EvidencePacketModel): string {
  const rootTail = model.search_root.includes("/") ? (model.search_root.split("/").pop() ?? model.search_root) : model.search_root;
  const lines: string[] = [
    `# Strategist operator evidence runbook (read-plane)`,
    ``,
    `> **Not deployment approval.** This checklist is generated from GET /ui/* JSON only.`,
    `> **Operator signoff requires backend evidence** on disk or in the ledger — never this markdown alone.`,
    `> **Missing or stale evidence blocks confidence** — treat UNKNOWN rows as review-required.`,
    ``,
    `| Field | Value |`,
    `| --- | --- |`,
    `| packet_id | ${model.packet_id} |`,
    `| packet_status | ${model.packet_status} |`,
    `| generated_at_utc | ${model.generated_at_utc} |`,
    `| trust_status | ${model.trust_status} |`,
    `| search_root | ${rootTail} |`,
    `| recommended_next_review_action | ${model.recommended_next_review_action} |`,
    `| present / missing / stale | ${model.present_count} / ${model.missing_count} / ${model.stale_count} |`,
    ``,
    `## Artifact checklist`,
    ``,
    `| Label | Presence | Digest | Cockpit | Review-only |`,
    `| --- | --- | --- | --- | --- |`,
  ];
  for (const r of model.rows) {
    lines.push(
      `| ${r.label.replace(/\|/g, "/")} | ${r.presence} | ${r.digest_prefix} | ${r.cockpit_pane.replace(/\|/g, "/")} | ${r.operator_review_only ? "yes" : "no"} |`,
    );
  }
  lines.push(``, `## CLI provenance (labels only)`, ``);
  for (const r of model.rows) {
    if (r.command_hint_id) {
      const cmd = localOpsCommandById(r.command_hint_id);
      if (cmd) lines.push(`- **${r.label}**: ${cmd.label}`);
    }
  }
  lines.push(``, `_Generated by Strategist cockpit · browser did not execute shell._`);
  return lines.join("\n");
}
