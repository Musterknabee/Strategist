/** @vitest-environment jsdom */

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RemediationGovernancePane } from "./RemediationGovernancePane";
import type { RemediationGovernanceInput } from "@/lib/operator/remediation-governance-model";

afterEach(() => cleanup());

const idle: RemediationGovernanceInput = {
  readyzBody: null,
  readyzLoading: true,
  readyzError: false,
  deployment: null,
  deploymentLoading: true,
  deploymentError: false,
  policyGatePayload: null,
  policyGateLoading: true,
  policyGateError: false,
  exceptionPayload: null,
  exceptionLoading: true,
  exceptionError: false,
  remediationPayload: null,
  remediationLoading: true,
  remediationError: false,
  drift: null,
  driftLoading: true,
  driftError: false,
  releaseReadiness: null,
  releaseLoading: true,
  releaseError: false,
  reviewJournal: null,
  reviewJournalLoading: true,
  reviewJournalError: false,
  providerStaleCount: null,
  providerBlockedCount: null,
};

describe("RemediationGovernancePane", () => {
  it("renders without crashing when sources are pending", () => {
    render(<RemediationGovernancePane governanceInput={idle} queryFailed={false} openInspector={vi.fn()} />);
    expect(screen.getByTestId("cockpit-remediation-governance")).toBeTruthy();
    expect(screen.getByTestId("cockpit-governance-counts")).toBeTruthy();
  });

  it("does not render secret-like substrings in the table body", () => {
    const input: RemediationGovernanceInput = {
      ...idle,
      readyzLoading: false,
      readyzBody: { status: "READY", blockers: ["NO_SECRET_VALUE"], warnings: [], checked_at_utc: "2026-05-04T12:00:00Z" },
      deploymentLoading: false,
      deploymentError: true,
      policyGateLoading: false,
      policyGateError: true,
      exceptionLoading: false,
      exceptionError: true,
      remediationLoading: false,
      remediationError: true,
      driftLoading: false,
      driftError: true,
      releaseLoading: false,
      releaseError: true,
      reviewJournalLoading: false,
      reviewJournalError: true,
    };
    const { container } = render(<RemediationGovernancePane governanceInput={input} queryFailed openInspector={vi.fn()} />);
    expect(container.textContent).not.toMatch(/sk-[a-z0-9]{20,}/i);
  });
});
