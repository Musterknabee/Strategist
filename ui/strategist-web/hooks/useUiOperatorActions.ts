"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiOperatorActions() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiOperatorActions,
    "/ui/operator-actions?readonly=true",
  );
}
