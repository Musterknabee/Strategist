import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buildFrontendDiagnosticsSummary } from "@/lib/server/diagnostics-summary";

export default async function DiagnosticsSummaryPage() {
  const summary = await buildFrontendDiagnosticsSummary();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / summary</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics summary</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Aggregate view of recent local frontend diagnostics exports. Use this page when you want posture trends before drilling into full history.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/summary" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open summary JSON</Link>
          <Link href="/settings/history" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open history</Link>
          <Link href="/settings/quick-actions" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open quick actions</Link>
          <Link href="/settings/trends" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open trends</Link>
          <Link href="/settings/compare" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Compare latest vs summary</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard title="Total runs" value={String(summary.totalRuns)} />
        <MetricCard title="Backend-connected" value={String(summary.backendConnectedRuns)} />
        <MetricCard title="Mock-backed" value={String(summary.mockBackedRuns)} />
        <MetricCard title="OK" value={String(summary.okRuns)} />
        <MetricCard title="Warnings" value={String(summary.warningRuns)} />
        <MetricCard title="Attention" value={String(summary.attentionRuns)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Latest aggregate posture</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Latest export</div>
                <div className="mt-2 text-zinc-100">{summary.latestExportId ?? "no-history"}</div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Latest mode</div>
                <div className="mt-2 text-zinc-100">{summary.latestMode ?? "unknown"}</div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Latest posture</div>
                <div className="mt-2 text-zinc-100">{summary.latestPosture ?? "unknown"}</div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Generated</div>
                <div className="mt-2 text-zinc-100">{summary.latestGeneratedAt ?? "n/a"}</div>
              </div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-xs text-zinc-400">
              Summary is derived from the local diagnostics history trail, not from live backend state directly.
                          <Link href="/settings/status-board" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open status board
              </Link>
              <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 hover:bg-zinc-800 text-zinc-200">Open action queue</Link>
        <Link href="/settings/recommendations" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open recommendations</Link>
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Posture breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            {summary.postureBreakdown.length ? (
              summary.postureBreakdown.map((row) => (
                <div key={row.posture} className="flex items-center justify-between rounded-2xl border border-zinc-800 bg-zinc-950/60 p-3">
                  <span>{row.posture}</span>
                  <span className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-300">{row.count}</span>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">
                No local diagnostics history yet. Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> first.
              </div>
            )}
          </CardContent>
        </Card>
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
