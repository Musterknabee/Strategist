/**
 * Read-plane audit timeline + lightweight forensic diffs from existing GET payloads.
 * Does not infer chain validity beyond backend flags and issue_codes.
 */
import { asBool, asNumber, asRecord, asString, asStringArray } from "@/lib/operator/payload-utils";

export type AuditTimelineFilter =
  | "ALL"
  | "PROMOTION_LEDGER"
  | "OPERATOR_ACTIONS"
  | "RESEARCH_OS"
  | "RELEASE_DEPLOYMENT"
  | "PAPER_EXECUTION"
  | "BROKEN_LINEAGE"
  | "ISSUES";

export type AuditChainSemantic = "CHAINED" | "UNCHAINED" | "BROKEN" | "UNKNOWN";

export type AuditTrustSemantic = "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED" | "UNKNOWN";

export type AuditPassFail = "PASS" | "WARN" | "FAIL" | "DEGRADED" | "PENDING" | "UNKNOWN";

export type AuditTimelineEntry = {
  timeline_id: string;
  timestamp: string;
  source_family: string;
  event_type: string;
  action: string;
  status: string;
  actor: string;
  sequence_number: number | null;
  chain_semantic: AuditChainSemantic;
  trust_semantic: AuditTrustSemantic;
  pass_fail: AuditPassFail;
  digest_prefix: string;
  digest_full: string | null;
  issue_count: number;
  issue_codes: string[];
  related_artifact: string;
  raw: Record<string, unknown>;
};

export type ForensicDiffBlock = {
  id: string;
  title: string;
  baseline: "NO_BASELINE" | "PAIR";
  lines: string[];
};

export type AuditTimelineModel = {
  timeline_id: string;
  generated_at_utc: string;
  degraded: string[];
  chain_summary_ok: boolean | null;
  entry_count: number;
  entries: AuditTimelineEntry[];
  forensic_diffs: ForensicDiffBlock[];
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 14 ? `${s.slice(0, 14)}…` : s;
}

function pickDigestFull(row: Record<string, unknown>): string | null {
  for (const k of ["event_hash", "payload_digest_sha256", "manifest_hash", "target_payload_digest"]) {
    const s = asString(row[k]);
    if (s && s.length >= 16) return s;
  }
  return null;
}

function chainSemantic(chained: boolean | undefined, issues: string[]): AuditChainSemantic {
  if (issues.some((i) => /CHAIN|VERIFICATION|MISSING/i.test(i))) return "BROKEN";
  if (issues.includes("LEGACY_UNCHAINED_EVENT")) return "UNCHAINED";
  if (chained === true && issues.length === 0) return "CHAINED";
  if (issues.length > 0) return "BROKEN";
  if (chained === false) return "UNCHAINED";
  return "UNKNOWN";
}

function trustFromBanner(banner: string | undefined): AuditTrustSemantic {
  const u = (banner ?? "").toUpperCase();
  if (u.includes("TRUST_OK") || u === "TRUSTED") return "TRUSTED";
  if (u.includes("RESTRICT")) return "TRUST_RESTRICTED";
  if (u.includes("UNTRUST") || u.includes("BLOCK")) return "UNTRUSTED";
  if (!u) return "UNKNOWN";
  return "UNKNOWN";
}

function passFailFromStatus(status: string, issues: string[]): AuditPassFail {
  const su = status.toUpperCase();
  if (issues.length > 0) return "DEGRADED";
  if (su.includes("FAIL") || su.includes("BLOCK")) return "FAIL";
  if (su.includes("WARN") || su.includes("RESTRICT")) return "WARN";
  if (su.includes("PASS") || su.includes("READY") || su.includes("VERIFIED")) return "PASS";
  if (su === "" || su === "UNKNOWN") return "UNKNOWN";
  return "PENDING";
}

function parseTs(iso: string): number {
  const t = Date.parse(iso);
  return Number.isFinite(t) ? t : 0;
}

