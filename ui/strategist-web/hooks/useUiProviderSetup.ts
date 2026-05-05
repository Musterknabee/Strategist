"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiProviderSetupConsolePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiProviderSetup() {
  return useReadPlaneJsonQuery<UiProviderSetupConsolePayload>(queryKeys.uiProviderSetup, "/ui/provider-setup");
}
