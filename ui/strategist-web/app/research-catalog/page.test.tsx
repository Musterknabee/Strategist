/** @vitest-environment jsdom */

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import ResearchCatalogPage from "./page";

vi.mock("@/hooks/useUiResearchOsCatalog", () => ({
  useUiResearchOsCatalogLatest: () => ({
    data: {
      schema_version: "ui_research_os_evidence_catalog/v1",
      generated_at_utc: "2026-05-01T00:00:00+00:00",
      degraded: [],
      latest: {
        catalog_id: "catalog-demo",
        status: "RESTRICTED",
        trust_banner: "TRUST_RESTRICTED",
        entry_count: 2,
        latest_entry_count: 1,
        catalog_spine_sha256: "a".repeat(64),
        manifest_sha256: "b".repeat(64),
        category_counts: { OPERATOR_RUN: 1, EXPORT: 1 },
        latest_by_category: { OPERATOR_RUN: "research_os_operator_runs/latest/research_os_operator_run_manifest.json" },
        warnings: ["NO_PROVIDER_PAPER_LOOP"],
        blockers: [],
        entries: [
          {
            relative_path: "research_os_operator_runs/latest/research_os_operator_run_manifest.json",
            category: "OPERATOR_RUN",
            status_hint: "RESTRICTED",
            latest_alias: true,
            size_bytes: 123,
            file_sha256: "c".repeat(64),
            warnings: [],
            blockers: [],
          },
        ],
      },
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true, baseUrl: "http://127.0.0.1:8000" }),
}));

vi.mock("@/hooks/useTerminalPageBind", () => ({ useTerminalPageBind: () => {} }));

vi.mock("@/lib/terminal/cockpit-context", () => ({
  useTerminalCockpit: () => ({ openInspector: vi.fn() }),
}));

describe("ResearchCatalogPage", () => {
  it("renders evidence catalog summary and entries without token copy", () => {
    const { container } = render(<ResearchCatalogPage />);
    expect(screen.getByText(/Research Catalog/i)).toBeTruthy();
    expect(screen.getByText(/catalog-demo/i)).toBeTruthy();
    expect(screen.getAllByText(/OPERATOR_RUN/i).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /warnings/i }));
    expect(screen.getByText(/NO_PROVIDER_PAPER_LOOP/i)).toBeTruthy();
    expect(container.textContent?.includes("STRATEGY_VALIDATOR_API_TOKEN")).toBe(false);
  });
});
