import { describe, expect, it } from "vitest";

import ResearchReviewJournalPage from "./page";

describe("ResearchReviewJournalPage", () => {
  it("exports a page component", () => {
    expect(typeof ResearchReviewJournalPage).toBe("function");
  });
});
