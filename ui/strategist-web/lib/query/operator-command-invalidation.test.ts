import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import type { UiOperatorCommandReceipt } from "@/lib/api/types";
import { invalidateReadPlaneAfterOperatorCommand } from "./operator-command-invalidation";
import { queryKeys } from "./keys";

function receipt(accepted: boolean): UiOperatorCommandReceipt {
  return {
    schema_version: "ui_operator_command_receipt/v1",
    accepted,
    action: "claim-item",
  };
}

describe("invalidateReadPlaneAfterOperatorCommand", () => {
  it("does not invalidate when receipt is not accepted", async () => {
    const queryClient = new QueryClient();
    const spy = vi.spyOn(queryClient, "invalidateQueries");
    await invalidateReadPlaneAfterOperatorCommand(queryClient, "operator", receipt(false));
    expect(spy).not.toHaveBeenCalled();
  });

  it("invalidates only workboard, operator-actions, evidence-chain, and default evidence", async () => {
    const queryClient = new QueryClient();
    const spy = vi.spyOn(queryClient, "invalidateQueries");
    await invalidateReadPlaneAfterOperatorCommand(queryClient, "my-board", receipt(true));
    expect(spy).toHaveBeenCalledTimes(4);
    const keys = spy.mock.calls.map((c) => c[0]!.queryKey);
    expect(keys).toContainEqual(queryKeys.uiWorkboard("my-board"));
    expect(keys).toContainEqual(queryKeys.uiOperatorActions);
    expect(keys).toContainEqual(queryKeys.uiEvidenceChain);
    expect(keys).toContainEqual(queryKeys.uiEvidence(undefined));
  });
});
