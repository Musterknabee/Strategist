"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiFacadePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiFacade() {
  return useReadPlaneJsonQuery<UiFacadePayload>(queryKeys.uiFacade, "/ui/facade");
}
