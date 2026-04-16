"use client";

import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { TribunalWorkspace } from "@/features/tribunal/components/tribunal-workspace";
import { useTribunal } from "@/features/tribunal/hooks/use-tribunal";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { ConsoleErrorState, ConsoleLoadingState } from "@/features/shared/components/console-state";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function TribunalPage() {
  const { data, isLoading, isError } = useTribunal();

  if (isLoading) {
    return <ConsoleLoadingState title="Loading Tribunal workspace" message="Hydrating blindness-safe qualitative workflow, doctrine memory, and thesis graph projections…" />;
  }

  if (isError || !data) {
    return <ConsoleErrorState title="Tribunal workspace unavailable" message="Projection read failed. Check `/ui/tribunal` or backend reachability." />;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc, 15 * 60_000);

  return (
    <DomainPolicyGate domain="tribunal" title="Tribunal workspace">
      <div className="space-y-4">
      <DeepLinkContextPills />
      <ProvenanceStrip
        provenance={{
          generatedAtUtc: data.generated_at_utc,
          sourceLabel: "tribunal qualitative projection",
          verificationLabel: data.blindness.operator_message,
          verificationTone: data.blindness.quantitative_payloads_present ? "warning" : "verified",
          projectionFamily: "tribunal",
          trustLabel: data.blindness.mode,
        }}
      />
      <ReadPlaneDriftBanner drifted={drifted} message="Tribunal projections are stale. Keep the workspace in review mode and wait for a fresh qualitative snapshot before making governance judgments." />
      <ProjectionDriftNotifier active={drifted} dedupeKey="tribunal-projection-drift" title="Tribunal projection stale" message="Qualitative doctrine and thesis projections are stale. Hold governance judgments until a fresh blindness-safe snapshot arrives." />
      <div className="flex flex-wrap justify-end gap-2">
        <ReviewPacketActions packetKind="tribunal-workspace" pagePayload={data} provenance={{ blindness: data.blindness, doctrine: data.doctrine_stats }} notes={data.operator_lines} />
        <ExportSnapshotActions payload={data} fileStem="strategist-tribunal-workspace-snapshot" />
      </div>
      <TribunalWorkspace data={data} />
      </div>
    </DomainPolicyGate>
  );
}
