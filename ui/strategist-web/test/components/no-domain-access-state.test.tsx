import type React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { NoDomainAccessState } from "@/features/shared/components/no-domain-access-state";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => ({ operatorRole: "tribunal" }),
}));

describe("NoDomainAccessState", () => {
  it("renders a governed no-access message", () => {
    render(<NoDomainAccessState />);
    expect(screen.getByText(/no governed domains available/i)).toBeInTheDocument();
    expect(screen.getByText(/tribunal/i)).toBeInTheDocument();
  });
});
