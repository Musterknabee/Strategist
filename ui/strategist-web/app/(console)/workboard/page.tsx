"use client";

import { OperatorWorkboard } from "@/features/control-plane/components/operator-workboard";
import { useWorkboard } from "@/features/control-plane/hooks/use-workboard";
import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { ConsoleErrorState, ConsoleLoadingState } from "@/features/shared/components/console-state";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function WorkboardPage() {
  const { data, isLoading, isError } = useWorkboard();

  if (isLoading) {
    return <ConsoleLoadingState title="Loading workboard" message="Hydrating control-plane queue, workbench, and transition projections…" />;
  }

  if (isError || !data) {
    return <ConsoleErrorState title="Workboard unavailable" message="Projection read failed. Check `/ui/workboard` or backend reachability." />;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc);

  return (
    <DomainPolicyGate domain="control-plane" title="Workboard">
      <div className="space-y-4">
      <DeepLinkContextPills />
      <ProvenanceStrip
        provenance={{
          generatedAtUtc: data.generated_at_utc,
          sourceLabel: "operator workboard projection",
          verificationLabel: "command-gated read plane",
          verificationTone: drifted ? "restricted" : "verified",
          projectionFamily: "control-plane",
          trustLabel: drifted ? "stale projection" : "live projection",
        }}
      />
      <ReadPlaneDriftBanner drifted={drifted} />
      <ProjectionDriftNotifier active={drifted} dedupeKey="workboard-projection-drift" title="Stale projection warning" message="This surface is operating on a stale read-plane snapshot. Governed actions should stay frozen until projections refresh." />
      <div className="flex flex-wrap justify-end gap-2">
        <ReviewPacketActions packetKind="workboard" pagePayload={data} provenance={{ stats: data.stats, boardLabel: data.board_label }} notes={["Control-plane snapshot is projection-backed and command-gated."]} />
        <ExportSnapshotActions payload={data} fileStem="strategist-workboard-snapshot" />
      </div>
      <OperatorWorkboard data={data} actionsFrozen={drifted} />
      </div>
    </DomainPolicyGate>
  );
}
