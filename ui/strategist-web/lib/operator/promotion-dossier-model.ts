/**
 * Read-only promotion evidence dossier from existing UI read-plane payloads.
 * Does not adjudicate, mutate ledger, or infer promotability beyond explicit payload fields.
 */
import { resolveAnchorIds } from "@/lib/operator/strategy-lifecycle-model";
import {
  asBool,
  asNumber,
  asRecord,
  asString,
  asStringArray,
} from "@/lib/operator/payload-utils";

export type PromotionReviewAction =
  | "FIND_EXPERIMENT_EVIDENCE"
  | "REVIEW_LEDGER_CHAIN"
  | "REVIEW_FAILED_GATES"
  | "REVIEW_ROBUSTNESS_EVIDENCE"
  | "REVIEW_EXECUTION_REALISM"
  | "REVIEW_MARKET_DATA"
  | "OPERATOR_REVIEW_DECISION"
  | "UNKNOWN";

export type DossierGateRow = {
  gate_name: string;
  status: string;
  reason?: string;
  category: string;
  source_evidence: string;
  severity: "INFO" | "WARN" | "FAIL" | "UNKNOWN";
};

export type DossierEvidenceItem = {
  label: string;
  digest_prefix: string;
  source_endpoint: string;
  status: string;
};

export type PromotionDossierModel = {
  dossier_id: string;
  experiment_id: string;
  strategy_id: string;
  run_id: string;
  tracking_id: string;
  intake_id: string;
  thesis_id: string;
  current_state: string;
  previous_state: string;
  decision_status: string;
  latest_event_type: string;
  ledger_event_hash: string;
  ledger_previous_event_hash: string;
  manifest_hash: string;
  payload_digest_prefix: string;
  writer_identity: string;
  sequence_number: string;
  chain_status: "VERIFIED" | "DEGRADED" | "UNKNOWN";
  decision_ledger_chain_ok: boolean | null;
  selected_ledger_chained: boolean | null;
  gate_pass_count: number;
  gate_fail_count: number;
  gate_unknown_count: number;
  warning_count: number;
  blocker_count: number;
  generated_at_utc: string;
  decision_time_utc: string;
  config_fingerprint: string;
  recommended_review_action: PromotionReviewAction;
  gate_rows: DossierGateRow[];
  benchmark_lines: string[];
  robustness_lines: string[];
  execution_realism_lines: string[];
  market_data_lines: string[];
  evidence_items: DossierEvidenceItem[];
  ledger_proof_lines: string[];
  operator_review_lines: string[];
  degraded_flags: string[];
  raw_sources: Record<string, unknown>;
};

export type PromotionDossierInput = {
  readyzBody: Record<string, unknown> | null;
  strategyIntakeLatest: unknown;
  strategyThesisLatest: unknown;
  strategyThesisGenerationLatest: unknown;
  paperTrackingLatest: unknown;
  strategyBatchLatest: unknown;
  backtestForensicsLatest: unknown;
  evidenceChain: unknown;
  operatorActions: unknown;
  workboard: unknown;
  evidence: unknown;
  paperExecution: unknown;
  queryFailed: boolean;
};

function digestPrefix(v: unknown): string {
  const s = asString(v);
  if (!s) return "—";
  return s.length > 14 ? `${s.slice(0, 12)}…` : s;
}

function getDecisionLedgerEntries(evidenceChain: unknown): Record<string, unknown>[] {
  const c = asRecord(evidenceChain);
  const streams = asRecord(c?.streams);
  const dl = streams ? asRecord(streams.decision_ledger) : null;
  const ent = dl?.entries;
  if (Array.isArray(ent)) return ent.map((e) => asRecord(e)).filter((x): x is Record<string, unknown> => x != null);
  const tl = asRecord(c?.timeline)?.entries;
  if (Array.isArray(tl)) {
    return tl
      .map((e) => asRecord(e))
      .filter((x): x is Record<string, unknown> => x != null && asString(x.stream_family) === "decision_ledger");
  }
  return [];
}

