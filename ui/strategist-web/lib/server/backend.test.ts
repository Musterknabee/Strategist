import { afterEach, describe, expect, it, vi } from "vitest";

const originalEnv = { ...process.env };

describe("backend mutation auth forwarding", () => {
  afterEach(() => {
    process.env = { ...originalEnv };
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it("forwards the configured mutation token on UI command POSTs", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "secret-token";
    process.env.STRATEGIST_STRICT_BACKEND = "true";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) =>
      new Response(JSON.stringify({ accepted: true, action: "claim-item" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");
    await backend.submitUiCommand("claim-item", { operator_id: "jp", work_item_key: "w1" });

    const [, init] = fetchSpy.mock.calls[0] as [RequestInfo | URL, RequestInit];
    const headers = new Headers(init.headers);
    expect(headers.get("X-Strategy-Validator-Token")).toBe("secret-token");
  });

  it("does not attach the mutation token to read-only fetches", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "secret-token";
    process.env.STRATEGIST_STRICT_BACKEND = "true";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async (_input: RequestInfo | URL, init?: RequestInit) =>
      new Response(JSON.stringify({ schema_version: "ui_runtime_status/v1" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");
    await backend.fetchRuntime();

    const [, init] = fetchSpy.mock.calls[0] as [RequestInfo | URL, RequestInit];
    const headers = new Headers(init.headers);
    expect(headers.get("X-Strategy-Validator-Token")).toBeNull();
  });

  it("fails closed for UI command POSTs when the backend base URL is not configured", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "secret-token";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const backend = await import("./backend");

    await expect(backend.submitUiCommand("claim-item", { operator_id: "jp", work_item_key: "w1" })).rejects.toThrow(
      /Backend mutation route is unavailable/,
    );
  });

  it("fails closed for UI command POSTs when the backend rejects the mutation", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "secret-token";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async () =>
      new Response(JSON.stringify({ detail: "blocked" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");

    await expect(backend.submitUiCommand("renew-lease", { operator_id: "jp", work_item_key: "w1" })).rejects.toThrow(
      /Backend mutation request failed/,
    );
  });

  it("fails closed for workboard reads when the backend base URL is not configured", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const backend = await import("./backend");

    await expect(backend.fetchWorkboard()).rejects.toThrow(/Backend read route is unavailable/);
  });

  it("fails closed for workboard reads when the backend rejects the projection", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async () =>
      new Response(JSON.stringify({ detail: "stale" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");

    await expect(backend.fetchWorkboard()).rejects.toThrow(/Backend read request failed/);
  });

  it("fails closed for pack detail reads when the backend base URL is not configured", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const backend = await import("./backend");

    await expect(backend.fetchPackDetail({ pack_kind: "incident_pack" })).rejects.toThrow(/Backend read route is unavailable/);
  });

  it("fails closed for pack detail reads when the backend rejects the projection", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async () =>
      new Response(JSON.stringify({ detail: "missing" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");

    await expect(backend.fetchPackDetail({ pack_kind: "incident_pack" })).rejects.toThrow(/Backend read request failed/);
  });

  it("fails closed for burn-in, tribunal, and evidence reads when the backend base URL is not configured", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const backend = await import("./backend");

    await expect(backend.fetchBurnIn()).rejects.toThrow(/Backend read route is unavailable/);
    await expect(backend.fetchTribunal()).rejects.toThrow(/Backend read route is unavailable/);
    await expect(backend.fetchEvidence()).rejects.toThrow(/Backend read route is unavailable/);
  });

  it("fails closed for burn-in, tribunal, and evidence reads when the backend rejects the projection", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "http://backend.test";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "false";

    const fetchSpy = vi.fn(async () =>
      new Response(JSON.stringify({ detail: "downstream unavailable" }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);

    const backend = await import("./backend");

    await expect(backend.fetchBurnIn()).rejects.toThrow(/Backend read request failed/);
    await expect(backend.fetchTribunal()).rejects.toThrow(/Backend read request failed/);
    await expect(backend.fetchEvidence()).rejects.toThrow(/Backend read request failed/);
  });

  it("preserves explicit force-mocks mode for read-only dashboard fetches", async () => {
    process.env.STRATEGIST_BACKEND_BASE_URL = "";
    process.env.STRATEGIST_BACKEND_API_TOKEN = "";
    process.env.STRATEGIST_STRICT_BACKEND = "false";
    process.env.STRATEGIST_FORCE_MOCKS = "true";

    const backend = await import("./backend");

    await expect(backend.fetchWorkboard()).resolves.toMatchObject({ schema_version: "ui_workboard_dashboard/v1" });
    await expect(backend.fetchPackDetail({ pack_kind: "incident_pack" })).resolves.toMatchObject({ schema_version: "ui_pack_detail/v1" });
    await expect(backend.fetchBurnIn()).resolves.toMatchObject({ schema_version: "ui_burnin_dashboard/v1" });
    await expect(backend.fetchTribunal()).resolves.toMatchObject({ schema_version: "ui_tribunal_workspace/v1" });
    await expect(backend.fetchEvidence()).resolves.toMatchObject({ schema_version: "ui_evidence_dashboard/v1" });
  });
});
