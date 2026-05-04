"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsRunLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsRunLatest,
    queryFn: () => strategistGetJson("/ui/research-os/run/latest"),
  });
}
