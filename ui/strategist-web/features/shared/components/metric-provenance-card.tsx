"use client";

import { useState } from "react";
import { Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { MetricProvenance } from "@/lib/contracts/ui";

export function MetricProvenanceCard({
  title,
  provenance,
}: {
  title: string;
  provenance?: MetricProvenance;
}) {
  const [open, setOpen] = useState(false);

  if (!provenance) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <Info className="h-3.5 w-3.5" />
          <span>{title} provenance</span>
        </div>
        <Button
          type="button"
          variant="outline"
          className="h-8 rounded-full border-zinc-700 bg-transparent px-3 text-xs"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? "Hide context" : "Show context"}
        </Button>
      </div>
      {open ? (
        <Card className="border-zinc-800 bg-zinc-950/70">
          <CardContent className="space-y-3 p-4 text-sm text-zinc-300">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                {provenance.source_label}
              </Badge>
              <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                {provenance.projection_family}
              </Badge>
              <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                {provenance.artifact_count} artifacts
              </Badge>
            </div>
            <div>{provenance.verification_label}</div>
            {provenance.artifact_paths.length ? (
              <div>
                <div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Artifact paths</div>
                <div className="space-y-1 text-xs text-zinc-400">
                  {provenance.artifact_paths.map((path) => (
                    <div key={path}>{path}</div>
                  ))}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
