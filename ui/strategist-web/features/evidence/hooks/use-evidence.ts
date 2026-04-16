"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiEvidenceDashboard } from "@/lib/contracts/ui";

export function useEvidence() {
  return useQuery<UiEvidenceDashboard>({
    queryKey: ["ui", "evidence"],
    queryFn: async () => {
      const response = await fetch("/api/ui/evidence", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load evidence explorer payload.");
      }
      return response.json();
    },
    refetchInterval: 30_000,
  });
}
