import Link from "next/link";
import type { Route } from "next";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsCertificationManifest } from "@/lib/server/diagnostics-certification-manifest";

export default async function CertificationManifestPage() {
  const report = await buildFrontendDiagnosticsCertificationManifest();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">diagnostics certification manifest</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Final local attestation</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Final go / conditional / withhold certification derived from readiness, decision posture, handoff packet,
            and checkpoint alignment.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{report.certificationId}</Badge>
          <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{report.certificationLevel}</Badge>
          <Link
            href="/api/ui/diagnostics/certification-manifest"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Certification JSON
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard title="Certification" value={report.certificationLevel} subtitle={report.attestation} />
        <SummaryCard title="Latest posture" value={report.latest?.posture ?? "unknown"} subtitle={report.latest?.mode ?? "unknown"} />
        <SummaryCard title="Readiness" value={report.readiness.decision.level} subtitle={report.readiness.decision.rationale} />
        <SummaryCard title="Decision pressure" value={`${report.decisionLog.summary.totalEntries}`} subtitle={`hold=${report.decisionLog.summary.holdEntries} stabilize=${report.decisionLog.summary.stabilizeEntries}`} />
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base">Certification attestation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-zinc-300">
          <p>{report.attestation}</p>
          <CopyCommandBlock
            label="Finalize validation block"
            description="Copy the final sequence recommended by the certification manifest."
            command={report.finalizeSequence}
          />
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base">Certification checks</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {report.certificationChecks.map((check) => (
            <div key={check.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="text-sm font-medium text-zinc-100">{check.label}</div>
                  <div className="mt-1 text-sm text-zinc-400">{check.detail}</div>
                </div>
                <Badge className="border-zinc-700 bg-zinc-900 text-zinc-300">{check.status}</Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link href={check.route as Route} className="rounded-full border border-zinc-700 bg-zinc-900 px-3 py-2 text-xs text-zinc-300 transition hover:border-zinc-600 hover:text-white">
                  Open supporting route
                </Link>
              </div>
              {check.command ? (
                <div className="mt-4">
                  <CopyCommandBlock label="Suggested command" command={check.command} />
                </div>
              ) : null}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base">Related surfaces</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 text-sm">
          {[
            ["/settings/readiness-gate", "Readiness gate"],
            ["/settings/decision-log", "Decision log"],
            ["/settings/handoff-packet", "Handoff packet"],
            ["/settings/checkpoint-register", "Checkpoint register"],
            ["/settings/recovery-scorecard", "Recovery scorecard"],
            ["/settings/release-candidate-dossier", "Release-candidate dossier"],
          ].map(([href, label]) => (
            <Link key={href} href={href as Route} className="rounded-full border border-zinc-700 bg-zinc-950 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white">
              {label}
            </Link>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base">Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {report.notes.map((note) => (
            <div key={note} className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
              {note}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({ title, value, subtitle }: { title: string; value: string; subtitle: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-zinc-300">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold text-zinc-100">{value}</div>
        <div className="mt-1 text-xs text-zinc-500">{subtitle}</div>
      </CardContent>
    </Card>
  );
}
