"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiWorkboardDashboard } from "@/lib/contracts/ui";

export function useWorkboard() {
  return useQuery<UiWorkboardDashboard>({
    queryKey: ["ui", "workboard"],
    queryFn: async () => {
      const response = await fetch("/api/ui/workboard", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load workboard payload.");
      }
      return response.json();
    },
    refetchInterval: 10_000,
  });
}