function sortDecisionEntries(rows: Record<string, unknown>[]): Record<string, unknown>[] {
  return [...rows].sort((a, b) => {
    const sa = asNumber(a.sequence_number);
    const sb = asNumber(b.sequence_number);
    if (sa !== undefined && sb !== undefined && sa !== sb) return sa - sb;
    const ta = asString(a.created_at_utc) ?? "";
    const tb = asString(b.created_at_utc) ?? "";
    return ta.localeCompare(tb);
  });
}

function gateCategory(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("robust") || n.includes("cpcv") || n.includes("pbo") || n.includes("dsr")) return "Robustness";
  if (n.includes("execution") || n.includes("realism")) return "Execution realism";
  if (n.includes("market") || n.includes("data") || n.includes("pit")) return "Market data";
  if (n.includes("promotion")) return "Promotion";
  if (n.includes("adjud")) return "Adjudication";
  return "Gate";
}

function flattenGateMatrix(gm: Record<string, unknown> | null): DossierGateRow[] {
  if (!gm) return [];
  const skip = new Set(["promotion_blocked_reasons", "sample_count", "data_coverage_ratio"]);
  const rows: DossierGateRow[] = [];
  for (const [k, v] of Object.entries(gm)) {
    if (skip.has(k)) continue;
    if (k === "promotion_eligible") {
      const ok = asBool(v);
      rows.push({
        gate_name: k,
        status: ok === true ? "TRUE" : ok === false ? "FALSE" : "UNKNOWN",
        reason: typeof v === "boolean" ? String(v) : asString(v),
        category: "Promotion",
        source_evidence: "strategy_batch.gate_summary",
        severity: ok === false ? "FAIL" : ok === true ? "INFO" : "UNKNOWN",
      });
      continue;
    }
    const raw =
      typeof v === "string" || typeof v === "number" || typeof v === "boolean"
        ? String(v)
        : JSON.stringify(v).slice(0, 200);
    const upper = raw.toUpperCase();
    let status = "UNKNOWN";
    let severity: DossierGateRow["severity"] = "UNKNOWN";
    if (["PASS", "OK", "TRUE", "COMPLETE", "VERIFIED"].some((x) => upper === x)) {
      status = "PASS";
      severity = "INFO";
    } else if (["FAIL", "FAILED", "BLOCKED", "FALSE", "ERROR"].some((x) => upper.includes(x))) {
      status = "FAIL";
      severity = "FAIL";
    } else if (upper.includes("WARN") || upper === "REVIEW") {
      status = "WARN";
      severity = "WARN";
    } else if (["NOT_RUN", "UNKNOWN", "NOT_INVOKED", "PENDING", "NOT_PRESENT"].some((x) => upper.includes(x))) {
      status = upper.slice(0, 32);
      severity = "UNKNOWN";
    } else {
      status = raw.slice(0, 48);
      severity = "INFO";
    }
    rows.push({
      gate_name: k,
      status,
      reason: raw.length > 48 ? `${raw.slice(0, 48)}…` : raw,
      category: gateCategory(k),
      source_evidence: "/ui/backtest-forensics/latest · gate_matrix",
      severity,
    });
  }
  return rows;
}

function deriveReviewAction(opts: {
  anchorOk: boolean;
  chainOk: boolean | null | undefined;
  ledgerIssues: boolean;
  gateFail: number;
  robUnknown: boolean;
  execUnknown: boolean;
  marketWarn: boolean;
  hasDecision: boolean;
}): PromotionReviewAction {
  if (!opts.anchorOk) return "FIND_EXPERIMENT_EVIDENCE";
  if (opts.chainOk === false || opts.ledgerIssues) return "REVIEW_LEDGER_CHAIN";
  if (opts.gateFail > 0) return "REVIEW_FAILED_GATES";
  if (opts.robUnknown) return "REVIEW_ROBUSTNESS_EVIDENCE";
  if (opts.execUnknown) return "REVIEW_EXECUTION_REALISM";
  if (opts.marketWarn) return "REVIEW_MARKET_DATA";
  if (opts.hasDecision && opts.chainOk === true && !opts.ledgerIssues) return "OPERATOR_REVIEW_DECISION";
  return "UNKNOWN";
}

