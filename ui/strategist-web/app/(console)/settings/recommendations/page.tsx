import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsRecommendations } from "@/lib/server/diagnostics-recommendations";

export default async function DiagnosticsRecommendationsPage() {
  const payload = await buildFrontendDiagnosticsRecommendations();

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Recommendations</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{payload.recommendations.length}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Latest posture</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{payload.latest?.posture ?? "no-history"}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Warning pressure</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{payload.compare.warningPressure}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Latest mode</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{payload.summary.latestMode ?? "unknown"}</CardContent></Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base text-zinc-100">Recommended next moves</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          {payload.recommendations.map((rec) => (
            <div key={rec.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-100">{rec.title}</div>
                  <div className="mt-1 text-sm text-zinc-400">{rec.rationale}</div>
                </div>
                <Badge className={rec.priority === "high" ? "border-red-500/30 bg-red-500/10 text-red-300" : rec.priority === "medium" ? "border-amber-500/30 bg-amber-500/10 text-amber-300" : "border-zinc-700 bg-zinc-900 text-zinc-300"}>{rec.priority}</Badge>
              </div>
              {rec.command ? <div className="mt-4"><CopyCommandBlock label="Suggested command" command={rec.command} /></div> : null}
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        <Link href="/api/ui/diagnostics/recommendations" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open recommendations JSON</Link>
        <Link href="/settings/status-board" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open status board</Link>
        <Link href="/settings/runbook" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open runbook</Link>
      </div>
    </div>
  );
}
