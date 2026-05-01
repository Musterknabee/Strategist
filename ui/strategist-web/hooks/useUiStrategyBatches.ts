"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyBatchLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyBatchesLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/strategy-batches/latest");
      return data;
    },
  });
}

export function useUiStrategyBatchList() {
  return useQuery({
    queryKey: queryKeys.uiStrategyBatchesList,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/strategy-batches");
      return data;
    },
  });
}
