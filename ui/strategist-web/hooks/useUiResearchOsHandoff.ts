"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsHandoffLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsHandoffLatest,
    queryFn: () => strategistGetJson("/ui/research-os/handoff/latest"),
  });
}
