import type React from "react";
import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReviewPacketLaneProvider, useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";

describe("ReviewPacketLaneProvider", () => {
  it("syncs inspected id to the reviewPacket query param", () => {
    window.history.replaceState({}, "", "http://localhost/workboard");
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <ReviewPacketLaneProvider>{children}</ReviewPacketLaneProvider>
    );
    const { result } = renderHook(() => useReviewPacketLane(), { wrapper });

    act(() => {
      result.current.inspectPacket("packet-42");
    });

    expect(new URL(window.location.href).searchParams.get("reviewPacket")).toBe("packet-42");

    act(() => {
      result.current.inspectPacket(null);
    });

    expect(new URL(window.location.href).searchParams.get("reviewPacket")).toBeNull();
  });

  it("syncs lane open state to the reviewPacketLane query param", () => {
    function Harness() {
      const { isLaneOpen, setLaneOpen } = useReviewPacketLane();
      return (
        <div>
          <button onClick={() => setLaneOpen(!isLaneOpen)}>toggle</button>
          <span>{isLaneOpen ? "open" : "closed"}</span>
        </div>
      );
    }

    window.history.replaceState({}, "", "http://localhost/workboard");
    render(
      <ReviewPacketLaneProvider>
        <Harness />
      </ReviewPacketLaneProvider>,
    );

    fireEvent.click(screen.getByText("toggle"));
    expect(new URL(window.location.href).searchParams.get("reviewPacketLane")).toBe("open");
    fireEvent.click(screen.getByText("toggle"));
    expect(new URL(window.location.href).searchParams.get("reviewPacketLane")).toBeNull();
  });
});
