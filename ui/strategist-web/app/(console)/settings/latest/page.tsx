import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

export default async function DiagnosticsLatestPage() {
  const latest = await readLatestFrontendDiagnosticsHistoryEntry();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / latest</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Latest diagnostics snapshot</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Quick view of the most recent local frontend diagnostics export. Use this page when you want the current posture without scanning the full history.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/latest" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open latest JSON</Link>
          <Link href="/settings/history" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open history</Link>
          <Link href="/settings/trends" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open trends</Link>
          <Link href="/settings/compare" className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Compare latest vs summary</Link>
        </div>
      </div>

      {latest ? (
        <>
          <div className="grid gap-4 md:grid-cols-5">
            <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Export id</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{latest.exportId}</CardContent></Card>
            <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Mode</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{latest.mode}</CardContent></Card>
            <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Posture</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{latest.posture}</CardContent></Card>
            <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Warnings</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{latest.warningCount ?? 0}</CardContent></Card>
            <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Generated</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{latest.generatedAt}</CardContent></Card>
          </div>

          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base text-zinc-100">Latest run detail</CardTitle></CardHeader>
            <CardContent className="space-y-4 text-sm text-zinc-300">
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Runtime env</div><div className="mt-2 text-zinc-100">{latest.runtimeEnvironment ?? "unknown"}</div></div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Status</div><div className="mt-2 text-zinc-100">{latest.status ?? "n/a"}</div></div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Probe count</div><div className="mt-2 text-zinc-100">{latest.probeCount ?? 0}</div></div>
                <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4"><div className="text-xs uppercase tracking-[0.16em] text-zinc-500">Notes</div><div className="mt-2 text-zinc-100">{latest.notesCount ?? 0}</div></div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-xs text-zinc-400">
                <div>Latest URL: {latest.url ?? "n/a"}</div>
                <div className="mt-1">Use <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">/settings/history</code> for filtered review or <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> to append a fresh local run.</div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">No diagnostics history yet</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-400">
            <p>Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> to generate the first local frontend diagnostics snapshot.</p>
            <div className="flex flex-wrap gap-2">
              <Link href="/settings/checklist" className="rounded-full border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open setup checklist</Link>
              <Link href="/settings/export" className="rounded-full border border-zinc-700 bg-zinc-950 px-3 py-2 text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open diagnostics export</Link>
                          <Link href="/settings/status-board" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open status board
              </Link>
              <Link href="/settings/recommendations" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">Open recommendations</Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