function normalizeChainRow(row: Record<string, unknown>, index: number): AuditTimelineEntry {
  const stream = asString(row.stream_family) ?? "unknown";
  const issues = asStringArray(row.issue_codes);
  const chained = asBool(row.chained);
  const ts = asString(row.created_at_utc) ?? "1970-01-01T00:00:00Z";
  const recordId = asString(row.record_id) ?? asString(row.action_event_id) ?? `row-${index}`;
  const digestFull = pickDigestFull(row);
  const seq = row.sequence_number == null ? null : asNumber(row.sequence_number) ?? null;
  const status = asString(row.status) ?? asString(row.promotion_state) ?? "UNKNOWN";
  const actor = asString(row.operator_id) ?? asString(row.actor_id) ?? asString(row.writer_identity) ?? "—";
  return {
    timeline_id: `chain|${stream}|${recordId}|${ts}`,
    timestamp: ts,
    source_family: stream,
    event_type: asString(row.event_type) ?? "—",
    action: asString(row.action) ?? asString(row.event_type) ?? "—",
    status,
    actor,
    sequence_number: seq,
    chain_semantic: chainSemantic(chained, issues),
    trust_semantic: "UNKNOWN",
    pass_fail: passFailFromStatus(status, issues),
    digest_prefix: digestPrefix(digestFull ?? recordId),
    digest_full: digestFull,
    issue_count: issues.length,
    issue_codes: issues,
    related_artifact: stream,
    raw: row,
  };
}

function synth(
  id: string,
  ts: string,
  sourceFamily: string,
  eventType: string,
  action: string,
  status: string,
  actor: string,
  digest: unknown,
  trustBanner: string | undefined,
  raw: Record<string, unknown>,
): AuditTimelineEntry {
  const issues = asStringArray(raw.issue_codes ?? raw.blockers);
  const digestFull = pickDigestFull({ ...raw, event_hash: raw.event_hash ?? digest });
  return {
    timeline_id: id,
    timestamp: ts || "1970-01-01T00:00:00Z",
    source_family: sourceFamily,
    event_type: eventType,
    action,
    status,
    actor,
    sequence_number: null,
    chain_semantic: "UNKNOWN",
    trust_semantic: trustFromBanner(trustBanner ?? asString(raw.trust_banner)),
    pass_fail: passFailFromStatus(status, issues),
    digest_prefix: digestPrefix(digestFull ?? digest),
    digest_full: digestFull ?? (typeof digest === "string" && digest.length >= 16 ? digest : null),
    issue_count: issues.length,
    issue_codes: issues,
    related_artifact: eventType,
    raw,
  };
}

function timelineRowsFromChain(chain: Record<string, unknown> | null): Record<string, unknown>[] {
  if (!chain) return [];
  const tl = asRecord(chain.timeline);
  const direct = tl?.entries;
  if (Array.isArray(direct) && direct.length > 0) return direct.map((x) => asRecord(x)).filter(Boolean) as Record<string, unknown>[];
  const streams = asRecord(chain.streams);
  const dec = streams?.decision_ledger ? asRecord(streams.decision_ledger) : null;
  const op = streams?.operator_action_journal ? asRecord(streams.operator_action_journal) : null;
  const out: Record<string, unknown>[] = [];
  const de = dec?.entries;
  const oe = op?.entries;
  if (Array.isArray(de)) {
    for (const x of de) {
      const r = asRecord(x);
      if (r) out.push(r);
    }
  }
  if (Array.isArray(oe)) {
    for (const x of oe) {
      const r = asRecord(x);
      if (r) out.push(r);
    }
  }
  out.sort(
    (a, b) =>
      parseTs(asString(a.created_at_utc) ?? "") - parseTs(asString(b.created_at_utc) ?? "") ||
      String(a.stream_family).localeCompare(String(b.stream_family)),
  );
  return out;
}

function supplementOperatorIndex(op: Record<string, unknown> | null, existing: AuditTimelineEntry[]): AuditTimelineEntry[] {
  if (existing.length > 0 || !op) return [];
  const entries = op.entries;
  if (!Array.isArray(entries)) return [];
  return entries.map((e, i) => normalizeChainRow(asRecord(e) ?? {}, i));
}

