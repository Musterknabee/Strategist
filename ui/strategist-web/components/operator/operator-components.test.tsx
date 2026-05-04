import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { DegradedBanner } from "./DegradedBanner";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";

describe("operator presentation components", () => {
  it("renders empty state", () => {
    const html = renderToStaticMarkup(<EmptyState title="None" detail="No rows" />);
    expect(html).toContain("None");
    expect(html).toContain("No rows");
  });

  it("renders error state", () => {
    const html = renderToStaticMarkup(<ErrorState title="Fail" message="oops" />);
    expect(html).toContain("Fail");
    expect(html).toContain("oops");
  });

  it("renders degraded banner with role status", () => {
    const html = renderToStaticMarkup(<DegradedBanner message="stale projection" />);
    expect(html).toContain('role="status"');
    expect(html).toContain("stale projection");
  });
});
