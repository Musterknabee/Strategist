/** @vitest-environment jsdom */

import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClientProvider } from "@tanstack/react-query";
import { StatusBadge } from "@/components/operator/StatusBadge";
import { JsonDetails } from "@/components/operator/JsonDetails";
import { DegradedBanner } from "@/components/operator/DegradedBanner";
import { ErrorState } from "@/components/operator/ErrorState";
import { createStrategistQueryClient } from "@/lib/query/query-client";
import { TerminalCockpitProvider, useTerminalCockpit } from "@/lib/terminal/cockpit-context";
import { CommandPalette } from "./CommandPalette";
import { DenseTable } from "./DenseTable";
import { InspectorDrawer } from "./InspectorDrawer";
import { TerminalShell } from "./TerminalShell";

const mockPush = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  usePathname: () => "/",
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: ReactNode;
    className?: string;
    title?: string;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

function TestHarness({ children }: { children: ReactNode }) {
  const [client] = useState(() => createStrategistQueryClient());
  return (
    <QueryClientProvider client={client}>
      <TerminalCockpitProvider>{children}</TerminalCockpitProvider>
    </QueryClientProvider>
  );
}

function OpenPaletteButton() {
  const { setPaletteOpen } = useTerminalCockpit();
  return (
    <button type="button" onClick={() => setPaletteOpen(true)}>
      open-palette
    </button>
  );
}

function OpenInspectorButton() {
  const { openInspector } = useTerminalCockpit();
  return (
    <button
      type="button"
      onClick={() =>
        openInspector({
          title: "InspTitle",
          body: <span>insp-body</span>,
          rawJson: { x: 1 },
        })
      }
    >
      open-inspector
    </button>
  );
}

beforeEach(() => {
  mockPush.mockClear();
  document.body.focus?.();
});

describe("TerminalShell", () => {
  it("renders rail links, main workspace, footer hints, and status/tape regions", () => {
    render(
      <TestHarness>
        <TerminalShell>
          <div data-testid="page">page</div>
        </TerminalShell>
      </TestHarness>,
    );
    expect(screen.getByLabelText(/quick nav/i)).toBeTruthy();
    expect(screen.getByTitle("/").textContent).toBe("OV");
    expect(screen.getByTestId("page").textContent).toBe("page");
    expect(screen.getByText(/G\+O\/W\/R\/E\/L\/P\/T nav/i)).toBeTruthy();
    expect(document.getElementById("terminal-status-rail")).toBeTruthy();
    expect(document.getElementById("terminal-event-tape")).toBeTruthy();
  });

  it("navigates via G chord when not typing in an input", async () => {
    render(
      <TestHarness>
        <TerminalShell>
          <span>x</span>
        </TerminalShell>
      </TestHarness>,
    );
    fireEvent.keyDown(window, { key: "g" });
    fireEvent.keyDown(window, { key: "e" });
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/evidence"));
  });

  it("does not fire G chord while an input is focused", () => {
    render(
      <TestHarness>
        <TerminalShell>
          <input data-testid="inp" defaultValue="" />
        </TerminalShell>
      </TestHarness>,
    );
    const inp = screen.getByTestId("inp");
    inp.focus();
    fireEvent.keyDown(window, { key: "g" });
    fireEvent.keyDown(window, { key: "o" });
    expect(mockPush).not.toHaveBeenCalled();
  });
});

describe("CommandPalette", () => {
  it("filters commands and navigates on select", async () => {
    render(
      <TestHarness>
        <OpenPaletteButton />
        <CommandPalette />
      </TestHarness>,
    );
    fireEvent.click(screen.getByText("open-palette"));
    const input = await screen.findByPlaceholderText(/command/i);
    fireEvent.change(input, { target: { value: "ledger" } });
    const opt = await screen.findByRole("option", { name: /go: ledger/i });
    fireEvent.click(opt);
    expect(mockPush).toHaveBeenCalledWith("/ledger");
  });
});

describe("InspectorDrawer", () => {
  it("shows title, body, raw JSON toggle, and closes", async () => {
    render(
      <TestHarness>
        <OpenInspectorButton />
        <InspectorDrawer />
      </TestHarness>,
    );
    fireEvent.click(screen.getByText("open-inspector"));
    expect(screen.getByText("InspTitle")).toBeTruthy();
    expect(screen.getByText("insp-body")).toBeTruthy();
    const rawBtn = screen.getByRole("button", { name: /show raw json/i });
    fireEvent.click(rawBtn);
    expect(screen.getByText(/"x": 1/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /close inspector/i }));
    await waitFor(() => expect(screen.queryByText("InspTitle")).toBeNull());
  });
});

describe("DenseTable", () => {
  it("renders empty state and invokes onRowClick", () => {
    const cols = [{ key: "a", header: "A", cell: (r: { id: string }) => r.id }];
    const { unmount } = render(
      <DenseTable columns={cols} rows={[]} rowKey={(r) => r.id} empty="no rows" />,
    );
    expect(screen.getByText("no rows")).toBeTruthy();
    unmount();
    cleanup();
    const onRowClick = vi.fn();
    const { container } = render(
      <DenseTable
        columns={cols}
        rows={[{ id: "r1" }]}
        rowKey={(r) => r.id}
        onRowClick={onRowClick}
      />,
    );
    const row = container.querySelector("tr[role='button']");
    expect(row).toBeTruthy();
    fireEvent.click(row!);
    expect(onRowClick).toHaveBeenCalledWith({ id: "r1" }, 0);
  });
});

describe("StatusBadge", () => {
  it("maps READY to ok tone", () => {
    const { container } = render(<StatusBadge raw="READY" />);
    expect(container.querySelector(".status-badge--ok")).toBeTruthy();
  });
});

describe("JsonDetails", () => {
  it("toggles JSON preview on click", () => {
    render(<JsonDetails summary="raw" data={{ z: 2 }} />);
    expect(screen.queryByText(/"z": 2/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /raw/i }));
    expect(screen.getByText(/"z": 2/)).toBeTruthy();
  });
});

describe("degraded / error presentation", () => {
  it("renders degraded and error states", () => {
    const { container: d1 } = render(<DegradedBanner message="deg" />);
    expect(d1.textContent).toContain("deg");
    const { container: d2 } = render(<ErrorState title="t" message="m" />);
    expect(d2.textContent).toContain("m");
  });
});
