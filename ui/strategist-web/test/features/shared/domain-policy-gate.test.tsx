import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";

vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => ({
    operatorRole: "tribunal",
    canAccessDomain: (domain: string) => domain === "tribunal",
  }),
}));

describe("DomainPolicyGate", () => {
  it("renders a restriction card when the domain is redacted", () => {
    render(
      <DomainPolicyGate domain="validator" title="Validator burn-in">
        <div>hidden child</div>
      </DomainPolicyGate>,
    );

    expect(screen.getByText("Validator burn-in restricted")).toBeInTheDocument();
    expect(screen.getByText(/redacted for the active/i)).toBeInTheDocument();
    expect(screen.queryByText("hidden child")).not.toBeInTheDocument();
  });
});
