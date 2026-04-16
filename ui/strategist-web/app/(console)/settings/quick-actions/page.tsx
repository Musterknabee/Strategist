import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsQuickActions } from "@/lib/server/diagnostics-quick-actions";

export default async function DiagnosticsQuickActionsPage() {
  const payload = await buildFrontendDiagnosticsQuickActions();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / quick actions</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics quick actions</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Copy/paste-ready local commands for the most common frontend bring-up and diagnostics loops.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/quick-actions" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open quick-actions JSON</Link>
          <Link href="/settings/checklist" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open checklist</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard title="Total runs" value={String(payload.summary.totalRuns)} />
        <MetricCard title="Backend-connected" value={String(payload.summary.backendConnectedRuns)} />
        <MetricCard title="Latest posture" value={payload.summary.latestPosture ?? "no-history"} />
        <MetricCard title="Latest mode" value={payload.summary.latestMode ?? "unknown"} />
      </div>

      <div className="grid gap-6">
        {payload.groups.map((group) => (
          <Card key={group.id} className="border-zinc-800 bg-zinc-900">
            <CardHeader>
              <CardTitle className="text-base text-zinc-100">{group.label}</CardTitle>
              <p className="text-sm text-zinc-400">{group.description}</p>
            </CardHeader>
            <CardContent className="space-y-3">
              {group.commands.map((command) => (
                <CopyCommandBlock
                  key={command.label}
                  label={command.label}
                  description={command.description}
                  command={command.command}
                />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
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
