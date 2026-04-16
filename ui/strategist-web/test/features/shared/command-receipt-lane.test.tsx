import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CommandReceiptLane } from "@/features/shared/components/command-receipt-lane";

const inspectPacket = vi.fn();

vi.mock("@/features/shared/command-receipts/command-receipt-lane-provider", () => ({
  useCommandReceiptLane: () => ({
    receipts: [
      {
        command_id: "cmd-1",
        action: "claim-item",
        accepted: true,
        execution_mode: "SIMULATED_RECEIPT_ONLY",
        requires_projection_refresh: true,
        summary_line: "Claim receipt",
        operator_message: "Wait for refresh.",
        generated_at_utc: new Date("2026-04-16T10:00:00Z").toISOString(),
        target: { pack_kind: "pack-1", work_item_key: "wk-1" },
      },
      {
        command_id: "cmd-2",
        action: "renew-lease",
        accepted: false,
        execution_mode: "SIMULATED_RECEIPT_ONLY",
        requires_projection_refresh: false,
        summary_line: "Renew lease rejected",
        operator_message: "Check escalation.",
        generated_at_utc: new Date("2026-04-16T09:00:00Z").toISOString(),
        target: { pack_kind: null, work_item_key: null },
      },
    ],
    dismissReceipt: vi.fn(),
    clearReceipts: vi.fn(),
  }),
}));

vi.mock("@/features/shared/review-packets/review-packet-lane-provider", () => ({
  useReviewPacketLane: () => ({
    packets: [
      {
        packet_id: "p-1",
        packet_kind: "pack-detail",
        generated_at_utc: new Date("2026-04-16T10:05:00Z").toISOString(),
        file_name: "pack-1.json",
        note_count: 1,
        provenance_keys: ["pack"],
        summary_line: "Pack packet",
        related_pack_kind: "pack-1",
        related_work_item_key: "wk-1",
      },
    ],
    inspectPacket,
  }),
}));

vi.mock("@/features/control-plane/receipt-correlation", () => ({
  deriveReceiptCorrelationHint: () => ({ summary: "Projection confirmation pending." }),
}));

describe("CommandReceiptLane", () => {
  it("renders grouped receipt sections and searchable controls", () => {
    render(<CommandReceiptLane />);
    expect(screen.getByText(/governed command lane/i)).toBeInTheDocument();
    expect(screen.getByText("awaiting-refresh")).toBeInTheDocument();
    expect(screen.getAllByText("attention").length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/search action, execution mode/i)).toBeInTheDocument();
  });

  it("renders cross-lane navigation affordances", () => {
    render(<CommandReceiptLane />);
    expect(screen.getByRole("link", { name: /open related pack/i })).toHaveAttribute("href", "/packs/pack-1?receipt=cmd-1&receiptLane=open");
    expect(screen.getByRole("button", { name: /inspect related review packet/i })).toBeInTheDocument();
  });
});
