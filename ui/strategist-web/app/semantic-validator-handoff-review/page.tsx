"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiSemanticValidatorHandoffReview, type UiSemanticValidatorHandoffReviewQuery } from "@/hooks/useUiSemanticValidatorHandoffReview";
import type { UiSemanticValidatorHandoffReviewCheck, UiSemanticValidatorHandoffReviewComponentPath, UiSemanticValidatorHandoffReviewRecord } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type ReviewStatusMode = "all" | "READY_FOR_OPERATOR_REVIEW" | "REMEDIATION_REQUIRED" | "EVIDENCE_REPAIR_REQUIRED" | "LINEAGE_RECONSTRUCTION_REQUIRED";
type TrustMode = "all" | "TRUSTED" | "TRUST_RESTRICTED" | "UNTRUSTED";
type BoolMode = "all" | "yes" | "no";
type ReviewRow = UiSemanticValidatorHandoffReviewRecord & { __id: string };

const REVIEW_STATUS_MODES: ReviewStatusMode[] = ["all", "READY_FOR_OPERATOR_REVIEW", "REMEDIATION_REQUIRED", "EVIDENCE_REPAIR_REQUIRED", "LINEAGE_RECONSTRUCTION_REQUIRED"];
const TRUST_MODES: TrustMode[] = ["all", "TRUSTED", "TRUST_RESTRICTED", "UNTRUSTED"];
const BOOL_MODES: BoolMode[] = ["all", "yes", "no"];

function boolParam(mode: BoolMode): boolean | null {
  if (mode === "yes") return true;
  if (mode === "no") return false;
  return null;
}

