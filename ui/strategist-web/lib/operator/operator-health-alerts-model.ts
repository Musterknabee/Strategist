/**
 * Read-plane operator health / alert derivation (no fabricated pass states).
 */
import type { UiEvidenceChainPayload, UiMutationSafetyStatus, UiProviderSetupConsolePayload } from "@/lib/api/types";
import type { UiEvidenceCockpitFields } from "@/lib/operator/ui-evidence-cockpit";
import { buildExecutionFirewallModel } from "@/lib/operator/execution-firewall-model";
import { asBool, asNumber, asRecord, asString, asStringArray, classifyProviderClassifiedStatus } from "@/lib/operator/payload-utils";

export type OperatorHealthAlertSeverity = "CRITICAL" | "WARNING" | "INFO" | "UNKNOWN";

export type OperatorHealthAlertCategory =
  | "Service Reachability"
  | "Readiness"
  | "Production Auth"
  | "Ledger / Evidence Chain"
  | "Provider Freshness"
  | "Deployment Evidence"
  | "Frontend Readiness"
  | "Release / CI Drift"
  | "Paper / Execution Firewall"
  | "Research OS Drift";

export type OperatorHealthAlert = {
  alert_id: string;
  severity: OperatorHealthAlertSeverity;
  category: OperatorHealthAlertCategory;
  status: string;
  summary: string;
  source_endpoint: string;
  evidence_digest_prefix: string;
  generated_at_utc: string;
  remediation: string;
  raw: Record<string, unknown>;
};

export type OperatorHealthAlertsInput = {
  healthz: { data: unknown; isError: boolean; isLoading: boolean };
  livez: { httpStatus: number | undefined; isError: boolean; isLoading: boolean };
  readyz: { httpStatus: number | undefined; body: Record<string, unknown> | null | undefined; isError: boolean; isLoading: boolean };
  runtimeBody: Record<string, unknown> | null;
  runtimeError: boolean;
  runtimeLoading: boolean;
  mutationSafety: UiMutationSafetyStatus | null;
  evidencePayload: Record<string, unknown> | null;
  evidenceError: boolean;
  evidenceLoading: boolean;
  cockpit: UiEvidenceCockpitFields | null;
  evidenceChain: { data: UiEvidenceChainPayload | null | undefined; isError: boolean; isLoading: boolean };
  providerSetup: { data: UiProviderSetupConsolePayload | null | undefined; isError: boolean; isLoading: boolean };
  providerHealth: Record<string, unknown> | null;
  providerHealthError: boolean;
  deploymentReadiness: Record<string, unknown> | null;
  deploymentReadinessError: boolean;
  deploymentReadinessLoading: boolean;
  facade: Record<string, unknown> | null;
  facadeError: boolean;
  facadeLoading: boolean;
  releaseReadiness: Record<string, unknown> | null;
  releaseReadinessError: boolean;
  releaseReadinessLoading: boolean;
  researchOsDrift: Record<string, unknown> | null;
  researchOsDriftError: boolean;
  researchOsDriftLoading: boolean;
  paperExecution: Record<string, unknown> | null;
  paperExecutionError: boolean;
  paperBroker: Record<string, unknown> | null;
  paperBrokerError: boolean;
};

export type OperatorHealthAlertsResult = {
  alerts: OperatorHealthAlert[];
  counts: Record<OperatorHealthAlertSeverity, number>;
  generated_at_utc: string;
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 14 ? `${s.slice(0, 12)}…` : s;
}

function isProductionRuntime(mode: string | undefined): boolean {
  if (!mode) return false;
  const u = mode.toUpperCase();
  return u.includes("PRODUCTION") && !u.includes("NON_PRODUCTION");
}

export function severityRank(s: OperatorHealthAlertSeverity): number {
  switch (s) {
    case "CRITICAL":
      return 0;
    case "WARNING":
      return 1;
    case "INFO":
      return 2;
    default:
      return 3;
  }
}

