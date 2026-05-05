/**
 * Normalized read-plane model for release candidate + deployment evidence + Research OS
 * release-readiness / handoff / signoff. Does not infer approval or fabricate PASS.
 */
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";
import { RELEASE_CONTROL_COMMAND_HINTS } from "@/lib/operator/local-ops-command-hints";

export { RELEASE_CONTROL_COMMAND_HINTS };
import type { UiEvidenceCockpitFields } from "@/lib/operator/ui-evidence-cockpit";

export type ReleaseControlStage =
  | "RC_UNKNOWN"
  | "EVIDENCE_PENDING"
  | "ARCHIVE_VERIFIED"
  | "DEPLOYMENT_EVIDENCE_PRESENT"
  | "FRONTEND_CLAIM_ABSENT"
  | "FRONTEND_CLAIM_PRESENT"
  | "RELEASE_READINESS_PASS"
  | "RELEASE_READINESS_WARN"
  | "RELEASE_READINESS_FAIL"
  | "HANDOFF_READY"
  | "SIGNOFF_PENDING"
  | "SIGNOFF_COMPLETE"
  | "DEGRADED";

export type ReleaseControlNextAction =
  | "GENERATE_RELEASE_CANDIDATE"
  | "VERIFY_CLEAN_ARCHIVE"
  | "BUILD_DEPLOYMENT_EVIDENCE"
  | "REVIEW_FRONTEND_READINESS_CLAIM"
  | "RESOLVE_RELEASE_BLOCKERS"
  | "OPERATOR_SIGNOFF_REVIEW"
  | "READY_FOR_OPERATOR_DECISION";

export type ReleaseControlRow = {
  __id: string;
  section: string;
  stage: ReleaseControlStage;
  status: string;
  trust: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  digest_full: string | null;
  generated_at_utc: string;
  review_hint: string;
  raw: Record<string, unknown>;
};

export type ReleaseControlModel = {
  release_control_id: string;
  current_stage: ReleaseControlStage;
  readiness_bucket: "PASS" | "WARN" | "FAIL" | "UNKNOWN";
  trust_or_freshness: string;
  blocker_count: number;
  warning_count: number;
  digest_prefix: string;
  generated_at_utc: string;
  next_action: ReleaseControlNextAction;
  command_hint_primary: string;
  rows: ReleaseControlRow[];
};

function digestPrefix(input: unknown): string {
  const s = asString(input);
  if (!s) return "—";
  return s.length > 12 ? `${s.slice(0, 12)}...` : s;
}

function digestFull(input: unknown): string | null {
  const s = asString(input);
  return s && s.length >= 16 ? s : null;
}

function countCriteriaStatuses(latest: Record<string, unknown> | null, target: string): number {
  if (!latest) return 0;
  const criteria = latest.criteria;
  if (!Array.isArray(criteria)) return 0;
  let n = 0;
  for (const c of criteria) {
    const r = asRecord(c);
    if (asString(r?.status)?.toUpperCase() === target) n += 1;
  }
  return n;
}

function readinessBucketFromReport(latest: Record<string, unknown> | null, degraded: string[]): "PASS" | "WARN" | "FAIL" | "UNKNOWN" {
  if (!latest || degraded.some((d) => d.includes("NO_RESEARCH_OS_RELEASE_READINESS"))) return "UNKNOWN";
  const decision = asString(latest.decision)?.toUpperCase() ?? "";
  const status = asString(latest.status)?.toUpperCase() ?? "";
  const failC = countCriteriaStatuses(latest, "FAIL");
  const warnC = countCriteriaStatuses(latest, "WARN");
  if (failC > 0 || decision.includes("BLOCKED") || status === "BLOCKED" || decision === "REMEDIATION_REQUIRED") return "FAIL";
  if (decision === "SINGLE_TENANT_REVIEW_READY" && status === "READY_FOR_REVIEW" && failC === 0 && warnC === 0) return "PASS";
  if (warnC > 0 || decision === "REVIEW_WITH_RESTRICTIONS" || status === "RESTRICTED_REVIEW") return "WARN";
  if (decision === "NO_EVIDENCE" || status === "EMPTY") return "UNKNOWN";
  return "WARN";
}

