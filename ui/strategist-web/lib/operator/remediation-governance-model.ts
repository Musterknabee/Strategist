/**
 * Read-plane incident / remediation / exception governance (no resolver authority in-browser).
 */
import { severityRank } from "@/lib/operator/operator-health-alerts-model";
import { asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";

export type GovernanceExceptionSemantics =
  | "NO_EXCEPTION"
  | "EXCEPTION_ACTIVE"
  | "EXCEPTION_EXPIRED"
  | "EXCEPTION_UNSCOPED"
  | "EXCEPTION_UNVERIFIED"
  | "EXCEPTION_UNKNOWN";

export type GovernanceRemediationSemantics =
  | "REMEDIATION_PROPOSED"
  | "REMEDIATION_IN_PROGRESS"
  | "REMEDIATION_COMPLETE"
  | "REMEDIATION_UNVERIFIED"
  | "REMEDIATION_MISSING"
  | "UNKNOWN";

export type GovernanceItemCategory =
  | "Readiness Blocker"
  | "Provider / Freshness"
  | "Evidence Drift"
  | "Policy Gate"
  | "Release Readiness"
  | "Research OS Exception"
  | "Remediation"
  | "Review Journal"
  | "Unknown";

export type GovernanceItem = {
  item_id: string;
  category: GovernanceItemCategory;
  severity: "CRITICAL" | "WARNING" | "INFO" | "UNKNOWN";
  status: string;
  blocker_code: string;
  exception_semantics: GovernanceExceptionSemantics;
  exception_scope: string;
  exception_expiry: string;
  remediation_semantics: GovernanceRemediationSemantics;
  owner_operator: string;
  generated_at_utc: string;
  evidence_digest_prefix: string;
  recommended_next_action: string;
  raw: Record<string, unknown>;
};

export type RemediationGovernanceInput = {
  readyzBody: Record<string, unknown> | null;
  readyzLoading: boolean;
  readyzError: boolean;
  deployment: Record<string, unknown> | null;
  deploymentLoading: boolean;
  deploymentError: boolean;
  policyGatePayload: unknown;
  policyGateLoading: boolean;
  policyGateError: boolean;
  exceptionPayload: unknown;
  exceptionLoading: boolean;
  exceptionError: boolean;
  remediationPayload: unknown;
  remediationLoading: boolean;
  remediationError: boolean;
  drift: Record<string, unknown> | null;
  driftLoading: boolean;
  driftError: boolean;
  releaseReadiness: Record<string, unknown> | null;
  releaseLoading: boolean;
  releaseError: boolean;
  reviewJournal: Record<string, unknown> | null;
  reviewJournalLoading: boolean;
  reviewJournalError: boolean;
  providerStaleCount: number | null;
  providerBlockedCount: number | null;
};

export type RemediationGovernanceResult = {
  items: GovernanceItem[];
  counts: Record<"CRITICAL" | "WARNING" | "INFO" | "UNKNOWN", number>;
  generated_at_utc: string;
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 14 ? `${s.slice(0, 12)}…` : s;
}

/** Hooks vary: some return `{ data: T }`, others return `T` at root. */
export function unwrapApiPayload(v: unknown): Record<string, unknown> | null {
  const r = asRecord(v);
  if (!r) return null;
  const inner = asRecord(r.data);
  if (inner && (typeof inner.schema_version === "string" || "latest" in inner || "degraded" in inner)) {
    return inner;
  }
  return r;
}

function maxUtc(...xs: (string | undefined)[]): string {
  const ok = xs.filter((x): x is string => !!x);
  return ok.length ? ok.sort().slice(-1)[0]! : "UNKNOWN";
}

function mapRemediationSemantics(plan: Record<string, unknown> | null, trust: string | undefined): GovernanceRemediationSemantics {
  if (!plan) return "REMEDIATION_MISSING";
  const st = asString(plan.status)?.toUpperCase() ?? "";
  const t = (trust || "").toUpperCase();
  const complete = st.includes("COMPLETE") || st.includes("DONE") || st.includes("CLOSED");
  if (complete && t && t !== "TRUSTED" && t !== "TRUST_RESTRICTED") return "REMEDIATION_UNVERIFIED";
  if (complete) return "REMEDIATION_COMPLETE";
  if (t && t !== "TRUSTED" && t !== "TRUST_RESTRICTED") return "REMEDIATION_UNVERIFIED";
  if (st.includes("OPEN") || st.includes("PROGRESS")) return "REMEDIATION_IN_PROGRESS";
  if (st.includes("DRAFT") || st.includes("PROPOSE")) return "REMEDIATION_PROPOSED";
  return "UNKNOWN";
}

function parseGlobalException(latest: Record<string, unknown> | null): {
  semantics: GovernanceExceptionSemantics;
  scope: string;
  expiry: string;
  operatorId: string;
} {
  if (!latest) {
    return { semantics: "NO_EXCEPTION", scope: "—", expiry: "—", operatorId: "—" };
  }
  const status = asString(latest.status)?.toUpperCase() ?? "";
  const exp = asString(latest.expires_at_utc) ?? "—";
  const constraints = asStringArray(latest.constraints);
  const trust = asString(latest.trust_banner)?.toUpperCase() ?? "";
  const operatorId = asString(latest.operator_id) ?? "—";

  if (exp !== "—" && !Number.isNaN(Date.parse(exp)) && Date.parse(exp) < Date.now()) {
    return { semantics: "EXCEPTION_EXPIRED", scope: String(constraints.length), expiry: exp, operatorId };
  }
  if (status === "ACTIVE" && constraints.length === 0) {
    return { semantics: "EXCEPTION_UNSCOPED", scope: "NONE", expiry: exp, operatorId };
  }
  if (trust && trust !== "TRUSTED" && trust !== "TRUST_RESTRICTED") {
    return { semantics: "EXCEPTION_UNVERIFIED", scope: String(constraints.length), expiry: exp, operatorId };
  }
  if (status === "ACTIVE") {
    return { semantics: "EXCEPTION_ACTIVE", scope: String(constraints.length), expiry: exp, operatorId };
  }
  if (!status) {
    return { semantics: "EXCEPTION_UNKNOWN", scope: "—", expiry: exp, operatorId };
  }
  return { semantics: "NO_EXCEPTION", scope: String(constraints.length), expiry: exp, operatorId };
}

function blockerOverlay(
  blocker: string,
  exLatest: Record<string, unknown> | null,
  global: ReturnType<typeof parseGlobalException>,
): GovernanceExceptionSemantics {
  if (global.semantics === "EXCEPTION_EXPIRED" || global.semantics === "EXCEPTION_UNSCOPED" || global.semantics === "EXCEPTION_UNVERIFIED") {
    return global.semantics;
  }
  if (global.semantics === "EXCEPTION_ACTIVE") {
    const residual = exLatest ? asStringArray(exLatest.residual_blockers) : [];
    return residual.includes(blocker) ? "EXCEPTION_ACTIVE" : "EXCEPTION_UNKNOWN";
  }
  return "NO_EXCEPTION";
}

function severityForReadinessBlocker(ex: GovernanceExceptionSemantics): "CRITICAL" | "WARNING" | "INFO" | "UNKNOWN" {
  if (ex === "EXCEPTION_EXPIRED" || ex === "EXCEPTION_UNSCOPED") return "CRITICAL";
  if (ex === "EXCEPTION_ACTIVE") return "WARNING";
  if (ex === "EXCEPTION_UNVERIFIED") return "WARNING";
  if (ex === "EXCEPTION_UNKNOWN") return "CRITICAL";
  return "CRITICAL";
}

function pushItem(
  out: GovernanceItem[],
  id: string,
  category: GovernanceItemCategory,
  severity: GovernanceItem["severity"],
  status: string,
  blocker: string,
  ex: GovernanceExceptionSemantics,
  scope: string,
  exp: string,
  rem: GovernanceRemediationSemantics,
  owner: string,
  gen: string,
  digest: string,
  next: string,
  raw: Record<string, unknown>,
): void {
  out.push({
    item_id: id,
    category,
    severity,
    status,
    blocker_code: blocker,
    exception_semantics: ex,
    exception_scope: scope,
    exception_expiry: exp,
    remediation_semantics: rem,
    owner_operator: owner,
    generated_at_utc: gen,
    evidence_digest_prefix: digest,
    recommended_next_action: next,
    raw,
  });
}

export function buildRemediationGovernanceItems(input: RemediationGovernanceInput): RemediationGovernanceResult {
  const items: GovernanceItem[] = [];
  const genTimes: string[] = [];

  const remRoot = input.remediationLoading || input.remediationError ? null : unwrapApiPayload(input.remediationPayload);
  const remLatest = remRoot?.latest != null ? asRecord(remRoot.latest) : null;
  const remTrust = asString(remLatest?.trust_banner);
  const remSem = mapRemediationSemantics(remLatest, remTrust);
  const exRoot = input.exceptionLoading || input.exceptionError ? null : unwrapApiPayload(input.exceptionPayload);
  const exLatest = exRoot?.latest != null ? asRecord(exRoot.latest) : null;
  const globalEx = parseGlobalException(exLatest);
  const remDigest =
    digestPrefix(remLatest?.manifest_sha256) !== "—"
      ? digestPrefix(remLatest?.manifest_sha256)
      : digestPrefix(remLatest?.remediation_spine_sha256);
  const remActions = remLatest ? asStringArray(remLatest.recommended_next_actions).slice(0, 3).join(" · ") : "";

  const pgRoot = input.policyGateLoading || input.policyGateError ? null : unwrapApiPayload(input.policyGatePayload);
  const pgLatest = pgRoot?.latest != null ? asRecord(pgRoot.latest) : null;

  if (exRoot) genTimes.push(asString(exRoot.generated_at_utc) ?? "");
  if (remRoot) genTimes.push(asString(remRoot.generated_at_utc) ?? "");
  if (pgRoot) genTimes.push(asString(pgRoot.generated_at_utc) ?? "");

  if (input.exceptionLoading) {
    pushItem(
      items,
      "exception:pending",
      "Research OS Exception",
      "UNKNOWN",
      "PENDING",
      "EXCEPTION_PAYLOAD",
      "EXCEPTION_UNKNOWN",
      "—",
      "—",
      "REMEDIATION_MISSING",
      "—",
      "UNKNOWN",
      "—",
      "Wait for /ui/research-os/exceptions/latest",
      { pending: true },
    );
  } else if (input.exceptionError || !exRoot) {
    pushItem(
      items,
      "exception:unknown",
      "Research OS Exception",
      "UNKNOWN",
      "UNKNOWN",
      "EXCEPTION_PAYLOAD",
      "EXCEPTION_UNKNOWN",
      "—",
      "—",
      "REMEDIATION_MISSING",
      "—",
      "UNKNOWN",
      "—",
      "Restore exceptions read-plane or run CLI to publish governed exception evidence.",
      { isError: input.exceptionError },
    );
  } else if (exLatest) {
    const st = asString(exLatest.status) ?? "UNKNOWN";
    const next =
      globalEx.semantics === "EXCEPTION_EXPIRED"
        ? "Close or renew governed exception via CLI; treat residual risk as unmitigated until renewed."
        : globalEx.semantics === "EXCEPTION_UNSCOPED"
          ? "Add explicit constraints/scope to exception record — unscoped exceptions are governance-critical."
          : globalEx.semantics === "EXCEPTION_UNVERIFIED"
            ? "Verify exception trust banner against catalog and policy gate spine."
            : "Review residual_blockers vs readiness blockers; exceptions do not erase underlying evidence.";
    pushItem(
      items,
      "exception:summary",
      "Research OS Exception",
      globalEx.semantics === "EXCEPTION_EXPIRED" || globalEx.semantics === "EXCEPTION_UNSCOPED" ? "CRITICAL" : globalEx.semantics === "EXCEPTION_ACTIVE" ? "WARNING" : "INFO",
      st,
      asString(exLatest.exception_id) ?? "EXCEPTION",
      globalEx.semantics,
      globalEx.scope,
      globalEx.expiry,
      remSem,
      globalEx.operatorId,
      asString(exRoot.generated_at_utc) ?? "UNKNOWN",
      digestPrefix(exLatest.manifest_sha256 ?? exLatest.exception_spine_sha256),
      next,
      {
        latest: exLatest,
        degraded: asStringArray(exRoot.degraded),
        digest_full: asString(exLatest.manifest_sha256) ?? asString(exLatest.exception_spine_sha256) ?? null,
      },
    );
  }

  if (!input.readyzLoading && !input.readyzError && input.readyzBody) {
    const rb = input.readyzBody;
    const blockers = asStringArray(rb.blockers);
    const rzGen = asString(rb.checked_at_utc) ?? "";
    if (rzGen) genTimes.push(rzGen);
    blockers.forEach((b, i) => {
      const overlay = blockerOverlay(b, exLatest, globalEx);
      const sev = severityForReadinessBlocker(overlay);
      pushItem(
        items,
        `readyz:blocker:${i}`,
        "Readiness Blocker",
        sev,
        "BLOCKER",
        b,
        overlay,
        globalEx.scope,
        globalEx.expiry,
        remSem,
        globalEx.operatorId,
        rzGen || "UNKNOWN",
        digestPrefix(rb.config_fingerprint),
        remActions || "Resolve readiness blocker via deployment checklist; do not dismiss without evidence.",
        { blocker: b, readyz_status: asString(rb.status) },
      );
    });
  }

  if (!input.deploymentLoading && !input.deploymentError && input.deployment) {
    const dep = input.deployment;
    const codes = Array.isArray(dep.blocker_codes) ? (dep.blocker_codes as unknown[]) : [];
    const dg = asString(dep.generated_at_utc) ?? "";
    if (dg) genTimes.push(dg);
    codes.forEach((c, i) => {
      const code = typeof c === "string" ? c : String(c);
      const overlay = blockerOverlay(code, exLatest, globalEx);
      pushItem(
        items,
        `deployment:blocker:${i}`,
        "Readiness Blocker",
        severityForReadinessBlocker(overlay),
        "BLOCKER",
        code,
        overlay,
        globalEx.scope,
        globalEx.expiry,
        remSem,
        "—",
        dg || "UNKNOWN",
        digestPrefix(dep.content_digest),
        remActions || "Clear deployment tier blocker_codes using env + ledger path evidence.",
        { blocker_code: code },
      );
    });
  }

  if (!input.policyGateLoading && !input.policyGateError && pgLatest) {
    const ggen = asString(pgRoot?.generated_at_utc) ?? "";
    if (ggen) genTimes.push(ggen);
    const pBlockers = asStringArray(pgLatest.blockers);
    pBlockers.forEach((b, i) => {
      pushItem(
        items,
        `policy:blocker:${i}`,
        "Policy Gate",
        "CRITICAL",
        asString(pgLatest.decision) ?? "BLOCK",
        b,
        blockerOverlay(b, exLatest, globalEx),
        globalEx.scope,
        globalEx.expiry,
        remSem,
        "—",
        ggen || "UNKNOWN",
        digestPrefix(pgLatest.manifest_sha256 ?? pgLatest.gate_spine_sha256),
        asStringArray(pgLatest.recommended_operator_actions).slice(0, 2).join(" · ") || "Rebuild policy gate after evidence fixes.",
        { gate_id: pgLatest.gate_id, blocker: b },
      );
    });
    const rules = Array.isArray(pgLatest.rules) ? pgLatest.rules : [];
    rules.forEach((rule, i) => {
      const r = asRecord(rule);
      if (!r) return;
      const rs = asString(r.status)?.toUpperCase() ?? "";
      if (rs.includes("BLOCK") || rs === "FAIL") {
        pushItem(
          items,
          `policy:rule:${i}`,
          "Policy Gate",
          "CRITICAL",
          rs,
          asString(r.rule_id) ?? `rule-${i}`,
          blockerOverlay(asString(r.rule_id) ?? "", exLatest, globalEx),
          globalEx.scope,
          globalEx.expiry,
          remSem,
          "—",
          ggen || "UNKNOWN",
          digestPrefix(pgLatest.gate_spine_sha256),
          asString(r.message) ?? "Fix failing gate rule inputs and rebuild gate spine.",
          { rule: r },
        );
      }
    });
  }

  if (!input.driftLoading && !input.driftError && input.drift) {
    const drift = input.drift;
    const dgen = asString(drift.generated_at_utc) ?? "";
    if (dgen) genTimes.push(dgen);
    asStringArray(drift.degraded).forEach((d, i) => {
      pushItem(
        items,
        `drift:${i}`,
        "Evidence Drift",
        "WARNING",
        "DEGRADED",
        d,
        "NO_EXCEPTION",
        "—",
        "—",
        remSem,
        "—",
        dgen || "UNKNOWN",
        digestPrefix(asRecord(drift.latest)?.artifact_sha256),
        "Run drift build CLI and reconcile catalog vs workspace artifacts.",
        { degraded: d },
      );
    });
  }

  if (!input.releaseLoading && !input.releaseError && input.releaseReadiness) {
    const rel = input.releaseReadiness;
    const rgen = asString(rel.generated_at_utc) ?? "";
    if (rgen) genTimes.push(rgen);
    asStringArray(rel.degraded).forEach((d, i) => {
      pushItem(
        items,
        `release:${i}`,
        "Release Readiness",
        "WARNING",
        asString(rel.status) ?? "DEGRADED",
        d,
        "NO_EXCEPTION",
        "—",
        "—",
        remSem,
        "—",
        rgen || "UNKNOWN",
        digestPrefix(asRecord(rel.latest)?.artifact_sha256),
        "Generate release readiness report before promotion discussions.",
        { degraded: d },
      );
    });
  }

  if (!input.reviewJournalLoading && !input.reviewJournalError && input.reviewJournal) {
    const jroot = input.reviewJournal;
    const jlatest = jroot.latest != null ? asRecord(jroot.latest) : null;
    const jgen = asString(jroot.generated_at_utc) ?? "";
    if (jgen) genTimes.push(jgen);
    asStringArray(jlatest?.blockers).forEach((b, i) => {
      pushItem(
        items,
        `journal:blocker:${i}`,
        "Review Journal",
        "WARNING",
        asString(jlatest?.status) ?? "BLOCK",
        b,
        "NO_EXCEPTION",
        "—",
        "—",
        remSem,
        "—",
        jgen || "UNKNOWN",
        digestPrefix(jlatest?.manifest_sha256 ?? jlatest?.journal_spine_sha256),
        "Update review journal after policy/exception posture changes.",
        { blocker: b },
      );
    });
  }

  if (!input.remediationLoading && !input.remediationError && remLatest) {
    const rgen = asString(remRoot?.generated_at_utc) ?? "";
    if (rgen) genTimes.push(rgen);
    const planStatus = asString(remLatest.status) ?? "UNKNOWN";
    const planSev: GovernanceItem["severity"] =
      remSem === "REMEDIATION_UNVERIFIED" || remSem === "UNKNOWN"
        ? "WARNING"
        : remSem === "REMEDIATION_COMPLETE"
          ? "INFO"
          : "WARNING";
    pushItem(
      items,
      "remediation:plan",
      "Remediation",
      planSev,
      planStatus,
      asString(remLatest.plan_id) ?? "PLAN",
      globalEx.semantics,
      globalEx.scope,
      globalEx.expiry,
      remSem,
      "—",
      rgen || "UNKNOWN",
      remDigest,
      remActions || "Run remediation build CLI to refresh action queue.",
      {
        plan: remLatest,
        blockers: asStringArray(remLatest.blockers),
        digest_full: asString(remLatest.manifest_sha256) ?? asString(remLatest.remediation_spine_sha256) ?? null,
      },
    );

    const qItems = Array.isArray(remLatest.items) ? remLatest.items : [];
    const manFull = asString(remLatest.manifest_sha256) ?? asString(remLatest.remediation_spine_sha256) ?? null;
    qItems.forEach((it, i) => {
      const row = asRecord(it);
      if (!row) return;
      const ist = asString(row.status)?.toUpperCase() ?? "";
      const isem: GovernanceRemediationSemantics =
        ist.includes("COMPLETE") || ist.includes("DONE")
          ? "REMEDIATION_COMPLETE"
          : ist.includes("OPEN") || ist.includes("PROGRESS")
            ? "REMEDIATION_IN_PROGRESS"
            : ist.includes("DRAFT") || ist.includes("PROPOSE")
              ? "REMEDIATION_PROPOSED"
              : "UNKNOWN";
      const isev: GovernanceItem["severity"] =
        isem === "REMEDIATION_COMPLETE" ? ((remTrust ?? "").toUpperCase() === "TRUSTED" ? "INFO" : "WARNING") : "WARNING";
      pushItem(
        items,
        `remediation:item:${asString(row.item_id) ?? String(i)}`,
        "Remediation",
        isev,
        ist || "UNKNOWN",
        asString(row.title) ?? asString(row.item_id) ?? "ITEM",
        "NO_EXCEPTION",
        "—",
        "—",
        isem,
        "—",
        rgen || "UNKNOWN",
        remDigest,
        asString(row.source) ?? "Execute CLI-backed remediation; browser does not apply fixes.",
        { item: row, digest_full: manFull },
      );
    });
  } else if (!input.remediationLoading && (input.remediationError || !remRoot)) {
    pushItem(
      items,
      "remediation:missing",
      "Remediation",
      "WARNING",
      "MISSING",
      "REMEDIATION_PLAN",
      globalEx.semantics,
      globalEx.scope,
      globalEx.expiry,
      "REMEDIATION_MISSING",
      "—",
      "UNKNOWN",
      "—",
      "Build remediation plan read-plane artifact to link blockers to actions.",
      { isError: input.remediationError },
    );
  }

  if (input.providerBlockedCount != null && input.providerBlockedCount > 0) {
    pushItem(
      items,
      "provider:blocked",
      "Provider / Freshness",
      "WARNING",
      "BLOCKED",
      `blocked_count=${input.providerBlockedCount}`,
      "NO_EXCEPTION",
      "—",
      "—",
      remSem,
      "—",
      "UNKNOWN",
      "—",
      "Resolve provider setup blockers in Provider Matrix / setup console evidence.",
      { blocked_count: input.providerBlockedCount },
    );
  }
  if (input.providerStaleCount != null && input.providerStaleCount > 0) {
    pushItem(
      items,
      "provider:stale",
      "Provider / Freshness",
      "WARNING",
      "STALE",
      `stale_count=${input.providerStaleCount}`,
      "NO_EXCEPTION",
      "—",
      "—",
      remSem,
      "—",
      "UNKNOWN",
      "—",
      "Refresh provider samples / health checks before trusting research attestation.",
      { stale_count: input.providerStaleCount },
    );
  }

  items.sort((a, b) => {
    const d = severityRank(a.severity) - severityRank(b.severity);
    if (d !== 0) return d;
    return a.item_id.localeCompare(b.item_id);
  });

  const counts = { CRITICAL: 0, WARNING: 0, INFO: 0, UNKNOWN: 0 };
  for (const it of items) {
    counts[it.severity] += 1;
  }

  return { items, counts, generated_at_utc: maxUtc(...genTimes) };
}
