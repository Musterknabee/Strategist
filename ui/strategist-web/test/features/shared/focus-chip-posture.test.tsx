import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RuntimeStatusRail } from "@/features/shared/components/runtime-status-rail";
import { CommandBar } from "@/features/shared/components/command-bar";
import { makeRuntimeStatus } from "@/test/utils/mock-ui";

const setPolicy = vi.fn();
const setOperatorRole = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/workboard",
}));

vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => ({
    operatorRole: "operator",
    setOperatorRole,
    setPolicy,
  }),
}));

vi.mock("@/features/shared/hooks/use-runtime-status", () => ({
  useRuntimeStatus: () => ({ data: makeRuntimeStatus() }),
}));

vi.mock("@/features/shared/components/projection-drift-notifier", () => ({
  ProjectionDriftNotifier: () => null,
}));

vi.mock("@/features/shared/command-receipts/command-receipt-lane-provider", () => ({
  useCommandReceiptLane: () => ({
    receipts: [{ command_id: "cmd-1234567890", action: "claim-item", accepted: true }],
    inspectedReceiptId: "cmd-1234567890",
    isLaneOpen: false,
    inspectReceipt: vi.fn(),
    setLaneOpen: vi.fn(),
  }),
}));

vi.mock("@/features/shared/review-packets/review-packet-lane-provider", () => ({
  useReviewPacketLane: () => ({
    packets: [{ packet_id: "packet-abcdefghi", packet_kind: "workboard" }],
    inspectedPacketId: "packet-abcdefghi",
    isLaneOpen: true,
    inspectPacket: vi.fn(),
    setLaneOpen: vi.fn(),
  }),
}));

describe("shell focus chip posture", () => {
  it("renders focused context posture in runtime rail", () => {
    render(<RuntimeStatusRail />);
    expect(screen.getByText(/focused receipt cmd-123456/i)).toBeInTheDocument();
    expect(screen.getByText(/lane collapsed/i)).toBeInTheDocument();
    expect(screen.getByText(/focused packet packet-abc/i)).toBeInTheDocument();
    expect(screen.getByText(/lane open/i)).toBeInTheDocument();
  });

  it("renders focused context posture in command bar", () => {
    render(<CommandBar />);
    expect(screen.getByText(/focused receipt cmd-123456/i)).toBeInTheDocument();
    expect(screen.getByText(/collapsed/i)).toBeInTheDocument();
    expect(screen.getByText(/focused packet packet-abc/i)).toBeInTheDocument();
    expect(screen.getByText(/\(open\)/i)).toBeInTheDocument();
  });
});
