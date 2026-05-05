"use client";

import { useQuery, type UseQueryOptions } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { readPlaneJsonQueryDefaults } from "@/lib/query/read-plane-query";

type QueryKey = readonly unknown[];

/**
 * Single entry point for GET JSON read-plane queries: stable keys, stale/retry policy, no throw.
 */
export function useReadPlaneJsonQuery<TData>(
  queryKey: QueryKey,
  path: string,
  options?: Omit<UseQueryOptions<TData, Error, TData, QueryKey>, "queryKey" | "queryFn">,
) {
  return useQuery({
    ...readPlaneJsonQueryDefaults<TData>(),
    ...options,
    queryKey,
    queryFn: async () => {
      const { data } = await strategistGetJson<TData>(path);
      return data;
    },
  });
}
