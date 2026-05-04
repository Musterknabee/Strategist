"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiOperatorActions() {
  return useQuery({
    queryKey: queryKeys.uiOperatorActions,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/operator-actions?readonly=true");
      return data;
    },
  });
}
