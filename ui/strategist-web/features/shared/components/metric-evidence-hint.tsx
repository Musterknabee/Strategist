"use client";

import { Info } from "lucide-react";

import { MetricProvenance } from "@/lib/contracts/ui";

export function MetricEvidenceHint({
  label,
  provenance,
}: {
  label: string;
  provenance?: MetricProvenance | null;
}) {
  if (!provenance) {
    return null;
  }

  return (
    <div className="group relative inline-flex">
      <button
        type="button"
        className="inline-flex items-center gap-1 rounded-full border border-zinc-700 bg-zinc-900 px-2 py-1 text-[11px] text-zinc-300 hover:border-emerald-500/40 hover:text-emerald-200"
      >
        <Info className="h-3.5 w-3.5" />
        {label}
      </button>
      <div className="pointer-events-none absolute left-0 top-full z-30 mt-2 hidden min-w-[260px] rounded-2xl border border-zinc-800 bg-zinc-950/95 p-3 text-xs text-zinc-300 shadow-2xl group-hover:block">
        <div className="font-medium text-zinc-100">{provenance.source_label}</div>
        <div className="mt-1 text-zinc-400">{provenance.verification_label}</div>
        <div className="mt-2 grid gap-1">
          <div>family: {provenance.projection_family}</div>
          <div>artifacts: {provenance.artifact_count}</div>
        </div>
        {provenance.artifact_paths.length ? (
          <div className="mt-2 space-y-1 border-t border-zinc-800 pt-2">
            {provenance.artifact_paths.slice(0, 3).map((path) => (
              <div key={path} className="truncate text-zinc-400">{path}</div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
