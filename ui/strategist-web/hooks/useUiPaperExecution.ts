"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";
import type { UiPaperExecutionCockpitPayload } from "@/lib/api/types";

export function useUiPaperExecutionCockpit() {
  return useQuery({
    queryKey: queryKeys.uiPaperExecutionLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiPaperExecutionCockpitPayload>("/ui/paper-execution/latest");
      return data;
    },
  });
}
