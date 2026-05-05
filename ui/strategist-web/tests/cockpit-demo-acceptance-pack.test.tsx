/** @vitest-environment jsdom */

import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CandidateWorkbenchPane } from "@/components/cockpit/CandidateWorkbenchPane";
import { OperatorModeSwitchboard } from "@/components/cockpit/OperatorModeSwitchboard";
import { DemoModeBanner } from "@/components/demo/DemoModeBanner";
import { getOperatorModeDefinition, getPostGridSectionOrder } from "@/lib/operator/operator-modes";
import { buildCandidateWorkbenchModel } from "@/lib/operator/candidate-workbench-model";

const allowedNegatedAuthority = [
  /no live trading/i,
  /no live trading or broker orders/i,
  /no broker orders/i,
  /no deployment approval/i,
  /no operator signoff/i,
  /no profitability claim/i,
  /no promotion approval/i,
];

const forbiddenAuthority = [
  /execute trade/i,
  /place order/i,
  /live order/i,
  /approve live/i,
  /production approved/i,
  /operator signed off/i,
  /guaranteed profit/i,
  /profitable strategy/i,
  /ready for live trading/i,
  /deploy approved/i,
  /broker order submitted/i,
];

function assertNoForbiddenAuthorityUnlessNegated(text: string) {
  for (const phrase of forbiddenAuthority) {
    if (!phrase.test(text)) continue;
    expect(allowedNegatedAuthority.some((allowed) => allowed.test(text))).toBe(true);
  }
}

function baseModelInput() {
  return {
    strategyMemoryLatest: null,
    strategyGraveyardLatest: null,
    backtestForensicsLatest: null,
    paperTrackingLatest: null,
    providerSetup: null,
    providerHealth: null,
    evidenceChain: null,
  };
}

function renderWorkbench(overrides: Partial<ReturnType<typeof baseModelInput>> = {}) {
  return render(
    <CandidateWorkbenchPane
      {...baseModelInput()}
      {...overrides}
      openInspector={vi.fn()}
      onOpenMode={vi.fn()}
    />,
  );
}

afterEach(() => {
  cleanup();
  delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
});

