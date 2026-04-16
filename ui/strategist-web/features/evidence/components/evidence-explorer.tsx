"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { UiEvidenceDashboard } from "@/lib/contracts/ui";
import { SectionProvenanceCard } from "@/features/shared/components/section-provenance-card";

export function EvidenceExplorer({ data }: { data: UiEvidenceDashboard }) {
  const checklist = data.daily_checklist as Record<string, unknown>;
  const review = data.runtime_review as Record<string, unknown>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-4">
        <Metric title="Trust status" value={data.verification.trust_status} />
        <Metric title="Seal status" value={data.verification.seal_status} />
        <Metric title="Artifacts" value={String(data.registry.source_artifact_count)} />
        <Metric title="Lineage completeness" value={`${data.verification.completeness_percent}%`} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_1fr]">
        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader>
              <CardTitle className="text-base">Artifact registry</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.registry.source_artifacts.map((artifact) => (
                <div key={`${artifact.artifact_label}-${artifact.path}`} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-zinc-100">{artifact.artifact_label}</div>
                      <div className="mt-1 break-all text-xs text-zinc-500">{artifact.path}</div>
                    </div>
                    <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                      {artifact.exists ? "present" : "missing"}
                    </Badge>
                  </div>
                  <div className="mt-3 grid gap-3 text-xs text-zinc-400 md:grid-cols-3">
                    <div>sha256<div className="mt-1 break-all text-zinc-300">{artifact.sha256 ?? "n/a"}</div></div>
                    <div>size bytes<div className="mt-1 text-zinc-300">{artifact.size_bytes ?? "n/a"}</div></div>
                    <div>modified<div className="mt-1 text-zinc-300">{artifact.modified_at_utc ?? "n/a"}</div></div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          <SectionProvenanceCard title="Registry provenance" provenance={data.section_provenance.registry} />
        </div>

        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base">Verification posture</CardTitle></CardHeader>
            <CardContent className="space-y-3 text-sm text-zinc-300">
              <div>{data.verification.lineage_reason}</div>
              <div className="flex flex-wrap gap-2">
                <Badge className="border-emerald-500/30 bg-emerald-500/10 text-emerald-300">
                  snapshot {data.verification.projection_snapshot_verified ? "verified" : "unverified"}
                </Badge>
                <Badge variant="outline" className="border-zinc-700 text-zinc-300">{data.registry.projection_digest_sha256}</Badge>
              </div>
              {data.verification.integrity_warnings.map((warning) => (
                <div key={warning} className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-amber-200">{warning}</div>
              ))}
            </CardContent>
          </Card>
          <SectionProvenanceCard title="Verification provenance" provenance={data.section_provenance.verification} />

          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base">Keyed host fingerprint</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm text-zinc-300">
              {data.host_fingerprint ? (
                <>
                  <div>Host: <span className="text-zinc-100">{data.host_fingerprint.host_label}</span></div>
                  <div>Runtime: <span className="text-zinc-100">{data.host_fingerprint.runtime_mode}</span></div>
                  <div>Config fingerprint: <span className="break-all text-zinc-100">{data.host_fingerprint.config_fingerprint}</span></div>
                  <div>Git: <span className="text-zinc-100">{data.host_fingerprint.git_tag ?? data.host_fingerprint.git_commit ?? "unknown"}</span></div>
                  <div className="pt-2 text-xs uppercase tracking-wide text-zinc-500">Present secret env keys</div>
                  <div className="flex flex-wrap gap-2">
                    {data.host_fingerprint.present_env_keys.map((key) => (
                      <Badge key={key} variant="outline" className="border-zinc-700 text-zinc-300">{key}</Badge>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-zinc-400">No keyed host fingerprint artifact found under the evidence search root.</div>
              )}
            </CardContent>
          </Card>
          <SectionProvenanceCard title="Host fingerprint provenance" provenance={data.section_provenance.host_fingerprint} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base">Daily checklist & runtime review</CardTitle></CardHeader>
            <CardContent className="grid gap-4 text-sm text-zinc-300 md:grid-cols-2">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Checklist</div>
                <div>Readiness: <span className="text-zinc-100">{String(checklist.readiness_status ?? "unknown")}</span></div>
                <div>Startup passed: <span className="text-zinc-100">{String(checklist.startup_check_passed ?? "unknown")}</span></div>
                <div>Provider availability: <span className="text-zinc-100">{String(checklist.provider_availability_ok ?? "unknown")}</span></div>
                <div>Fallback count: <span className="text-zinc-100">{String(checklist.fallback_count ?? 0)}</span></div>
                <div>Telemetry healthy: <span className="text-zinc-100">{String(checklist.telemetry_sink_healthy ?? "unknown")}</span></div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Runtime review</div>
                <div>Decision: <span className="text-zinc-100">{String(review.decision ?? "unknown")}</span></div>
                <div>Signoff: <span className="text-zinc-100">{String(review.signoff_status ?? "unknown")}</span></div>
                <div>Primary classification: <span className="text-zinc-100">{String(review.primary_classification ?? "unknown")}</span></div>
              </div>
            </CardContent>
          </Card>
          <SectionProvenanceCard title="Checklist / runtime provenance" provenance={data.section_provenance.checklist_runtime} />
        </div>

        <div className="space-y-6">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base">Lineage explorer</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="text-sm text-zinc-400">{data.lineage.summary_line}</div>
              {data.lineage.layers.map((layer) => (
                <div key={layer.layer} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-zinc-100">{layer.layer}</div>
                    <Badge variant="outline" className="border-zinc-700 text-zinc-300">{layer.count}</Badge>
                  </div>
                  <div className="mt-2 space-y-1 text-xs text-zinc-400">
                    {layer.sample_paths.length > 0 ? layer.sample_paths.map((path) => <div key={path}>{path}</div>) : <div>no indexed paths</div>}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
          <SectionProvenanceCard title="Lineage provenance" provenance={data.section_provenance.lineage} />
        </div>
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base">Operator guidance</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {data.operator_lines.map((line) => (
            <div key={line}>• {line}</div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">{title}</CardTitle></CardHeader>
      <CardContent><div className="text-lg font-semibold text-zinc-100">{value}</div></CardContent>
    </Card>
  );
}
