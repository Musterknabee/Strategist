/**
 * Pure first-run / single-tenant deployment checklist derived from read-plane API payloads only.
 * Does not infer DEPLOYMENT_APPROVED or fabricate pass states.
 */
import type { UiEvidenceCockpitFields } from "@/lib/operator/ui-evidence-cockpit";
import type {
  UiEvidenceChainPayload,
  UiFacadePayload,
  UiMutationSafetyStatus,
  UiProviderSetupConsolePayload,
} from "@/lib/api/types";
import {
  FIRST_RUN_CLI_HINTS,
  FIRST_RUN_HINT_ENV,
  FIRST_RUN_HINT_EVIDENCE,
  FIRST_RUN_HINT_MIGRATE,
  FIRST_RUN_HINT_PREFLIGHT,
  FIRST_RUN_HINT_SMOKE,
} from "@/lib/operator/local-ops-command-hints";
import { asRecord, asString } from "@/lib/operator/payload-utils";

export { FIRST_RUN_CLI_HINTS };

export type FirstRunStepStatus = "PASS" | "WARN" | "FAIL" | "UNKNOWN" | "PENDING";

export type FirstRunChecklistStep = {
  id: string;
  title: string;
  status: FirstRunStepStatus;
  /** Human-readable source (endpoint or field family). */
  source: string;
  remediation: string;
  blockerCount?: number;
  warningCount?: number;
  digestPrefix?: string;
  generatedAtUtc?: string;
  /** Extra read-plane context (e.g. evidence chain summary). */
  supplementalLine?: string;
};

export type FirstRunChecklistInput = {
  deployment: {
    data: Record<string, unknown> | null | undefined;
    isLoading: boolean;
    isError: boolean;
  };
  readyz: {
    httpStatus: number | undefined;
    body: Record<string, unknown> | null | undefined;
    isError: boolean;
    isLoading: boolean;
  };
  healthz: { isError: boolean; isLoading: boolean; data: unknown };
  livez: { httpStatus: number | undefined; isError: boolean; isLoading: boolean };
  facade: { data: UiFacadePayload | null | undefined; isError: boolean };
  mutationSafety: UiMutationSafetyStatus | null;
  cockpit: UiEvidenceCockpitFields | null;
  evidencePayload: Record<string, unknown> | null | undefined;
  providerSetup: {
    data: UiProviderSetupConsolePayload | null | undefined;
    isError: boolean;
    isLoading: boolean;
  };
  /** Optional GET /ui/evidence-chain summary for ledger stream health. */
  evidenceChain: {
    data: UiEvidenceChainPayload | null | undefined;
    isError: boolean;
    isLoading: boolean;
  };
};

export type NextFirstRunCommand = {
  stepId: string;
  label: string;
  command: string;
};

/** First non-PASS step in canonical order → suggested CLI (or empty command for console-only actions). */
export function suggestNextFirstRunCommand(steps: FirstRunChecklistStep[]): NextFirstRunCommand | null {
  const order = [
    "backend_reachable",
    "health_probe",
    "readiness_probe",
    "production_auth",
    "ledger_configured",
    "migration_current",
    "backup_restore",
    "api_smoke",
    "provider_setup",
    "frontend_readiness",
    "deployment_evidence",
    "operator_signoff",
  ];
  const pick = (pred: (s: FirstRunChecklistStep) => boolean): FirstRunChecklistStep | undefined => {
    for (const id of order) {
      const s = steps.find((x) => x.id === id);
      if (s && pred(s)) return s;
    }
    return undefined;
  };
  const urgent = pick((s) => s.status === "FAIL" || s.status === "PENDING");
  const target = urgent ?? pick((s) => s.status === "WARN");
  if (!target) return null;

  switch (target.id) {
    case "backend_reachable":
    case "health_probe":
    case "readiness_probe":
      return {
        stepId: target.id,
        label: "Boot or repair the API process, then re-run preflight",
        command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_PREFLIGHT].command,
      };
    case "production_auth":
    case "ledger_configured":
      return {
        stepId: target.id,
        label: "Fix env / token contract",
        command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_ENV].command,
      };
    case "migration_current":
      return { stepId: target.id, label: "Apply migrations", command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_MIGRATE].command };
    case "backup_restore":
      return {
        stepId: target.id,
        label: "Verify backup roots and restore drill",
        command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_PREFLIGHT].command,
      };
    case "api_smoke":
      return { stepId: target.id, label: "Run API smoke", command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_SMOKE].command };
    case "provider_setup":
      return {
        stepId: target.id,
        label: "Review provider rows in /providers (read-plane only here)",
        command: "",
      };
    case "frontend_readiness":
      return {
        stepId: target.id,
        label: "Read facade hint; opt-in claim is separate from package detection",
        command: "",
      };
    case "deployment_evidence":
      return {
        stepId: target.id,
        label: "Collect deployment evidence manifest",
        command: FIRST_RUN_CLI_HINTS[FIRST_RUN_HINT_EVIDENCE].command,
      };
    case "operator_signoff":
      return {
        stepId: target.id,
        label: "Complete governed runtime review / signoff artifacts (no UI mutation)",
        command: "",
      };
    default:
      return { stepId: target.id, label: "See copyable CLI hints below", command: "" };
  }
}

