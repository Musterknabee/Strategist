import type React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "@/components/app-shell";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

const mockedBoundary = vi.fn();
vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => mockedBoundary(),
}));

vi.mock("@/features/shared/components/runtime-status-rail", () => ({ RuntimeStatusRail: () => <div>runtime rail</div> }));
vi.mock("@/features/shared/components/command-bar", () => ({ CommandBar: () => <div>command bar</div> }));
vi.mock("@/features/shared/components/notification-lane", () => ({ NotificationLane: () => <div>notification lane</div> }));
vi.mock("@/features/shared/components/command-receipt-lane", () => ({ CommandReceiptLane: () => <div>command receipts</div> }));
vi.mock("@/features/shared/components/review-packet-lane", () => ({ ReviewPacketLane: () => <div>review packets</div> }));
vi.mock("@/features/shared/components/no-domain-access-state", () => ({ NoDomainAccessState: () => <div>no domains</div> }));

describe("AppShell nav policy", () => {
  it("hides redacted validator navigation and shows redacted domain summary", () => {
    mockedBoundary.mockReturnValue({
      operatorRole: "tribunal",
      allowedDomains: ["control-plane", "tribunal", "evidence"],
      canAccessDomain: (domain: string) => domain !== "validator",
      redactedDomains: ["validator"],
    });
    render(<AppShell><div>child</div></AppShell>);
    expect(screen.queryByText("Validator")).not.toBeInTheDocument();
    expect(screen.getByText(/redacted domains: validator/i)).toBeInTheDocument();
    expect(screen.getByText("Tribunal")).toBeInTheDocument();
  });

  it("renders the no-domain state when policy removes every governed surface", () => {
    mockedBoundary.mockReturnValue({
      operatorRole: "tribunal",
      allowedDomains: [],
      canAccessDomain: () => false,
      redactedDomains: ["control-plane", "validator", "tribunal", "evidence"],
    });
    render(<AppShell><div>child</div></AppShell>);
    expect(screen.getAllByText("no domains").length).toBeGreaterThan(0);
  });
});
