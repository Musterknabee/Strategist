"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffArchivePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffArchiveQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  archiveStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  archiveManifestVerified?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffArchiveQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/archive";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "archive_manifest_verified", query.archiveManifestVerified);
  append(params, "limit", query.limit);
  if (query.archiveStatus) params.append("archive_status", query.archiveStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/archive?${qs}` : "/ui/semantic-validator-handoff/archive";
}

export function useUiSemanticValidatorHandoffArchive(query?: UiSemanticValidatorHandoffArchiveQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffArchivePayload>(
    queryKeys.uiSemanticValidatorHandoffArchiveFiltered(query ?? {}),
    buildPath(query),
  );
}
