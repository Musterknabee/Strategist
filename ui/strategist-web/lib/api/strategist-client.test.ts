import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { strategistProbeGetJson } from "./strategist-client";

describe("strategistProbeGetJson", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL = "http://127.0.0.1:9";
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns JSON body on 500 (probe-style)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 500,
        text: async () => JSON.stringify({ ok: false, error: "internal" }),
      }),
    );
    const r = await strategistProbeGetJson<{ ok: boolean; error: string }>("/livez");
    expect(r.status).toBe(500);
    expect(r.data).toEqual({ ok: false, error: "internal" });
  });

  it("returns JSON body on 503 (readyz-style)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 503,
        text: async () => JSON.stringify({ ok: false, status: "BLOCKED" }),
      }),
    );
    const r = await strategistProbeGetJson<{ ok: boolean; status: string }>("/readyz");
    expect(r.status).toBe(503);
    expect(r.data).toEqual({ ok: false, status: "BLOCKED" });
  });

  it("throws on invalid JSON body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 200,
        text: async () => "not-json",
      }),
    );
    await expect(strategistProbeGetJson("/readyz")).rejects.toThrow(/valid JSON/);
  });
});
