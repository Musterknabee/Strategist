"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { MetricProvenance } from "@/lib/contracts/ui";

export function SectionProvenanceCard({
  title,
  provenance,
}: {
  title: string;
  provenance?: MetricProvenance;
}) {
  if (!provenance) {
    return null;
  }

  return (
    <Card className="border-zinc-800 bg-zinc-900/70">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-zinc-300">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-zinc-300">
        <div className="flex flex-wrap gap-2">
          <Badge variant="outline" className="border-zinc-700 text-zinc-300">
            {provenance.projection_family}
          </Badge>
          <Badge variant="outline" className="border-zinc-700 text-zinc-300">
            {provenance.artifact_count} artifacts
          </Badge>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-zinc-500">Source</div>
          <div className="mt-1 text-zinc-100">{provenance.source_label}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-zinc-500">Verification</div>
          <div className="mt-1 text-zinc-100">{provenance.verification_label}</div>
        </div>
        {provenance.artifact_paths.length > 0 ? (
          <div>
            <div className="text-xs uppercase tracking-wide text-zinc-500">Artifact paths</div>
            <div className="mt-2 space-y-1 text-xs text-zinc-400">
              {provenance.artifact_paths.slice(0, 3).map((artifactPath) => (
                <div key={artifactPath} className="break-all">
                  {artifactPath}
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
