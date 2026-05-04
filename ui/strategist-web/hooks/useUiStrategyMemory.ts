"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyMemoryLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyMemoryLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/strategy-memory/latest");
      return data;
    },
  });
}
