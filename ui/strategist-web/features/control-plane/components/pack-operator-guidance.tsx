"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { UiOperatorCommandReceipt, UiPackDetail, WorkbenchItem } from "@/lib/contracts/ui";

export function PackOperatorGuidance({
  pack,
  detail,
  receipt,
}: {
  pack?: WorkbenchItem | null;
  detail?: UiPackDetail;
  receipt?: UiOperatorCommandReceipt | null;
}) {
  const guidance = [
    {
      title: "Claim / lease posture",
      body: receipt?.requires_projection_refresh
        ? "A governed command receipt is present. Refresh the pack projection before assuming lease state has changed."
        : "No recent receipt is attached. Use claim or renew only after confirming lease and lifecycle projections are current.",
    },
    {
      title: "Escalation routing",
      body: detail?.escalation?.item_count
        ? `Escalation projections show ${detail.escalation.item_count} routed item(s). Review escalation before accepting terminal action.`
        : "No escalation rows are projected. Treat this as a normal workboard handling path unless runtime posture changes.",
    },
    {
      title: "Evidence sufficiency",
      body: (pack?.output_artifact_paths?.length ?? 0) > 0
        ? `Pack evidence currently exposes ${pack?.output_artifact_paths?.length ?? 0} artifact(s). Check artifact lineage before handoff or closure.`
        : "No evidence artifacts are projected for this pack yet. Keep the pack in review mode until evidence is materialized.",
    },
  ];

  return (
    <div className="grid gap-4 xl:grid-cols-3">
      {guidance.map((item) => (
        <Card key={item.title} className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm text-zinc-200">{item.title}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm leading-6 text-zinc-400">{item.body}</CardContent>
        </Card>
      ))}
    </div>
  );
}
