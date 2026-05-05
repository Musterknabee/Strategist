import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { strategistGetJson, strategistPostJson, strategistProbeGetJson } from "./strategist-client";

describe("strategistGetJson demo mode", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns demo read-plane payloads when explicitly enabled and backend is absent", async () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const r = await strategistGetJson<{ demo_only: boolean; schema_version: string }>("/ui/facade");

    expect(r.status).toBe(299);
    expect(r.data.demo_only).toBe(true);
    expect(r.data.schema_version).toBe("ui_public_facade/v1");
  });

  it("does not mask backend absence by default", async () => {
    process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL = "http://127.0.0.1:9";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(strategistGetJson("/ui/facade")).rejects.toMatchObject({ kind: "unavailable" });
  });
});

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

  it("returns blocked demo readiness when demo mode is enabled without a backend URL", async () => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL;
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";

    const r = await strategistProbeGetJson<{ demo_only: boolean; status: string }>("/readyz");

    expect(r.status).toBe(503);
    expect(r.data).toMatchObject({ demo_only: true, status: "DEMO_ONLY_NOT_READY" });
  });
});


describe("strategistPostJson", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL = "http://127.0.0.1:9";
  });

  afterEach(() => {
    delete process.env.NEXT_PUBLIC_STRATEGIST_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE;
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("refuses mutation calls in demo mode without making a network request", async () => {
    process.env.NEXT_PUBLIC_STRATEGIST_DEMO_MODE = "true";
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    await expect(strategistPostJson("/ui/commands/claim-item", { operator_id: "demo" })).rejects.toMatchObject({
      kind: "unauthorized",
      message: expect.stringContaining("Demo mode disables mutation"),
    });
    expect(fetchMock).not.toHaveBeenCalled();
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

  it("sends X-Strategy-Validator-Token when tokenDelivery requests it", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ accepted: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await strategistPostJson(
      "/ui/commands/renew-lease",
      { operator_id: "a", work_item_key: "w" },
      { mutationToken: "t", operatorId: "a", tokenDelivery: "x_strategy_validator_token" },
    );

    const init = fetchMock.mock.calls[0][1] as { headers: Record<string, string> };
    expect(init.headers["x-strategy-validator-token"]).toBe("t");
    expect(init.headers.authorization).toBeUndefined();
    expect(init.headers["x-strategy-validator-operator"]).toBe("a");
  });

  it("throws StrategistApiError with operator-safe copy on 401 with FastAPI detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ detail: "missing bearer" }),
      }),
    );
    await expect(
      strategistPostJson("/ui/commands/claim-item", { operator_id: "x", work_item_key: "y" }),
    ).rejects.toMatchObject({
      name: "StrategistApiError",
      kind: "unauthorized",
      message: expect.stringContaining("missing bearer"),
    });
  });

  it("throws on 403 with forbidden label", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        text: async () => JSON.stringify({ detail: "policy block" }),
      }),
    );
    await expect(strategistPostJson("/ui/commands/claim-item", {})).rejects.toMatchObject({
      kind: "unauthorized",
      message: expect.stringContaining("forbidden"),
    });
  });

  it("throws on 503 with detail when JSON body includes detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        text: async () => JSON.stringify({ detail: "not ready" }),
      }),
    );
    await expect(strategistPostJson("/ui/commands/claim-item", {})).rejects.toMatchObject({
      kind: "unavailable",
      message: expect.stringMatching(/Backend unavailable.*not ready/),
    });
  });
});
