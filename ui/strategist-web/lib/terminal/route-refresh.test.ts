import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { queryKeys } from "@/lib/query/keys";
import { invalidateQueriesForRoute } from "./route-refresh";

describe("invalidateQueriesForRoute", () => {
  it("invalidates overview keys for /", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiFacade]);
    expect(keys).toContainEqual([...queryKeys.uiWorkboard("operator")]);
    expect(keys).toContainEqual([...queryKeys.uiProviderHealth]);
    spy.mockRestore();
  });

  it("invalidates ledger-only keys for /ledger", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/ledger");
    expect(spy).toHaveBeenCalledTimes(1);
    const first = spy.mock.calls[0]?.[0] as { queryKey?: unknown[] } | undefined;
    expect(first?.queryKey).toEqual([...queryKeys.uiOperatorActions]);
    spy.mockRestore();
  });

  it("invalidates readiness probes for /readiness", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/readiness");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.probeLivez]);
    expect(keys).toContainEqual([...queryKeys.probeReadyz]);
    spy.mockRestore();
  });
});
