import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsTrends } from "@/lib/server/diagnostics-trends";

export default async function DiagnosticsTrendsPage() {
  const trends = await buildFrontendDiagnosticsTrends();
  const latestPoint = trends.trendPoints[trends.trendPoints.length - 1] ?? null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / trends</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics trends</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">Daily posture and mode trend buckets derived from local diagnostics history.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/trends" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open trends JSON</Link>
          <Link href="/settings/summary" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open summary</Link>
          <Link href="/settings/history" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open history</Link>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard title="Window size" value={String(trends.windowSize)} />
        <MetricCard title="History entries" value={String(trends.totalEntries)} />
        <MetricCard title="Trend points" value={String(trends.trendPoints.length)} />
        <MetricCard title="Earliest date" value={trends.earliestDate ?? "n/a"} />
        <MetricCard title="Latest date" value={trends.latestDate ?? "n/a"} />
      </div>
      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Trend window</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            {trends.trendPoints.length ? trends.trendPoints.map((point) => (
              <div key={point.date} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-medium text-zinc-100">{point.date}</div>
                  <div className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-300">{point.totalRuns} runs</div>
                </div>
                <div className="mt-3 grid gap-2 md:grid-cols-3 xl:grid-cols-6 text-xs text-zinc-400">
                  <div>Backend: {point.backendConnectedRuns}</div><div>Mock: {point.mockBackedRuns}</div><div>OK: {point.okRuns}</div><div>Warnings: {point.warningRuns}</div><div>Attention: {point.attentionRuns}</div><div>Total: {point.totalRuns}</div>
                </div>
              </div>
            )) : <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">No local diagnostics history yet. Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> first.</div>}
          </CardContent>
        </Card>
        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base text-zinc-100">Latest trend bucket</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-zinc-300">
              {latestPoint ? <>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Date</div><div className="mt-2 text-zinc-100">{latestPoint.date}</div></div>
                <div className="grid gap-3 md:grid-cols-2"><SmallCard title="Backend" value={String(latestPoint.backendConnectedRuns)} /><SmallCard title="Mock" value={String(latestPoint.mockBackedRuns)} /><SmallCard title="Warnings" value={String(latestPoint.warningRuns)} /><SmallCard title="Attention" value={String(latestPoint.attentionRuns)} /></div>
              </> : <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">No recent trend bucket available yet.</div>}
            </CardContent>
          </Card>
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base text-zinc-100">Maintenance loop</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <CopyCommandBlock label="Trend-aware maintenance loop" description="Export a fresh snapshot, review trends, then prune diagnostics history deliberately." command={["npm run export:diagnostics","npm run summarize:diagnostics","npm run prune:diagnostics"].join(" && ")} />
              <div className="space-y-2 text-sm text-zinc-300">{trends.notes.map((note) => <div key={note}>• {note}</div>)}</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
function MetricCard({ title, value }: { title: string; value: string }) { return <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">{title}</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{value}</CardContent></Card>; }
function SmallCard({ title, value }: { title: string; value: string }) { return <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">{title}</div><div className="mt-2 text-zinc-100">{value}</div></div>; }
