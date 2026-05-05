"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiPaperExecutionCockpitPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiPaperExecutionCockpit() {
  return useReadPlaneJsonQuery<UiPaperExecutionCockpitPayload>(
    queryKeys.uiPaperExecutionLatest,
    "/ui/paper-execution/latest",
  );
}