export function buildForensicDiffs(
  normalized: AuditTimelineEntry[],
  evidence: Record<string, unknown> | null,
  releaseReadiness: Record<string, unknown> | null,
  handoff: Record<string, unknown> | null,
  handoffSignoff: Record<string, unknown> | null,
): ForensicDiffBlock[] {
  const blocks: ForensicDiffBlock[] = [];
  const decisions = normalized.filter((e) => e.source_family === "decision_ledger");
  if (decisions.length >= 2) {
    const a = decisions[decisions.length - 2];
    const b = decisions[decisions.length - 1];
    blocks.push({
      id: "promotion-tail",
      title: "Promotion ledger (last two events)",
      baseline: "PAIR",
      lines: [
        `prev seq=${a.sequence_number ?? "—"} state=${a.status} hash=${a.digest_prefix}`,
        `curr seq=${b.sequence_number ?? "—"} state=${b.status} hash=${b.digest_prefix}`,
        a.status === b.status ? "promotion_state unchanged" : `promotion_state changed: ${a.status} → ${b.status}`,
      ],
    });
  } else {
    blocks.push({
      id: "promotion-tail",
      title: "Promotion ledger (longitudinal)",
      baseline: "NO_BASELINE",
      lines: ["Fewer than two decision_ledger events in the current timeline window — no pairwise diff."],
    });
  }

  const operators = normalized.filter((e) => e.source_family === "operator_action_journal");
  if (operators.length >= 2) {
    const a = operators[operators.length - 2];
    const b = operators[operators.length - 1];
    blocks.push({
      id: "operator-tail",
      title: "Operator journal (last two events)",
      baseline: "PAIR",
      lines: [
        `prev action=${a.action} status=${a.status}`,
        `curr action=${b.action} status=${b.status}`,
        a.digest_full && b.digest_full && a.digest_full !== b.digest_full ? "event_hash / digest changed" : "digest comparison limited to displayed window",
      ],
    });
  } else {
    blocks.push({
      id: "operator-tail",
      title: "Operator journal (longitudinal)",
      baseline: "NO_BASELINE",
      lines: ["Fewer than two operator_action_journal events in the current timeline window — no pairwise diff."],
    });
  }

  const reg = evidence ? asRecord(evidence.registry) : null;
  blocks.push({
    id: "evidence-registry",
    title: "UI evidence registry digest (temporal delta)",
    baseline: "NO_BASELINE",
    lines: [
      `current projection_digest_sha256 prefix: ${digestPrefix(reg?.projection_digest_sha256)}`,
      "Prior snapshot not available from read-plane APIs — store offline manifests if you need longitudinal digest diff.",
    ],
  });

  const rr = releaseReadiness?.latest ? asRecord(releaseReadiness.latest) : null;
  const ho = handoff?.latest ? asRecord(handoff.latest) : null;
  const ver = handoffSignoff?.latest_verification ? asRecord(handoffSignoff.latest_verification) : null;
  const sg = handoffSignoff?.latest_signoff ? asRecord(handoffSignoff.latest_signoff) : null;
  blocks.push({
    id: "research-os-triad",
    title: "Research OS latest snapshots (cross-surface)",
    baseline: "NO_BASELINE",
    lines: [
      `release_readiness: ${asString(rr?.decision) ?? "—"} / ${asString(rr?.status) ?? "—"}`,
      `handoff: ${asString(ho?.decision) ?? "—"}`,
      `handoff_signoff verify: ${asString(ver?.status) ?? "—"} · signoff: ${asString(sg?.decision) ?? "—"}`,
      "Read-plane exposes latest-only payloads — no prior handoff/signoff revision in this view for automatic delta.",
    ],
  });

  return blocks;
}

