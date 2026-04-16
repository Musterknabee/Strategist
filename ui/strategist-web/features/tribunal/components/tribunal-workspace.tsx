"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { UiTribunalWorkspace } from "@/lib/contracts/ui";
import { SectionProvenanceCard } from "@/features/shared/components/section-provenance-card";
import { MetricEvidenceHint } from "@/features/shared/components/metric-evidence-hint";

export function TribunalWorkspace({ data }: { data: UiTribunalWorkspace }) {
  const workflows = Object.values(data.agent_workflows);
  const thesisNodes = data.thesis_graph.nodes;
  const thesisEdges = data.thesis_graph.edges;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 lg:grid-cols-4">
        <Metric title="Blindness posture" value={data.blindness.mode} />
        <Metric title="Active doctrine" value={String(data.doctrine_stats.active_doctrine_count)} />
        <Metric title="Sealed history" value={String(data.doctrine_stats.sealed_history_count)} />
        <Metric title="Graph density" value={data.doctrine_stats.graph_density_label} />
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="flex items-center justify-between gap-3 text-base">
            <span>Tribunal blindness posture</span>
            <Badge className="border-amber-500/30 bg-amber-500/10 text-amber-300">
              {data.blindness.mode}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-zinc-300">
          <div>{data.blindness.operator_message}</div>
          <div className="flex flex-wrap gap-2">
            {data.blindness.forbidden_metric_families.map((metric) => (
              <Badge key={metric} variant="outline" className="border-zinc-700 text-zinc-300">
                {metric}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base">Agent workflows</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {workflows.map((workflow) => (
              <div key={workflow.stage} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-zinc-100">{workflow.stage}</div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-300">{workflow.status}</Badge>
                </div>
                <div className="mt-2 text-sm text-zinc-400">{workflow.summary_line}</div>
                <div className="mt-3 text-xs uppercase tracking-wide text-zinc-500">Prompt law</div>
                <div className="mt-1 text-sm text-zinc-300">{workflow.prompt_law}</div>
              </div>
            ))}
          </CardContent>
        </Card>
        <SectionProvenanceCard title="Workflow provenance" provenance={data.section_provenance.agent_workflows} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 text-base">
              <span>Prompt evaluations</span>
              <MetricEvidenceHint label="prompt provenance" provenance={data.section_provenance.agent_workflows} />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.prompt_evaluations.map((evaluation) => (
              <div key={evaluation.evaluation_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-zinc-100">{evaluation.stage}</div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-300">{evaluation.status}</Badge>
                </div>
                <div className="mt-2 text-xs uppercase tracking-wide text-zinc-500">Constraint</div>
                <div className="mt-1 text-sm text-zinc-300">{evaluation.constraint}</div>
                <div className="mt-2 text-sm text-zinc-400">{evaluation.summary_line}</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 text-base">
              <span>Falsification checks</span>
              <MetricEvidenceHint label="falsification provenance" provenance={data.section_provenance.doctrine_memory} />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.falsification_checks.map((check) => (
              <div key={check.check_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-zinc-100">{check.check_id}</div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-300">{check.status}</Badge>
                </div>
                <div className="mt-2 text-sm text-zinc-400">{check.summary_line}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr_0.9fr]">
        <Card className="border-zinc-800 bg-zinc-900 xl:col-span-1">
          <CardHeader><CardTitle className="text-base">Sealed history</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {data.sealed_history.map((entry) => (
              <div key={entry.event_id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-zinc-100">{entry.event_id}</div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-300">{entry.forensic_status}</Badge>
                </div>
                <div className="mt-2 flex items-center justify-between gap-3 text-sm text-zinc-400">
                  <span>{entry.summary_line}</span>
                  <MetricEvidenceHint label="evidence" provenance={data.section_provenance.doctrine_memory} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900 xl:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 text-base">
              <span>Doctrine memory</span>
              <MetricEvidenceHint label="doctrine evidence" provenance={data.section_provenance.doctrine_memory} />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.doctrine_memory.map((entry) => (
              <div key={entry.doctrine_key} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-semibold text-zinc-100">{entry.doctrine_key}</div>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-300">{entry.adaptation_status}</Badge>
                </div>
                <div className="mt-2 text-sm text-zinc-400">{entry.summary_line}</div>
              </div>
            ))}
          </CardContent>
        </Card>

        <SectionProvenanceCard title="Doctrine provenance" provenance={data.section_provenance.doctrine_memory} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="flex items-center justify-between gap-3 text-base">
              <span>Thesis graph</span>
              <MetricEvidenceHint label="graph evidence" provenance={data.section_provenance.thesis_graph} />
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-3 md:grid-cols-3">
              {thesisNodes.map((node) => (
                <div key={node.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                  <div className="flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-zinc-500"><span>{node.kind}</span><MetricEvidenceHint label="node" provenance={data.section_provenance.thesis_graph} /></div>
                  <div className="mt-2 text-sm font-semibold text-zinc-100">{node.label}</div>
                </div>
              ))}
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
              <div className="mb-3 text-xs uppercase tracking-wide text-zinc-500">Inference edges</div>
              <div className="space-y-2">
                {thesisEdges.map((edge, idx) => (
                  <div key={`${edge.source}-${edge.target}-${idx}`} className="flex items-center justify-between gap-3 rounded-xl border border-zinc-800 px-3 py-2 text-sm text-zinc-300">
                    <span><span className="font-medium text-zinc-100">{edge.source}</span> → <span className="font-medium text-zinc-100">{edge.target}</span></span>
                    <div className="flex items-center gap-2">
                      <MetricEvidenceHint label="edge" provenance={data.section_provenance.thesis_graph} />
                      <Badge variant="outline" className="border-zinc-700 text-zinc-300">{edge.relation}</Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
        <SectionProvenanceCard title="Thesis graph provenance" provenance={data.section_provenance.thesis_graph} />
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