function depChecks(deployment: FirstRunChecklistInput["deployment"]): Record<string, unknown> | null {
  if (deployment.isLoading || deployment.isError || !deployment.data) return null;
  return asRecord(deployment.data.checks);
}

function readyzChecks(body: Record<string, unknown> | null | undefined): Record<string, unknown> | null {
  if (!body) return null;
  return asRecord(body.checks);
}

function isProductionRuntime(mode: string | undefined): boolean {
  if (!mode) return false;
  const u = mode.toUpperCase();
  return u.includes("PRODUCTION") && !u.includes("NON_PRODUCTION");
}

export function buildFirstRunDeploymentChecklist(input: FirstRunChecklistInput): FirstRunChecklistStep[] {
  const ck = depChecks(input.deployment);
  const rz = readyzChecks(input.readyz.body);
  const depPending = input.deployment.isLoading;
  const depMissing = !input.deployment.isLoading && (input.deployment.isError || !input.deployment.data);

  const readyzStatus = asString(input.readyz.body?.status);
  const readyzBlockers = Array.isArray(input.readyz.body?.blockers) ? input.readyz.body?.blockers.length : 0;
  const readyzWarnings = Array.isArray(input.readyz.body?.warnings) ? input.readyz.body?.warnings.length : 0;

  const envOk =
    ck != null && ck.environment_overrides_valid === true && ck.private_key_material_absent === true;

  const ledgerPathOk =
    ck != null && ck.ledger_database_path_configured === true && ck.ledger_path_resolved === true;

  const ledgerConfiguredOk = envOk && ledgerPathOk;

  const migrationOk =
    (ck != null && ck.schema_compatibility === true) || (rz != null && rz.schema_current === true);

  const migrationUnknown = !depPending && ck == null && rz == null;

  const backupConfigOk =
    ck != null && ck.ledger_backup_dir_configured === true && ck.backup_root_writable === true;

  const depRec = asRecord(input.deployment.data);
  const depBlockers = Array.isArray(depRec?.blocker_codes) ? (depRec.blocker_codes as unknown[]).length : 0;
  const depWarnings = Array.isArray(depRec?.warning_codes) ? (depRec.warning_codes as unknown[]).length : 0;

  const chain = input.evidenceChain.data;
  const chainSummary = chain?.summary;
  const chainIssues = chainSummary != null ? Number(chainSummary.chain_issue_count_total ?? 0) : null;
  const decisionOk = chainSummary != null ? chainSummary.decision_ledger_chain_ok === true : null;
  const operatorOk = chainSummary != null ? chainSummary.operator_action_chain_ok === true : null;
  const chainSupplemental =
    input.evidenceChain.isLoading
      ? "Evidence chain: loading…"
      : input.evidenceChain.isError || !chain
        ? "Evidence chain: UNKNOWN (read-plane query failed or empty)"
        : `Evidence chain: issues=${chainIssues ?? "—"} decision_ledger_chain_ok=${String(decisionOk)} operator_action_chain_ok=${String(operatorOk)} · GET /ui/evidence-chain`;

  const evReg = asRecord(asRecord(input.evidencePayload)?.registry);
  const registryDigest = asString(evReg?.projection_digest_sha256);
  const digestPrefix = registryDigest ? registryDigest.slice(0, 24) : undefined;
  const evidenceGenerated = asString(input.evidencePayload?.generated_at_utc) ?? input.cockpit?.evidence_generated_at_utc;

  const steps: FirstRunChecklistStep[] = [];

  const livezPending = input.livez.isLoading;
  const livezOk =
    !input.livez.isError && input.livez.httpStatus === 200 && !livezPending;

  steps.push({
    id: "backend_reachable",
    title: "Backend reachable (liveness)",
    status: livezPending ? "PENDING" : input.livez.isError || input.livez.httpStatus !== 200 ? "FAIL" : "PASS",
    source: "GET /livez",
    remediation: "Start the API process or fix the operator console base URL (NEXT_PUBLIC_STRATEGIST_API_BASE_URL).",
    generatedAtUtc: asString(input.readyz.body?.checked_at_utc) ?? undefined,
  });

  const hzPending = input.healthz.isLoading;
  const hzOk = !input.healthz.isError && input.healthz.data != null;
  steps.push({
    id: "health_probe",
    title: "Health probe",
    status: hzPending ? "PENDING" : input.healthz.isError ? "FAIL" : hzOk ? "PASS" : "FAIL",
    source: "GET /healthz",
    remediation: "Restore API health; inspect process logs and listening port.",
  });

  const rzPending = input.readyz.isLoading;
  let readinessStatus: FirstRunStepStatus = "UNKNOWN";
  if (rzPending) readinessStatus = "PENDING";
  else if (input.readyz.isError && input.readyz.httpStatus !== 200) readinessStatus = "FAIL";
  else if (readyzStatus === "READY") readinessStatus = "PASS";
  else if (readyzStatus === "DEGRADED") readinessStatus = "WARN";
  else if (readyzStatus === "BLOCKED" || input.readyz.httpStatus === 503) readinessStatus = "FAIL";
  else if (input.readyz.body) readinessStatus = readyzBlockers > 0 ? "FAIL" : "WARN";

  steps.push({
    id: "readiness_probe",
    title: "Readiness probe (/readyz)",
    status: readinessStatus,
    source: "GET /readyz · status, blockers, warnings",
    remediation: "Resolve readiness blockers (ledger, auth, schema) using deployment readiness payload and CLI hints.",
    blockerCount: readyzBlockers,
    warningCount: readyzWarnings,
    generatedAtUtc: asString(input.readyz.body?.checked_at_utc) ?? undefined,
    digestPrefix: asString(input.readyz.body?.config_fingerprint)?.slice(0, 24) ?? undefined,
  });

  const ms = input.mutationSafety;
  const prod = isProductionRuntime(ms?.runtime_mode);
  let authStatus: FirstRunStepStatus = "UNKNOWN";
  if (ms == null) authStatus = "UNKNOWN";
  else if (!ms.mutation_routes_safe) authStatus = "FAIL";
  else if (prod && ms.authorization_mode !== "TOKEN_PROTECTED") authStatus = "FAIL";
  else if (prod && ms.authorization_mode === "TOKEN_PROTECTED") authStatus = "PASS";
  else if (!prod && ms.authorization_mode === "NON_PRODUCTION_BYPASS") authStatus = "WARN";
  else if (ms.authorization_mode === "TOKEN_PROTECTED") authStatus = "PASS";
  else authStatus = "WARN";

  steps.push({
    id: "production_auth",
    title: "Production auth configured safely",
    status: authStatus,
    source: "GET /ui/runtime · mutation_safety",
    remediation:
      "Production requires TOKEN_PROTECTED with mutation_routes_safe. Dev may show NON_PRODUCTION_BYPASS (WARN) — still fail-closed for unsafe server posture.",
  });

  steps.push({
    id: "ledger_configured",
    title: "Ledger path configured",
    status: depPending ? "PENDING" : depMissing ? "UNKNOWN" : ledgerConfiguredOk ? "PASS" : "FAIL",
    source: "GET /readiness/deployment · env overrides, ledger path, private key scan",
    remediation:
      "Set STRATEGY_VALIDATOR_LEDGER_DB_PATH and valid env overrides; remove private key material from the scanned tree.",
    blockerCount: depBlockers,
    warningCount: depWarnings,
  });

  steps.push({
    id: "migration_current",
    title: "Migrations applied (schema current)",
    status: depPending ? "PENDING" : migrationUnknown ? "UNKNOWN" : migrationOk ? "PASS" : "FAIL",
    source: "GET /readiness/deployment · schema_compatibility · GET /readyz · checks.schema_current",
    remediation: "Run strategy-validator-migrate --json or preflight with --prepare.",
  });

  const backupStatus: FirstRunStepStatus = depPending
    ? "PENDING"
    : depMissing
      ? "UNKNOWN"
      : backupConfigOk
        ? input.cockpit?.backup_restore_ok === false
          ? "WARN"
          : "PASS"
        : "FAIL";

  steps.push({
    id: "backup_restore",
    title: "Backup / restore evidence",
    status: backupStatus,
    source: "GET /readiness/deployment · backup roots · GET /ui/evidence cockpit backup_restore_ok",
    remediation:
      "Configure backup dir; run preflight with --verify-backup-restore; refresh /ui/evidence after publishing reports.",
    digestPrefix,
    generatedAtUtc: evidenceGenerated,
  });

  const smoke = input.cockpit?.api_smoke_ok;
  let smokeStatus: FirstRunStepStatus = "UNKNOWN";
  if (smoke === true) smokeStatus = "PASS";
  else if (smoke === false) smokeStatus = "FAIL";

  steps.push({
    id: "api_smoke",
    title: "API smoke evidence",
    status: smokeStatus,
    source: "GET /ui/evidence · api_smoke_ok, api_smoke_status",
    remediation: "Run strategy-validator-single-tenant-api-smoke with --require-pass; publish report under evidence search root.",
    generatedAtUtc: evidenceGenerated,
  });

  const ps = input.providerSetup.data?.summary;
  let providerStatus: FirstRunStepStatus = "UNKNOWN";
  if (input.providerSetup.isLoading) providerStatus = "PENDING";
  else if (input.providerSetup.isError) providerStatus = "UNKNOWN";
  else if (ps) {
    const blocked = Number(ps.blocked_count ?? 0);
    const actionReq = Number(ps.action_required_count ?? 0);
    const stale = Number(ps.stale_count ?? 0);
    const missingSecret = Number(ps.missing_secret_count ?? 0);
    const notChecked = Number(ps.not_checked_count ?? 0);
    if (blocked > 0) providerStatus = "FAIL";
    else if (actionReq > 0 || stale > 0 || missingSecret > 0 || notChecked > 0) providerStatus = "WARN";
    else providerStatus = "PASS";
  }

  steps.push({
    id: "provider_setup",
    title: "Provider setup reviewed",
    status: providerStatus,
    source: "GET /ui/provider-setup · summary counts (no secret values)",
    remediation: "Open /providers for row-level status; never paste secrets into the browser.",
    blockerCount: ps != null ? Number(ps.blocked_count ?? 0) : undefined,
    warningCount:
      ps != null
        ? Number(ps.action_required_count ?? 0) +
          Number(ps.stale_count ?? 0) +
          Number(ps.not_checked_count ?? 0) +
          Number(ps.missing_secret_count ?? 0)
        : undefined,
    generatedAtUtc: input.providerSetup.data?.generated_at_utc,
  });

  const pkg = input.facade.data?.frontend_package_present === true;
  const claimed = input.facade.data?.frontend_readiness_claimed === true;
  let feStatus: FirstRunStepStatus = "UNKNOWN";
  if (input.facade.isError || !input.facade.data) feStatus = "UNKNOWN";
  else if (claimed) feStatus = "PASS";
  else if (!pkg) feStatus = "WARN";
  else feStatus = "WARN";

  steps.push({
    id: "frontend_readiness",
    title: "Frontend readiness (package vs claim)",
    status: feStatus,
    source: "GET /ui/facade · frontend_package_present, frontend_readiness_claimed",
    remediation:
      "Package-present ≠ browser certified. Readiness claim is opt-in and not automatic production certification.",
  });

  const ds = input.cockpit?.deployment_status?.toUpperCase();
  let evidenceStatus: FirstRunStepStatus = "UNKNOWN";
  if (ds === "PASS" && input.cockpit?.deployment_evidence_ok === true) evidenceStatus = "PASS";
  else if (ds === "FAIL" || input.cockpit?.deployment_evidence_ok === false) evidenceStatus = "FAIL";
  else if (ds === "DEGRADED" || ds === "WARN") evidenceStatus = "WARN";

  if (evidenceStatus === "PASS" && chainIssues != null && chainIssues > 0) {
    evidenceStatus = "WARN";
  }

  steps.push({
    id: "deployment_evidence",
    title: "Deployment evidence present",
    status: evidenceStatus,
    source: "GET /ui/evidence · deployment manifest + registry digest · GET /ui/evidence-chain",
    remediation: "Run strategy-validator-single-tenant-evidence --require-pass --json after other gates pass.",
    digestPrefix,
    generatedAtUtc: evidenceGenerated,
    supplementalLine: chainSupplemental,
  });

  const sig = input.cockpit?.manual_operator_signoff_present;
  let signoffStatus: FirstRunStepStatus = "UNKNOWN";
  if (sig === true) signoffStatus = "PASS";
  else if (sig === false) signoffStatus = "PENDING";
  else signoffStatus = "UNKNOWN";

  steps.push({
    id: "operator_signoff",
    title: "Operator signoff",
    status: signoffStatus,
    source: "GET /ui/evidence · manual_operator_signoff_present · RUNTIME_REVIEW.json",
    remediation: "Signoff is artifact-backed only; this UI never posts signoff mutations.",
    generatedAtUtc: evidenceGenerated,
  });

  return steps;
}

export function firstRunTrustSummary(evidencePayload: Record<string, unknown> | null | undefined): {
  trustStatus: string;
  digestPrefix: string;
  searchRoot: string;
  warnings: string[];
} {
  const ev = evidencePayload ?? {};
  const ver = asRecord(ev.verification);
  const reg = asRecord(ev.registry);
  const trustStatus = asString(ver?.trust_status) ?? "UNKNOWN";
  const digest = asString(reg?.projection_digest_sha256);
  const searchRoot = asString(ev.search_root) ?? "—";
  const warnsRaw = ver?.integrity_warnings;
  const warnings = Array.isArray(warnsRaw) ? warnsRaw.map((x) => String(x)) : [];
  return {
    trustStatus,
    digestPrefix: digest ? digest.slice(0, 24) : "—",
    searchRoot,
    warnings,
  };
}
