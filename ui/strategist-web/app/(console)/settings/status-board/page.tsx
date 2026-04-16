import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsStatusBoard } from "@/lib/server/diagnostics-status-board";

export default async function DiagnosticsStatusBoardPage() {
  const board = await buildFrontendDiagnosticsStatusBoard();
  const latest = board.latest;
  const summary = board.summary;
  const trends = board.trends;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard title="Latest posture" value={latest?.posture ?? "no-history"} />
        <MetricCard title="Latest mode" value={latest?.mode ?? "unknown"} />
        <MetricCard title="Total runs" value={String(summary.totalRuns)} />
        <MetricCard title="Warning pressure" value={board.compare.warningPressure} />
        <MetricCard title="Trend buckets" value={String(trends.trendPoints.length)} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board JSON</Link>
        <Link href="/settings/compare" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open compare</Link>
        <Link href="/settings/trends" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open trends</Link>
        <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue</Link>
        <Link href="/settings/recommendations" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recommendations</Link>
        <Link href="/settings/escalation-matrix" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open escalation matrix</Link>
        <Link href="/settings/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook</Link>
        <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
        <Link href="/settings/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Status board notes</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm text-zinc-300">
            {board.statusNotes.map((note) => <div key={note}>• {note}</div>)}
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Maintenance loop</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <CopyCommandBlock label="Recurring maintenance sequence" description="Use this once the shell is already bootstrapped and you want to check current posture, export a run, summarize it, and keep local history tidy." command={board.maintenanceLoop} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <MetricDetailCard title="Summary posture" lines={[`Latest summary posture: ${summary.latestPosture ?? 'unknown'}`, `Backend-connected runs: ${summary.backendConnectedRuns}`, `Mock-backed runs: ${summary.mockBackedRuns}`]} />
        <MetricDetailCard title="Compare alignment" lines={[`Posture aligned: ${board.compare.postureAligned ? 'yes' : 'no'}`, `Mode aligned: ${board.compare.modeAligned ? 'yes' : 'no'}`, `Latest export: ${summary.latestExportId ?? 'none'}`]} />
        <MetricDetailCard title="Trend window" lines={[`Earliest: ${trends.earliestDate ?? 'n/a'}`, `Latest: ${trends.latestDate ?? 'n/a'}`, `Total tracked exports: ${trends.totalEntries}`]} />
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader><CardTitle className="text-base text-zinc-100">{title}</CardTitle></CardHeader>
      <CardContent className="text-sm text-zinc-300">{value}</CardContent>
    </Card>
  );
}

function MetricDetailCard({ title, lines }: { title: string; lines: string[] }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader><CardTitle className="text-base text-zinc-100">{title}</CardTitle></CardHeader>
      <CardContent className="space-y-1 text-sm text-zinc-300">{lines.map((line) => <div key={line}>{line}</div>)}</CardContent>
    </Card>
  );
}