function text(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

function shortDigest(value: unknown): string {
  const s = typeof value === "string" ? value : "";
  if (!s) return "—";
  return s.length > 16 ? `${s.slice(0, 10)}…${s.slice(-6)}` : s;
}

function countRows(counts?: Record<string, number>) {
  return Object.entries(counts ?? {}).map(([k, v]) => ({ k, v: String(v) }));
}

function selectedChecks(row: ReviewRow | null): UiSemanticValidatorHandoffReviewCheck[] {
  return row?.review_checklist ?? [];
}

function selectedComponents(row: ReviewRow | null): UiSemanticValidatorHandoffReviewComponentPath[] {
  return row?.component_paths ?? [];
}

export default function SemanticValidatorHandoffReviewPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [reviewStatusMode, setReviewStatusMode] = useState<ReviewStatusMode>("all");
  const [trustMode, setTrustMode] = useState<TrustMode>("all");
  const [operatorReviewMode, setOperatorReviewMode] = useState<BoolMode>("all");
  const [experimentNeedle, setExperimentNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiSemanticValidatorHandoffReviewQuery = useMemo(
    () => ({
      reviewStatus: reviewStatusMode === "all" ? null : reviewStatusMode,
      trustBanner: trustMode === "all" ? null : trustMode,
      operatorReviewAllowed: boolParam(operatorReviewMode),
      experimentIdContains: experimentNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [experimentNeedle, issueNeedle, operatorReviewMode, reviewStatusMode, trustMode],
  );

  const review = useUiSemanticValidatorHandoffReview(query);
  const summary = review.data?.summary;
  const rows = useMemo<ReviewRow[]>(
    () => (review.data?.reviews ?? []).map((row, i) => ({ ...row, __id: `${row.review_id}:${i}` })),
    [review.data?.reviews],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(review.data?.degraded);
  const guardrails = asStringArray(review.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "semantic-validator-handoff-review-counts",
        severity: (summary?.blocked_review_count ?? 0) > 0 || (summary?.untrusted_count ?? 0) > 0 ? "warn" : "ok",
        text: `review gates=${summary?.review_count_returned ?? 0}/${summary?.review_count_total ?? 0} ready=${summary?.ready_for_operator_review_count ?? 0} blocked=${summary?.blocked_review_count ?? 0} untrusted=${summary?.untrusted_count ?? 0}`,
      },
      {
        id: "semantic-validator-handoff-review-boundary",
        severity: "info",
        text: "operator-review gate only · validator submission, promotion, and execution remain forbidden by this read-plane",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.ready_for_operator_review_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `REV ${summary?.review_count_returned ?? 0}` },
      { severity: (summary?.blocked_review_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `BLK ${summary?.blocked_review_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<ReviewRow>[] = useMemo(
    () => [
      { key: "trust", header: "trust", width: "10%", cell: (row) => <StatusBadge raw={row.trust_banner} /> },
      { key: "status", header: "review", width: "21%", cell: (row) => <StatusBadge raw={row.review_status} /> },
      { key: "experiment", header: "experiment", width: "18%", cell: (row) => <code>{text(row.experiment_id)}</code> },
      { key: "checks", header: "checks", width: "8%", cell: (row) => <code>{row.review_pass_count}/{row.review_check_count}</code> },
      { key: "blocks", header: "blocks", width: "8%", cell: (row) => <code>{row.review_block_count}</code> },
      { key: "components", header: "components", width: "9%", cell: (row) => <code>{row.component_count_present}/{row.component_count_expected}</code> },
      { key: "submit", header: "validator_submit", width: "12%", cell: (row) => <StatusBadge raw={row.validator_submission_allowed ? "ALLOWED" : "FORBIDDEN"} /> },
      { key: "action", header: "recommended", cell: (row) => <code>{row.recommended_action}</code> },
    ],
    [],
  );

  const checkColumns: DenseColumn<UiSemanticValidatorHandoffReviewCheck>[] = useMemo(
    () => [
      { key: "status", header: "status", width: "10%", cell: (row) => <StatusBadge raw={row.status} /> },
      { key: "check", header: "check", width: "24%", cell: (row) => <code>{row.check_id}</code> },
      { key: "label", header: "label", width: "30%", cell: (row) => <span>{row.label}</span> },
      { key: "detail", header: "detail", cell: (row) => <span>{row.detail}</span> },
    ],
    [],
  );

  const componentColumns: DenseColumn<UiSemanticValidatorHandoffReviewComponentPath>[] = useMemo(
    () => [
      { key: "present", header: "present", width: "9%", cell: (row) => <StatusBadge raw={row.present ? "PRESENT" : "MISSING"} /> },
      { key: "component", header: "component", width: "18%", cell: (row) => <code>{row.component}</code> },
      { key: "artifact", header: "artifact", width: "24%", cell: (row) => <code>{text(row.artifact_id)}</code> },
      { key: "verified", header: "verified", width: "9%", cell: (row) => <StatusBadge raw={row.verified ? "YES" : "NO"} /> },
      { key: "handoff", header: "handoff", width: "9%", cell: (row) => <StatusBadge raw={row.handoff_allowed ? "YES" : "NO"} /> },
      { key: "path", header: "artifact_path", cell: (row) => <code>{text(row.artifact_path)}</code> },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">SEMANTIC · VALIDATOR REVIEW</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">SEMANTIC · VALIDATOR REVIEW</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/semantic-validator-handoff/review · read-only operator review gate over remediation-cleared validator handoff chains</p>
      {review.isLoading && <p className="muted">Loading…</p>}
      {review.isError && <p className="term-error">{review.error.message}</p>}

      {review.data && summary && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Review inventory" badge={<StatusBadge raw={degraded.length ? "DEGRADED" : "OK"} />} onInspect={() => openInspector({ title: "/ui/semantic-validator-handoff/review", rawJson: review.data })}>
              <TermKV rows={[{ k: "schema", v: review.data.schema_version }, { k: "reviews_total", v: String(summary.review_count_total) }, { k: "filtered", v: String(summary.review_count_filtered) }, { k: "returned", v: String(summary.review_count_returned) }, { k: "source_remediation", v: String(summary.source_remediation_count_total) }]} />
            </Pane>
            <Pane title="Gate posture">
              <TermKV rows={[{ k: "ready_for_review", v: String(summary.ready_for_operator_review_count) }, { k: "blocked", v: String(summary.blocked_review_count) }, { k: "trusted", v: String(summary.trusted_count) }, { k: "untrusted", v: String(summary.untrusted_count) }, { k: "validator_submit_allowed", v: String(summary.validator_submission_allowed_count) }]} />
            </Pane>
            <Pane title="Selected review" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff review", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "status", v: selectedRow?.review_status ?? "—" }, { k: "trust", v: selectedRow?.trust_banner ?? "—" }, { k: "chain", v: selectedRow?.chain_id ?? "—" }, { k: "digest", v: shortDigest(selectedRow?.chain_digest) }, { k: "checks", v: selectedRow ? `${selectedRow.review_pass_count}/${selectedRow.review_check_count}` : "—" }]} />
              {selectedRow?.chain_digest && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.chain_digest ?? "")}>Copy chain digest</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              <select className="term-input" value={reviewStatusMode} onChange={(e) => setReviewStatusMode(e.target.value as ReviewStatusMode)} aria-label="review status filter" style={{ width: "280px" }}>{REVIEW_STATUS_MODES.map((m) => <option key={m} value={m}>review:{m}</option>)}</select>
              <select className="term-input" value={trustMode} onChange={(e) => setTrustMode(e.target.value as TrustMode)} aria-label="trust banner filter" style={{ width: "185px" }}>{TRUST_MODES.map((m) => <option key={m} value={m}>trust:{m}</option>)}</select>
              <select className="term-input" value={operatorReviewMode} onChange={(e) => setOperatorReviewMode(e.target.value as BoolMode)} aria-label="operator review allowed filter" style={{ width: "185px" }}>{BOOL_MODES.map((m) => <option key={m} value={m}>review_allowed:{m}</option>)}</select>
              <label className="term-field"><span>experiment</span><input className="term-input" value={experimentNeedle} onChange={(e) => setExperimentNeedle(e.target.value)} placeholder="contains" style={{ width: "200px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="checksum/missing/reconstruct" style={{ width: "230px" }} /></label>
            </div>
          </Pane>

          <Pane title="Semantic validator handoff review gates" badge={<StatusBadge raw={(summary.blocked_review_count ?? 0) > 0 ? "BLOCKED" : "READY"} />}>
            <DenseTable columns={columns} rows={rows} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No semantic validator handoff review gates matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Review statuses"><TermKV rows={countRows(review.data.review_status_counts)} /></Pane>
            <Pane title="Trust banners"><TermKV rows={countRows(review.data.trust_banner_counts)} /></Pane>
            <Pane title="Authority gates"><TermKV rows={[{ k: "validator_submission", v: "always false" }, { k: "promotion", v: "always false" }, { k: "execution", v: "always false" }, { k: "mutation", v: review.data.mutation_authority }]} /></Pane>
          </PaneGrid>

          <Pane title="Selected review checklist" badge={<StatusBadge raw={(selectedRow?.review_block_count ?? 0) > 0 ? "BLOCKED" : "PASS"} />} onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff review checklist", rawJson: { review_id: selectedRow.review_id, review_checklist: selectedRow.review_checklist } }) : undefined}>
            <DenseTable columns={checkColumns} rows={selectedChecks(selectedRow)} rowKey={(row) => row.check_id} empty="No review checklist available." />
          </Pane>

          <Pane title="Selected component evidence map" onInspect={selectedRow ? () => openInspector({ title: "Semantic validator handoff component paths", rawJson: { review_id: selectedRow.review_id, component_paths: selectedRow.component_paths } }) : undefined}>
            <DenseTable columns={componentColumns} rows={selectedComponents(selectedRow)} rowKey={(row) => row.component} empty="No component evidence map available." />
          </Pane>

          {selectedRow && selectedRow.review_blocker_codes.length > 0 && <Pane title="Selected review blockers" badge={<StatusBadge raw="BLOCKED" />}><ul className="term-list">{selectedRow.review_blocker_codes.slice(0, 20).map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Semantic validator review degraded", rawJson: { degraded, source_degraded: review.data?.source_degraded } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}
          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/semantic-validator-handoff/review JSON" data={review.data} />
        </>
      )}
    </div>
  );
}
