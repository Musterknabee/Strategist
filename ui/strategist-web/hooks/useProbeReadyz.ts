"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistProbeGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useProbeReadyz() {
  return useQuery({
    queryKey: queryKeys.probeReadyz,
    queryFn: async () => {
      const { data, status } = await strategistProbeGetJson<Record<string, unknown>>("/readyz");
      return { data, httpStatus: status };
    },
  });
}
