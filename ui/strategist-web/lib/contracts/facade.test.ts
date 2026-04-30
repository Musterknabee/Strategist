import { describe, expect, it } from "vitest";
import { UI_FACADE_PATH } from "./facade";

describe("facade contract anchor", () => {
  it("uses the backend /ui/facade path", () => {
    expect(UI_FACADE_PATH).toBe("/ui/facade");
  });
});
