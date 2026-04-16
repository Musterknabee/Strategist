"use client";

import { Badge } from "@/components/ui/badge";
import { SurfaceProvenance, formatAge, getFreshnessTone } from "@/lib/read-plane";

function toneClass(tone: "fresh" | "aging" | "stale") {
  if (tone === "fresh") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  if (tone === "aging") return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  return "border-rose-500/30 bg-rose-500/10 text-rose-300";
}

function verificationClass(tone: SurfaceProvenance["verificationTone"]) {
  if (tone === "verified") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  if (tone === "restricted") return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  return "border-zinc-700 text-zinc-300";
}

export function ProvenanceStrip({ provenance }: { provenance: SurfaceProvenance }) {
  const freshness = getFreshnessTone(provenance.generatedAtUtc);
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/80 px-4 py-3 text-xs text-zinc-300">
      <Badge variant="outline" className="border-zinc-700 text-zinc-300">
        source: {provenance.sourceLabel}
      </Badge>
      <Badge className={toneClass(freshness)}>
        freshness: {freshness}
      </Badge>
      <Badge variant="outline" className="border-zinc-700 text-zinc-300">
        updated {formatAge(provenance.generatedAtUtc)}
      </Badge>
      <Badge className={verificationClass(provenance.verificationTone)}>
        {provenance.verificationLabel}
      </Badge>
      {provenance.trustLabel ? (
        <Badge variant="outline" className="border-zinc-700 text-zinc-300">
          trust: {provenance.trustLabel}
        </Badge>
      ) : null}
      {provenance.projectionFamily ? (
        <Badge variant="outline" className="border-zinc-700 text-zinc-300">
          family: {provenance.projectionFamily}
        </Badge>
      ) : null}
    </div>
  );
}
