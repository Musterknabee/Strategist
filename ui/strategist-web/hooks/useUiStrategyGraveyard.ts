"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiStrategyGraveyardPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyGraveyardLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyGraveyardLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiStrategyGraveyardPayload>("/ui/strategy-graveyard/latest");
      return data;
    },
  });
}
