import { queryKeys } from "@/lib/query/keys";
import { useReadPlaneJsonQuery } from "@/lib/query/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffClearanceReleaseRetentionBoardPayload } from "@/lib/api/types";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffClearanceReleaseRetentionBoardQuery = {
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  evidenceLane?: Nullable<string>;
  releaseRetentionStatus?: Nullable<string>;
  releaseRetentionReadiness?: Nullable<string>;
  releaseArchiveStatus?: Nullable<string>;
  releaseArchiveReadiness?: Nullable<string>;
  releaseCompletionStatus?: Nullable<string>;
  releaseCompletionReadiness?: Nullable<string>;
  releaseAcknowledgmentStatus?: Nullable<string>;
  releaseAcknowledgmentReadiness?: Nullable<string>;
  releaseReceiptStatus?: Nullable<string>;
  releaseReceiptReadiness?: Nullable<string>;
  releaseCustodyStatus?: Nullable<string>;
  releaseCustodyReadiness?: Nullable<string>;
  releaseHandoffStatus?: Nullable<string>;
  releaseHandoffReadiness?: Nullable<string>;
  releasePacketStatus?: Nullable<string>;
  releasePacketReadiness?: Nullable<string>;
  releaseStatus?: Nullable<string>;
  releaseReadiness?: Nullable<string>;
  acceptanceStatus?: Nullable<string>;
  acceptanceReadiness?: Nullable<string>;
  priority?: Nullable<string>;
  severity?: Nullable<string>;
  trustBanner?: Nullable<string>;
  ownerHint?: Nullable<string>;
  readyForHumanRetentionObservation?: Nullable<boolean>;
  blocked?: Nullable<boolean>;
  waiting?: Nullable<boolean>;
  requiresAcceptanceObservation?: Nullable<boolean>;
  requiresExternalArtifact?: Nullable<boolean>;
  requiresReleaseArchiveReview?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(p: URLSearchParams, k: string, v: Nullable<string | number | boolean>) {
  if (v !== null && v !== undefined && v !== "") p.append(k, String(v));
}

function path(q?: UiSemanticValidatorHandoffClearanceReleaseRetentionBoardQuery) {
  const p = new URLSearchParams();
  if (q) {
    append(p, "experiment_id_contains", q.experimentIdContains);
    append(p, "issue_contains", q.issueContains);
    append(p, "ready_for_human_retention_observation", q.readyForHumanRetentionObservation);
    append(p, "blocked", q.blocked);
    append(p, "waiting", q.waiting);
    append(p, "requires_acceptance_observation", q.requiresAcceptanceObservation);
    append(p, "requires_external_artifact", q.requiresExternalArtifact);
    append(p, "requires_release_archive_review", q.requiresReleaseArchiveReview);
    append(p, "limit", q.limit);
    if (q.evidenceLane) p.append("evidence_lane", q.evidenceLane);
    if (q.releaseRetentionStatus) p.append("release_retention_status", q.releaseRetentionStatus);
    if (q.releaseRetentionReadiness) p.append("release_retention_readiness", q.releaseRetentionReadiness);
    if (q.releaseArchiveStatus) p.append("release_archive_status", q.releaseArchiveStatus);
    if (q.releaseArchiveReadiness) p.append("release_archive_readiness", q.releaseArchiveReadiness);
    if (q.releaseCompletionStatus) p.append("release_completion_status", q.releaseCompletionStatus);
    if (q.releaseCompletionReadiness) p.append("release_completion_readiness", q.releaseCompletionReadiness);
    if (q.releaseAcknowledgmentStatus) p.append("release_acknowledgment_status", q.releaseAcknowledgmentStatus);
    if (q.releaseAcknowledgmentReadiness) p.append("release_acknowledgment_readiness", q.releaseAcknowledgmentReadiness);
    if (q.releaseReceiptStatus) p.append("release_receipt_status", q.releaseReceiptStatus);
    if (q.releaseReceiptReadiness) p.append("release_receipt_readiness", q.releaseReceiptReadiness);
    if (q.releaseCustodyStatus) p.append("release_custody_status", q.releaseCustodyStatus);
    if (q.releaseCustodyReadiness) p.append("release_custody_readiness", q.releaseCustodyReadiness);
    if (q.releaseHandoffStatus) p.append("release_handoff_status", q.releaseHandoffStatus);
    if (q.releaseHandoffReadiness) p.append("release_handoff_readiness", q.releaseHandoffReadiness);
    if (q.releasePacketStatus) p.append("release_packet_status", q.releasePacketStatus);
    if (q.releasePacketReadiness) p.append("release_packet_readiness", q.releasePacketReadiness);
    if (q.releaseStatus) p.append("release_status", q.releaseStatus);
    if (q.releaseReadiness) p.append("release_readiness", q.releaseReadiness);
    if (q.acceptanceStatus) p.append("acceptance_status", q.acceptanceStatus);
    if (q.acceptanceReadiness) p.append("acceptance_readiness", q.acceptanceReadiness);
    if (q.priority) p.append("priority", q.priority);
    if (q.severity) p.append("severity", q.severity);
    if (q.trustBanner) p.append("trust_banner", q.trustBanner);
    if (q.ownerHint) p.append("owner_hint", q.ownerHint);
  }
  const qs = p.toString();
  return qs
    ? `/ui/semantic-validator-handoff/clearance-release-retention-board?${qs}`
    : "/ui/semantic-validator-handoff/clearance-release-retention-board";
}

export function useUiSemanticValidatorHandoffClearanceReleaseRetentionBoard(
  query?: UiSemanticValidatorHandoffClearanceReleaseRetentionBoardQuery,
) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffClearanceReleaseRetentionBoardPayload>(
    queryKeys.uiSemanticValidatorHandoffClearanceReleaseRetentionBoardFiltered(query ?? {}),
    path(query),
  );
}