export function buildPromotionDossierModel(input: PromotionDossierInput): PromotionDossierModel {
  const anchor = resolveAnchorIds({
    strategyThesisLatest: input.strategyThesisLatest,
    strategyThesisGenerationLatest: input.strategyThesisGenerationLatest,
    paperTrackingLatest: input.paperTrackingLatest,
    strategyBatchLatest: input.strategyBatchLatest,
    strategyIntakeLatest: input.strategyIntakeLatest,
  });
  const experimentId = anchor.strategyId !== "UNKNOWN" ? anchor.strategyId : "UNKNOWN";

  const allDecisions = sortDecisionEntries(getDecisionLedgerEntries(input.evidenceChain));
  const strategyId = anchor.strategyId;
  const filtered =
    strategyId !== "UNKNOWN"
      ? allDecisions.filter((e) => asString(e.experiment_id) === strategyId || asString(e.aggregate_id) === strategyId)
      : allDecisions;
  const useDecisions = filtered.length ? filtered : allDecisions;
  const latest = useDecisions.length ? useDecisions[useDecisions.length - 1] : null;
  const prev = useDecisions.length > 1 ? useDecisions[useDecisions.length - 2] : null;

  const chainRec = asRecord(input.evidenceChain);
  const summary = asRecord(chainRec?.summary);
  const decisionLedgerOk = asBool(summary?.decision_ledger_chain_ok);

  const issueCodes = latest ? asStringArray(latest.issue_codes) : [];
  const selectedChained = latest != null ? asBool(latest.chained) : null;
  const ledgerIssues = issueCodes.length > 0 || selectedChained === false;

  let chainStatus: PromotionDossierModel["chain_status"] = "UNKNOWN";
  if (decisionLedgerOk === true && !ledgerIssues && latest) chainStatus = "VERIFIED";
  else if (decisionLedgerOk === false || ledgerIssues) chainStatus = "DEGRADED";

  const forensics = asRecord(input.backtestForensicsLatest);
  const strategies = Array.isArray(forensics?.strategies)
    ? (forensics.strategies as unknown[]).map((s) => asRecord(s)).filter((x): x is Record<string, unknown> => x != null)
    : [];
  const forensicRow =
    strategyId !== "UNKNOWN"
      ? strategies.find((s) => asString(s.strategy_id) === strategyId) ?? strategies[0]
      : strategies[0];
  const gm = forensicRow ? asRecord(forensicRow.gate_matrix) : null;
  const gateRows = flattenGateMatrix(gm);
  let gatePass = 0;
  let gateFail = 0;
  let gateUnknown = 0;
  for (const g of gateRows) {
    if (g.status === "PASS" || g.status === "TRUE") gatePass += 1;
    else if (g.status === "FAIL" || g.status === "FALSE" || g.severity === "FAIL") gateFail += 1;
    else gateUnknown += 1;
  }

  const robust = forensicRow ? asRecord(forensicRow.robustness) : null;
  const exec = forensicRow ? asRecord(forensicRow.execution_realism) : null;
  const robGate = asString(gm?.robustness_gate) ?? asString(robust?.gate_status);
  const cpcvGate = asString(gm?.cpcv_robustness_gate) ?? asString(robust?.cpcv_gate_status);
  const execGate = asString(gm?.execution_realism_gate) ?? asString(exec?.gate_status);
  const robUnknown = !robGate && !cpcvGate
    ? true
    : ["NOT_RUN", "UNKNOWN", ""].includes((robGate ?? "").toUpperCase()) ||
      ["NOT_RUN", "UNKNOWN", ""].includes((cpcvGate ?? "").toUpperCase());
  const execUnknown = !execGate || ["NOT_RUN", "UNKNOWN", ""].includes(execGate.toUpperCase());

  const dataPlane = asString(forensicRow?.data_plane);
  const pitStatus = asString(forensicRow?.pit_status);
  const marketWarn =
    dataPlane === "SYNTHETIC" ||
    dataPlane === "PROVIDER_SNAPSHOT" ||
    (pitStatus ? !["PASS", "OK", "COMPLETE"].includes(pitStatus.toUpperCase()) : false);

  const hasAnchor = strategyId !== "UNKNOWN";
  const hasForensics = forensicRow != null;
  const hasLedgerDecision = latest != null;
  const needExperiment = !hasAnchor && !hasForensics && !hasLedgerDecision;

  const recommended = deriveReviewAction({
    anchorOk: !needExperiment,
    chainOk: decisionLedgerOk,
    ledgerIssues,
    gateFail: gateFail + (asStringArray(forensicRow?.blockers).length > 0 ? 1 : 0),
    robUnknown: !!forensicRow && robUnknown,
    execUnknown: !!forensicRow && execUnknown,
    marketWarn: !!forensicRow && marketWarn,
    hasDecision: hasLedgerDecision,
  });

  const paper = asRecord(input.paperTrackingLatest);
  const paperLatest = asRecord(paper?.latest);
  const paperManifest = asRecord(paperLatest?.manifest);
  const paperManifestSha = asString(paperManifest?.manifest_sha256);
  const wb = asRecord(input.workboard);
  const wbQueue = asRecord(wb?.queue);
  const wbEntries = Array.isArray(wbQueue?.entries) ? wbQueue.entries : [];
  const operatorRec = asRecord(input.operatorActions);
  const opEntries = Array.isArray(operatorRec?.entries) ? operatorRec.entries : [];
  const lastOps = opEntries.slice(-4);

  const ev = asRecord(input.evidence);
  const registry = asRecord(ev?.registry);
  const verification = asRecord(ev?.verification);

  const benchmarkLines: string[] = [];
  const metrics = forensicRow ? asRecord(forensicRow.metrics) : null;
  const bid = asString(metrics?.benchmark_id) ?? asString(gm?.benchmark_id);
  const bver = asString(metrics?.benchmark_version);
  const bd = asNumber(metrics?.benchmark_delta);
  if (bid) benchmarkLines.push(`benchmark_id=${bid}`);
  if (bver) benchmarkLines.push(`benchmark_version=${bver}`);
  if (bd !== undefined) benchmarkLines.push(`benchmark_delta=${bd}`);
  if (!benchmarkLines.length) benchmarkLines.push("UNKNOWN · no benchmark fields on forensic row");

  const robustnessLines: string[] = [];
  if (robust) {
    if (robGate) robustnessLines.push(`robustness_gate=${robGate}`);
    if (cpcvGate) robustnessLines.push(`cpcv_robustness_gate=${cpcvGate}`);
    const pbo = asNumber(robust.pbo_like_score);
    const dsr = asNumber(robust.dsr_like_score);
    if (pbo !== undefined) robustnessLines.push(`pbo_like_score=${pbo}`);
    if (dsr !== undefined) robustnessLines.push(`dsr_like_score=${dsr}`);
    const dec = gm ? asBool((gm as { decoy_survival_passed?: unknown }).decoy_survival_passed) : undefined;
    if (dec !== undefined) robustnessLines.push(`decoy_survival_passed=${dec}`);
  } else robustnessLines.push("UNKNOWN · no forensic robustness object");

  const execLines: string[] = [];
  if (exec || execGate) {
    if (execGate) execLines.push(`execution_realism_gate=${execGate}`);
    if (exec) {
      const lab = asString(exec.model_label);
      if (lab) execLines.push(`model_label=${lab}`);
      const slip = asNumber(exec.estimated_slippage_bps);
      const fee = asNumber(exec.estimated_fee_bps);
      if (slip !== undefined) execLines.push(`est_slippage_bps=${slip}`);
      if (fee !== undefined) execLines.push(`est_fee_bps=${fee}`);
    }
  } else execLines.push("UNKNOWN · no execution realism slice");

  const marketLines: string[] = [];
  if (forensicRow) {
    marketLines.push(`data_plane=${dataPlane || "UNKNOWN"}`);
    marketLines.push(`data_status=${asString(forensicRow.data_status) ?? "UNKNOWN"}`);
    marketLines.push(`pit_status=${pitStatus || "UNKNOWN"}`);
    marketLines.push(`bars_row_count=${asNumber(forensicRow.bars_row_count) ?? "UNKNOWN"}`);
  } else marketLines.push("UNKNOWN · no forensic strategy row");

  const evidenceItems: DossierEvidenceItem[] = [];
  if (latest) {
    evidenceItems.push({
      label: "Latest decision ledger event",
      digest_prefix: digestPrefix(latest.event_hash),
      source_endpoint: "/ui/evidence-chain · decision_ledger",
      status: asBool(latest.chained) === false ? "DEGRADED" : "PRESENT",
    });
    if (asString(latest.manifest_hash))
      evidenceItems.push({
        label: "Manifest hash (ledger)",
        digest_prefix: digestPrefix(latest.manifest_hash),
        source_endpoint: "/ui/evidence-chain",
        status: "PRESENT",
      });
  }
  const art = forensicRow ? asRecord(forensicRow.artifacts) : null;
  const obs = art ? asRecord(art.observed_sha256) : null;
  if (obs) {
    for (const k of ["evidence_manifest", "robustness", "cpcv"]) {
      const h = asString((obs as Record<string, unknown>)[k]);
      if (h)
        evidenceItems.push({
          label: `Artifact sha256 · ${k}`,
          digest_prefix: digestPrefix(h),
          source_endpoint: "/ui/backtest-forensics/latest",
          status: "PRESENT",
        });
    }
  }
  if (registry?.projection_digest_sha256)
    evidenceItems.push({
      label: "Evidence registry projection digest",
      digest_prefix: digestPrefix(registry.projection_digest_sha256),
      source_endpoint: "/ui/evidence",
      status: asString(verification?.trust_status) ?? "UNKNOWN",
    });
  if (paperManifestSha)
    evidenceItems.push({
      label: "Paper tracking manifest digest",
      digest_prefix: digestPrefix(paperManifestSha),
      source_endpoint: "/ui/paper-tracking/latest",
      status: asString(paperManifest?.trust_banner) ?? "UNKNOWN",
    });

  const ledgerProofLines: string[] = [];
  ledgerProofLines.push(`decision_ledger_chain_ok=${decisionLedgerOk === null ? "UNKNOWN" : String(decisionLedgerOk)}`);
  if (latest) {
    ledgerProofLines.push(`latest_sequence=${asNumber(latest.sequence_number) ?? "—"}`);
    ledgerProofLines.push(`payload_digest_prefix=${digestPrefix(latest.payload_digest_sha256)}`);
    ledgerProofLines.push(`previous_event_hash_prefix=${digestPrefix(latest.previous_event_hash)}`);
  } else ledgerProofLines.push("NO_DECISION_EVENTS_FOR_DOSSIER_SCOPE");

  const operatorReviewLines: string[] = [];
  const disc = asString(paperLatest?.lifecycle_promotion_disclaimer);
  if (disc) operatorReviewLines.push(`paper_tracking: ${disc.slice(0, 220)}`);
  const basis = asString(paperLatest?.lifecycle_basis_summary);
  if (basis) operatorReviewLines.push(`lifecycle_basis: ${basis.slice(0, 180)}`);
  for (const e of wbEntries.slice(0, 4)) {
    const r = asRecord(e);
    const key = asString(r?.work_item_key);
    if (key && (strategyId === "UNKNOWN" || key.includes(strategyId)))
      operatorReviewLines.push(`workboard: ${key} · ${asString(r?.attention_state) ?? "—"}`);
  }
  for (const o of lastOps) {
    const r = asRecord(o);
    if (!r) continue;
    operatorReviewLines.push(
      `operator_journal: ${asString(r.action) ?? "?"} · hash_prefix=${digestPrefix(r.event_hash)}`,
    );
  }
  if (!operatorReviewLines.length) operatorReviewLines.push("PENDING · no workboard/paper review lines for anchor");

  const degraded = [...asStringArray(chainRec?.degraded), ...asStringArray(forensics?.degraded)];
  if (input.queryFailed) degraded.push("READ_PLANE_QUERY_FAILED");

  const blockers =
    (forensicRow ? asStringArray(forensicRow.blockers).length : 0) +
    issueCodes.length +
    asStringArray(paperLatest?.lifecycle_blockers).length;
  const warnings = forensicRow ? asStringArray(forensicRow.warnings).length : 0;

  return {
    dossier_id: `dossier:${experimentId}:${asString(forensicRow?.strategy_id) ?? "none"}:${anchor.runId}`,
    experiment_id: asString(latest?.experiment_id) ?? experimentId,
    strategy_id: strategyId,
    run_id: anchor.runId,
    tracking_id: anchor.trackingId,
    intake_id: anchor.intakeId,
    thesis_id: anchor.thesisId,
    current_state: asString(latest?.promotion_state) ?? asString(latest?.status) ?? "UNKNOWN",
    previous_state: asString(prev?.promotion_state) ?? asString(prev?.status) ?? "UNKNOWN",
    decision_status: asString(latest?.promotion_state) ?? asString(latest?.event_type) ?? "UNKNOWN",
    latest_event_type: asString(latest?.event_type) ?? "UNKNOWN",
    ledger_event_hash: asString(latest?.event_hash) ?? "UNKNOWN",
    ledger_previous_event_hash: asString(latest?.previous_event_hash) ?? "UNKNOWN",
    manifest_hash: asString(latest?.manifest_hash) ?? "UNKNOWN",
    payload_digest_prefix: digestPrefix(latest?.payload_digest_sha256),
    writer_identity: asString(latest?.writer_identity) ?? asString(latest?.actor_id) ?? "UNKNOWN",
    sequence_number: latest != null && asNumber(latest.sequence_number) !== undefined ? String(asNumber(latest.sequence_number)) : "UNKNOWN",
    chain_status: chainStatus,
    decision_ledger_chain_ok: decisionLedgerOk ?? null,
    selected_ledger_chained: selectedChained === undefined ? null : selectedChained,
    gate_pass_count: gatePass,
    gate_fail_count: gateFail,
    gate_unknown_count: gateUnknown,
    warning_count: warnings,
    blocker_count: blockers,
    generated_at_utc: asString(forensics?.generated_at_utc) ?? asString(chainRec?.generated_at_utc) ?? "UNKNOWN",
    decision_time_utc: asString(latest?.created_at_utc) ?? "UNKNOWN",
    config_fingerprint: asString(input.readyzBody?.config_fingerprint) ?? "UNKNOWN",
    recommended_review_action: recommended,
    gate_rows: gateRows,
    benchmark_lines: benchmarkLines,
    robustness_lines: robustnessLines,
    execution_realism_lines: execLines,
    market_data_lines: marketLines,
    evidence_items: evidenceItems,
    ledger_proof_lines: ledgerProofLines,
    operator_review_lines: operatorReviewLines,
    degraded_flags: degraded.slice(0, 12),
    raw_sources: {
      latest_decision_event: latest ?? {},
      forensic_strategy_row: forensicRow ?? {},
      operator_actions_tail: lastOps,
      evidence_chain_summary: summary ?? {},
    },
  };
}
