import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

const replaceMock = vi.fn();
const setReceiptLaneOpen = vi.fn();
const inspectReceipt = vi.fn();
const setReviewLaneOpen = vi.fn();
const inspectPacket = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams(window.location.search),
  usePathname: () => "/workboard",
  useRouter: () => ({ replace: replaceMock }),
}));

vi.mock("@/features/shared/command-receipts/command-receipt-lane-provider", () => ({
  useCommandReceiptLane: () => ({ setLaneOpen: setReceiptLaneOpen, inspectReceipt }),
}));

vi.mock("@/features/shared/review-packets/review-packet-lane-provider", () => ({
  useReviewPacketLane: () => ({ setLaneOpen: setReviewLaneOpen, inspectPacket }),
}));

describe("DeepLinkContextPills", () => {
  it("renders receipt and review context actions from query params", () => {
    window.history.replaceState({}, "", "http://localhost/workboard?receipt=cmd-42&reviewPacket=packet-9");
    render(<DeepLinkContextPills />);

    expect(screen.getByText(/receipt cmd-42/i)).toBeInTheDocument();
    expect(screen.getByText(/review packet packet-9/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /open receipt lane/i }));
    expect(setReceiptLaneOpen).toHaveBeenCalledWith(true);
    expect(inspectReceipt).toHaveBeenCalledWith("cmd-42");

    fireEvent.click(screen.getByRole("button", { name: /open review lane/i }));
    expect(setReviewLaneOpen).toHaveBeenCalledWith(true);
    expect(inspectPacket).toHaveBeenCalledWith("packet-9");
  });

  it("clears deep-link params through router replace", () => {
    window.history.replaceState({}, "", "http://localhost/workboard?receipt=cmd-42");
    render(<DeepLinkContextPills />);

    fireEvent.click(screen.getByRole("button", { name: /clear receipt context/i }));
    expect(replaceMock).toHaveBeenCalledWith("/workboard");
  });
});
