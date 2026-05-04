"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiBacktestForensicsPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiBacktestForensicsLatest() {
  return useQuery({
    queryKey: queryKeys.uiBacktestForensicsLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiBacktestForensicsPayload>("/ui/backtest-forensics/latest");
      return data;
    },
  });
}
