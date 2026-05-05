/**
 * Read-plane risk gate normalization for operator cockpit.
 * Does not infer PASS from missing fields; does not mark strategies promotable.
 */
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  asStringArray,
  classifyProviderClassifiedStatus,
  readinessBlockerRows,
} from "@/lib/operator/payload-utils";

export type RiskGateCategory =
  | "Readiness"
  | "Production Policy"
  | "Auth Safety"
  | "Ledger / Evidence"
  | "Provider Freshness"
  | "Market Data Validity"
  | "Execution Realism"
  | "Robustness / Overfit Control"
  | "Benchmark Evidence"
  | "Paper / Live Safety";

export type RiskGateStatus = "PASS" | "WARN" | "FAIL" | "UNKNOWN" | "PENDING" | "CRITICAL";

export type RiskGateSeverity = "INFO" | "LOW" | "MED" | "HIGH" | "CRITICAL";

export type RiskGateEntry = {
  gate_id: string;
  label: string;
  category: RiskGateCategory;
  status: RiskGateStatus;
  severity: RiskGateSeverity;
  source_endpoint: string;
  evidence_digest_prefix?: string;
  generated_at_utc?: string;
  blocker_count: number;
  warning_count: number;
  remediation?: string;
  raw: Record<string, unknown>;
};

export type RiskPosture = "READY" | "DEGRADED" | "BLOCKED" | "UNKNOWN";

export type PolicyRiskGatesModel = {
  posture: RiskPosture;
  posture_reason: string;
  counts: { pass: number; warn: number; fail: number; unknown: number; pending: number; critical: number };
  gates: RiskGateEntry[];
  blocker_lines: string[];
  warning_lines: string[];
  freshness_summary: string;
  robustness_summary: string;
  execution_realism_summary: string;
  benchmark_summary: string;
  paper_safety_summary: string;
  next_review_hint: string;
};

export type PolicyRiskGatesInput = {
  readyzBody: Record<string, unknown> | null;
  readyzError: boolean;
  runtimeBody: Record<string, unknown> | null;
  mutationSafety: UiMutationSafetyStatus | null;
  facade: Record<string, unknown> | null;
  evidence: Record<string, unknown> | null;
  operatorActions: Record<string, unknown> | null;
  providerHealth: Record<string, unknown> | null;
  backtestForensics: Record<string, unknown> | null;
  paperExecution: Record<string, unknown> | null;
  paperTracking: Record<string, unknown> | null;
  queryFailed: boolean;
};

function digestPrefix(v: unknown): string | undefined {
  const s = asString(v);
  if (!s) return undefined;
  return s.length > 14 ? `${s.slice(0, 12)}…` : s;
}

function isProductionish(mode: string | undefined): boolean {
  const u = (mode || "").toUpperCase();
  return u.includes("PRODUCTION");
}

/** Map backend gate literals to UI status; missing → UNKNOWN (never PASS). */
export function interpretRiskLiteral(raw: string | undefined | null): RiskGateStatus {
  const u = (raw || "").trim().toUpperCase();
  if (!u) return "UNKNOWN";
  if (["PASS", "OK", "READY", "TRUE", "VERIFIED", "COMPLETE", "HEALTHY", "PROVEN"].includes(u)) return "PASS";
  if (["FAIL", "FAILED", "BLOCKED", "FALSE", "ERROR", "REJECTED", "FALSIFIED"].includes(u)) return "FAIL";
  if (["WARN", "WARNING", "STALE", "DEGRADED", "REVIEW", "LIMITED", "PENDING_MANUAL", "NOT_APPLICABLE"].includes(u)) return "WARN";
  if (["PENDING", "IN_PROGRESS", "QUEUED"].includes(u)) return "PENDING";
  if (["NOT_RUN", "UNKNOWN", "NOT_INVOKED", "NOT_PRESENT", "NOT_CHECKED", "MISSING", "SKIPPED"].includes(u)) return "UNKNOWN";
  return "UNKNOWN";
}

