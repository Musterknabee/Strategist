"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiOperatorPackWorkbenchPayload, UiPackDetailPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

const PACK_WORKBENCH_PATH = "/ui/packs/workbench";
const PACK_DETAIL_PATH = "/ui/packs/detail";

function packDetailPath(params: { manifestPath?: string | null; packKind?: string | null }): string {
  const q = new URLSearchParams();
  if (params.manifestPath) q.set("manifest_path", params.manifestPath);
  else if (params.packKind) q.set("pack_kind", params.packKind);
  const suffix = q.toString();
  return suffix ? `${PACK_DETAIL_PATH}?${suffix}` : PACK_DETAIL_PATH;
}

export function useUiOperatorPackWorkbench() {
  return useReadPlaneJsonQuery<UiOperatorPackWorkbenchPayload>(queryKeys.uiOperatorPackWorkbench, PACK_WORKBENCH_PATH);
}

export function useUiPackDetail(params: { manifestPath?: string | null; packKind?: string | null }) {
  const enabled = Boolean(params.manifestPath || params.packKind);
  const path = packDetailPath(params);
  return useReadPlaneJsonQuery<UiPackDetailPayload>(
    queryKeys.uiPackDetail(params.manifestPath ?? params.packKind ?? "none"),
    path,
    { enabled },
  );
}
