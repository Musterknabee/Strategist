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

  it("invalidates paper tracking keys for /paper-tracking", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/paper-tracking");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiPaperTrackingLatest]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff lineage keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-lineage");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffLineage]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff remediation keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-remediation");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffRemediation]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff review keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-review");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffReview]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff signoff keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-signoff");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffSignoff]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff custody keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-custody");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffCustody]);
    spy.mockRestore();
  });

  it("invalidates semantic validator handoff archive keys", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/semantic-validator-handoff-archive");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiSemanticValidatorHandoffArchive]);
    spy.mockRestore();
  });

  it("invalidates strategy batch keys for /strategy-lab", () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    invalidateQueriesForRoute(client, "/strategy-lab");
    const keys = spy.mock.calls.map((c) => c[0]?.queryKey);
    expect(keys).toContainEqual([...queryKeys.uiStrategyBatchesLatest]);
    expect(keys).toContainEqual([...queryKeys.uiStrategyBatchesList]);
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
