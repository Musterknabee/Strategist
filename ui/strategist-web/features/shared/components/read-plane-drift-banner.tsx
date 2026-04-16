"use client";

import { AlertTriangle } from "lucide-react";

export function ReadPlaneDriftBanner({
  drifted,
  message,
}: {
  drifted: boolean;
  message?: string;
}) {
  if (!drifted) return null;
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>
        <div className="font-medium">Read-plane drift detected</div>
        <div className="mt-1 text-amber-200/90">
          {message ?? "Projection freshness is outside the safe operating window. Destructive operator actions are temporarily frozen until the read-plane catches up."}
        </div>
      </div>
    </div>
  );
}
