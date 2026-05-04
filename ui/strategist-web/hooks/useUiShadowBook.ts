"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiShadowBookLatest() {
  return useQuery({
    queryKey: queryKeys.uiShadowBookLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/shadow-book/latest");
      return data;
    },
  });
}
