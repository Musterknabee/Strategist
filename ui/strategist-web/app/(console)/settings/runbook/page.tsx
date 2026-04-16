import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsRunbook } from "@/lib/server/diagnostics-runbook";

export default async function DiagnosticsRunbookPage() {
  const payload = await buildFrontendDiagnosticsRunbook();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / runbook</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics runbook</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Copy/paste-ready workflow sequences for first-run bring-up, verification before build, and diagnostics maintenance.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/runbook" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open runbook JSON</Link>
          <Link href="/settings/quick-actions" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open quick actions</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Total runs" value={String(payload.summary.totalRuns)} />
        <MetricCard title="Backend-connected" value={String(payload.summary.backendConnectedRuns)} />
        <MetricCard title="Latest posture" value={payload.summary.latestPosture ?? "no-history"} />
        <MetricCard title="Latest mode" value={payload.summary.latestMode ?? "unknown"} />
      </div>

      <div className="grid gap-6">
        {payload.workflows.map((workflow) => (
          <Card key={workflow.id} className="border-zinc-800 bg-zinc-900">
            <CardHeader>
              <CardTitle className="text-base text-zinc-100">{workflow.label}</CardTitle>
              <p className="text-sm text-zinc-400">{workflow.description}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <CopyCommandBlock
                label={`${workflow.label} — combined`}
                description="Run the whole workflow in one shell sequence."
                command={workflow.combinedCommand}
              />
              <div className="grid gap-3">
                {workflow.steps.map((step) => (
                  <CopyCommandBlock key={step.id} label={step.label} description={step.description} command={step.command} />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Guidance</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-zinc-300">
            {payload.guidance.map((line) => (
              <li key={line}>• {line}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader>
        <CardTitle className="text-base text-zinc-100">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-zinc-300">{value}</CardContent>
    </Card>
  );
}
