import Link from "next/link";
import type { Route } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { getFrontendDiagnosticsManifest } from "@/lib/diagnostics";
import { buildFrontendDiagnosticsIndex } from "@/lib/server/diagnostics-index";

export default async function SettingsIndexPage() {
  const manifest = getFrontendDiagnosticsManifest();
  const diagnosticsIndex = await buildFrontendDiagnosticsIndex();
  const summary = diagnosticsIndex.summary;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Total runs</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{summary.totalRuns}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Backend-connected</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{summary.backendConnectedRuns}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Mock-backed</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{summary.mockBackedRuns}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Latest posture</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{summary.latestPosture ?? "no-history"}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Latest mode</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{summary.latestMode ?? "unknown"}</CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {manifest.routes.map((item) => (
          <Link key={item.href} href={item.href as Route}>
            <Card className="h-full border-zinc-800 bg-zinc-900 transition hover:border-zinc-700">
              <CardHeader>
                <CardTitle className="text-base text-zinc-100">{item.label}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-zinc-400">{item.description}</CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">Recommended local commands</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {manifest.commands.slice(0, 4).map((command) => (
              <CopyCommandBlock key={command.label} label={command.label} description={command.description} command={command.command} />
            ))}
            <div className="flex flex-wrap gap-2">
              <Link href="/settings/quick-actions" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics quick actions
              </Link>
              <Link href="/settings/runbook" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics runbook
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-base text-zinc-100">End-to-end validation block</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <CopyCommandBlock
              label="Recommended sequence"
              description="Use this once you are ready to move from env bootstrap to smoke, typecheck/tests, and production build."
              command={diagnosticsIndex.recommendedValidationSequence}
            />
            <div className="space-y-2 text-sm text-zinc-300">
              {diagnosticsIndex.notes.map((note) => (
                <div key={note}>• {note}</div>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              <Link href="/api/ui/diagnostics/index" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics index JSON
              </Link>
              <Link href="/settings/summary" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics summary
              </Link>
              <Link href="/settings/trends" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics trends
              </Link>
              <Link href="/settings/compare" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Compare latest vs summary
              </Link>
              <Link href="/settings/status-board" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics status board
              </Link>
              <Link href="/settings/recommendations" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open diagnostics recommendations
              </Link>
              <Link href="/settings/escalation-matrix" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open escalation matrix
              </Link>
              <Link href="/settings/incident-playbook" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open incident playbook
              </Link>
              <Link href="/settings/recovery-scorecard" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open recovery scorecard
              </Link>
              <Link href="/settings/readiness-gate" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open readiness gate
              </Link>
              <Link href="/settings/decision-log" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open decision log
              </Link>
              <Link href="/settings/handoff-packet" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open handoff packet
              </Link>
              <Link href="/settings/checkpoint-register" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open checkpoint register
              </Link>
              <Link href="/settings/certification-manifest" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open certification manifest
              </Link>
              <Link href="/settings/release-candidate-dossier" className="inline-flex rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                Open release-candidate dossier
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
