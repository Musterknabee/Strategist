"use client";

import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { BurnInMetrics } from "@/features/validator/components/burn-in-metrics";
import { useBurnIn } from "@/features/validator/hooks/use-burn-in";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { ConsoleErrorState, ConsoleLoadingState } from "@/features/shared/components/console-state";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function BurnInPage() {
  const { data, isLoading, isError } = useBurnIn();

  if (isLoading) {
    return <ConsoleLoadingState title="Loading validator burn-in" message="Hydrating burn-in artifacts, calibration curves, realism posture, and provider paths…" />;
  }

  if (isError || !data) {
    return <ConsoleErrorState title="Burn-in dashboard unavailable" message="Projection read failed. Check `/ui/burnin` or backend reachability." />;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc, 30 * 60_000);
  const staleArtifacts = data.artifact_summary.total_stale_count > 0;

  return (
    <DomainPolicyGate domain="validator" title="Validator burn-in">
      <div className="space-y-4">
      <DeepLinkContextPills />
      <ProvenanceStrip
        provenance={{
          generatedAtUtc: data.generated_at_utc,
          sourceLabel: "validator burn-in projection",
          verificationLabel: staleArtifacts ? "stale artifacts present" : "burn-in artifacts hydrated",
          verificationTone: staleArtifacts ? "restricted" : "verified",
          projectionFamily: "validator",
          trustLabel: `${data.artifact_summary.artifact_count} artifacts`,
        }}
      />
      <ReadPlaneDriftBanner drifted={drifted} message="Burn-in projections are outside the freshness window. Review metrics as forensic diagnostics only until the validator read-plane refreshes." />
      <ProjectionDriftNotifier active={drifted} dedupeKey="validator-burnin-projection-drift" title="Validator projection stale" message="Burn-in metrics are outside the freshness window. Keep this route in forensic-only mode until validator projections refresh." />
      <div className="flex flex-wrap justify-end gap-2">
        <ReviewPacketActions packetKind="validator-burnin" pagePayload={data} provenance={{ artifactSummary: data.artifact_summary, forensicSummary: data.metrics.forensicSummary }} notes={data.metrics.forensicSummary.forensic_notes} />
        <ExportSnapshotActions payload={data} fileStem="strategist-validator-burnin-snapshot" />
      </div>
      <BurnInMetrics data={data} />
      </div>
    </DomainPolicyGate>
  );
}
