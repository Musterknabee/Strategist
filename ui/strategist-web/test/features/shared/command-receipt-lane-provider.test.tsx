import type React from "react";
import { act, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CommandReceiptLaneProvider, useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";

describe("CommandReceiptLaneProvider", () => {
  it("syncs inspected id to the receipt query param", () => {
    window.history.replaceState({}, "", "http://localhost/workboard");
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <CommandReceiptLaneProvider>{children}</CommandReceiptLaneProvider>
    );
    const { result } = renderHook(() => useCommandReceiptLane(), { wrapper });

    act(() => {
      result.current.inspectReceipt("cmd-42");
    });

    expect(new URL(window.location.href).searchParams.get("receipt")).toBe("cmd-42");

    act(() => {
      result.current.inspectReceipt(null);
    });

    expect(new URL(window.location.href).searchParams.get("receipt")).toBeNull();
  });

  it("syncs lane open state to the receiptLane query param", () => {
    function Harness() {
      const { isLaneOpen, setLaneOpen } = useCommandReceiptLane();
      return (
        <div>
          <button onClick={() => setLaneOpen(!isLaneOpen)}>toggle</button>
          <span>{isLaneOpen ? "open" : "closed"}</span>
        </div>
      );
    }

    window.history.replaceState({}, "", "http://localhost/workboard");
    render(
      <CommandReceiptLaneProvider>
        <Harness />
      </CommandReceiptLaneProvider>,
    );

    fireEvent.click(screen.getByText("toggle"));
    expect(new URL(window.location.href).searchParams.get("receiptLane")).toBe("open");
    fireEvent.click(screen.getByText("toggle"));
    expect(new URL(window.location.href).searchParams.get("receiptLane")).toBeNull();
  });
});
