"use client";

import { useMemo, useState } from "react";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { DenseTable, type DenseColumn } from "@/components/terminal/DenseTable";
import { Pane } from "@/components/terminal/Pane";
import { PaneGrid } from "@/components/terminal/PaneGrid";
import { TermKV } from "@/components/terminal/TermKV";
import { useTerminalPageBind } from "@/hooks/useTerminalPageBind";
import { useUiPromotionReview, type UiPromotionReviewQuery } from "@/hooks/useUiPromotionReview";
import type { UiPromotionReviewPacket } from "@/lib/api/types";
import { tryGetPublicStrategistApiBaseUrl } from "@/lib/config/public-config";
import { asStringArray } from "@/lib/operator/payload-utils";
import { useTerminalCockpit, type TapeLine } from "@/lib/terminal/cockpit-context";

type RecommendationMode = "all" | "READY_FOR_HUMAN_REVIEW" | "REVIEW_FOR_PAPER_EXTENSION" | "DO_NOT_PROMOTE";
type BlockerMode = "all" | "blocked" | "clear";
type PacketRow = UiPromotionReviewPacket & { __id: string };

const RECOMMENDATIONS: RecommendationMode[] = ["all", "READY_FOR_HUMAN_REVIEW", "REVIEW_FOR_PAPER_EXTENSION", "DO_NOT_PROMOTE"];
const BLOCKER_MODES: BlockerMode[] = ["all", "blocked", "clear"];

