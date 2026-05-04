import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { SeverityBadge } from "./SeverityBadge";

describe("SeverityBadge (terminal tape)", () => {
  it("applies sev--ok for ok severity", () => {
    const h = renderToStaticMarkup(<SeverityBadge severity="ok">PASS</SeverityBadge>);
    expect(h).toContain("sev--ok");
    expect(h).toContain("PASS");
  });

  it("maps warn, bad, info, neutral classes", () => {
    expect(renderToStaticMarkup(<SeverityBadge severity="warn">W</SeverityBadge>)).toContain("sev--warn");
    expect(renderToStaticMarkup(<SeverityBadge severity="bad">B</SeverityBadge>)).toContain("sev--bad");
    expect(renderToStaticMarkup(<SeverityBadge severity="info">I</SeverityBadge>)).toContain("sev--info");
    expect(renderToStaticMarkup(<SeverityBadge severity="neutral">N</SeverityBadge>)).toContain("sev--neutral");
  });
});
