"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiDailyOperatorRunPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiDailyOperatorRunLatest() {
  return useReadPlaneJsonQuery<UiDailyOperatorRunPayload>(
    queryKeys.uiDailyOperatorRunLatest,
    "/ui/daily-operator-run/latest",
  );
}
