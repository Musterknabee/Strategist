"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiDailyOperatorRunPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiDailyOperatorRunLatest() {
  return useQuery({
    queryKey: queryKeys.uiDailyOperatorRunLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiDailyOperatorRunPayload>("/ui/daily-operator-run/latest");
      return data;
    },
  });
}
