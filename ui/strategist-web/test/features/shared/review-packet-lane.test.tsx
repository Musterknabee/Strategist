import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ReviewPacketLane } from "@/features/shared/components/review-packet-lane";

const packets = [
  {
    packet_id: "p1",
    packet_kind: "validator",
    generated_at_utc: "2026-04-16T10:00:00Z",
    file_name: "validator-a.json",
    note_count: 1,
    provenance_keys: ["metrics"],
    summary_line: "Validator summary",
    pinned: false,
    related_pack_kind: "validator-pack",
  },
  {
    packet_id: "p2",
    packet_kind: "tribunal",
    generated_at_utc: "2026-04-16T09:00:00Z",
    file_name: "tribunal-a.json",
    note_count: 4,
    provenance_keys: ["doctrine"],
    summary_line: "Tribunal summary",
    pinned: true,
  },
];

const togglePinned = vi.fn();
const inspectPacket = vi.fn();

vi.mock("@/features/shared/review-packets/review-packet-lane-provider", () => ({
  useReviewPacketLane: () => ({
    packets,
    inspectedPacketId: null,
    dismissPacket: vi.fn(),
    clearPackets: vi.fn(),
    togglePinned,
    inspectPacket,
  }),
}));

vi.mock("@/features/shared/components/review-packet-inspector", () => ({
  ReviewPacketInspector: () => null,
}));

describe("ReviewPacketLane", () => {
  it("renders pinned packets first and supports text filtering", () => {
    render(<ReviewPacketLane />);
    const summaries = screen.getAllByText(/summary/i).map((node) => node.textContent);
    expect(summaries[0]).toContain("Tribunal");

    fireEvent.change(screen.getByPlaceholderText(/search packet kind/i), {
      target: { value: "validator" },
    });
    expect(screen.getByText("Validator summary")).toBeInTheDocument();
    expect(screen.queryByText("Tribunal summary")).not.toBeInTheDocument();
  });

  it("allows pinning from the lane", () => {
    render(<ReviewPacketLane />);
    fireEvent.click(screen.getAllByRole("button", { name: /pin|unpin/i })[0]);
    expect(togglePinned).toHaveBeenCalled();
  });

  it("shows direct pack links when related pack metadata is present", () => {
    render(<ReviewPacketLane />);
    expect(screen.getByRole("link", { name: /open pack/i })).toHaveAttribute("href", "/packs/validator-pack?reviewPacket=p1&reviewPacketLane=open");
  });
});
