import { describe, expect, it } from "vitest";
import { buildOperatorHomeSummary } from "@/lib/operator/operator-home-summary-model";
describe("operator-home-summary-model", () => {
  it("shows UNKNOWN/NO_PAPER_DATA defaults without fabricating wins", () => {
    const s = buildOperatorHomeSummary({ strategyIntakeLatest: null, strategyThesisLatest: null, strategyThesisGenerationLatest: null, strategyMemoryLatest: null, strategyGraveyardLatest: null, paperTrackingLatest: null, backtestForensicsLatest: null, strategyBatchLatest: null, workboard: null, evidenceChain: null, providerHealth: null, providerSetup: null, anyError: false });
    expect(s.paper_win_count).toBe(0); expect(s.paper_loss_count).toBe(0); expect(s.paper_unknown_count).toBe(1); expect(s.strategy_rows[0].paper_result).toBe("NO_PAPER_DATA");
  });
});
