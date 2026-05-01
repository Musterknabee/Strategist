"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

/** GET / on the API host (operator banner JSON), not the Next.js app root. */
export function useProbeApiRoot() {
  return useQuery({
    queryKey: queryKeys.probeApiRoot,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/");
      return data;
    },
    retry: false,
  });
}
