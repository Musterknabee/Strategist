"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsHandoffSignoffLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsHandoffSignoffLatest,
    queryFn: () => strategistGetJson("/ui/research-os/handoff-signoff/latest"),
  });
}
