"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiEvidenceBundleIndexPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

const EVIDENCE_BUNDLES_PATH = "/ui/evidence-bundles";

export function useUiEvidenceBundles() {
  return useReadPlaneJsonQuery<UiEvidenceBundleIndexPayload>(queryKeys.uiEvidenceBundles, EVIDENCE_BUNDLES_PATH);
}
