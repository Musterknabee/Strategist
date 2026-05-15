/** @vitest-environment jsdom */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { OperatorHomePane, type OperatorReadPlaneStatus } from "@/components/cockpit/OperatorHomePane";
import type { OperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
describe("OperatorHomePane", () => {
  const summary: OperatorHomeSummary = { generated_at_utc: "2026-05-05T09:00:00Z", overall_status: "NEEDS_REVIEW", strategy_count: null, active_candidate_count: null, paper_win_count: 0, paper_loss_count: 0, paper_unknown_count: 1, blocked_count: 1, warning_count: 2, graveyarded_count: 0, duplicate_warning_count: 0, replay_verified_count: 0, replay_problem_count: 0, provider_ok_count: 0, provider_pending_key_count: 1, stale_data_count: 0, next_action: "REVIEW_BLOCKERS", next_action_reason: "Blockers present", top_attention_items: ["Blocked items: 1"], strategy_rows: [{ strategy_id: "UNKNOWN", label: "Unknown strategy", status: "UNKNOWN", paper_result: "NO_PAPER_DATA", paper_result_label: "No paper result yet", evidence_status: "UNKNOWN", provider_status: "Data key missing", replay_status: "REPLAY_UNKNOWN", blocker_count: 1, warning_count: 0, graveyard_status: "CLEAR", duplicate_status: "NONE", last_seen_at_utc: "UNKNOWN", digest_prefix: "-", next_action: "REVIEW_BLOCKERS", detail_target: "RESEARCH_REVIEW" }] };
  const readPlaneStatus: OperatorReadPlaneStatus = { label: "Read-plane connected", tone: "OK", api: "127.0.0.1:8000", readiness: "READY", facade: "loaded", hint: "Backend probes and facade are available." };
  it("renders calm triage, safety boundary, and advanced/candidate paths", () => {
    const onShowAdvanced = vi.fn();
    const onOpenDetail = vi.fn();
    render(<OperatorHomePane summary={summary} readPlaneStatus={readPlaneStatus} onShowAdvanced={onShowAdvanced} onOpenDetail={onOpenDetail} />);
    expect(screen.getByRole("heading", { name: "Operator Home" })).toBeTruthy();
    expect(screen.getByTestId("cockpit-read-plane-status").textContent).toMatch(/Read-plane connected/);
    expect(screen.getByTestId("cockpit-read-plane-status").textContent).toMatch(/127\.0\.0\.1:8000/);
    expect(screen.getByTestId("cockpit-guided-flow").textContent).toMatch(/Start here/);
    expect(screen.getByTestId("cockpit-guided-research").textContent).toMatch(/Run or import strategy batch data/);
    expect(screen.getByTestId("cockpit-home-safety").textContent).toMatch(/Paper\/research only/i);
    expect(screen.getByTestId("cockpit-home-safety").textContent).toMatch(/No live trading/i);
    expect(screen.getByText("Overall status")).toBeTruthy();
    expect(screen.getByText("Evidence / replay")).toBeTruthy();
    fireEvent.click(screen.getByTestId("cockpit-guided-paper"));
    expect(onOpenDetail).toHaveBeenCalledWith("CAPITAL_FIREWALL");
    fireEvent.click(screen.getByTestId("cockpit-open-candidate-workbench"));
    expect(onOpenDetail).toHaveBeenCalledWith("RESEARCH_REVIEW");
    fireEvent.click(screen.getByTestId("cockpit-show-advanced"));
    expect(onShowAdvanced).toHaveBeenCalled();
  });
});
