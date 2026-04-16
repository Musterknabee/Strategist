"use client";

import { EvidenceExplorer } from "@/features/evidence/components/evidence-explorer";
import { useEvidence } from "@/features/evidence/hooks/use-evidence";
import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { ConsoleErrorState, ConsoleLoadingState } from "@/features/shared/components/console-state";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function EvidencePage() {
  const { data, isLoading, isError } = useEvidence();

  if (isLoading) {
    return <ConsoleLoadingState title="Loading evidence explorer" message="Hydrating artifact registry, verification posture, host fingerprint, and lineage summaries…" />;
  }

  if (isError || !data) {
    return <ConsoleErrorState title="Evidence explorer unavailable" message="Projection read failed. Check `/ui/evidence` or backend reachability." />;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc, 20 * 60_000);

  return (
    <DomainPolicyGate domain="evidence" title="Evidence explorer">
      <div className="space-y-4">
      <DeepLinkContextPills />
      <ProvenanceStrip
        provenance={{
          generatedAtUtc: data.generated_at_utc,
          sourceLabel: "evidence backbone projection",
          verificationLabel: `${data.verification.seal_status} / snapshot ${data.verification.projection_snapshot_verified ? "verified" : "unverified"}`,
          verificationTone: data.verification.projection_snapshot_verified ? "verified" : "restricted",
          projectionFamily: data.registry.projection_family,
          trustLabel: data.verification.trust_status,
        }}
      />
      <ReadPlaneDriftBanner drifted={drifted} message="Evidence projection freshness is outside the normal audit window. Hashes and checklist data should be treated as potentially lagged until the read-plane refreshes." />
      <ProjectionDriftNotifier active={drifted} dedupeKey="evidence-projection-drift" title="Evidence projection stale" message="Evidence hashes, checklist posture, or lineage summaries may be lagged. Refresh projections before relying on audit decisions." />
      <div className="flex flex-wrap justify-end gap-2">
        <ReviewPacketActions packetKind="evidence-explorer" pagePayload={data} provenance={{ verification: data.verification, searchRoot: data.search_root }} notes={data.operator_lines} />
        <ExportSnapshotActions payload={data} fileStem="strategist-evidence-snapshot" />
      </div>
      <EvidenceExplorer data={data} />
      </div>
    </DomainPolicyGate>
  );
}
