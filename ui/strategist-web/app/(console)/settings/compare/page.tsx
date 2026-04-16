import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buildFrontendDiagnosticsCompare } from "@/lib/server/diagnostics-compare";

export default async function DiagnosticsComparePage() {
  const compare = await buildFrontendDiagnosticsCompare();
  const latest = compare.latest;
  const summary = compare.summary;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / compare</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Latest vs summary</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Compare the most recent diagnostics export against the aggregate summary derived from the local diagnostics history trail.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/compare" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open compare JSON</Link>
          <Link href="/settings/latest" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open latest</Link>
          <Link href="/settings/summary" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open summary</Link>
          <Link href="/settings/trends" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open trends</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <CompareMetric title="Latest posture" value={latest?.posture ?? "no-history"} />
        <CompareMetric title="Summary posture" value={summary.latestPosture ?? "no-history"} />
        <CompareMetric title="Posture aligned" value={compare.postureAligned ? "yes" : "no"} />
        <CompareMetric title="Latest mode" value={latest?.mode ?? "unknown"} />
        <CompareMetric title="Summary mode" value={summary.latestMode ?? "unknown"} />
        <CompareMetric title="Warning pressure" value={compare.warningPressure} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Latest snapshot</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            {latest ? (
              <>
                <div className="grid gap-3 md:grid-cols-2">
                  <InfoBlock label="Export id" value={latest.exportId} />
                  <InfoBlock label="Generated" value={latest.generatedAt} />
                  <InfoBlock label="Runtime env" value={latest.runtimeEnvironment ?? "unknown"} />
                  <InfoBlock label="Warnings" value={String(latest.warningCount ?? 0)} />
                </div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-xs text-zinc-400">
                  Latest URL: {latest.url ?? "n/a"}
                </div>
              </>
            ) : (
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">
                No diagnostics history yet. Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> first.
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Aggregate summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            <div className="grid gap-3 md:grid-cols-2">
              <InfoBlock label="Total runs" value={String(summary.totalRuns)} />
              <InfoBlock label="Backend-connected" value={String(summary.backendConnectedRuns)} />
              <InfoBlock label="Mock-backed" value={String(summary.mockBackedRuns)} />
              <InfoBlock label="Warning runs" value={String(summary.warningRuns)} />
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-xs text-zinc-400">
              Summary posture is derived from local diagnostics history, not direct live runtime state.
                          <Link href="/settings/status-board" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open status board
              </Link>
              <Link href="/settings/recommendations" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open recommendations</Link>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Comparison notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {compare.notes.map((note) => (
            <div key={note}>• {note}</div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function CompareMetric({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader>
        <CardTitle className="text-base text-zinc-100">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-sm text-zinc-300">{value}</CardContent>
    </Card>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
      <div className="text-xs uppercase tracking-[0.16em] text-zinc-500">{label}</div>
      <div className="mt-2 text-zinc-100">{value}</div>
    </div>
  );
}
