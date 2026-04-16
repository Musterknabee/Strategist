import type { UiOperatorCommandReceipt, UiPackDetail, WorkbenchItem } from "@/lib/contracts/ui";

export type PackReceiptCorrelation = {
  status: "none" | "pending_projection" | "reflected";
  title: string;
  message: string;
  recommended_actions: string[];
};

function parseTime(value?: string | null) {
  if (!value) return null;
  const parsed = Date.parse(value);
  return Number.isNaN(parsed) ? null : parsed;
}

export function derivePackReceiptCorrelation(
  receipt?: UiOperatorCommandReceipt | null,
  detail?: UiPackDetail,
  pack?: WorkbenchItem | null,
): PackReceiptCorrelation | null {
  if (!receipt || !pack) return null;
  if (receipt.target.pack_kind && receipt.target.pack_kind !== pack.pack_kind) return null;

  const receiptTime = parseTime(receipt.generated_at_utc);
  const timelineTimes = (detail?.timeline?.items ?? [])
    .map((item) => typeof item.generated_at_utc === "string" ? parseTime(item.generated_at_utc) : null)
    .filter((value): value is number => typeof value === "number");
  const latestTimelineTime = timelineTimes.length ? Math.max(...timelineTimes) : null;

  if (!latestTimelineTime || (receiptTime && latestTimelineTime < receiptTime)) {
    return {
      status: "pending_projection",
      title: "Command receipt not yet reflected in the timeline",
      message: "A governed command receipt exists for this pack, but the current timeline projection has not yet caught up to that action.",
      recommended_actions: [
        "Refresh the pack timeline before acting on downstream assumptions.",
        "Use the receipt lane as temporary operator evidence while the read-plane catches up.",
        "Export a review packet if the lag affects adjudication or handoff.",
      ],
    };
  }

  return {
    status: "reflected",
    title: "Timeline has caught up to the latest governed receipt",
    message: "The current pack timeline is at least as recent as the latest in-session governed command receipt for this pack.",
    recommended_actions: [
      "Continue using pack projections as the primary operator surface.",
      "Retain the receipt as supplemental evidence in handoff exports.",
    ],
  };
}
