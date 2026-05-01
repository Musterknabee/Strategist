import type { QueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/lib/query/keys";

const OPERATOR_BOARD = "operator";
const RUNTIME_ROLE = "operator";

function normalizePath(pathname: string): string {
  const t = pathname.trim();
  if (!t || t === "/") return "/";
  return t.replace(/\/+$/, "") || "/";
}

/**
 * Invalidate TanStack Query caches for hooks used by the given App Router path.
 * Unknown paths fall back to full strategist invalidation.
 */
export function invalidateQueriesForRoute(client: QueryClient, pathname: string): void {
  const p = normalizePath(pathname);
  const inv = (key: readonly unknown[]) => {
    void client.invalidateQueries({ queryKey: [...key] });
  };

  switch (p) {
    case "/":
      inv(queryKeys.uiFacade);
      inv(queryKeys.probeApiRoot);
      inv(queryKeys.probeHealthz);
      inv(queryKeys.probeReadyz);
      inv(queryKeys.uiHealth);
      inv(queryKeys.uiWorkboard(OPERATOR_BOARD));
      inv(queryKeys.uiProviderHealth);
      inv(queryKeys.uiEvidence(undefined));
      inv(queryKeys.uiOperatorActions);
      break;
    case "/workboard":
      inv(queryKeys.uiFacade);
      inv(queryKeys.uiWorkboard(OPERATOR_BOARD));
      break;
    case "/readiness":
      inv(queryKeys.probeHealthz);
      inv(queryKeys.probeLivez);
      inv(queryKeys.probeReadyz);
      inv(queryKeys.uiHealth);
      break;
    case "/evidence":
      inv(queryKeys.uiEvidence(undefined));
      break;
    case "/ledger":
      inv(queryKeys.uiOperatorActions);
      break;
    case "/providers":
      inv(queryKeys.uiProviderHealth);
      break;
    case "/runtime":
      inv(queryKeys.uiRuntime(RUNTIME_ROLE));
      inv(queryKeys.uiFacade);
      inv(queryKeys.uiResearchCompute);
      inv(queryKeys.probeApiRoot);
      break;
    case "/strategy-lab":
      inv(queryKeys.uiStrategyBatchesLatest);
      inv(queryKeys.uiStrategyBatchesList);
      break;
    case "/paper-tracking":
      inv(queryKeys.uiPaperTrackingLatest);
      break;
    default:
      void client.invalidateQueries({
        predicate: (q) => Array.isArray(q.queryKey) && q.queryKey[0] === "strategist",
      });
  }
}