export function buildAuditTimelineModel(input: {
  evidenceChain: unknown;
  operatorActions: unknown;
  evidence: unknown;
  releaseReadiness: unknown;
  handoff: unknown;
  handoffSignoff: unknown;
  reviewJournal: unknown;
  exportLatest: unknown;
  driftLatest: unknown;
  paperExecution: unknown;
}): AuditTimelineModel {
  const chain = asRecord(input.evidenceChain);
  const degraded = asStringArray(chain?.degraded);
  const rawRows = timelineRowsFromChain(chain);
  let normalized = rawRows.map((r, i) => normalizeChainRow(r, i));
  const opIdx = asRecord(input.operatorActions);
  if (normalized.length === 0) {
    normalized = supplementOperatorIndex(opIdx, normalized);
  }

  const ev = asRecord(input.evidence);
  const reg = ev ? asRecord(ev.registry) : null;
  const genEv = asString(ev?.generated_at_utc) ?? asString(chain?.generated_at_utc) ?? "UNKNOWN";
  if (ev) {
    normalized.push(
      synth(
        `artifact|ui_evidence|${genEv}`,
        genEv,
        "artifact_ui_evidence",
        "ui_evidence_dashboard",
        "snapshot",
        asString(ev.deployment_status) ?? "UNKNOWN",
        "read_plane",
        reg?.projection_digest_sha256,
        asString(asRecord(ev.verification)?.trust_status),
        { ...ev, issue_codes: asStringArray(asRecord(ev.verification)?.integrity_warnings) },
      ),
    );
  }

  const rr = asRecord(input.releaseReadiness);
  const rrLatest = rr?.latest ? asRecord(rr.latest) : null;
  const rrDegraded = rr ? asStringArray(rr.degraded) : [];
  const rrTs = asString(rrLatest?.generated_at_utc) ?? asString(rr?.generated_at_utc) ?? genEv;
  if (rrLatest && !rrDegraded.some((d) => d.includes("NO_RESEARCH_OS_RELEASE_READINESS"))) {
    normalized.push(
      synth(
        `artifact|research_os|release_readiness|${rrTs}`,
        rrTs,
        "research_os",
        "release_readiness",
        "latest",
        `${asString(rrLatest?.decision) ?? "UNKNOWN"} / ${asString(rrLatest?.status) ?? "UNKNOWN"}`,
        "artifact",
        rrLatest?.manifest_sha256,
        asString(rrLatest?.trust_banner),
        rr ?? {},
      ),
    );
  }

  const ho = asRecord(input.handoff);
  const hoLatest = ho?.latest ? asRecord(ho.latest) : null;
  const hoTs = asString(hoLatest?.generated_at_utc) ?? asString(ho?.generated_at_utc) ?? genEv;
  if (hoLatest) {
    normalized.push(
      synth(
        `artifact|research_os|handoff|${hoTs}`,
        hoTs,
        "research_os",
        "handoff",
        "latest",
        asString(hoLatest.decision) ?? "UNKNOWN",
        "artifact",
        hoLatest.manifest_sha256,
        asString(hoLatest.trust_banner),
        ho ?? {},
      ),
    );
  }

  const hs = asRecord(input.handoffSignoff);
  const ver = hs?.latest_verification ? asRecord(hs.latest_verification) : null;
  const sig = hs?.latest_signoff ? asRecord(hs.latest_signoff) : null;
  const hsTs =
    asString(sig?.signed_at_utc) ?? asString(ver?.verified_at_utc) ?? asString(hs?.generated_at_utc) ?? genEv;
  if (ver || sig) {
    normalized.push(
      synth(
        `artifact|research_os|handoff_signoff|${hsTs}`,
        hsTs,
        "research_os",
        "handoff_signoff",
        "latest",
        `${asString(ver?.status) ?? "—"} / ${asString(sig?.decision) ?? "—"}`,
        "artifact",
        ver?.observed_handoff_manifest_sha256 ?? sig?.signoff_id,
        asString(sig?.trust_banner ?? ver?.trust_banner),
        hs ?? {},
      ),
    );
  }

  const rj = asRecord(input.reviewJournal);
  const rjLatest = rj?.latest ? asRecord(rj.latest) : null;
  const rjTs = asString(rjLatest?.generated_at_utc) ?? asString(rj?.generated_at_utc) ?? genEv;
  if (rjLatest) {
    normalized.push(
      synth(
        `artifact|research_os|review_journal|${rjTs}`,
        rjTs,
        "research_os",
        "review_journal",
        "latest",
        asString(rjLatest.status) ?? "UNKNOWN",
        "artifact",
        rjLatest.manifest_sha256,
        asString(rjLatest.trust_banner),
        rj ?? {},
      ),
    );
  }

  const ex = asRecord(input.exportLatest);
  const exMan = ex?.latest_export ? asRecord(ex.latest_export) : null;
  const exTs = asString(exMan?.generated_at_utc) ?? asString(ex?.generated_at_utc) ?? genEv;
  if (exMan) {
    normalized.push(
      synth(
        `artifact|research_os|export|${exTs}`,
        exTs,
        "research_os",
        "export_manifest",
        "latest",
        asString(exMan.status) ?? "UNKNOWN",
        "artifact",
        exMan.manifest_sha256 ?? exMan.export_spine_sha256,
        asString(exMan.trust_banner),
        ex ?? {},
      ),
    );
  }

  const drift = asRecord(input.driftLatest);
  const driftPayload = drift?.latest ? asRecord(drift.latest) : null;
  const driftDegraded = drift ? asStringArray(drift.degraded) : [];
  const driftTs = asString(driftPayload?.generated_at_utc) ?? asString(drift?.generated_at_utc) ?? genEv;
  if (driftPayload && !driftDegraded.some((d) => d.includes("NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT"))) {
    normalized.push(
      synth(
        `artifact|research_os|drift|${driftTs}`,
        driftTs,
        "research_os",
        "drift",
        "latest",
        asString(driftPayload.status) ?? asString(driftPayload.drift_status) ?? "UNKNOWN",
        "artifact",
        driftPayload.bundle_sha256 ?? driftPayload.artifact_sha256,
        asString(driftPayload.trust_banner),
        drift ?? {},
      ),
    );
  }

  const pe = asRecord(input.paperExecution);
  const peSummary = pe ? asRecord(pe.summary) : null;
  const peTs = asString(pe?.generated_at_utc) ?? genEv;
  if (pe) {
    normalized.push(
      synth(
        `artifact|paper_execution|${peTs}`,
        peTs,
        "paper_execution",
        "paper_execution_cockpit",
        "latest",
        asString(peSummary?.broker_policy_status) ?? "UNKNOWN",
        "cockpit",
        peSummary?.latest_evidence_bundle_sha256,
        asString(peSummary?.latest_evidence_bundle_trust_banner),
        pe ?? {},
      ),
    );
  }

  normalized.sort((a, b) => parseTs(a.timestamp) - parseTs(b.timestamp));

  const forensic = buildForensicDiffs(normalized, ev, rr, ho, hs);

  return {
    timeline_id: `audit_timeline|${digestPrefix(chain?.generated_at_utc)}|${normalized.length}`,
    generated_at_utc: asString(chain?.generated_at_utc) ?? genEv,
    degraded,
    chain_summary_ok: chain == null ? null : (asBool(chain.ok) ?? null),
    entry_count: normalized.length,
    entries: normalized,
    forensic_diffs: forensic,
  };
}

export function filterAuditTimeline(entries: AuditTimelineEntry[], filter: AuditTimelineFilter): AuditTimelineEntry[] {
  if (filter === "ALL") return entries;
  return entries.filter((e) => {
    switch (filter) {
      case "PROMOTION_LEDGER":
        return e.source_family === "decision_ledger";
      case "OPERATOR_ACTIONS":
        return e.source_family === "operator_action_journal";
      case "RESEARCH_OS":
        return e.source_family === "research_os";
      case "RELEASE_DEPLOYMENT":
        return e.source_family === "artifact_ui_evidence" || e.event_type === "ui_evidence_dashboard";
      case "PAPER_EXECUTION":
        return e.source_family === "paper_execution";
      case "BROKEN_LINEAGE":
        return e.chain_semantic === "BROKEN" || e.chain_semantic === "UNCHAINED";
      case "ISSUES":
        return e.issue_count > 0 || e.pass_fail === "DEGRADED" || e.pass_fail === "FAIL";
      default:
        return true;
    }
  });
}
