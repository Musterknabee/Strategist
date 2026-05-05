import type { UseQueryOptions } from "@tanstack/react-query";
import { StrategistApiError } from "@/lib/api/strategist-errors";

/** Default staleness for JSON read-plane routes (cockpit + operator pages). */
export const READ_PLANE_STALE_MS = 15_000;
export const READ_PLANE_GC_MS = 5 * 60_000;

/** Liveness probes and readiness JSON may need a fresher view than bulk UI payloads. */
export const READ_PLANE_PROBE_STALE_MS = 5_000;

/**
 * Read-plane retry: transient network / 5xx only — no hammering on 4xx or auth failures.
 * Matches global QueryClient defaults; kept here for tests and per-hook overrides.
 */
export function readPlaneRetry(failureCount: number, error: unknown): boolean {
  if (failureCount >= 2) return false;
  if (error instanceof StrategistApiError) {
    if (error.kind === "unauthorized") return false;
    const s = error.httpStatus;
    if (typeof s === "number" && s >= 400 && s < 500) return false;
  }
  return true;
}

type ReadPlanePartial<T> = Pick<
  UseQueryOptions<T, Error, T, readonly unknown[]>,
  "staleTime" | "gcTime" | "retry" | "refetchOnWindowFocus" | "throwOnError"
>;

export function readPlaneJsonQueryDefaults<T>(): ReadPlanePartial<T> {
  return {
    staleTime: READ_PLANE_STALE_MS,
    gcTime: READ_PLANE_GC_MS,
    retry: readPlaneRetry,
    refetchOnWindowFocus: false,
    throwOnError: false,
  };
}

export function readPlaneProbeQueryDefaults<T>(): ReadPlanePartial<T> {
  return {
    ...readPlaneJsonQueryDefaults<T>(),
    staleTime: READ_PLANE_PROBE_STALE_MS,
  };
}
