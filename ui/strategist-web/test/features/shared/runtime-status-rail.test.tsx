import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { RuntimeStatusRail } from "@/features/shared/components/runtime-status-rail";

const setPolicy = vi.fn();
const setOperatorRole = vi.fn();

vi.mock("@/features/shared/domain-boundary-provider", () => ({
  useDomainBoundary: () => ({
    operatorRole: "tribunal",
    setOperatorRole,
    setPolicy,
  }),
}));

vi.mock("@/features/shared/hooks/use-runtime-status", () => ({
  useRuntimeStatus: () => ({
    data: {
      generated_at_utc: new Date().toISOString(),
      environment: "staging",
      read_plane: { status: "ready", freshness_status: "fresh", operator_message: "All projections fresh." },
      backend: { status: "reachable", base_mode: "proxy", operator_message: "Backend reachable." },
      blindness: { tribunal_mode: "enforced", operator_message: "Blindness enforced." },
      providers: { enabled_count: 4, items: [] },
      persona: { active_role: "tribunal", active_label: "Tribunal", available_roles: ["operator", "validator", "tribunal"], default_route: "/tribunal" },
      command_bar: { allowed_actions: [], operator_hint: "Use governed actions only." },
      policy: { allowed_domains: ["tribunal", "evidence"], redacted_domains: ["validator"], allowed_actions: [] },
    },
  }),
}));

vi.mock("@/features/shared/components/projection-drift-notifier", () => ({
  ProjectionDriftNotifier: () => null,
}));

describe("RuntimeStatusRail", () => {
  it("renders runtime badges and applies policy to domain boundary state", () => {
    render(<RuntimeStatusRail />);
    expect(screen.getByText(/read plane fresh/i)).toBeInTheDocument();
    expect(screen.getByText(/backend reachable/i)).toBeInTheDocument();
    expect(screen.getByText(/allowed domains: tribunal, evidence/i)).toBeInTheDocument();
    expect(setPolicy).toHaveBeenCalled();
  });
});
