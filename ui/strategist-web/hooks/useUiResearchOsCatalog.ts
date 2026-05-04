"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsCatalogLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsCatalogLatest,
    queryFn: () => strategistGetJson("/ui/research-os/catalog/latest"),
  });
}