function worstStatus(a: RiskGateStatus, b: RiskGateStatus): RiskGateStatus {
  const rank: Record<RiskGateStatus, number> = {
    CRITICAL: 6,
    FAIL: 5,
    WARN: 4,
    PENDING: 3,
    UNKNOWN: 2,
    PASS: 1,
  };
  return rank[a] >= rank[b] ? a : b;
}

function foldStatuses(values: RiskGateStatus[]): RiskGateStatus {
  return values.reduce((acc, s) => worstStatus(acc, s), "PASS" as RiskGateStatus);
}

/** When no values, UNKNOWN — not PASS. */
function foldLiteralStatuses(raws: (string | undefined)[]): RiskGateStatus {
  if (!raws.length) return "UNKNOWN";
  return foldStatuses(raws.map((r) => interpretRiskLiteral(r)));
}

function entry(
  partial: Omit<RiskGateEntry, "raw"> & { raw?: Record<string, unknown> },
): RiskGateEntry {
  return {
    ...partial,
    raw: partial.raw ?? {},
  };
}

function derivePosture(gates: RiskGateEntry[], queryFailed: boolean, readyBlockers: number): { posture: RiskPosture; reason: string } {
  if (queryFailed) return { posture: "DEGRADED", reason: "READ_PLANE_QUERY_FAILED" };
  const crit = gates.filter((g) => g.status === "CRITICAL" || g.severity === "CRITICAL");
  if (crit.length) return { posture: "BLOCKED", reason: crit.map((c) => c.gate_id).join(",") };
  if (readyBlockers > 0) return { posture: "BLOCKED", reason: "READINESS_BLOCKERS_PRESENT" };
  const fail = gates.filter((g) => g.status === "FAIL");
  if (fail.length) return { posture: "BLOCKED", reason: fail.map((f) => f.gate_id).join(",") };
  const warnOrPending = gates.filter((g) => g.status === "WARN" || g.status === "PENDING");
  if (warnOrPending.length) return { posture: "DEGRADED", reason: "WARN_OR_PENDING_GATES_PRESENT" };
  const passCount = gates.filter((g) => g.status === "PASS").length;
  const unknownCount = gates.filter((g) => g.status === "UNKNOWN").length;
  if (gates.length && unknownCount === gates.length) return { posture: "UNKNOWN", reason: "ALL_GATES_UNPROVEN" };
  if (unknownCount > 0 && passCount === 0) return { posture: "UNKNOWN", reason: "NO_PASS_GATES" };
  if (unknownCount > 0) return { posture: "DEGRADED", reason: "PARTIAL_UNKNOWN_GATES" };
  const allPass = gates.length > 0 && gates.every((g) => g.status === "PASS");
  if (allPass) return { posture: "READY", reason: "ALL_GATES_PASS" };
  if (!gates.length) return { posture: "UNKNOWN", reason: "NO_GATE_EVIDENCE" };
  return { posture: "UNKNOWN", reason: "MIXED_OR_EMPTY_STATUS" };
}

export function filterPolicyRiskGatesByCategory(
  gates: RiskGateEntry[],
  cat: "ALL" | RiskGateCategory,
): RiskGateEntry[] {
  if (cat === "ALL") return gates;
  return gates.filter((g) => g.category === cat);
}

