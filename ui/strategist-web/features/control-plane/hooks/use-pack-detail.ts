"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiPackDetail } from "@/lib/contracts/ui";

export function usePackDetail(packKind?: string, manifestPath?: string) {
  return useQuery<UiPackDetail>({
    queryKey: ["ui", "pack-detail", packKind, manifestPath],
    enabled: Boolean(packKind || manifestPath),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (packKind) params.set("pack_kind", packKind);
      if (manifestPath) params.set("manifest_path", manifestPath);
      const response = await fetch(`/api/ui/packs/detail?${params.toString()}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load pack detail payload.");
      }
      return response.json();
    },
    refetchInterval: 15_000,
  });
}
