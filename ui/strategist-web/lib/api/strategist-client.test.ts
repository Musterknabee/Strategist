import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { strategistPostJson, strategistProbeGetJson } from "./strategist-client";

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


describe("strategistPostJson", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL = "http://127.0.0.1:9";
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts mutation JSON with explicit runtime token and operator principal headers", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ accepted: true, action: "claim-item" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await strategistPostJson(
      "/ui/commands/claim-item",
      { operator_id: "jp", work_item_key: "WB-1" },
      { mutationToken: "secret-token", operatorId: "jp" },
    );

    expect(result.data).toEqual({ accepted: true, action: "claim-item" });
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:9/ui/commands/claim-item",
      expect.objectContaining({
        method: "POST",
        cache: "no-store",
        body: JSON.stringify({ operator_id: "jp", work_item_key: "WB-1" }),
        headers: expect.objectContaining({
          authorization: "Bearer secret-token",
          "x-strategy-validator-operator": "jp",
          accept: "application/json",
          "content-type": "application/json",
        }),
      }),
    );
  });

  it("does not synthesize mutation auth headers when no runtime token is supplied", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ accepted: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await strategistPostJson("/ui/commands/claim-item", { operator_id: "operator", work_item_key: "WB-1" });

    const init = fetchMock.mock.calls[0][1] as { headers: Record<string, string> };
    expect(init.headers.authorization).toBeUndefined();
    expect(init.headers["x-strategy-validator-operator"]).toBeUndefined();
  });
});