function text(value: unknown, fallback = "—"): string {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function shortDigest(value: string | null | undefined): string {
  if (!value) return "—";
  return value.length > 18 ? `${value.slice(0, 10)}…${value.slice(-6)}` : value;
}

function countRows(counts: Record<string, number> | undefined): { k: string; v: string }[] {
  return Object.entries(counts ?? {})
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .slice(0, 8)
    .map(([k, v]) => ({ k, v: String(v) }));
}

function blockerParam(mode: BlockerMode): boolean | null {
  if (mode === "blocked") return true;
  if (mode === "clear") return false;
  return null;
}

export default function PromotionReviewPage() {
  const config = tryGetPublicStrategistApiBaseUrl();
  const { openInspector, setLastDigest } = useTerminalCockpit();
  const [recommendation, setRecommendation] = useState<RecommendationMode>("all");
  const [blockerMode, setBlockerMode] = useState<BlockerMode>("all");
  const [strategyNeedle, setStrategyNeedle] = useState("");
  const [trackingNeedle, setTrackingNeedle] = useState("");
  const [issueNeedle, setIssueNeedle] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const query: UiPromotionReviewQuery = useMemo(
    () => ({
      recommendation: recommendation === "all" ? null : recommendation,
      requireBlockers: blockerParam(blockerMode),
      strategyIdContains: strategyNeedle.trim() || null,
      trackingId: trackingNeedle.trim() || null,
      issueContains: issueNeedle.trim() || null,
      limit: 300,
    }),
    [blockerMode, issueNeedle, recommendation, strategyNeedle, trackingNeedle],
  );

  const review = useUiPromotionReview(query);
  const summary = review.data?.summary;
  const rows = useMemo<PacketRow[]>(
    () => (review.data?.packets ?? []).map((packet, i) => ({ ...packet, __id: `${packet.packet_id}:${packet.tracking_id}:${i}` })),
    [review.data?.packets],
  );
  const selectedRow = useMemo(() => rows.find((row) => row.__id === selected) ?? rows[0] ?? null, [rows, selected]);
  const degraded = asStringArray(review.data?.degraded);
  const guardrails = asStringArray(review.data?.guardrails);

  const tape: TapeLine[] = useMemo(
    () => [
      {
        id: "promotion-review-counts",
        severity: (summary?.blocked_packet_count ?? 0) > 0 ? "warn" : "ok",
        text: `promotion_review packets=${summary?.packet_count_returned ?? 0}/${summary?.packet_count_total ?? 0} ready=${summary?.ready_for_human_review_count ?? 0} blocked=${summary?.blocked_packet_count ?? 0}`,
      },
      {
        id: "promotion-review-boundary",
        severity: "info",
        text: "human review only · no promotion, adjudication, broker order, or live execution authority",
      },
    ],
    [summary],
  );
  const ticker = useMemo(
    () => [
      { severity: (summary?.blocked_packet_count ?? 0) > 0 ? ("warn" as const) : ("neutral" as const), text: `PR ${summary?.packet_count_returned ?? 0}` },
      { severity: (summary?.ready_for_human_review_count ?? 0) > 0 ? ("ok" as const) : ("neutral" as const), text: `READY ${summary?.ready_for_human_review_count ?? 0}` },
    ],
    [summary],
  );
  useTerminalPageBind(tape, ticker);

  const columns: DenseColumn<PacketRow>[] = useMemo(
    () => [
      { key: "generated", header: "generated", width: "17%", cell: (row) => <code>{text(row.generated_at_utc)}</code> },
      { key: "strategy", header: "strategy", width: "16%", cell: (row) => <code>{row.strategy_id}</code> },
      { key: "tracking", header: "tracking", width: "14%", cell: (row) => <code>{row.tracking_id}</code> },
      { key: "state", header: "state", width: "15%", cell: (row) => <StatusBadge raw={row.candidate_lifecycle_state} /> },
      { key: "rec", header: "recommendation", width: "19%", cell: (row) => <StatusBadge raw={row.recommendation_status} /> },
      { key: "issues", header: "issues", width: "9%", cell: (row) => `${row.blocker_count}B / ${row.warning_count}W` },
      { key: "refs", header: "refs", cell: (row) => `${row.evidence_ref_count} refs` },
    ],
    [],
  );

  if (!config.ok) {
    return <div className="term-page"><h1 className="term-page__title">PROMOTION · REVIEW PACKETS</h1><p className="muted">{config.error.message}</p></div>;
  }

  return (
    <div className="term-page">
      <h1 className="term-page__title">PROMOTION · REVIEW PACKETS</h1>
      <p className="muted" style={{ fontSize: "10px" }}>GET /ui/promotion-review · human-only evidence packet index from paper-tracking artifacts</p>

      {review.isLoading && <p className="muted">Loading…</p>}
      {review.isError && <p className="term-error">{review.error.message}</p>}

      {review.data && (
        <>
          <PaneGrid cols={3}>
            <Pane title="Packet inventory" badge={<StatusBadge raw={(summary?.blocked_packet_count ?? 0) > 0 ? "REVIEW" : "CLEAR"} />}>
              <TermKV rows={[{ k: "total", v: String(summary?.packet_count_total ?? 0) }, { k: "filtered", v: String(summary?.packet_count_filtered ?? 0) }, { k: "returned", v: String(summary?.packet_count_returned ?? 0) }, { k: "invalid", v: String(summary?.invalid_artifact_count ?? 0) }, { k: "latest", v: text(summary?.latest_generated_at_utc) }]} />
            </Pane>
            <Pane title="Review posture">
              <TermKV rows={[{ k: "ready", v: String(summary?.ready_for_human_review_count ?? 0) }, { k: "extend_paper", v: String(summary?.review_for_paper_extension_count ?? 0) }, { k: "do_not_promote", v: String(summary?.do_not_promote_count ?? 0) }, { k: "blocked", v: String(summary?.blocked_packet_count ?? 0) }, { k: "warnings", v: String(summary?.warning_count_total ?? 0) }]} />
            </Pane>
            <Pane title="Selected packet" onInspect={selectedRow ? () => openInspector({ title: "Promotion review packet", rawJson: selectedRow }) : undefined}>
              <TermKV rows={[{ k: "packet", v: selectedRow?.packet_id ?? "—" }, { k: "state", v: <StatusBadge raw={selectedRow?.candidate_lifecycle_state} /> }, { k: "recommendation", v: <StatusBadge raw={selectedRow?.recommendation_status} /> }, { k: "days", v: text(selectedRow?.paper_days_of_signals) }, { k: "packet_sha", v: shortDigest(selectedRow?.packet_sha256) }, { k: "artifact_sha", v: shortDigest(selectedRow?.artifact_sha256) }]} />
              {(selectedRow?.packet_sha256 || selectedRow?.artifact_sha256) && <button type="button" className="term-button" style={{ marginTop: "6px" }} onClick={() => setLastDigest(selectedRow.packet_sha256 ?? selectedRow.artifact_sha256 ?? null)}>Copy digest target</button>}
            </Pane>
          </PaneGrid>

          <Pane title="Filters">
            <div className="term-toolbar">
              {RECOMMENDATIONS.map((m) => <button key={m} type="button" className={recommendation === m ? "term-chip active" : "term-chip"} onClick={() => setRecommendation(m)}>{m}</button>)}
              <select className="term-input" value={blockerMode} onChange={(e) => setBlockerMode(e.target.value as BlockerMode)} aria-label="blocker filter" style={{ width: "150px" }}>{BLOCKER_MODES.map((m) => <option key={m} value={m}>{m}</option>)}</select>
              <label className="term-field"><span>strategy</span><input className="term-input" value={strategyNeedle} onChange={(e) => setStrategyNeedle(e.target.value)} placeholder="contains" style={{ width: "170px" }} /></label>
              <label className="term-field"><span>tracking</span><input className="term-input" value={trackingNeedle} onChange={(e) => setTrackingNeedle(e.target.value)} placeholder="exact id" style={{ width: "170px" }} /></label>
              <label className="term-field"><span>issue</span><input className="term-input" value={issueNeedle} onChange={(e) => setIssueNeedle(e.target.value)} placeholder="blocker/warning/risk" style={{ width: "190px" }} /></label>
            </div>
          </Pane>

          <Pane title="Promotion review packets">
            <DenseTable<PacketRow> rows={rows} columns={columns} rowKey={(row) => row.__id} selectedKey={selectedRow?.__id ?? null} onRowClick={(row) => setSelected(row.__id)} empty="No promotion review packets matched the current filters." />
          </Pane>

          <PaneGrid cols={3}>
            <Pane title="Recommendation counts"><TermKV rows={countRows(review.data.recommendation_counts)} /></Pane>
            <Pane title="Lifecycle counts"><TermKV rows={countRows(review.data.lifecycle_state_counts)} /></Pane>
            <Pane title="Risk gates"><TermKV rows={countRows(review.data.portfolio_gate_counts)} /></Pane>
          </PaneGrid>

          {selectedRow && (selectedRow.blockers.length > 0 || selectedRow.warnings.length > 0 || selectedRow.known_risks.length > 0) && (
            <Pane title="Selected packet issues" onInspect={() => openInspector({ title: "Promotion review packet issues", rawJson: { blockers: selectedRow.blockers, warnings: selectedRow.warnings, known_risks: selectedRow.known_risks } })}>
              <ul className="term-list">{[...selectedRow.blockers.map((x) => `BLOCKER · ${x}`), ...selectedRow.warnings.map((x) => `WARNING · ${x}`), ...selectedRow.known_risks.map((x) => `RISK · ${x}`)].slice(0, 12).map((line) => <li key={line}>{line}</li>)}</ul>
            </Pane>
          )}

          {degraded.length > 0 && <Pane title="Degraded signals" badge={<StatusBadge raw="DEGRADED" />} onInspect={() => openInspector({ title: "Promotion review degradation", rawJson: { degraded, invalid_artifacts: review.data?.invalid_artifacts } })}><ul className="term-list">{degraded.map((line) => <li key={line}>{line}</li>)}</ul></Pane>}

          <Pane title="Guardrails"><ul className="term-list">{guardrails.map((line) => <li key={line}>{line}</li>)}</ul></Pane>
          <JsonDetails summary="Drilldown: /ui/promotion-review JSON" data={review.data} />
        </>
      )}
    </div>
  );
}
