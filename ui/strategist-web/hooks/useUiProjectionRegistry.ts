"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiProjectionRegistryPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiProjectionRegistryQuery = {
  searchRoot?: Nullable<string>;
  projectionFamily?: Nullable<string>;
  projectionLabel?: Nullable<string>;
  supportsCheckpoints?: Nullable<boolean>;
  outputLabelContains?: Nullable<string>;
  handlerContains?: Nullable<string>;
  limit?: Nullable<number>;
  includeArtifactEntries?: Nullable<boolean>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiProjectionRegistryQuery): string {
  if (!query) return "/ui/projection-registry";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "supports_checkpoints", query.supportsCheckpoints);
  append(params, "output_label_contains", query.outputLabelContains);
  append(params, "handler_contains", query.handlerContains);
  append(params, "limit", query.limit);
  append(params, "include_artifact_entries", query.includeArtifactEntries);
  if (query.projectionFamily) params.append("projection_family", query.projectionFamily);
  if (query.projectionLabel) params.append("projection_label", query.projectionLabel);
  const qs = params.toString();
  return qs ? `/ui/projection-registry?${qs}` : "/ui/projection-registry";
}

export function useUiProjectionRegistry(query?: UiProjectionRegistryQuery) {
  return useReadPlaneJsonQuery<UiProjectionRegistryPayload>(queryKeys.uiProjectionRegistryFiltered(query ?? {}), buildPath(query));
}