function push(
  out: OperatorHealthAlert[],
  id: string,
  severity: OperatorHealthAlertSeverity,
  category: OperatorHealthAlertCategory,
  status: string,
  summary: string,
  source_endpoint: string,
  digest: string,
  generated_at_utc: string,
  remediation: string,
  raw: Record<string, unknown>,
): void {
  out.push({
    alert_id: id,
    severity,
    category,
    status,
    summary,
    source_endpoint,
    evidence_digest_prefix: digest,
    generated_at_utc,
    remediation,
    raw,
  });
}

function maxUtc(...vals: (string | undefined)[]): string {
  const xs = vals.filter((x): x is string => !!x);
  if (!xs.length) return "UNKNOWN";
  return xs.sort().slice(-1)[0] ?? "UNKNOWN";
}

export function buildOperatorHealthAlerts(input: OperatorHealthAlertsInput): OperatorHealthAlertsResult {
  const alerts: OperatorHealthAlert[] = [];
  const rzBody = input.readyz.body;
  const readyStatus = asString(rzBody?.status)?.toUpperCase() ?? "";
  const readyBlockers = asStringArray(rzBody?.blockers);
  const readyWarnings = asStringArray(rzBody?.warnings);
  const rzChecked = asString(rzBody?.checked_at_utc);
  const rzFp = digestPrefix(rzBody?.config_fingerprint);

  const dep = input.deploymentReadiness;
  const depBlockers = Array.isArray(dep?.blocker_codes) ? (dep!.blocker_codes as unknown[]).length : 0;
  const depWarnings = Array.isArray(dep?.warning_codes) ? (dep!.warning_codes as unknown[]).length : 0;
  const depGenerated = asString(dep?.generated_at_utc);

  const ms = input.mutationSafety;
  const prod = isProductionRuntime(ms?.runtime_mode);
  const rtGenerated = asString(input.runtimeBody?.generated_at_utc);

  const ev = input.evidencePayload;
  const evGenerated = asString(ev?.generated_at_utc) ?? input.cockpit?.evidence_generated_at_utc;
  const evReg = asRecord(asRecord(ev)?.registry);
  const registryDigest = digestPrefix(evReg?.projection_digest_sha256);

  const chain = input.evidenceChain.data;
  const chainSummary = chain?.summary;
  const chainIssues = asNumber(chainSummary?.chain_issue_count_total) ?? 0;
  const decisionOk = chainSummary != null ? chainSummary.decision_ledger_chain_ok === true : null;
  const operatorOk = chainSummary != null ? chainSummary.operator_action_chain_ok === true : null;
  const chainGenerated = asString(chain?.generated_at_utc);

  const ps = input.providerSetup.data;
  const psSummary = ps?.summary;
  const staleCount = asNumber(psSummary?.stale_count) ?? 0;
  const blockedCount = asNumber(psSummary?.blocked_count) ?? 0;
  const psGenerated = asString(ps?.generated_at_utc);

  const facade = input.facade;
  const facadeClaimed = asBool(facade?.frontend_readiness_claimed) === true;

  const rel = input.releaseReadiness;
  const relStatus = asString(rel?.status)?.toUpperCase() ?? "";
  const relDegraded = asStringArray(rel?.degraded);
  const relGenerated = asString(rel?.generated_at_utc);

  const drift = input.researchOsDrift;
  const driftDegraded = asStringArray(drift?.degraded);
  const driftGenerated = asString(drift?.generated_at_utc);

  const pe = input.paperExecution;
  const peSummary = pe ? asRecord(pe.summary) : null;
  const peFresh = asString(peSummary?.evidence_freshness_status) ?? asString(peSummary?.latest_submission_evidence_freshness_status);
  const peGenerated = asString(pe?.generated_at_utc);

  const firewall = buildExecutionFirewallModel({
    paperExecution: input.paperExecution,
    paperBroker: input.paperBroker,
    paperTracking: null,
    providerSetup: input.providerSetup.data != null ? (input.providerSetup.data as unknown as Record<string, unknown>) : null,
    providerHealth: input.providerHealth,
    runtimeMutationSafety: input.mutationSafety,
    executionAuthorityHint: asString(input.runtimeBody?.execution_authority) ?? null,
    queryFailed:
      input.paperExecutionError ||
      input.paperBrokerError ||
      input.providerSetup.isError ||
      input.providerHealthError,
  });

  /** —— Service reachability —— */
  if (input.livez.isLoading) {
    push(
      alerts,
      "reachability:livez:pending",
      "UNKNOWN",
      "Service Reachability",
      "PENDING",
      "Liveness probe still loading",
      "GET /livez",
      "—",
      rzChecked ?? "UNKNOWN",
      "Wait for the liveness probe to complete or verify the API base URL.",
      { httpStatus: input.livez.httpStatus, isError: input.livez.isError },
    );
  } else if (input.livez.isError || input.livez.httpStatus !== 200) {
    push(
      alerts,
      "reachability:livez:fail",
      "CRITICAL",
      "Service Reachability",
      "DOWN",
      "Liveness probe failed or non-200 response",
      "GET /livez",
      "—",
      rzChecked ?? "UNKNOWN",
      "Start the API process or fix NEXT_PUBLIC_STRATEGIST_API_BASE_URL; confirm reverse proxy routes /livez.",
      { httpStatus: input.livez.httpStatus, isError: input.livez.isError },
    );
  }

  if (input.healthz.isLoading) {
    push(
      alerts,
      "reachability:healthz:pending",
      "UNKNOWN",
      "Service Reachability",
      "PENDING",
      "Health probe still loading",
      "GET /healthz",
      "—",
      rzChecked ?? "UNKNOWN",
      "Wait for /healthz or verify API reachability.",
      { isError: input.healthz.isError },
    );
  } else if (input.healthz.isError || input.healthz.data == null) {
    push(
      alerts,
      "reachability:healthz:fail",
      "CRITICAL",
      "Service Reachability",
      "DOWN",
      "Health probe failed or empty body",
      "GET /healthz",
      "—",
      rzChecked ?? "UNKNOWN",
      "Restore API health; inspect process logs and listening port.",
      { isError: input.healthz.isError, hasData: input.healthz.data != null },
    );
  }

  /** —— Readiness (/readyz + deployment tier) —— */
  if (input.readyz.isLoading) {
    push(
      alerts,
      "readiness:readyz:pending",
      "UNKNOWN",
      "Readiness",
      "PENDING",
      "Readiness payload still loading",
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "Wait for readiness results before treating the system as operational.",
      { status: readyStatus },
    );
  } else if (input.readyz.isError && input.readyz.httpStatus !== 200) {
    push(
      alerts,
      "readiness:readyz:http",
      "CRITICAL",
      "Readiness",
      "ERROR",
      "Readiness HTTP error",
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "Fix API readiness wiring; inspect load balancer and API logs.",
      { httpStatus: input.readyz.httpStatus },
    );
  } else if (readyStatus === "BLOCKED" || input.readyz.httpStatus === 503) {
    push(
      alerts,
      "readiness:readyz:blocked",
      "CRITICAL",
      "Readiness",
      "BLOCKED",
      "Readiness reports BLOCKED or HTTP 503",
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "Resolve readiness blockers (ledger, schema, auth) using /readyz blockers and deployment readiness checks.",
      { status: readyStatus, blockers: readyBlockers.slice(0, 12) },
    );
  } else if (readyBlockers.length > 0) {
    readyBlockers.slice(0, 8).forEach((b, i) => {
      push(
        alerts,
        `readiness:blocker:${i}`,
        "CRITICAL",
        "Readiness",
        "BLOCKER",
        b,
        "GET /readyz",
        rzFp,
        rzChecked ?? "UNKNOWN",
        "Clear the listed readiness blocker before treating the tenant as operational.",
        { blocker: b },
      );
    });
  } else if (readyStatus === "DEGRADED") {
    push(
      alerts,
      "readiness:readyz:degraded",
      "WARNING",
      "Readiness",
      "DEGRADED",
      "Readiness status DEGRADED",
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "Review /readyz warnings and checks; degraded tenants may still serve read-plane traffic.",
      { warnings: readyWarnings.slice(0, 12) },
    );
  } else if (readyWarnings.length > 0) {
    push(
      alerts,
      "readiness:readyz:warnings",
      "WARNING",
      "Readiness",
      "WARN",
      `${readyWarnings.length} readiness warning(s)`,
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "Inspect /readyz warnings for non-fatal configuration issues.",
      { warnings: readyWarnings.slice(0, 12) },
    );
  } else if (readyStatus === "READY" && !input.readyz.isError) {
    push(
      alerts,
      "readiness:readyz:ok",
      "INFO",
      "Readiness",
      "READY",
      "Readiness status READY",
      "GET /readyz",
      rzFp,
      rzChecked ?? "UNKNOWN",
      "No readiness blockers reported by /readyz.",
      { status: readyStatus },
    );
  }

  if (input.deploymentReadinessLoading) {
    push(
      alerts,
      "readiness:deployment:pending",
      "UNKNOWN",
      "Readiness",
      "PENDING",
      "Deployment readiness still loading",
      "GET /readiness/deployment",
      "—",
      depGenerated ?? "UNKNOWN",
      "Wait for deployment tier checks before assessing ledger paths.",
      {},
    );
  } else if (input.deploymentReadinessError || !dep) {
    push(
      alerts,
      "readiness:deployment:unknown",
      "UNKNOWN",
      "Readiness",
      "UNKNOWN",
      "Deployment readiness payload missing or query failed",
      "GET /readiness/deployment",
      "—",
      depGenerated ?? "UNKNOWN",
      "Run deployment readiness probe when API is reachable; fix query/auth if this request failed.",
      { isError: input.deploymentReadinessError },
    );
  } else if (depBlockers > 0) {
    push(
      alerts,
      "readiness:deployment:blockers",
      "CRITICAL",
      "Readiness",
      "BLOCKED",
      `Deployment tier reports ${depBlockers} blocker code(s)`,
      "GET /readiness/deployment",
      digestPrefix(dep?.content_digest),
      depGenerated ?? "UNKNOWN",
      "Resolve deployment readiness blocker_codes (ledger paths, secrets scan, schema).",
      { blocker_codes: dep?.blocker_codes },
    );
  } else if (depWarnings > 0) {
    push(
      alerts,
      "readiness:deployment:warnings",
      "WARNING",
      "Readiness",
      "WARN",
      `Deployment tier reports ${depWarnings} warning code(s)`,
      "GET /readiness/deployment",
      digestPrefix(dep?.content_digest),
      depGenerated ?? "UNKNOWN",
      "Review deployment warning_codes in the read-plane payload.",
      { warning_codes: dep?.warning_codes },
    );
  }

  /** —— Production auth —— */
  if (input.runtimeLoading) {
    push(
      alerts,
      "auth:runtime:pending",
      "UNKNOWN",
      "Production Auth",
      "PENDING",
      "Runtime / mutation safety still loading",
      "GET /ui/runtime",
      "—",
      rtGenerated ?? "UNKNOWN",
      "Wait for /ui/runtime before assessing production auth posture.",
      {},
    );
  } else if (input.runtimeError || !input.runtimeBody) {
    push(
      alerts,
      "auth:runtime:unknown",
      "UNKNOWN",
      "Production Auth",
      "UNKNOWN",
      "Runtime / mutation safety payload unavailable",
      "GET /ui/runtime",
      "—",
      rtGenerated ?? "UNKNOWN",
      "Fetch /ui/runtime when API is reachable to assess authorization posture.",
      { isError: input.runtimeError },
    );
  } else if (ms && !ms.mutation_routes_safe) {
    push(
      alerts,
      "auth:mutation_unsafe",
      "CRITICAL",
      "Production Auth",
      "UNSAFE",
      "mutation_routes_safe is false",
      "GET /ui/runtime · mutation_safety",
      digestPrefix(ms.detail_code),
      rtGenerated ?? "UNKNOWN",
      "Harden server mutation posture before exposing the API; follow detail_code from runtime payload.",
      {
        runtime_mode: ms.runtime_mode,
        authorization_mode: ms.authorization_mode,
        detail_code: ms.detail_code,
      },
    );
  } else if (prod && ms && ms.authorization_mode !== "TOKEN_PROTECTED") {
    push(
      alerts,
      "auth:prod:not_token",
      "CRITICAL",
      "Production Auth",
      "UNSAFE",
      "Production runtime without TOKEN_PROTECTED authorization",
      "GET /ui/runtime · mutation_safety",
      digestPrefix(ms.authorization_mode),
      rtGenerated ?? "UNKNOWN",
      "Production must use TOKEN_PROTECTED with mutation_routes_safe; fix deployment configuration.",
      { runtime_mode: ms.runtime_mode, authorization_mode: ms.authorization_mode },
    );
  } else if (prod && ms && ms.authorization_mode === "TOKEN_PROTECTED" && !ms.token_configured) {
    push(
      alerts,
      "auth:prod:token_missing",
      "CRITICAL",
      "Production Auth",
      "UNSAFE",
      "Production token-protected mode but token not configured server-side",
      "GET /ui/runtime · mutation_safety",
      "—",
      rtGenerated ?? "UNKNOWN",
      "Configure operator API token per deployment runbook; browser must not fabricate readiness.",
      { token_configured: ms.token_configured },
    );
  } else if (ms && ms.mutation_routes_safe && ms.authorization_mode === "TOKEN_PROTECTED") {
    push(
      alerts,
      "auth:token_ok",
      "INFO",
      "Production Auth",
      "SAFE",
      "Mutation routes gated; TOKEN_PROTECTED posture",
      "GET /ui/runtime · mutation_safety",
      digestPrefix(ms.detail_code),
      rtGenerated ?? "UNKNOWN",
      "Continue to verify browser token attachment for mutation calls when using the operator console.",
      { authorization_mode: ms.authorization_mode, token_configured: ms.token_configured },
    );
  }

  /** —— Ledger / evidence chain —— */
  if (input.evidenceChain.isLoading) {
    push(
      alerts,
      "ledger:chain:pending",
      "UNKNOWN",
      "Ledger / Evidence Chain",
      "PENDING",
      "Evidence chain projection loading",
      "GET /ui/evidence-chain",
      registryDigest,
      chainGenerated ?? "UNKNOWN",
      "Wait for evidence chain read-plane projection.",
      {},
    );
  } else if (input.evidenceChain.isError || !chain) {
    push(
      alerts,
      "ledger:chain:unknown",
      "UNKNOWN",
      "Ledger / Evidence Chain",
      "UNKNOWN",
      "Evidence chain unavailable or query failed",
      "GET /ui/evidence-chain",
      registryDigest,
      chainGenerated ?? "UNKNOWN",
      "Repair evidence chain read route or database connectivity; operator cannot verify ledger without this payload.",
      { isError: input.evidenceChain.isError },
    );
  } else if (chain.ok === false || decisionOk === false || operatorOk === false) {
    push(
      alerts,
      "ledger:chain:broken",
      "CRITICAL",
      "Ledger / Evidence Chain",
      "BROKEN",
      `Chain integrity issue (ok=${String(chain.ok)} decision_ledger_chain_ok=${String(decisionOk)} operator_action_chain_ok=${String(operatorOk)})`,
      "GET /ui/evidence-chain",
      registryDigest,
      chainGenerated ?? "UNKNOWN",
      "Investigate chain_issue_count_total and timeline entries; do not treat promotion or execution evidence as trusted.",
      {
        ok: chain.ok,
        chain_issue_count_total: chainIssues,
        decision_ledger_chain_ok: decisionOk,
        operator_action_chain_ok: operatorOk,
        digest_full: asString(evReg?.projection_digest_sha256) ?? null,
      },
    );
  } else if (chainIssues > 0) {
    push(
      alerts,
      "ledger:chain:issues",
      "WARNING",
      "Ledger / Evidence Chain",
      "WARN",
      `Evidence chain reports ${chainIssues} issue(s) while stream flags are true — review timeline`,
      "GET /ui/evidence-chain",
      registryDigest,
      chainGenerated ?? "UNKNOWN",
      "Open evidence chain timeline in inspector and reconcile issue_codes on recent entries.",
      { chain_issue_count_total: chainIssues, digest_full: asString(evReg?.projection_digest_sha256) ?? null },
    );
  } else {
    push(
      alerts,
      "ledger:chain:ok",
      "INFO",
      "Ledger / Evidence Chain",
      "OK",
      "Decision and operator action chains report OK",
      "GET /ui/evidence-chain",
      registryDigest,
      chainGenerated ?? "UNKNOWN",
      "Continue periodic verification; stale projections still require freshness checks elsewhere.",
      {
        event_count_total: chainSummary?.event_count_total,
        digest_full: asString(evReg?.projection_digest_sha256) ?? null,
      },
    );
  }

  if (input.cockpit?.ledger_integrity_ok === false) {
    push(
      alerts,
      "ledger:cockpit:integrity",
      "CRITICAL",
      "Ledger / Evidence Chain",
      "FAIL",
      "Evidence cockpit reports ledger_integrity_ok=false",
      "GET /ui/evidence",
      registryDigest,
      evGenerated ?? "UNKNOWN",
      "Run ledger integrity diagnostics from deployment runbook; treat attestation as untrusted until fixed.",
      { ledger_integrity_ok: false },
    );
  }

  /** —— Evidence / deployment cockpit —— */
  if (!input.evidenceLoading && (input.evidenceError || ev == null)) {
    push(
      alerts,
      "evidence:dashboard:missing",
      "UNKNOWN",
      "Deployment Evidence",
      "UNKNOWN",
      "Evidence dashboard payload missing or query failed",
      "GET /ui/evidence",
      registryDigest,
      evGenerated ?? "UNKNOWN",
      "Restore /ui/evidence read-plane; deployment and smoke summaries are unavailable.",
      { isError: input.evidenceError },
    );
  } else if (input.cockpit?.deployment_evidence_ok === false) {
    push(
      alerts,
      "evidence:deployment:fail",
      "CRITICAL",
      "Deployment Evidence",
      "FAIL",
      "deployment_evidence_ok is false",
      "GET /ui/evidence",
      registryDigest,
      evGenerated ?? "UNKNOWN",
      "Regenerate or restore deployment evidence pack; review deployment_status and manifest path fields.",
      { deployment_status: input.cockpit.deployment_status, deployment_evidence_ok: false },
    );
  } else if (input.cockpit?.ci_local_verify_ok === false) {
    push(
      alerts,
      "evidence:ci:verify",
      "WARNING",
      "Release / CI Drift",
      "FAIL",
      "ci_local_verify_ok is false in evidence cockpit",
      "GET /ui/evidence",
      registryDigest,
      evGenerated ?? "UNKNOWN",
      "Re-run local CI verify and refresh deployment evidence per release process.",
      { ci_local_verify_ok: false },
    );
  }

  const freshUpper = (peFresh || "").toUpperCase();
  if (freshUpper.includes("STALE") || freshUpper.includes("EXPIRED")) {
    push(
      alerts,
      "paper:evidence_freshness",
      "WARNING",
      "Paper / Execution Firewall",
      peFresh ?? "STALE",
      "Paper execution evidence freshness is not current",
      "GET /ui/paper-execution/latest",
      firewall.digest_prefix,
      peGenerated ?? firewall.generated_at_utc,
      "Refresh paper execution evidence bundle; treat operator submission receipts as stale.",
      { evidence_freshness_status: peFresh },
    );
  }

  if (firewall.blocker_count > 0) {
    push(
      alerts,
      "paper:firewall:blockers",
      "WARNING",
      "Paper / Execution Firewall",
      "BLOCKED",
      `Execution firewall aggregates ${firewall.blocker_count} blocker signal(s)`,
      "GET /ui/paper-execution/latest (+ broker/setup context in cockpit)",
      firewall.digest_prefix,
      firewall.generated_at_utc,
      "Review Capital / execution firewall pane and broker/provider setup before any capital authority discussion.",
      { blocker_count: firewall.blocker_count, recommended_review_action: firewall.recommended_review_action },
    );
  }

  /** —— Provider freshness —— */
  if (input.providerSetup.isLoading) {
    push(
      alerts,
      "provider:setup:pending",
      "UNKNOWN",
      "Provider Freshness",
      "PENDING",
      "Provider setup console still loading",
      "GET /ui/provider-setup",
      digestPrefix(ps?.samples_manifest_digest_prefix),
      psGenerated ?? "UNKNOWN",
      "Wait for provider setup projection.",
      {},
    );
  } else if (input.providerSetup.isError || !ps) {
    push(
      alerts,
      "provider:setup:unknown",
      "UNKNOWN",
      "Provider Freshness",
      "UNKNOWN",
      "Provider setup payload missing or query failed",
      "GET /ui/provider-setup",
      "—",
      psGenerated ?? "UNKNOWN",
      "Fix provider setup read route; cannot assess sample staleness without this payload.",
      { isError: input.providerSetup.isError },
    );
  } else if (staleCount > 0) {
    push(
      alerts,
      "provider:stale",
      "WARNING",
      "Provider Freshness",
      "STALE",
      `Provider setup reports stale_count=${staleCount}`,
      "GET /ui/provider-setup",
      digestPrefix(ps?.samples_manifest_digest_prefix),
      psGenerated ?? "UNKNOWN",
      "Refresh provider samples or re-run health checks; stale samples weaken research attestation.",
      { stale_count: staleCount },
    );
  } else if (blockedCount > 0) {
    push(
      alerts,
      "provider:blocked",
      "WARNING",
      "Provider Freshness",
      "BLOCKED",
      `Provider setup reports blocked_count=${blockedCount}`,
      "GET /ui/provider-setup",
      digestPrefix(ps?.samples_manifest_digest_prefix),
      psGenerated ?? "UNKNOWN",
      "Resolve broker/provider blockers in setup console before relying on execution-adjacent workflows.",
      { blocked_count: blockedCount },
    );
  }

  if (input.providerHealthError) {
    push(
      alerts,
      "provider:health:error",
      "WARNING",
      "Provider Freshness",
      "ERROR",
      "Provider health query failed",
      "GET /ui/provider-health",
      "—",
      psGenerated ?? "UNKNOWN",
      "Restore provider health read-plane to classify live sample freshness.",
      { isError: true },
    );
  } else {
    const entries = asRecord(input.providerHealth)?.entries;
    if (Array.isArray(entries)) {
      let bad = 0;
      let warn = 0;
      entries.forEach((e) => {
        const r = asRecord(e);
        if (!r) return;
        const cl = classifyProviderClassifiedStatus(asString(r.classified_status));
        if (cl === "bad") bad += 1;
        if (cl === "warn") warn += 1;
      });
      if (bad > 0) {
        push(
          alerts,
          "provider:health:bad",
          "WARNING",
          "Provider Freshness",
          "DEGRADED",
          `${bad} provider(s) classified as failing health checks`,
          "GET /ui/provider-health",
          digestPrefix(ps?.samples_manifest_digest_prefix),
          psGenerated ?? "UNKNOWN",
          "Inspect failing providers in Provider Matrix; fix credentials or network policy outside the browser.",
          { failing_count: bad },
        );
      } else if (warn > 0) {
        push(
          alerts,
          "provider:health:warn",
          "WARNING",
          "Provider Freshness",
          "PENDING",
          `${warn} provider(s) not fully verified (NOT_CHECKED / pending keys)`,
          "GET /ui/provider-health",
          digestPrefix(ps?.samples_manifest_digest_prefix),
          psGenerated ?? "UNKNOWN",
          "Complete provider setup checks; unknown classification is not approval to promote.",
          { warn_count: warn },
        );
      }
    }
  }

  /** —— Frontend readiness —— */
  if (input.facadeLoading) {
    /* defer facade-derived alerts until loaded */
  } else if (input.facadeError || !facade) {
    push(
      alerts,
      "frontend:facade:unknown",
      "UNKNOWN",
      "Frontend Readiness",
      "UNKNOWN",
      "UI facade payload missing or query failed",
      "GET /ui/facade",
      "—",
      asString(facade?.schema_version) ?? "UNKNOWN",
      "Restore /ui/facade; frontend packaging hints unavailable.",
      { isError: input.facadeError },
    );
  } else if (!facadeClaimed) {
    push(
      alerts,
      "frontend:readiness:unclaimed",
      "WARNING",
      "Frontend Readiness",
      "UNCLAIMED",
      "frontend_readiness_claimed is false",
      "GET /ui/facade",
      "—",
      asString(facade?.schema_version) ?? "UNKNOWN",
      "Backend has not observed a claimed frontend readiness bundle — follow operator console deployment checklist.",
      { frontend_readiness_claimed: false, frontend_status: facade.frontend_status },
    );
  } else {
    push(
      alerts,
      "frontend:readiness:claimed",
      "INFO",
      "Frontend Readiness",
      "CLAIMED",
      "frontend_readiness_claimed is true (backend-observed signal only)",
      "GET /ui/facade",
      "—",
      asString(facade?.schema_version) ?? "UNKNOWN",
      "This is not an approval to trade live; continue verifying auth, ledger, and paper execution boundaries.",
      { frontend_readiness_claimed: true },
    );
  }

  /** —— Release / CI drift —— */
  if (input.releaseReadinessLoading) {
    /* defer UNKNOWN until projection settles */
  } else if (input.releaseReadinessError || rel == null) {
    push(
      alerts,
      "release:readiness:unknown",
      "UNKNOWN",
      "Release / CI Drift",
      "UNKNOWN",
      "Research OS release readiness latest unavailable",
      "GET /ui/research-os/release-readiness/latest",
      "—",
      relGenerated ?? "UNKNOWN",
      "Fetch release readiness report via CLI when API read-plane is healthy.",
      { isError: input.releaseReadinessError },
    );
  } else if (relStatus === "MISSING" || relStatus === "NOT_PRESENT" || relDegraded.length > 0) {
    push(
      alerts,
      "release:readiness:degraded",
      "WARNING",
      "Release / CI Drift",
      relStatus || "DEGRADED",
      "Release readiness missing or degraded",
      "GET /ui/research-os/release-readiness/latest",
      digestPrefix(asRecord(rel?.latest)?.artifact_sha256),
      relGenerated ?? "UNKNOWN",
      "Generate research OS release readiness evidence before promotion discussions.",
      { status: relStatus, degraded: relDegraded.slice(0, 8) },
    );
  }

  /** —— Research OS drift —— */
  if (input.researchOsDriftLoading) {
    /* defer UNKNOWN until projection settles */
  } else if (input.researchOsDriftError || drift == null) {
    push(
      alerts,
      "ros:drift:unknown",
      "UNKNOWN",
      "Research OS Drift",
      "UNKNOWN",
      "Research OS drift latest unavailable",
      "GET /ui/research-os/drift/latest",
      "—",
      driftGenerated ?? "UNKNOWN",
      "Restore drift read-plane projection.",
      { isError: input.researchOsDriftError },
    );
  } else if (driftDegraded.length > 0) {
    push(
      alerts,
      "ros:drift:degraded",
      "WARNING",
      "Research OS Drift",
      "DEGRADED",
      "Research OS drift report missing or degraded",
      "GET /ui/research-os/drift/latest",
      digestPrefix(asRecord(drift?.latest)?.artifact_sha256),
      driftGenerated ?? "UNKNOWN",
      "Produce drift evidence to compare catalog vs workspace artifacts.",
      { degraded: driftDegraded.slice(0, 8) },
    );
  }

  alerts.sort((a, b) => {
    const d = severityRank(a.severity) - severityRank(b.severity);
    if (d !== 0) return d;
    const c = a.category.localeCompare(b.category);
    if (c !== 0) return c;
    return a.alert_id.localeCompare(b.alert_id);
  });

  const counts: Record<OperatorHealthAlertSeverity, number> = {
    CRITICAL: 0,
    WARNING: 0,
    INFO: 0,
    UNKNOWN: 0,
  };
  for (const a of alerts) {
    counts[a.severity] += 1;
  }

  const generated_at_utc = maxUtc(
    rzChecked,
    depGenerated,
    rtGenerated,
    evGenerated,
    chainGenerated,
    psGenerated,
    relGenerated,
    driftGenerated,
    peGenerated,
  );

  return { alerts, counts, generated_at_utc };
}
