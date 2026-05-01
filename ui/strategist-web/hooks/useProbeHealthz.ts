"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useProbeHealthz() {
  return useQuery({
    queryKey: queryKeys.probeHealthz,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/healthz");
      return data;
    },
  });
}
