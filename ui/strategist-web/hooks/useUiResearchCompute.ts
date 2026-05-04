"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchCompute() {
  return useQuery({
    queryKey: queryKeys.uiResearchCompute,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/research-compute");
      return data;
    },
  });
}
