import { describe, expect, it } from "vitest";

import { deriveReceiptCorrelationHint } from "@/features/control-plane/receipt-correlation";

describe("deriveReceiptCorrelationHint", () => {
  it("returns a pending-projection hint for accepted receipts awaiting refresh", () => {
    const hint = deriveReceiptCorrelationHint({
      schema_version: "1",
      generated_at_utc: "2026-04-16T10:00:00Z",
      command_id: "c1",
      action: "claim-item",
      accepted: true,
      operator_id: "op-1",
      execution_mode: "SIMULATED_RECEIPT_ONLY",
      requires_projection_refresh: true,
      target: { pack_kind: "validator_pack" },
      summary_line: "Claim accepted",
      operator_message: "Projection refresh pending",
    });

    expect(hint?.status).toBe("pending_projection");
    expect(hint?.summary).toContain("validator_pack");
  });
});
