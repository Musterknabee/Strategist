import type { QueryClient } from "@tanstack/react-query";
import type { UiOperatorCommandReceipt } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

/**
 * After an accepted operator UI command mutation, refresh only read-plane surfaces
 * that typically change (workboard queue, operator projection, evidence chain, default evidence cockpit).
 */
export async function invalidateReadPlaneAfterOperatorCommand(
  queryClient: QueryClient,
  boardLabel: string,
  receipt: UiOperatorCommandReceipt,
): Promise<void> {
  if (receipt.accepted !== true) return;
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.uiWorkboard(boardLabel) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.uiOperatorActions }),
    queryClient.invalidateQueries({ queryKey: queryKeys.uiEvidenceChain }),
    queryClient.invalidateQueries({ queryKey: queryKeys.uiEvidence(undefined) }),
  ]);
}
