/** @vitest-environment jsdom */

import { render, screen, cleanup } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ReleaseControlPane } from "./ReleaseControlPane";

beforeEach(() => cleanup());

describe("ReleaseControlPane", () => {
  const openInspector = vi.fn();

  it("renders UNKNOWN/PENDING posture and frontend claim explanation", () => {
    render(
      <ReleaseControlPane
        facade={null}
        evidence={null}
        evidenceChain={null}
        releaseReadiness={null}
        handoff={null}
        handoffSignoff={null}
        reviewJournal={null}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    expect(screen.getByTestId("cockpit-release-control")).toBeTruthy();
    expect(screen.getByTestId("cockpit-release-control-frontend-claim-note")).toBeTruthy();
    expect(screen.getByText(/opt-in operator/i)).toBeTruthy();
  });

  it("renders copyable command hints without invoking network", () => {
    render(
      <ReleaseControlPane
        facade={{}}
        evidence={{}}
        evidenceChain={{}}
        releaseReadiness={{}}
        handoff={{}}
        handoffSignoff={{}}
        reviewJournal={{}}
        queryFailed={false}
        openInspector={openInspector}
      />,
    );
    const hints = screen.getByTestId("cockpit-release-control-command-hints");
    expect(hints.textContent).toContain("strategy-validator-release-candidate");
    expect(hints.textContent).toContain("python scripts/package_repo.py");
    expect(hints.textContent).toContain("PRODUCTION_SENSITIVE");
    expect(hints.textContent).toContain("Browser does not execute");
  });
});