export function buildPolicyRiskGatesModel(input: PolicyRiskGatesInput): PolicyRiskGatesModel {
  const gates: RiskGateEntry[] = [];
  const blockerLines: string[] = [];
  const warningLines: string[] = [];

  const rb = input.readyzBody;
  const readyStatus = asString(rb?.status);
  const readyBlockers = readinessBlockerRows(rb?.blockers);
  const readyWarnings = readinessBlockerRows(rb?.warnings);
  for (const b of readyBlockers) blockerLines.push(`${b.code}: ${b.message}`);
  for (const w of readyWarnings) warningLines.push(`${w.code}: ${w.message}`);

  gates.push(
    entry({
      gate_id: "readyz.status",
      label: "Readiness aggregate status",
      category: "Readiness",
      status: readyStatus ? interpretRiskLiteral(readyStatus) : input.readyzError ? "WARN" : "UNKNOWN",
      severity: readyBlockers.length ? "CRITICAL" : readyStatus === "READY" ? "INFO" : "MED",
      source_endpoint: "/readyz",
      evidence_digest_prefix: digestPrefix(rb?.config_fingerprint),
      generated_at_utc: asString(rb?.checked_at_utc),
      blocker_count: readyBlockers.length,
      warning_count: readyWarnings.length,
      remediation: readyBlockers[0]?.remediation ?? readyBlockers[0]?.message,
      raw: { status: readyStatus, blockers: rb?.blockers, warnings: rb?.warnings },
    }),
  );

  const runtimeMode = input.mutationSafety?.runtime_mode ?? asString(input.runtimeBody?.environment);
  const prod = isProductionish(runtimeMode);
  const ms = input.mutationSafety;

  if (ms) {
    const authFail = !ms.mutation_routes_safe;
    const critical = prod && authFail;
    gates.push(
      entry({
        gate_id: "auth.mutation_surface",
        label: "Mutation route authorization surface",
        category: "Auth Safety",
        status: critical ? "CRITICAL" : authFail ? "FAIL" : ms.mutation_routes_safe ? "PASS" : "UNKNOWN",
        severity: critical ? "CRITICAL" : authFail ? "HIGH" : "INFO",
        source_endpoint: "/ui/runtime",
        evidence_digest_prefix: undefined,
        generated_at_utc: asString(input.runtimeBody?.generated_at_utc),
        blocker_count: authFail ? 1 : 0,
        warning_count: !prod && authFail ? 1 : 0,
        remediation: critical
          ? "Configure production API token and scopes; remove placeholder tokens."
          : authFail
            ? asString(ms.detail_code)
            : undefined,
        raw: { mutation_safety: ms },
      }),
    );

    if (prod && ms.authorization_mode === "MISCONFIGURED") {
      gates.push(
        entry({
          gate_id: "auth.production_misconfiguration",
          label: "Production auth configuration",
          category: "Auth Safety",
          status: "CRITICAL",
          severity: "CRITICAL",
          source_endpoint: "/ui/runtime",
          generated_at_utc: asString(input.runtimeBody?.generated_at_utc),
          blocker_count: 1,
          warning_count: 0,
          remediation: asString(ms.detail_code),
          raw: { mutation_safety: ms },
        }),
      );
    }

    if (prod && ms.token_configured === false && ms.authorization_mode !== "TOKEN_PROTECTED") {
      gates.push(
        entry({
          gate_id: "auth.production_token_missing",
          label: "Production mutation token",
          category: "Auth Safety",
          status: "CRITICAL",
          severity: "CRITICAL",
          source_endpoint: "/ui/runtime",
          blocker_count: 1,
          warning_count: 0,
          remediation: "STRATEGY_VALIDATOR_API_TOKEN must be set in production.",
          raw: { mutation_safety: ms },
        }),
      );
    }
  } else {
    gates.push(
      entry({
        gate_id: "auth.mutation_surface",
        label: "Mutation route authorization surface",
        category: "Auth Safety",
        status: "UNKNOWN",
        severity: "MED",
        source_endpoint: "/ui/runtime",
        blocker_count: 0,
        warning_count: 0,
        remediation: "Runtime mutation safety payload absent.",
        raw: {},
      }),
    );
  }

  const facade = input.facade;
  gates.push(
    entry({
      gate_id: "policy.read_plane_facade",
      label: "Facade read-plane contract",
      category: "Production Policy",
      status: asBool(facade?.read_plane_only) === true ? "PASS" : facade ? "WARN" : "UNKNOWN",
      severity: asBool(facade?.read_plane_only) === true ? "INFO" : "HIGH",
      source_endpoint: "/ui/facade",
      evidence_digest_prefix: digestPrefix(facade?.schema_version),
      generated_at_utc: asString(facade?.generated_at_utc),
      blocker_count: asBool(facade?.read_plane_only) === false ? 1 : 0,
      warning_count: 0,
      remediation: asBool(facade?.read_plane_only) === false ? "read_plane_only must remain true for operator UI." : undefined,
      raw: { facade: facade ?? {} },
    }),
  );

  gates.push(
    entry({
      gate_id: "policy.runtime_environment",
      label: "Runtime environment (validator mode)",
      category: "Production Policy",
      status: "UNKNOWN",
      severity: prod ? "HIGH" : "INFO",
      source_endpoint: "/ui/runtime",
      generated_at_utc: asString(input.runtimeBody?.generated_at_utc),
      blocker_count: 0,
      warning_count: 0,
      remediation: runtimeMode ? `Observed mode string: ${runtimeMode}` : "environment string absent from runtime payload.",
      raw: { environment: runtimeMode },
    }),
  );

  const ev = input.evidence;
  const verification = ev ? asRecord(ev.verification) : null;
  const registry = ev ? asRecord(ev.registry) : null;
  const lineage = ev ? asRecord(ev.lineage) : null;
  const projOk = asBool(verification?.projection_snapshot_verified);
  gates.push(
    entry({
      gate_id: "ledger.projection_verification",
      label: "Evidence registry projection verification",
      category: "Ledger / Evidence",
      status: projOk === true ? "PASS" : projOk === false ? "FAIL" : ev ? "UNKNOWN" : "UNKNOWN",
      severity: projOk === false ? "HIGH" : "INFO",
      source_endpoint: "/ui/evidence",
      evidence_digest_prefix: digestPrefix(registry?.projection_digest_sha256),
      generated_at_utc: asString(ev?.generated_at_utc),
      blocker_count: projOk === false ? 1 : 0,
      warning_count: asStringArray(lineage?.warnings).length + asStringArray(verification?.integrity_warnings).length,
      remediation: asString(verification?.lineage_reason),
      raw: {
        verification: verification ?? {},
        registry: registry ?? {},
        digest_full: asString(registry?.projection_digest_sha256),
      },
    }),
  );

  const op = input.operatorActions;
  const chainOk = asBool(op?.chain_ok);
  gates.push(
    entry({
      gate_id: "ledger.operator_journal_chain",
      label: "Operator action journal chain integrity",
      category: "Ledger / Evidence",
      status: chainOk === true ? "PASS" : chainOk === false ? "FAIL" : op ? "UNKNOWN" : "UNKNOWN",
      severity: chainOk === false ? "HIGH" : "INFO",
      source_endpoint: "/ui/operator-actions",
      evidence_digest_prefix: digestPrefix(op?.head_event_hash ?? op?.tail_event_hash),
      generated_at_utc: asString(op?.generated_at_utc),
      blocker_count: asNumber(op?.chain_issue_count) ?? 0,
      warning_count: asNumber(op?.rejected_event_count) ?? 0,
      raw: { operator_actions: op ?? {} },
    }),
  );

  const ph = input.providerHealth;
  const provEntries = Array.isArray(ph?.entries) ? ph.entries.map((e) => asRecord(e)).filter(Boolean) : [];
  let provWorst: RiskGateStatus = "UNKNOWN";
  let provBlockers = 0;
  let provWarn = 0;
  for (const row of provEntries) {
    const cls = classifyProviderClassifiedStatus(asString(row?.classified_status));
    if (cls === "bad") {
      provWorst = worstStatus(provWorst, "FAIL");
      provBlockers += 1;
    } else if (cls === "warn") {
      provWorst = worstStatus(provWorst, "WARN");
      provWarn += 1;
    } else if (cls === "ok") provWorst = worstStatus(provWorst, "PASS");
  }
  if (!provEntries.length) provWorst = ph ? "UNKNOWN" : "UNKNOWN";
  const execBlk = asStringArray(ph?.execution_workflow_blockers);
  provBlockers += execBlk.length;
  for (const x of execBlk) blockerLines.push(`provider.exec: ${x}`);
  gates.push(
    entry({
      gate_id: "provider.freshness_matrix",
      label: "Provider credential / freshness matrix",
      category: "Provider Freshness",
      status: execBlk.length ? worstStatus(provWorst, "FAIL") : provWorst,
      severity: provWorst === "FAIL" || execBlk.length ? "HIGH" : "INFO",
      source_endpoint: "/ui/provider-health",
      evidence_digest_prefix: digestPrefix(ph?.samples_manifest_digest_prefix),
      generated_at_utc: asString(ph?.generated_at_utc),
      blocker_count: provBlockers,
      warning_count: provWarn,
      remediation:
        provWorst === "FAIL"
          ? "Resolve AUTH_FAILED / rate limits before trusting execution paths."
          : execBlk.length
            ? "Clear execution workflow blockers on provider plane."
            : undefined,
      raw: { provider_health: ph ?? {} },
    }),
  );

  const ff = input.backtestForensics;
  const degradedFf = asStringArray(ff?.degraded);
  const strategies = Array.isArray(ff?.strategies)
    ? (ff.strategies as unknown[]).map((s) => asRecord(s)).filter((x): x is Record<string, unknown> => x != null)
    : [];
  const batch = ff ? asRecord(ff.batch) : null;
  const summary = ff ? asRecord(ff.summary) : null;
  const ffGen = asString(ff?.generated_at_utc);

  if (!ff || degradedFf.includes("NO_BATCH_ARTIFACTS") || !summary?.batch_present) {
    gates.push(
      entry({
        gate_id: "forensics.batch_presence",
        label: "Strategy batch / forensics evidence",
        category: "Market Data Validity",
        status: "UNKNOWN",
        severity: "MED",
        source_endpoint: "/ui/backtest-forensics/latest",
        generated_at_utc: ffGen,
        blocker_count: 0,
        warning_count: degradedFf.length,
        remediation: "No batch artifacts under scan root; forensics gates remain unproven.",
        raw: { degraded: degradedFf, summary: summary ?? {} },
      }),
    );
  } else {
    const dataPlanes = strategies.map((s) => asString(s.data_plane));
    const pitStatuses = strategies.map((s) => asString(s.pit_status));
    const dataStatuses = strategies.map((s) => asString(s.data_status));
    const planeWorst = foldLiteralStatuses(dataPlanes);
    const pitWorst = foldLiteralStatuses(pitStatuses);
    const dataWorst = foldLiteralStatuses(dataStatuses);

    let marketStatus: RiskGateStatus = worstStatus(planeWorst, worstStatus(pitWorst, dataWorst));
    if (dataPlanes.some((p) => p === "SYNTHETIC")) marketStatus = worstStatus(marketStatus, "WARN");
    if (dataPlanes.some((p) => p === "PROVIDER_SNAPSHOT")) marketStatus = worstStatus(marketStatus, "WARN");

    gates.push(
      entry({
        gate_id: "market.data_plane",
        label: "Market data plane / PIT posture (batch aggregate)",
        category: "Market Data Validity",
        status: marketStatus,
        severity: marketStatus === "FAIL" ? "HIGH" : "MED",
        source_endpoint: "/ui/backtest-forensics/latest",
        evidence_digest_prefix: digestPrefix(batch?.run_id),
        generated_at_utc: ffGen,
        blocker_count: strategies.filter((s) => asString(s.status) === "BLOCKED").length,
        warning_count: (asNumber(summary?.synthetic_count) ?? 0) + (asNumber(summary?.provider_snapshot_count) ?? 0),
        remediation:
          dataPlanes.some((p) => p === "SYNTHETIC" || p === "PROVIDER_SNAPSHOT")
            ? "Synthetic or snapshot data is not live-ready; treat as research-only."
            : undefined,
        raw: { data_planes: dataPlanes, pit_statuses: pitStatuses },
      }),
    );

    const execGates = strategies.map((s) => {
      const gm = asRecord(s.gate_matrix);
      return asString(gm?.execution_realism_gate) ?? asString(asRecord(s.execution_realism)?.gate_status);
    });
    const execWorst = foldLiteralStatuses(execGates);
    gates.push(
      entry({
        gate_id: "exec.realism_gate",
        label: "Execution realism gate (aggregate)",
        category: "Execution Realism",
        status: execWorst,
        severity: execWorst === "FAIL" ? "HIGH" : "MED",
        source_endpoint: "/ui/backtest-forensics/latest",
        evidence_digest_prefix: digestPrefix(strategies[0]?.strategy_id),
        generated_at_utc: ffGen,
        blocker_count: execGates.filter((g) => interpretRiskLiteral(g) === "FAIL").length,
        warning_count: execGates.filter((g) => interpretRiskLiteral(g) === "WARN").length,
        raw: { execution_realism_gates: execGates },
      }),
    );

    const robGates = strategies.map((s) => {
      const gm = asRecord(s.gate_matrix);
      return asString(gm?.robustness_gate) ?? asString(asRecord(s.robustness)?.gate_status);
    });
    const cpcvGates = strategies.map((s) => {
      const gm = asRecord(s.gate_matrix);
      return asString(gm?.cpcv_robustness_gate) ?? asString(asRecord(s.robustness)?.cpcv_gate_status);
    });
    const robWorst = foldLiteralStatuses(robGates);
    const cpcvWorst = foldLiteralStatuses(cpcvGates);
    gates.push(
      entry({
        gate_id: "robustness.core_gate",
        label: "Robustness / CPCV gates (aggregate)",
        category: "Robustness / Overfit Control",
        status: worstStatus(robWorst, cpcvWorst),
        severity: "MED",
        source_endpoint: "/ui/backtest-forensics/latest",
        evidence_digest_prefix: digestPrefix(asRecord(asRecord(strategies[0]?.artifacts)?.observed_sha256)?.cpcv),
        generated_at_utc: ffGen,
        blocker_count: [...robGates, ...cpcvGates].filter((g) => interpretRiskLiteral(g) === "FAIL").length,
        warning_count: [...robGates, ...cpcvGates].filter((g) => interpretRiskLiteral(g) === "WARN").length,
        raw: { robustness_gate: robGates, cpcv_gate: cpcvGates },
      }),
    );

    const pboVals = strategies.map((s) => asNumber(asRecord(s.robustness)?.pbo_like_score)).filter((n) => n !== undefined) as number[];
    const dsrVals = strategies.map((s) => asNumber(asRecord(s.robustness)?.dsr_like_score)).filter((n) => n !== undefined) as number[];
    const decoyPasses = strategies.map((s) => {
      const gm = asRecord(s.gate_matrix);
      const dec = gm ? asBool((gm as { decoy_survival_passed?: unknown }).decoy_survival_passed) : undefined;
      return dec;
    });
    const decoyDefined = decoyPasses.filter((d) => d !== undefined);
    const hasDecoyField = decoyDefined.length > 0;
    let decoyStatus: RiskGateStatus = "UNKNOWN";
    if (hasDecoyField) {
      if (decoyDefined.some((d) => d === false)) decoyStatus = "FAIL";
      else if (decoyDefined.every((d) => d === true)) decoyStatus = "PASS";
      else decoyStatus = "UNKNOWN";
    } else if (pboVals.length || dsrVals.length) decoyStatus = "UNKNOWN";
    gates.push(
      entry({
        gate_id: "robustness.pbo_dsr_decoy",
        label: "PBO / DSR / decoy evidence",
        category: "Robustness / Overfit Control",
        status: decoyStatus,
        severity: "MED",
        source_endpoint: "/ui/backtest-forensics/latest",
        generated_at_utc: ffGen,
        blocker_count: decoyDefined.filter((d) => d === false).length,
        warning_count: 0,
        remediation: !hasDecoyField && !pboVals.length && !dsrVals.length ? "No PBO/DSR/decoy fields in forensic rows." : undefined,
        raw: { pbo_like_score: pboVals, dsr_like_score: dsrVals, decoy_survival_passed: decoyPasses },
      }),
    );

    const promoReasons: string[] = [];
    for (const s of strategies) {
      const rs = asStringArray(s.promotion_blocked_reasons);
      for (const r of rs) {
        if (!promoReasons.includes(r)) promoReasons.push(r);
      }
      for (const b of asStringArray(s.blockers)) {
        if (!promoReasons.includes(b)) promoReasons.push(b);
      }
    }
    for (const r of promoReasons.slice(0, 12)) blockerLines.push(`promotion:${r}`);

    const benchIds = strategies
      .map((s) => asString(asRecord(s.metrics)?.benchmark_id) ?? asString(asRecord(s.gate_matrix)?.benchmark_id))
      .filter(Boolean);
    const benchDelta = strategies.map((s) => asNumber(asRecord(s.metrics)?.benchmark_delta)).filter((n) => n !== undefined) as number[];
    const anyPromotionEligible = strategies.some((s) => asBool(asRecord(s.gate_matrix)?.promotion_eligible) === true);
    let benchStatus: RiskGateStatus = "UNKNOWN";
    if (benchIds.length) benchStatus = anyPromotionEligible ? "PASS" : "WARN";
    gates.push(
      entry({
        gate_id: "benchmark.context",
        label: "Benchmark context (forensic metrics)",
        category: "Benchmark Evidence",
        status: benchStatus,
        severity: "INFO",
        source_endpoint: "/ui/backtest-forensics/latest",
        generated_at_utc: ffGen,
        blocker_count: 0,
        warning_count: benchStatus === "WARN" ? 1 : benchIds.length ? 0 : 1,
        remediation: benchIds.length
          ? anyPromotionEligible
            ? undefined
            : "benchmark_id present without promotion_eligible=true in gate_matrix; promotability not established here."
          : "No benchmark_id on forensic metrics; compatibility unproven.",
        raw: { benchmark_ids: benchIds, benchmark_delta: benchDelta },
      }),
    );
  }

  const pt = input.paperTracking;
  const ptBundle = pt?.latest != null ? asRecord(pt.latest as object) : null;
  const ptScore = ptBundle?.scorecard != null ? asRecord(ptBundle.scorecard as object) : null;
  const benchReturn = asNumber(ptScore?.benchmark_return_1d);

  const ptGen = asString(pt?.generated_at_utc);
  if (benchReturn !== undefined || ptScore) {
    gates.push(
      entry({
        gate_id: "benchmark.paper_tracking_scorecard",
        label: "Paper tracking scorecard benchmark fields",
        category: "Benchmark Evidence",
        status: benchReturn !== undefined ? "PASS" : "UNKNOWN",
        severity: "INFO",
        source_endpoint: "/ui/paper-tracking/latest",
        evidence_digest_prefix: digestPrefix(ptBundle?.tracking_id),
        generated_at_utc: ptGen,
        blocker_count: 0,
        warning_count: benchReturn === undefined ? 1 : 0,
        raw: { scorecard: ptScore ?? {} },
      }),
    );
  }

  const pe = input.paperExecution;
  const peSummary = pe ? asRecord(pe.summary) : null;
  gates.push(
    entry({
      gate_id: "paper.execution_cockpit",
      label: "Paper execution safety envelope",
      category: "Paper / Live Safety",
      status: pe ? (asBool(pe.no_live_trading) === true ? "PASS" : "WARN") : "UNKNOWN",
      severity: "HIGH",
      source_endpoint: "/ui/paper-execution/latest",
      evidence_digest_prefix: digestPrefix(peSummary?.latest_evidence_bundle_sha256),
      generated_at_utc: asString(pe?.generated_at_utc),
      blocker_count:
        (asNumber(peSummary?.submission_guard_blocker_count) ?? 0) +
        (asNumber(peSummary?.evidence_bundle_blocker_count) ?? 0),
      warning_count: (asNumber(peSummary?.timeline_warning_count) ?? 0) + (asNumber(peSummary?.position_reconciliation_warning_count) ?? 0),
      remediation: asString(peSummary?.broker_policy_status),
      raw: { summary: peSummary ?? {}, no_live_trading: pe?.no_live_trading },
    }),
  );

  const counts = gates.reduce(
    (acc, g) => {
      acc.pass += g.status === "PASS" ? 1 : 0;
      acc.warn += g.status === "WARN" ? 1 : 0;
      acc.fail += g.status === "FAIL" ? 1 : 0;
      acc.unknown += g.status === "UNKNOWN" ? 1 : 0;
      acc.pending += g.status === "PENDING" ? 1 : 0;
      acc.critical += g.status === "CRITICAL" ? 1 : 0;
      return acc;
    },
    { pass: 0, warn: 0, fail: 0, unknown: 0, pending: 0, critical: 0 },
  );

  const { posture, reason } = derivePosture(gates, input.queryFailed, readyBlockers.length);

  const freshness_summary = (() => {
    if (!ph) return "UNKNOWN · provider health not loaded.";
    return `providers=${provEntries.length} worst=${provWorst} exec_workflow_blockers=${execBlk.length}`;
  })();

  const robustness_summary = (() => {
    if (!strategies.length) return "UNKNOWN · no forensic strategy rows.";
    const rob = strategies.map((s) => asString(asRecord(s.gate_matrix)?.robustness_gate));
    const cpcv = strategies.map((s) => asString(asRecord(s.gate_matrix)?.cpcv_robustness_gate));
    return `robustness_gate=${foldLiteralStatuses(rob)} cpcv=${foldLiteralStatuses(cpcv)}`;
  })();

  const execution_realism_summary = (() => {
    if (!strategies.length) return "UNKNOWN · no forensic strategy rows.";
    const eg = strategies.map((s) => asString(asRecord(s.gate_matrix)?.execution_realism_gate));
    return `execution_realism_gate=${foldLiteralStatuses(eg)}`;
  })();

  const benchmark_summary = (() => {
    const parts: string[] = [];
    if (strategies.length) {
      const ids = strategies
        .map((s) => asString(asRecord(s.metrics)?.benchmark_id) ?? asString(asRecord(s.gate_matrix)?.benchmark_id))
        .filter(Boolean);
      parts.push(ids.length ? `forensic_benchmark_ids=${ids.slice(0, 3).join(",")}` : "forensic_benchmark_ids=NONE");
    } else parts.push("forensics=ABSENT");
    if (benchReturn !== undefined) parts.push(`paper_benchmark_return_1d=${benchReturn}`);
    else parts.push("paper_benchmark_return_1d=UNKNOWN");
    return parts.join(" · ");
  })();

  const paper_safety_summary = (() => {
    if (!peSummary) return "UNKNOWN · paper execution summary absent.";
    return `no_live_trading=${String(pe?.no_live_trading)} broker_policy=${asString(peSummary.broker_policy_status) ?? "UNKNOWN"} freshness=${asString(peSummary.evidence_freshness_status) ?? "UNKNOWN"}`;
  })();

  const next_review_hint = (() => {
    const crit = gates.find((g) => g.status === "CRITICAL");
    if (crit) return `Review CRITICAL gate: ${crit.label}`;
    if (readyBlockers.length) return `Resolve readiness blockers (${readyBlockers[0]?.code}).`;
    const fail = gates.find((g) => g.status === "FAIL");
    if (fail) return `Review FAIL gate: ${fail.label}`;
    if (counts.unknown > counts.pass) return "Close UNKNOWN gates with additional read-plane evidence.";
    if (counts.warn) return "Triage WARN gates (stale providers, snapshot data, or policy drift).";
    return "No immediate gate-driven review (still verify authority outside UI).";
  })();

  return {
    posture,
    posture_reason: reason,
    counts,
    gates,
    blocker_lines: blockerLines.slice(0, 24),
    warning_lines: warningLines.slice(0, 16),
    freshness_summary,
    robustness_summary,
    execution_realism_summary,
    benchmark_summary,
    paper_safety_summary,
    next_review_hint,
  };
}
