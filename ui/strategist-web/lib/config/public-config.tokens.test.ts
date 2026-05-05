import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("public-config (browser safety)", () => {
  it("only reads allowlisted public browser flags (no token env vars)", () => {
    const src = readFileSync(join(here, "public-config.ts"), "utf8");
    const nextPublic = [...src.matchAll(/NEXT_PUBLIC_[A-Z0-9_]+/g)].map((m) => m[0]);
    expect(new Set(nextPublic)).toEqual(
      new Set(["NEXT_PUBLIC_STRATEGIST_API_BASE_URL", "NEXT_PUBLIC_STRATEGIST_DEMO_MODE"]),
    );
    expect(nextPublic.join("\n")).not.toMatch(/TOKEN|SECRET|PASSWORD|KEY/i);
  });
});