describe("cockpit demo and acceptance hardening", () => {
  it("shows demo mode as synthetic and non-authoritative when explicitly enabled", () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    render(<DemoModeBanner />);
    const banner = screen.getByRole("status", { name: /demo mode safety banner/i });

    expect(within(banner).getByText("DEMO MODE")).toBeTruthy();
    expect(banner.textContent).toContain("Synthetic read-plane data only");
    expect(banner.textContent).toContain("No backend readiness claim");
    expect(banner.textContent).toContain("No provider credentials");
    expect(banner.textContent).toContain("No deployment approval");
    expect(banner.textContent).toContain("No operator signoff");
    expect(banner.textContent).toContain("No live trading or broker orders");
    expect(banner.textContent).toContain("No profitability claim");
    assertNoForbiddenAuthorityUnlessNegated(banner.textContent ?? "");
  });

  it("keeps empty workbench data UNKNOWN instead of OK", () => {
    renderWorkbench();
    const pane = screen.getByTestId("cockpit-candidate-workbench");

    expect(within(pane).getByText(/Paper\/research only/i)).toBeTruthy();
    expect(within(pane).getByText(/UNKNOWN · no candidates returned/i)).toBeTruthy();
    expect(within(pane).queryByText(/^OK$/)).toBeNull();
  });

  it("covers candidate review states: paper win, loss, blocked, duplicate, graveyard, pending key, and replay degraded", () => {
    const model = buildCandidateWorkbenchModel({
      ...baseModelInput(),
      strategyMemoryLatest: {
        generated_at_utc: "2026-05-05T10:00:00Z",
        latest: {
          duplicate_variant_count: 1,
          memory_records: [{ strategy_id: "loss" }, { strategy_id: "grave" }],
        },
      },
      strategyGraveyardLatest: { entries: [{ strategy_id: "grave", status: "HARD_BLOCKED", hard_blockers: ["PRIOR_REJECTION"] }] },
      backtestForensicsLatest: { strategies: [] },
      paperTrackingLatest: {
        generated_at_utc: "2026-05-05T10:05:00Z",
        latest: {
          tracking_id: "trk-loss",
          manifest: { candidate: { strategy_id: "loss" } },
          lifecycle_blockers: [],
          scorecard: { cumulative_paper_return: -0.4, warning_count: 0 },
        },
      },
      providerSetup: { summary: { missing_secret_count: 1 } },
      providerHealth: { entries: [] },
      evidenceChain: { degraded: ["DIGEST_MISMATCH"], timeline: { entries: [] }, summary: { chain_issue_count_total: 1 } },
    });
    const winModel = buildCandidateWorkbenchModel({
      ...baseModelInput(),
      strategyMemoryLatest: { latest: { memory_records: [{ strategy_id: "win" }] } },
      paperTrackingLatest: {
        latest: {
          tracking_id: "trk-win",
          manifest: { candidate: { strategy_id: "win" } },
          lifecycle_blockers: [],
          scorecard: { cumulative_paper_return: 0.2, warning_count: 0 },
        },
      },
      evidenceChain: { degraded: [], timeline: { entries: [{}] }, summary: { chain_issue_count_total: 0 } },
    });
    const blockedModel = buildCandidateWorkbenchModel({
      ...baseModelInput(),
      strategyMemoryLatest: { latest: { memory_records: [{ strategy_id: "blocked" }] } },
      paperTrackingLatest: {
        latest: {
          tracking_id: "trk-blocked",
          manifest: { candidate: { strategy_id: "blocked" } },
          lifecycle_blockers: ["EXPLICIT_BLOCKER"],
          scorecard: { cumulative_paper_return: 0.9, warning_count: 0 },
        },
      },
    });

    expect(winModel.rows[0]?.paper_result).toBe("PAPER_WIN");
    expect(model.rows.find((row) => row.strategy_id === "loss")?.paper_result).toBe("PAPER_LOSS");
    expect(blockedModel.rows[0]?.lifecycle_state).toBe("BLOCKED");
    expect(blockedModel.rows[0]?.paper_result).toBe("BLOCKED");
    expect(model.duplicate_warning_count).toBeGreaterThan(0);
    expect(model.graveyard_warning_count).toBeGreaterThan(0);
    expect(model.rows.every((row) => row.provider_status === "PENDING_KEY")).toBe(true);
    expect(model.replay_problem_count).toBeGreaterThan(0);
  });

  it("keeps workbench filters and navigation reachable by accessible labels", () => {
    const onOpenMode = vi.fn();
    render(
      <CandidateWorkbenchPane
        {...baseModelInput()}
        strategyMemoryLatest={{ latest: { memory_records: [{ strategy_id: "strat-a" }] } }}
        paperTrackingLatest={{
          latest: {
            tracking_id: "trk-a",
            manifest: { candidate: { strategy_id: "strat-a" } },
            lifecycle_blockers: [],
            scorecard: { cumulative_paper_return: 0.1, warning_count: 0 },
          },
        }}
        openInspector={vi.fn()}
        onOpenMode={onOpenMode}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /show paper wins candidates/i }));
    expect(screen.getByRole("button", { name: /show paper wins candidates/i }).getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: "Forensic Audit" }));
    fireEvent.click(screen.getByRole("button", { name: "Capital Firewall" }));
    expect(onOpenMode).toHaveBeenCalledWith("FORENSIC_AUDIT");
    expect(onOpenMode).toHaveBeenCalledWith("CAPITAL_FIREWALL");
  });

  it("renders advanced cockpit mode switches with clear labels for research, forensic, capital, and release flows", () => {
    const onChange = vi.fn();
    render(
      <OperatorModeSwitchboard
        mode="DAILY_OPS"
        onChange={onChange}
        definition={getOperatorModeDefinition("DAILY_OPS")}
        nextFocusLines={["PENDING - acceptance coverage"]}
        postGridOrderPreview={getPostGridSectionOrder("DAILY_OPS")}
      />,
    );

    for (const label of ["RESEARCH REVIEW", "FORENSIC AUDIT", "CAPITAL FIREWALL", "RELEASE CONTROL"]) {
      fireEvent.click(screen.getByRole("button", { name: label }));
    }
    expect(onChange).toHaveBeenCalledWith("RESEARCH_REVIEW");
    expect(onChange).toHaveBeenCalledWith("FORENSIC_AUDIT");
    expect(onChange).toHaveBeenCalledWith("CAPITAL_FIREWALL");
    expect(onChange).toHaveBeenCalledWith("RELEASE_CONTROL");
    expect(screen.getByTestId("cockpit-mode-command-banner").textContent).toMatch(/token-gated|authenticated/);
  });

  it("does not render forbidden authority language in the acceptance surfaces", () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    render(
      <>
        <DemoModeBanner />
        <OperatorModeSwitchboard
          mode="CAPITAL_FIREWALL"
          onChange={vi.fn()}
          definition={getOperatorModeDefinition("CAPITAL_FIREWALL")}
          nextFocusLines={["Review paper execution + broker read routes; browser does not submit orders."]}
          postGridOrderPreview={getPostGridSectionOrder("CAPITAL_FIREWALL")}
        />
        <CandidateWorkbenchPane {...baseModelInput()} openInspector={vi.fn()} onOpenMode={vi.fn()} />
      </>,
    );
    assertNoForbiddenAuthorityUnlessNegated(document.body.textContent ?? "");
  });
});
