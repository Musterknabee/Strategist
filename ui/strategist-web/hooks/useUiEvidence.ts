"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiEvidence(searchRoot?: string) {
  const q = searchRoot ? `?search_root=${encodeURIComponent(searchRoot)}` : "";
  return useQuery({
    queryKey: queryKeys.uiEvidence(searchRoot),
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>(`/ui/evidence${q}`);
      return data;
    },
  });
}
