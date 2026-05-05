"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiRuntime(role = "operator") {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiRuntime(role),
    `/ui/runtime?role=${encodeURIComponent(role)}`,
  );
}
