"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyThesisLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyThesisLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/strategy-thesis/latest");
      return data;
    },
  });
}


export function useUiStrategyThesisGenerationLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyThesisGenerationLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/strategy-thesis/generation/latest");
      return data;
    },
  });
}
