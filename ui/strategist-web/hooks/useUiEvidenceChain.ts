"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiEvidenceChainPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

const EVIDENCE_CHAIN_PATH = "/ui/evidence-chain?readonly=true&limit=250";

export function useUiEvidenceChain() {
  return useReadPlaneJsonQuery<UiEvidenceChainPayload>(queryKeys.uiEvidenceChain, EVIDENCE_CHAIN_PATH);
}
