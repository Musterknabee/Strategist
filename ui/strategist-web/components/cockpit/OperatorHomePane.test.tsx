/** @vitest-environment jsdom */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OperatorHomePane } from "@/components/cockpit/OperatorHomePane";
import type { OperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
describe("OperatorHomePane", () => {
  const summary: OperatorHomeSummary = { generated_at_utc: "2026-05-05T09:00:00Z", overall_status: "NEEDS_REVIEW", strategy_count: null, active_candidate_count: null, paper_win_count: 0, paper_loss_count: 0, paper_unknown_count: 1, blocked_count: 1, warning_count: 2, graveyarded_count: 0, duplicate_warning_count: 0, replay_verified_count: 0, replay_problem_count: 0, provider_ok_count: 0, provider_pending_key_count: 1, stale_data_count: 0, next_action: "REVIEW_BLOCKERS", next_action_reason: "Blockers present", top_attention_items: ["Blocked items: 1"], strategy_rows: [{ strategy_id: "UNKNOWN", label: "Unknown strategy", status: "UNKNOWN", paper_result: "NO_PAPER_DATA", paper_result_label: "No paper result yet", evidence_status: "UNKNOWN", provider_status: "Data key missing", replay_status: "REPLAY_UNKNOWN", blocker_count: 1, warning_count: 0, graveyard_status: "CLEAR", duplicate_status: "NONE", last_seen_at_utc: "UNKNOWN", digest_prefix: "-", next_action: "REVIEW_BLOCKERS", detail_target: "RESEARCH_REVIEW" }] };
  it("renders disclaimer", () => { render(<OperatorHomePane summary={summary} onShowAdvanced={vi.fn()} onOpenDetail={vi.fn()} />); expect(screen.getByTestId("cockpit-home-safety").textContent).toMatch(/Paper\/research only/i); expect(screen.getByTestId("cockpit-home-safety").textContent).toMatch(/No live trading/i); });
});