function stageForReadiness(bucket: "PASS" | "WARN" | "FAIL" | "UNKNOWN", hasReport: boolean): ReleaseControlStage {
  if (!hasReport) return "EVIDENCE_PENDING";
  if (bucket === "PASS") return "RELEASE_READINESS_PASS";
  if (bucket === "WARN") return "RELEASE_READINESS_WARN";
  if (bucket === "FAIL") return "RELEASE_READINESS_FAIL";
  return "RC_UNKNOWN";
}

export function buildReleaseControlModel(input: {
  facade: unknown;
  evidence: unknown;
  evidenceChain: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  cockpit: UiEvidenceCockpitFields | null;
}): ReleaseControlModel {
  const facade = asRecord(input.facade);
  const ev = asRecord(input.evidence);
  const registry = ev ? asRecord(ev.registry) : null;
  const rr = asRecord(input.releaseReadiness);
  const rrLatest = rr?.latest ? asRecord(rr.latest) : null;
  const rrDegraded = asStringArray(rr?.degraded);
  const hasRr = rrLatest != null && !rrDegraded.some((d) => d.includes("NO_RESEARCH_OS_RELEASE_READINESS"));
  const bucket = readinessBucketFromReport(rrLatest, rrDegraded);

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

  const cockpit = input.cockpit;
  const deploymentPath = cockpit?.deployment_evidence_manifest_path;
  const deploymentStatus = (cockpit?.deployment_status ?? "UNKNOWN").toUpperCase();
  const ciOk = cockpit?.ci_local_verify_ok;
  const feStatus = (cockpit?.frontend_readiness_status ?? "UNKNOWN").toUpperCase();
  const facadeClaimed = asBool(facade?.frontend_readiness_claimed) === true;

  const rows: ReleaseControlRow[] = [];

  const rrBlockers = countCriteriaStatuses(rrLatest, "FAIL");
  const rrWarnings = countCriteriaStatuses(rrLatest, "WARN") + rrDegraded.length;
  rows.push({
    __id: "rc-release-readiness",
    section: "Release readiness (Research OS)",
    stage: stageForReadiness(bucket, hasRr),
    status: hasRr ? `${asString(rrLatest?.status) ?? "UNKNOWN"} · ${asString(rrLatest?.decision) ?? "UNKNOWN"}` : "MISSING",
    trust: asString(rrLatest?.trust_banner) ?? "UNKNOWN",
    blocker_count: rrBlockers,
    warning_count: rrWarnings,
    digest_prefix: digestPrefix(rrLatest?.manifest_sha256 ?? rr?.artifact_path),
    digest_full: digestFull(rrLatest?.manifest_sha256),
    generated_at_utc: asString(rrLatest?.generated_at_utc) ?? asString(rr?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "policy gate + remediation + catalog inputs to release-readiness report",
    raw: rr ?? {},
  });

  const deployBlockers =
    deploymentStatus === "FAIL" || cockpit?.deployment_evidence_ok === false
      ? 1
      : 0;
  let deployStage: ReleaseControlStage = "EVIDENCE_PENDING";
  if (deploymentPath && deploymentStatus === "PASS" && cockpit?.deployment_evidence_ok === true) {
    deployStage = "DEPLOYMENT_EVIDENCE_PRESENT";
  } else if (deploymentPath && deploymentStatus !== "UNKNOWN") {
    deployStage = cockpit?.deployment_evidence_ok === true ? "DEPLOYMENT_EVIDENCE_PRESENT" : "DEGRADED";
  }
  rows.push({
    __id: "rc-deployment-evidence",
    section: "Deployment evidence bundle",
    stage: deployStage,
    status: deploymentStatus,
    trust: asString(asRecord(ev?.verification)?.trust_status) ?? "UNKNOWN",
    blocker_count: deployBlockers,
    warning_count: deploymentStatus === "DEGRADED" ? 1 : 0,
    digest_prefix: digestPrefix(registry?.projection_digest_sha256 ?? deploymentPath),
    digest_full: digestFull(registry?.projection_digest_sha256),
    generated_at_utc: cockpit?.evidence_generated_at_utc ?? asString(ev?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "deployment-evidence.json roles: api_smoke, ledger_verify, ci_local_verify, …",
    raw: ev ?? {},
  });

  let feStage: ReleaseControlStage = "RC_UNKNOWN";
  if (feStatus === "CLAIMED" || facadeClaimed) feStage = "FRONTEND_CLAIM_PRESENT";
  else if (feStatus === "NOT_CLAIMED") feStage = "FRONTEND_CLAIM_ABSENT";
  else if (feStatus === "DEGRADED") feStage = "DEGRADED";
  rows.push({
    __id: "rc-frontend-readiness",
    section: "Frontend readiness claim",
    stage: feStage,
    status: `${feStatus} · facade_claimed=${facadeClaimed}`,
    trust: "READ_PLANE",
    blocker_count: 0,
    warning_count: feStatus === "NOT_CLAIMED" ? 1 : 0,
    digest_prefix: digestPrefix(facade?.frontend_package_present),
    digest_full: null,
    generated_at_utc: asString(ev?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "package detection ≠ production certification; claim is opt-in evidence adoption",
    raw: { facade_fragment: { frontend_readiness_claimed: facade?.frontend_readiness_claimed, frontend_package_present: facade?.frontend_package_present } },
  });

  let archStage: ReleaseControlStage = "RC_UNKNOWN";
  if (ciOk === true) archStage = "ARCHIVE_VERIFIED";
  else if (ciOk === false) archStage = "DEGRADED";
  else archStage = "EVIDENCE_PENDING";
  rows.push({
    __id: "rc-clean-archive-ci",
    section: "Clean archive / CI local verify",
    stage: archStage,
    status: ciOk === true ? "PASS" : ciOk === false ? "FAIL" : "UNKNOWN",
    trust: "READ_PLANE",
    blocker_count: ciOk === false ? 1 : 0,
    warning_count: ciOk == null ? 1 : 0,
    digest_prefix: "—",
    digest_full: null,
    generated_at_utc: cockpit?.evidence_generated_at_utc ?? "UNKNOWN",
    review_hint: "ci_local_verify role inside deployment-evidence manifest",
    raw: { ci_local_verify_ok: ciOk },
  });

  const signPresent = cockpit?.manual_operator_signoff_present;
  rows.push({
    __id: "rc-manual-signoff",
    section: "Manual operator signoff (runtime review)",
    stage: signPresent === true ? "SIGNOFF_COMPLETE" : signPresent === false ? "SIGNOFF_PENDING" : "RC_UNKNOWN",
    status: signPresent === true ? "PRESENT" : signPresent === false ? "ABSENT" : "UNKNOWN",
    trust: "READ_PLANE",
    blocker_count: signPresent === false ? 1 : 0,
    warning_count: signPresent == null ? 1 : 0,
    digest_prefix: digestPrefix(asString(asRecord(ev?.verification)?.projection_digest_sha256)),
    digest_full: null,
    generated_at_utc: cockpit?.evidence_generated_at_utc ?? "UNKNOWN",
    review_hint: "disk_runtime_review signoff_status in evidence projection",
    raw: { manual_operator_signoff_present: signPresent, operator_decision: cockpit?.operator_decision },
  });

  const hoBlockers = hoLatest ? asStringArray(hoLatest.blockers).length : hoDegraded.length;
  const hoWarnings = hoLatest ? asStringArray(hoLatest.warnings).length : 0;
  let hoStage: ReleaseControlStage = "EVIDENCE_PENDING";
  if (hoLatest && asBool(hoLatest.handoff_ready) === true) hoStage = "HANDOFF_READY";
  else if (hoDegraded.length > 0) hoStage = "DEGRADED";
  rows.push({
    __id: "rc-handoff-pack",
    section: "Research OS handoff pack",
    stage: hoStage,
    status: asString(hoLatest?.decision) ?? asString(ho?.status) ?? "UNKNOWN",
    trust: asString(hoLatest?.trust_banner) ?? "UNKNOWN",
    blocker_count: hoBlockers,
    warning_count: hoWarnings,
    digest_prefix: digestPrefix(hoLatest?.manifest_sha256 ?? ho?.artifact_path),
    digest_full: digestFull(hoLatest?.manifest_sha256),
    generated_at_utc: asString(hoLatest?.generated_at_utc) ?? asString(ho?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "handoff pack references release-readiness + exports + closure",
    raw: ho ?? {},
  });

  const verOk = asString(ver?.status)?.toUpperCase() === "VERIFIED";
  const sigDecision = asString(sig?.decision)?.toUpperCase() ?? "";
  let hsStage: ReleaseControlStage = "EVIDENCE_PENDING";
  if (!ver && !sig) hsStage = "EVIDENCE_PENDING";
  else if (ver && !verOk) hsStage = "DEGRADED";
  else if (verOk && !sig) hsStage = "SIGNOFF_PENDING";
  else if (sigDecision === "ACKNOWLEDGED" || sigDecision === "ACCEPTED_WITH_RESTRICTIONS") hsStage = "SIGNOFF_COMPLETE";
  else if (sigDecision === "REJECTED" || sigDecision === "BLOCKED") hsStage = "DEGRADED";
  else hsStage = "SIGNOFF_PENDING";
  rows.push({
    __id: "rc-handoff-signoff",
    section: "Handoff verification + reviewer signoff",
    stage: hsStage,
    status: ver ? `${asString(ver.status)} / ${sigDecision || "NO_SIGNOFF"}` : "MISSING",
    trust: asString(sig?.trust_banner) ?? asString(ver?.trust_banner) ?? "UNKNOWN",
    blocker_count: hsDegraded.filter((d) => d.includes("HANDOFF") || d.includes("SIGNOFF")).length,
    warning_count: hsDegraded.length,
    digest_prefix: digestPrefix(ver?.verification_id ?? sig?.signoff_id),
    digest_full: digestFull(ver?.observed_handoff_manifest_sha256),
    generated_at_utc:
      asString(sig?.signed_at_utc) ?? asString(ver?.verified_at_utc) ?? asString(hs?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "verify handoff spine; reviewer signoff is not deployment approval",
    raw: hs ?? {},
  });

  const rjStatus = asString(rjLatest?.status)?.toUpperCase() ?? "UNKNOWN";
  let rjStage: ReleaseControlStage = rjDegraded.length > 0 ? "DEGRADED" : "RC_UNKNOWN";
  if (rjLatest && rjStatus && rjStatus !== "READY") rjStage = "DEGRADED";
  if (!rjLatest && rjDegraded.some((d) => d.includes("NO_RESEARCH_OS_REVIEW_JOURNAL"))) rjStage = "EVIDENCE_PENDING";
  rows.push({
    __id: "rc-review-journal",
    section: "Review journal",
    stage: rjStage,
    status: rjLatest ? rjStatus : "NOT_PRESENT",
    trust: asString(rjLatest?.trust_banner) ?? "UNKNOWN",
    blocker_count: rjDegraded.length,
    warning_count: rjDegraded.length > 0 ? 1 : 0,
    digest_prefix: digestPrefix(rjLatest?.manifest_sha256 ?? rj?.manifest_path),
    digest_full: digestFull(rjLatest?.manifest_sha256),
    generated_at_utc: asString(rjLatest?.generated_at_utc) ?? asString(rj?.generated_at_utc) ?? "UNKNOWN",
    review_hint: "durable journal over research-os review artifacts",
    raw: rj ?? {},
  });

  const totalBlockers = rows.reduce((a, r) => a + r.blocker_count, 0);
  const totalWarnings = rows.reduce((a, r) => a + r.warning_count, 0);

  const chain = asRecord(input.evidenceChain);
  const chainDegraded = asStringArray(chain?.degraded);
  const staleChain = chainDegraded.length > 0;

  let currentStage: ReleaseControlStage = "RC_UNKNOWN";
  if (rows.some((r) => r.stage === "DEGRADED" || r.stage === "RELEASE_READINESS_FAIL")) {
    currentStage = rows.some((r) => r.stage === "RELEASE_READINESS_FAIL") ? "RELEASE_READINESS_FAIL" : "DEGRADED";
  } else if (bucket === "PASS" && deployStage === "DEPLOYMENT_EVIDENCE_PRESENT" && hsStage === "SIGNOFF_COMPLETE") {
    currentStage = "SIGNOFF_COMPLETE";
  } else if (bucket === "PASS") {
    currentStage = "RELEASE_READINESS_PASS";
  } else if (bucket === "WARN") {
    currentStage = "RELEASE_READINESS_WARN";
  } else if (bucket === "FAIL") {
    currentStage = "RELEASE_READINESS_FAIL";
  }

  const digestFirst =
    digestFull(rrLatest?.manifest_sha256) != null
      ? digestPrefix(rrLatest?.manifest_sha256)
      : digestPrefix(registry?.projection_digest_sha256);

  const generatedAt =
    asString(rrLatest?.generated_at_utc) ??
    cockpit?.evidence_generated_at_utc ??
    asString(ev?.generated_at_utc) ??
    "UNKNOWN";

  const releaseControlId = `rc:${digestPrefix(registry?.projection_digest_sha256)}:${digestPrefix(rrLatest?.manifest_sha256)}`.slice(0, 96);

  const noBootstrap = !hasRr && !deploymentPath && bucket === "UNKNOWN";
  let next: ReleaseControlNextAction;
  const signoffHardFailure = hsDegraded.some(
    (d) => d.includes("REJECTED") || d.includes("TAMPERED") || d.includes("HANDOFF_SIGNOFF_REJECTED"),
  );
  if (bucket === "FAIL" || rrBlockers > 0 || deployBlockers > 0 || signoffHardFailure) {
    next = "RESOLVE_RELEASE_BLOCKERS";
  } else if (noBootstrap) {
    next = "GENERATE_RELEASE_CANDIDATE";
  } else if (ciOk === false) {
    next = "VERIFY_CLEAN_ARCHIVE";
  } else if (!deploymentPath || deploymentStatus === "UNKNOWN") {
    next = "BUILD_DEPLOYMENT_EVIDENCE";
  } else if (feStage === "FRONTEND_CLAIM_ABSENT") {
    next = "REVIEW_FRONTEND_READINESS_CLAIM";
  } else if (hsStage === "SIGNOFF_PENDING" || signPresent !== true) {
    next = "OPERATOR_SIGNOFF_REVIEW";
  } else if (staleChain) {
    next = "RESOLVE_RELEASE_BLOCKERS";
  } else if (bucket === "WARN") {
    next = "OPERATOR_SIGNOFF_REVIEW";
  } else if (
    bucket === "PASS" &&
    deployStage === "DEPLOYMENT_EVIDENCE_PRESENT" &&
    hsStage === "SIGNOFF_COMPLETE" &&
    signPresent === true &&
    !staleChain
  ) {
    next = "READY_FOR_OPERATOR_DECISION";
  } else {
    next = "OPERATOR_SIGNOFF_REVIEW";
  }

  const trustOrFresh = staleChain ? "CHAIN_DEGRADED" : "CURRENT";

  const commandHintPrimary =
    next === "GENERATE_RELEASE_CANDIDATE"
      ? RELEASE_CONTROL_COMMAND_HINTS.rcGenerate
      : next === "VERIFY_CLEAN_ARCHIVE"
        ? `${RELEASE_CONTROL_COMMAND_HINTS.pkgRepoCheck} · ${RELEASE_CONTROL_COMMAND_HINTS.verifyArchive}`
        : next === "BUILD_DEPLOYMENT_EVIDENCE"
          ? RELEASE_CONTROL_COMMAND_HINTS.stEvidence
          : next === "REVIEW_FRONTEND_READINESS_CLAIM"
            ? `${RELEASE_CONTROL_COMMAND_HINTS.stAcceptance} (review claim in deployment evidence)`
            : next === "RESOLVE_RELEASE_BLOCKERS"
              ? RELEASE_CONTROL_COMMAND_HINTS.researchOsReleaseReadiness
              : next === "OPERATOR_SIGNOFF_REVIEW"
                ? `${RELEASE_CONTROL_COMMAND_HINTS.researchOsHandoffSignoffVerify} · ${RELEASE_CONTROL_COMMAND_HINTS.researchOsReviewJournal}`
                : `${RELEASE_CONTROL_COMMAND_HINTS.stAcceptance} · ${RELEASE_CONTROL_COMMAND_HINTS.stApiSmoke}`;

  return {
    release_control_id: releaseControlId,
    current_stage: currentStage,
    readiness_bucket: bucket,
    trust_or_freshness: trustOrFresh,
    blocker_count: totalBlockers,
    warning_count: totalWarnings,
    digest_prefix: digestFirst,
    generated_at_utc: generatedAt,
    next_action: next,
    command_hint_primary: commandHintPrimary,
    rows,
  };
}
