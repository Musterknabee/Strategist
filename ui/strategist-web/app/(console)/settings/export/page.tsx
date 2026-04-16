import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { buildDiagnosticsExportSnapshot } from "@/lib/server/diagnostics-export";
import { readFrontendDiagnosticsHistory, readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";
import type { FrontendPreflightCheck } from "@/lib/server/preflight";

export const dynamic = "force-dynamic";

export default async function DiagnosticsExportPage() {
  const snapshot = await buildDiagnosticsExportSnapshot();
  const history = await readFrontendDiagnosticsHistory(8);
  const latest = await readLatestFrontendDiagnosticsHistoryEntry();
  const preflightPosture = snapshot.preflight.checks.every((probe) => probe.ok) ? "ready" : "attention";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / export</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics export</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Single-snapshot diagnostics view for runtime posture, preflight status, and local bring-up guidance.
          </p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/api/ui/diagnostics/export"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open JSON export
          </Link>
          <Link
            href="/settings/history"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open history page
          </Link>
          <Link
            href="/settings"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Back to settings
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Mode</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{snapshot.mode}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Generated</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{snapshot.generatedAt}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Preflight posture</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{preflightPosture}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Export metadata</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-zinc-300">
            <div>ID: {snapshot.exportId}</div>
            <div>Routes: {snapshot.metadata.routeCount}</div>
            <div>Commands: {snapshot.metadata.commandCount}</div>
            <div>Warnings: {snapshot.metadata.warningCount}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Latest history</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-zinc-300">
            <div>ID: {latest?.exportId ?? "none"}</div>
            <div>Posture: {latest?.posture ?? "no-history"}</div>
          </CardContent>
        </Card>
      </div>


      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base text-zinc-100">Recent export history</CardTitle></CardHeader>
        <CardContent className="space-y-2">
          {history.length ? (
            history.map((entry) => (
              <div key={`${entry.exportId}-${entry.generatedAt}`} className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-sm text-zinc-300">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-medium text-zinc-100">{entry.exportId}</div>
                  <div className="text-xs text-zinc-400">{entry.generatedAt}</div>
                </div>
                <div className="mt-2 grid gap-2 md:grid-cols-3">
                  <div>Mode: {entry.mode}</div>
                  <div>Posture: {entry.posture}</div>
                  <div>Probes: {entry.probeCount}</div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3 text-sm text-zinc-400">
              No local diagnostics history yet. Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> to append a local history entry.
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base text-zinc-100">Notes</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {snapshot.notes.map((note) => (
            <div key={note} className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">{note}</div>
          ))}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Runtime summary</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm text-zinc-300">
            <div>Environment: {snapshot.runtime.environment}</div>
            <div>Read-plane: {snapshot.runtime.read_plane.status}</div>
            <div>Backend: {snapshot.runtime.backend.status}</div>
            <div>Providers enabled: {snapshot.runtime.providers.enabled_count}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Preflight probes</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm text-zinc-300">
            {snapshot.preflight.checks.map((probe: FrontendPreflightCheck) => (
              <div key={probe.id} className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
                <div className="font-medium text-zinc-100">{probe.label}</div>
                <div>Status: {probe.ok ? "ok" : "fail"}</div>
                <div>Duration: {probe.duration_ms} ms</div>
                <div className="text-zinc-400">{probe.detail}</div>
              </div>
            ))}
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Export metadata</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-zinc-300">
            <div>ID: {snapshot.exportId}</div>
            <div>Routes: {snapshot.metadata.routeCount}</div>
            <div>Commands: {snapshot.metadata.commandCount}</div>
            <div>Warnings: {snapshot.metadata.warningCount}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Latest history</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-zinc-300">
            <div>ID: {latest?.exportId ?? "none"}</div>
            <div>Posture: {latest?.posture ?? "no-history"}</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
