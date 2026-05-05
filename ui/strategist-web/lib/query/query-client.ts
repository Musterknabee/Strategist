import { QueryClient } from "@tanstack/react-query";
import { READ_PLANE_GC_MS, READ_PLANE_STALE_MS, readPlaneRetry } from "@/lib/query/read-plane-query";

export function createStrategistQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: READ_PLANE_STALE_MS,
        gcTime: READ_PLANE_GC_MS,
        retry: readPlaneRetry,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        throwOnError: false,
      },
    },
  });
}
