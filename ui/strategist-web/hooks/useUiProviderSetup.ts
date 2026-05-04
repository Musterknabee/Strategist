"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiProviderSetupConsolePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiProviderSetup() {
  return useQuery({
    queryKey: queryKeys.uiProviderSetup,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiProviderSetupConsolePayload>("/ui/provider-setup");
      return data;
    },
  });
}
