"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiTribunalWorkspacePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiTribunal() {
  return useReadPlaneJsonQuery<UiTribunalWorkspacePayload>(queryKeys.uiTribunal, "/ui/tribunal");
}
