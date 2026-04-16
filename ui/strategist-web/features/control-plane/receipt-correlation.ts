import type { UiOperatorCommandReceipt } from "@/lib/contracts/ui";

export type ReceiptCorrelationHint = {
  status: "pending_projection" | "ready_to_check";
  summary: string;
};

export function deriveReceiptCorrelationHint(receipt: UiOperatorCommandReceipt): ReceiptCorrelationHint | null {
  if (!receipt.requires_projection_refresh) {
    return null;
  }
  const packKind = receipt.target.pack_kind ?? receipt.target.review_target ?? "the target pack";
  if (receipt.accepted) {
    return {
      status: "pending_projection",
      summary: `Watch ${packKind} timeline/evidence projections for reflected state; receipt accepted but read-plane confirmation is still pending.`,
    };
  }
  return {
    status: "ready_to_check",
    summary: `Receipt was not accepted for ${packKind}; verify timeline/escalation projections before retrying any governed action.`,
  };
}
