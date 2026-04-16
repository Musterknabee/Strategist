import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CommandBar } from "@/features/shared/components/command-bar";

const push = vi.fn();
const setReceiptLaneOpen = vi.fn();
const setReviewLaneOpen = vi.fn();
const inspectReceipt = vi.fn();
const inspectPacket = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
  usePathname: () => "/workboard",
}));

vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => ({
    allowedDomains: ["control-plane", "validator", "evidence", "tribunal"],
    redactedDomains: [],
  }),
}));

vi.mock("@/features/shared/hooks/use-runtime-status", () => ({
  useRuntimeStatus: () => ({
    data: {
      command_bar: { allowed_actions: ["claim-item"], operator_hint: "Use governed actions only." },
    },
  }),
}));

vi.mock("@/features/shared/command-receipts/command-receipt-lane-provider", () => ({
  useCommandReceiptLane: () => ({
    receipts: [{ command_id: "cmd-00123456789", action: "claim-item" }],
    inspectedReceiptId: null,
    isLaneOpen: false,
    setLaneOpen: setReceiptLaneOpen,
    inspectReceipt,
  }),
}));

vi.mock("@/features/shared/review-packets/review-packet-lane-provider", () => ({
  useReviewPacketLane: () => ({
    packets: [{ packet_id: "pkt-00123456789", packet_kind: "burnin" }],
    inspectedPacketId: null,
    isLaneOpen: false,
    setLaneOpen: setReviewLaneOpen,
    inspectPacket,
  }),
}));

describe("CommandBar", () => {
  it("filters quick actions and routes to the selected page action", () => {
    render(<CommandBar />);
    fireEvent.change(screen.getByLabelText(/command bar search/i), {
      target: { value: "forensic" },
    });
    fireEvent.click(screen.getByText(/open validator forensic/i));
    expect(push).toHaveBeenCalledWith("/validator/forensic");
  });
});
